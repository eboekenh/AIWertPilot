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
