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
   (or `POST /api/v1/sources`) creates a `sources` row with
   `status='registered'`. Registration means "candidate known," never
   "content verified" (master prompt §11) — the `access_policy` default is
   `metadata_only` and `rights_status` defaults to `needs_review` unless
   explicitly overridden.
3. **Rights review + content review.** Every successfully imported source
   gets exactly two open `review_items` in the same transaction as its
   insert: `review_type='rights_review'` and `review_type='content_review'`.
   These are the human tasks that must complete before a source can
   legitimately progress toward `fetched`/`published`.
4. **Deduplicate (registry-level only).** `de-ai-kb sources duplicates`
   flags same-canonical-URL/different-publisher pairs and same-publisher
   near-duplicate titles (deterministic `difflib` similarity, threshold
   0.85) as `review_type='dedup_candidate'` review items. **Never merges
   automatically** — a human reviewer decides.
5. **Review decisions.** `POST /api/v1/review-items/{id}/decision` (or the
   equivalent service call) transitions a review item through
   `open→in_progress→approved|rejected|needs_changes|cancelled`, recording
   `decision_reason` and an `audit_events` row in the same transaction.

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
| Rights/legal reviewer | Resolves `rights_review` items: confirms `access_policy`/`rights_status`/`tdm_opt_out_status`, escalates unresolved legal questions to counsel per `docs/RIGHTS_AND_CONTENT_POLICY.md`. |
| Content/domain reviewer | Resolves `content_review` items: confirms the source's scope, tier, and topic tags are accurate. |
| Any reviewer | Resolves `dedup_candidate` items: approve (treat as duplicate, handle manually — no auto-merge exists) or reject (confirm they're genuinely distinct). |
