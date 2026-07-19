# Implementation Plan — Foundation Release 1

## Completed

- [x] Repository scaffolding (`pyproject.toml`, `.env.example`, `docker-compose.yml`, `alembic.ini`, `CLAUDE.md`, `README.md`).
- [x] `src/de_ai_kb/core`: settings (Pydantic Settings), structured JSON logging, typed domain exceptions.
- [x] `src/de_ai_kb/db`: declarative base with a stable naming convention and a
      `type_annotation_map` mapping `datetime` → `DateTime(timezone=True)`
      (every schema.sql timestamp column is `timestamptz`); async engine/session
      factory; SQLAlchemy 2.x models for all 28 `schema.sql` tables, split into
      11 modules by entity group.
- [x] `src/de_ai_kb/domain`: Python enum mirrors of every CHECK constraint,
      allowed state-transition tables for `sources.status` and
      `review_items.status`, URL canonicalization, freshness calculation,
      deterministic title-similarity scoring, slugify, and the
      RESEARCH_PROTOCOL.md §5 business-process seed vocabulary.
- [x] `migrations/`: `0001_baseline_schema.py` reproduces `schema.sql`
      verbatim (28 tables, 15 triggers, all indexes); `0002` and `0003` add
      the two documented, additive deviations (see
      `docs/ADR-001-architecture.md`).
- [x] `src/de_ai_kb/repositories`: thin CRUD per aggregate (sources,
      snapshots, quality evaluations, documents, claims/evidence, review
      items, audit events, business processes). Snapshot repository exposes
      no `update()`.
- [x] `src/de_ai_kb/services`: `SourceRegistryService`, `SeedImportService`,
      `ClaimsValidationService`, `ReviewService`, `DuplicateDetectionService`,
      `FreshnessService`, `EvidenceService`, `AuditService`,
      `TaxonomySeedService`.
- [x] `src/de_ai_kb/cli`: Typer CLI — `db check|init|migrate|seed-taxonomy`,
      `sources import|validate|duplicates|stale`, `review export`,
      `claims validate`.
- [x] `src/de_ai_kb/api`: FastAPI app with `GET /health`,
      `GET/POST /api/v1/sources`, `GET/PATCH /api/v1/sources/{id}`,
      `GET /api/v1/research/freshness`, `GET /api/v1/review-items`,
      `POST /api/v1/review-items/{id}/decision`; dev `X-API-Key` dependency
      on write routes; pagination + filtering; a consistent
      `{"error": {"code","message","details"}}` envelope for domain and
      validation errors.
- [x] `src/de_ai_kb/ingestion`: `Fetcher` protocol and `ObjectStorage`
      protocol + local-filesystem implementation. No live fetching.
- [x] Tests: 120 tests (unit + integration) covering URL canonicalization,
      freshness boundaries, deterministic duplicate similarity, the
      enum/CHECK-constraint lockstep, seed-source import (idempotency +
      malformed-row rejection), seed-claims validation (writes zero rows),
      source status transitions (valid + invalid), immutable snapshots,
      published-claim evidence requirement, review decisions + audit
      events, source-quality component bounds, dedup scanning (never
      merges, idempotent), taxonomy seeding, and API auth/pagination/
      filtering. All run against real PostgreSQL 16 + pgvector — never
      SQLite.
- [x] `uv run ruff check .`, `uv run mypy src`, `uv run pytest`,
      `docker compose config`, and an Alembic upgrade/downgrade/upgrade
      round trip all pass. See the top-level session report for exact
      commands and results.

## Deferred to later releases (see `docs/NEXT_RELEASES.md`)

- Real HTTP fetching, robots/terms/licence review automation, and change
  detection (Release 2).
- LLM-based extraction, claim/case-study/training candidate generation, and
  a reviewer UI (Release 3).
- Evidence search, company assessment, use-case matching, and the
  recommendation application (Release 4).
- Multi-tenancy, RBAC, SSO, and other commercial-product controls
  (Release 5).
- `document_chunks.embedding` has an HNSW index but no rows — nothing
  populates it in this release.
- `use_cases`, `case_studies`, `training_offerings`, `regulations`,
  `funding_programs`, and their taxonomy tables (`industries`,
  `capabilities`, non-seeded parts of `business_processes`) are modeled and
  migrated but intentionally have zero seed data, per "do not fabricate use
  cases, capabilities, industries, or other business records."

## Decision rationale highlights

- **Verbatim baseline migration.** `0001_baseline_schema.py` is a
  statement-by-statement copy of `schema.sql`'s DDL rather than an
  ORM-driven `autogenerate`, so the migration is trivially diffable against
  the frozen reference file and cannot silently drift from it.
- **`type_annotation_map` for `datetime`.** Discovered during integration
  testing: a bare `Mapped[datetime]` infers a timezone-naive
  `TIMESTAMP`, which asyncpg rejects once an aware `datetime.now(UTC)` is
  bound against it. Fixed once at the `Base` class rather than per-column.
- **Repository methods named `list` were renamed to `list_page`.** A method
  named `list` inside a class shadows the builtin `list` for every
  *subsequent* method's type annotations in that same class body under
  `from __future__ import annotations` + mypy's static resolution — this
  broke `list[Source]` return annotations on methods defined afterward.
  Renaming the paginated repository method sidesteps the shadow; the
  service-layer method can safely stay named `list` since nothing after it
  in that class references the builtin.

