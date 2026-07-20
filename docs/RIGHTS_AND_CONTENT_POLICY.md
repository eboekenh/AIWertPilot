# Rights and Content Policy — Operational Notes

This is engineering policy, not legal advice (see `RESEARCH_PROTOCOL.md`
§10, which is authoritative on the substance). This page documents how
Foundation Release 1's code enforces that policy and where a human must
still decide.

## What the code enforces today

- **Conservative defaults, not overridable at creation.**
  `sources.access_policy` is always `metadata_only` and `rights_status` is
  always `needs_review` on every path that creates a source
  (`SourceRegistryService.create_source`, the seed importer, the API) —
  these are hardcoded in the service, not caller-supplied defaults.
  `SourceCreate` has no `status`/`rights_status`/`access_policy` fields
  (`extra="forbid"` turns an attempt to set them into a `422`), and
  `create_source()` has no parameters for them either, so there is no code
  path — API, CLI/seed-import, or a future direct service call — that can
  register a source that starts out published, reviewed, or full-text
  allowed. Nothing defaults to `full_text_allowed`.
- **No bypass of access controls.** `src/de_ai_kb/ingestion/fetcher.py` is
  an interface only — there is no code in this release that fetches a URL,
  so there is nothing that could bypass robots.txt, auth, or a paywall.
  This is intentional: Release 2 is scoped to build the compliant fetcher
  against an explicit domain allowlist.
- **Immutable snapshots.** Once a `source_snapshots` row exists, it cannot
  be altered (DB trigger `prevent_snapshot_update()` plus a repository
  that exposes no `update()`), so a retention/rights decision recorded at
  fetch time can't be quietly changed after the fact — a *new* snapshot is
  required to reflect a changed source.
- **Takedown/block mechanism.** `POST /api/v1/sources/{id}/block` (or
  `de-ai-kb sources block <source-key-or-id> --reason ...`) calls
  `SourceRegistryService.block_source(...)`, which requires a non-blank
  `reason` (a whitespace-only reason is rejected at both the request-schema
  and service layer, raising `ValidationFailedError` — a proper typed
  domain error, not a bare `ValueError`, so it surfaces as a clean `422`)
  and transitions `sources.status` to `blocked` via the same audited
  state-transition path as any other status change — the reason lands in
  `audit_events.after_state`, never silently discarded.
- **Lifecycle and rights fields are not editable through the generic PATCH
  route, or through re-importing the seed CSV.** `PATCH /api/v1/sources/{id}`
  only edits metadata (`title`, `publisher`, `tier`, `topic_tags`,
  `refresh_interval_days`, `notes`). `status`, `rights_status`, and
  `access_policy` can only change through
  `POST /api/v1/sources/{id}/transition`,
  `POST /api/v1/sources/{id}/block`, and
  `POST /api/v1/review-items/{id}/rights-decision` respectively.
  `SourceRegistryService.update_source()` enforces an explicit allowlist of
  editable fields itself (`EDITABLE_SOURCE_FIELDS`), so this protection
  holds even for a direct service call that bypasses the API/Pydantic
  layer entirely — not just for HTTP requests. The seed importer uses a
  separate, wider allowlist (`update_source_from_seed()` /
  `SEED_UPDATABLE_FIELDS`) that also covers `source_type`, `language_code`,
  `geography_codes`, and the URL pair, so a corrected CSV re-import isn't
  silently rejected — but it excludes the same rights/lifecycle fields for
  the same reason: a CSV's `access_policy` column is discovery-level
  metadata only and is never diffed or applied to an existing source, so a
  completed rights review can never be silently overwritten by a
  re-import. A URL change is canonicalized and checked for a
  `(canonical_url, publisher)` conflict before being applied, exactly as
  at creation time.
- **`/transition` cannot be used to block a source, and blocking always
  requires a reason.** `SourceTransitionRequest` rejects
  `new_status="blocked"` (`422`), and the `sources transition` CLI command
  rejects `--status blocked` (exit code 1) — both point the caller at
  `POST /api/v1/sources/{id}/block` / `sources block` instead. The service
  layer (`SourceRegistryService.transition_status()`) independently
  rejects any transition to `blocked` that lacks a non-blank `reason`,
  regardless of entry point.
- **A source cannot reach `fetched`/`approved`/`published` without
  completing its review items.** See "Review gates on status transitions"
  in `docs/RESEARCH_WORKFLOW.md` — `fetched` requires an approved,
  non-blocked `rights_review`; `approved`/`published` additionally require
  an approved `content_review`; and a rights decision that resolves to
  `blocked`/`blocked` atomically blocks the source's lifecycle status too,
  so a source can never be rights-blocked while still nominally
  progressing toward publication.
- **No personal data collected.** The domain model has no field for
  contact details, and nothing in this release ingests or stores personal
  data — `organizations`/`training_providers` model companies, not
  individuals.
- **API never exposes more than the rights policy allows.** `SourceRead`
  and other response schemas are built only from fields that are always
  metadata/bibliographic (title, publisher, URLs, tags, status); there is
  no route in this release that returns `document_chunks.permitted_text`
  or any other retained full-text content, so the "never expose full
  copyrighted text via the API" rule has nothing to violate yet — this
  will need explicit enforcement in the schema layer once Release 2/3 add
  routes that touch `document_chunks`.

## What remains a human/legal decision

- Actually performing the `rights_review` that every imported source
  receives as an open review item (robots.txt, terms of service, licence,
  TDM reservation, database-right risk) — the software tracks that this is
  pending; it does not perform the review.
- Any case where rights are ambiguous must be escalated to qualified
  German/EU counsel, per `RESEARCH_PROTOCOL.md` §10. The software has no
  mechanism to make that determination and does not attempt to.
- Deciding whether a specific source's `access_policy` may be upgraded
  from `metadata_only` to `short_evidence` or `full_text_allowed` — this
  requires a documented rights basis (explicit licence, public-domain
  status, owner permission) that only a human reviewer can establish and
  record via `POST /api/v1/review-items/{id}/rights-decision`, never via
  the generic PATCH route or the API/CLI defaults. The reviewed
  `rights_status`/`access_policy` pair is validated before it is applied
  (`domain/rights_policy.py`) — e.g. a `blocked` rights outcome can never
  be paired with `short_evidence` or `full_text_allowed` — but the
  underlying legal judgment of *which* outcome is correct remains the
  reviewer's, not the software's.

## Escalation cases to flag for legal review

- A source whose `tdm_opt_out_status` is `reserved` but whose content a
  future release wants to retain beyond `metadata_only`.
- A source under a licence whose terms are ambiguous about redistribution
  of paraphrased (not verbatim) summaries.
- Any request to un-block a source that was previously blocked with a
  takedown reason — should require the same or higher level of review as
  the original block decision.
