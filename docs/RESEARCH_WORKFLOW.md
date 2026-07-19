# Research Workflow — Foundation Release 1

The full discovery-to-publication workflow and its editorial rules are
defined in the root `RESEARCH_PROTOCOL.md` (§7, §11, §12) — that document
is authoritative and is not duplicated here. This page describes what
Foundation Release 1 actually implements of that workflow, and who does
what.

## What this release implements

```
discover -> register -> rights review -> [fetch -> parse -> extract -> deduplicate
        -> evidence review -> approve -> publish -> monitor -> supersede/archive]
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   implemented this release
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                        deferred — see docs/NEXT_RELEASES.md
```

1. **Discover.** Out of scope for automated tooling this release; the
   supplied `seed_sources.csv` (65 rows) is the discovery output of a
   manual research pass dated 2026-07-18.
2. **Register.** `de-ai-kb sources import --file data/seed_sources.csv`
   or `POST /api/v1/sources` creates a `sources` row with
   `status='registered'`. Registration means "candidate known," never
   "content verified" (master prompt §11) — every newly created source
   **always** starts at `access_policy='metadata_only'` and
   `rights_status='needs_review'`, with no way for a caller to override
   this at creation time: `SourceCreate` has no `status`/`rights_status`/
   `access_policy` fields at all (`extra="forbid"` rejects an attempt to
   send them with `422`), and `SourceRegistryService.create_source()` has
   no parameters for them either — the governed defaults are hardcoded in
   the service, not merely defaulted. Both entry points call the same
   `SourceRegistryService.create_source`, which is the single place the
   next step is guaranteed — no caller can register a source without it,
   and none can register one that starts pre-approved.
3. **Rights review + content review.** Every newly registered source, from
   any entry point, gets exactly two open `review_items` in the same
   transaction as its insert: `review_type='rights_review'` and
   `review_type='content_review'`. These are the human tasks that must
   complete before a source can legitimately progress toward
   `fetched`/`published`.
4. **Deduplicate (registry-level only).** `de-ai-kb sources duplicates`
   flags same-canonical-URL/different-publisher pairs and same-publisher
   near-duplicate titles (deterministic `difflib` similarity, threshold
   0.85) as `review_type='dedup_candidate'` review items. **Never merges
   automatically** — a human reviewer decides.
5. **Review decisions.**
   - Non-rights review items (`content_review`, `dedup_candidate`, and any
     non-approval outcome of a `rights_review`) use
     `POST /api/v1/review-items/{id}/decision`, which transitions
     `open→in_progress→approved|rejected|needs_changes|cancelled` and
     records `decision_reason` plus an `audit_events` row in the same
     transaction.
   - Approving a `rights_review` item **must** go through
     `POST /api/v1/review-items/{id}/rights-decision` instead (see
     "Rights review resolution" below) — the generic decision endpoint
     rejects an attempt to approve a `rights_review` item with a 422,
     specifically so a source's rights fields can never change as a side
     effect of an unrelated-looking decision call.
6. **Status transitions and takedowns.** A source's `status` changes only
   through `POST /api/v1/sources/{id}/transition` (or
   `de-ai-kb sources transition`), which enforces the allowed-transition
   table and is audited. `PATCH /api/v1/sources/{id}` can no longer set
   `status`, `rights_status`, or `access_policy` — it edits only generic
   metadata (`title`, `publisher`, `tier`, `topic_tags`,
   `refresh_interval_days`, `notes`); attempting to include a lifecycle or
   rights field in a `PATCH` body now returns `422`. A takedown/block uses
   `POST /api/v1/sources/{id}/block` (or `de-ai-kb sources block`), which
   requires a non-blank `reason`. `/transition` (and the `sources
   transition` CLI command) refuse `new_status=blocked` outright — request
   or request-schema validation rejects it with `422` (CLI: exit code 1) —
   so blocking always goes through `/block`, which is the only path that
   makes the reason mandatory rather than merely optional; the service
   layer enforces the same non-blank-reason rule for any BLOCKED
   transition a second time, independent of which entry point is used.
7. **Review gates on status transitions.** `SourceRegistryService.
   transition_status()` will not let a source advance past `registered`
   until the review workflow has actually been completed — not just
   *started*:
   - **`fetched`** requires the source's `rights_review` item to be
     `approved` (via `rights-decision`, never the generic decision
     endpoint) **and** the resulting `rights_status` to be a valid,
     non-blocked outcome (`reviewed_allowed` or `reviewed_restricted`).
   - **`approved`** and **`published`** both additionally require the
     `content_review` item to be `approved`. `published` re-runs the full
     check rather than trusting the earlier `approved` transition, so
     nothing between those two steps can silently invalidate the source's
     review state without being caught.
   - A rights decision that resolves to `rights_status='blocked'` **and**
     `access_policy='blocked'` doesn't just record that outcome — it also
     moves `sources.status` to `blocked` in the same transaction (both
     changes share one `audit_events` entry set), so a source can never be
     "rights-blocked but lifecycle-still-registered." Once blocked, the
     allowed-transition table (`SOURCE_STATUS_TRANSITIONS`) only permits
     `blocked → archived`, so a blocked source cannot be fetched or
     published by any path.
   - Any of these gate failures raises `ValidationFailedError` (`422`),
     with a message naming the missing requirement.