## Foundation Hardening Release 1.1 — Phase 1

An independent security/correctness review of the merged Foundation
Release 1 found that `PATCH /api/v1/sources/{id}` could set `status`,
`rights_status`, and `access_policy` directly, bypassing the state
machine and the rights-review workflow entirely, and that
`POST /api/v1/sources` never created the two standard review items the
CSV importer did. Phase 1 closes both:

- `SourceUpdate` no longer accepts `status`/`rights_status`/`access_policy`;
  unknown/removed fields return `422` (`extra="forbid"`).
  `SourceRegistryService.update_source()` enforces the same restriction via
  an explicit `EDITABLE_SOURCE_FIELDS` allowlist, so a direct service call
  gets the same protection as the HTTP API — not just the Pydantic schema.
- New `POST /api/v1/sources/{id}/transition` (`de-ai-kb sources
  transition`) is now the only way to change `status`; invalid transitions
  return `409`.
- New `POST /api/v1/sources/{id}/block` (`de-ai-kb sources block`) exposes
  the previously-unreachable takedown mechanism, with a mandatory
  non-blank `reason`.
- `SourceRegistryService.create_source()` now creates the two standard
  review items itself, so every source-registration entry point
  (API, CSV import, and any future one) gets them automatically — the
  CSV importer no longer duplicates this call.
- New `POST /api/v1/review-items/{id}/rights-decision` is the only way to
  approve a `rights_review` item; it requires an explicit reviewed
  `rights_status`/`access_policy` pair (validated by
  `domain/rights_policy.py`), applies it to the source atomically in the
  same transaction as the review decision, and is fully audited. The
  generic decision endpoint now rejects an attempt to approve a
  `rights_review` item with `422`.

## Foundation Hardening Release 1.1 — Phase 1 corrections

A second independent review of Phase 1's own implementation found that
several governance bypasses remained even after the changes above. These
corrections close them, on the same branch/PR:

- **Creation-time bypass closed.** `SourceCreate` no longer accepts
  `status`/`rights_status`/`access_policy` (`extra="forbid"`), and
  `SourceRegistryService.create_source()` no longer has parameters for
  them either — every new source is hardcoded to
  `status=registered`/`rights_status=needs_review`/
  `access_policy=metadata_only` in the service itself, not merely
  defaulted. Phase 1 had only locked this down for `PATCH`-time edits, not
  creation-time.
- **`/transition` can no longer reach `blocked`.**
  `SourceTransitionRequest` rejects `new_status="blocked"` (`422`), and
  `sources transition --status blocked` is rejected by the CLI before any
  DB access (exit code 1) — both direct the caller to `/block` /
  `sources block`, which is the only path that makes the reason mandatory.
  `SourceRegistryService.transition_status()` also independently rejects
  any BLOCKED transition without a non-blank reason, so this holds for a
  direct service call too, not just the two officially-supported entry
  points.
- **Review gates now actually gate.** Phase 1 fixed *how* rights get
  recorded but not *whether* a transition should be allowed based on
  review completion — a caller could still walk
  `registered → fetched → extracted → under_review → approved → published`
  without ever resolving either review item.
  `SourceRegistryService.transition_status()` now requires an approved,
  non-blocked `rights_review` to reach `fetched`, and both an approved
  `rights_review` and `content_review` to reach `approved`/`published`
  (`published` re-checks rather than trusting the earlier `approved`
  transition). A rights decision that resolves to `blocked`/`blocked` now
  also atomically blocks the source's lifecycle status, and the
  allowed-transition table already prevents a blocked source from
  reaching `fetched` or `published`.
- **`SeedImportService` dry-run/real-import consistency fixed.**
  `_diff_fields()` could produce fields (`source_type`, `language_code`,
  `geography_codes`, `original_url`, `canonical_url`) that the generic
  `update_source()` allowlist rejected, so a dry-run "would update"
  prediction could disagree with what a real import actually did. A new
  `update_source_from_seed()` / `SEED_UPDATABLE_FIELDS` allowlist on
  `SourceRegistryService` — wider than the API-facing one, but still
  excluding rights/lifecycle fields — is now used by the real-import path,
  and the dry-run path gained the same duplicate-conflict pre-check the
  real path already raised on, so both paths agree in all cases including
  URL changes and canonical-URL conflicts.
- **Rights decisions hardened.** `RightsReviewDecisionRequest.
  decision_reason` now rejects whitespace-only values (not just empty),
  and `ReviewService.resolve_rights_review()` independently re-checks the
  same rule plus `review_item.entity_type == "source"` before writing
  anything — a malformed or misrouted review item changes neither record.
- **Audit provenance fixed.** `create_source`/`update_source`/
  `transition_status`/`block_source` all now take an explicit
  `actor_type` parameter from their caller instead of inferring it by
  comparing the literal `actor_id` string to `"cli"` (which broke for any
  CLI caller using a custom `--actor` value). API routes pass
  `actor_type="api_key"`; the CLI and the seed importer pass
  `actor_type="cli"`.

See `docs/RESEARCH_WORKFLOW.md` and `docs/RIGHTS_AND_CONTENT_POLICY.md`
for the updated workflow, and the PR description for the full verification
report this phase was scoped from. Deliberately out of scope for this
phase: production auth, CI, ORM/index parity, general URL validation,
freshness query validation, dedup redesign, quality scoring, provenance
changes, object-storage hardening — tracked as separate follow-up phases.