### Rights review resolution

Approving a `rights_review` item requires the reviewer to supply the
actual reviewed outcome — never inferred from the word "approved":

```
POST /api/v1/review-items/{id}/rights-decision
{
  "rights_status": "reviewed_allowed" | "reviewed_restricted" | "blocked",
  "access_policy": "metadata_only" | "short_evidence" | "full_text_allowed" | "blocked",
  "decision_reason": "...",
  "tdm_opt_out_status": "...",   // optional
  "licence_name": "...",         // optional
  "licence_url": "..."           // optional
}
```

The `rights_status`/`access_policy` pair is validated
(`domain/rights_policy.py`) before anything is written: `blocked` may only
pair with `access_policy="blocked"`, and `reviewed_restricted` may never
pair with `full_text_allowed`. `decision_reason` must be non-blank
(whitespace-only is rejected at both the request-schema and service
layer), and the review item must both be an open/in-progress
`rights_review` **and** belong to a source (`entity_type="source"`) — a
malformed or misrouted review item is rejected before any write. The
review-item decision and the source's rights fields are updated atomically
in one transaction — if any of these checks fail, **neither record
changes**. Both the review-item decision and the source policy change are
recorded as separate `audit_events` rows in that same transaction; a
blocked/blocked outcome additionally records a third `audit_events` row
for the resulting `source.status_transition` to `blocked` (see "Review
gates on status transitions" above).

### Audit provenance (`actor_type`)

Every audited mutation in `SourceRegistryService` (`create_source`,
`update_source`, `transition_status`, `block_source`) takes an explicit
`actor_type` parameter from its caller — it is never inferred from the
literal `actor_id` string. `POST /api/v1/sources*` routes always pass
`actor_type="api_key"`; the CLI (`sources import`, `sources transition`,
`sources block`) always passes `actor_type="cli"`. This means an operator
who runs `sources transition --actor alice` is correctly audited as a
`cli` actor named `alice`, not misclassified as an API caller because
their chosen `--actor` value happens not to be the literal string `"cli"`.

## What remains a human/future-release responsibility

- Fetch, parse, extract, and the rest of the pipeline through publish —
  Release 2/3 (see `docs/NEXT_RELEASES.md`).
- Actually performing the rights review and content review that this
  release's two auto-created review items request — a person (the
  founder/research administrator or a delegated reviewer) does this work;
  the software only tracks that it's pending.
- Resolving `dedup_candidate` items — a person decides whether two
  registered sources are truly the same underlying work, a new edition, or
  coincidentally similar.

## `seed_claims.csv` — validated, not published

`seed_claims.csv` (38 rows) is a first-pass evidence worksheet per
`RESEARCH_PROTOCOL.md` §12: *"The initial `seed_sources.csv` passes
discovery-level URL verification only. It does not pass \[the] publication
gates."* The same is true, more strongly, of `seed_claims.csv` — no
`source_snapshots`, `documents`, or `claim_evidence` rows exist yet to
anchor it to real evidence.

`de-ai-kb claims validate --file data/seed_claims.csv` checks structural
validity (required fields, numeric fields, `source_key` resolution against
the registered `sources`) and reports results, but **writes zero rows** to
`claims` or `claim_evidence`. See `docs/NEXT_RELEASES.md` for the planned
Release 2/3 import path that will create the snapshot/document/evidence
chain this worksheet is missing.

## Reviewer responsibilities (Foundation Release 1 scope)

| Role | Responsibility this release |
|---|---|
| Founder / research administrator | Curates `seed_sources.csv`/`seed_claims.csv`, runs imports, triages the review queue. |
| Rights/legal reviewer | Resolves `rights_review` items via `POST /api/v1/review-items/{id}/rights-decision`, supplying the actual reviewed `access_policy`/`rights_status`/`tdm_opt_out_status`; escalates unresolved legal questions to counsel per `docs/RIGHTS_AND_CONTENT_POLICY.md`. |
| Content/domain reviewer | Resolves `content_review` items: confirms the source's scope, tier, and topic tags are accurate. |
| Any reviewer | Resolves `dedup_candidate` items: approve (treat as duplicate, handle manually — no auto-merge exists) or reject (confirm they're genuinely distinct). |
