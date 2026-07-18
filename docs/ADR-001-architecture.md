# ADR-001 — Relational Evidence Graph + Optional Vector Retrieval

## Status

Accepted, Foundation Release 1.

## Context

The product must answer "which AI use cases fit this company, with what
evidence, and what's uncertain?" without ever inventing a fact. That rules
out an architecture where an LLM's own output is the system of record: LLM
generation is not reproducible, not auditable in the way a legal/compliance
reviewer needs, and cannot itself guarantee "no claim without evidence."

## Decision

Facts, relationships, and workflow state live in ordinary relational
tables (PostgreSQL 16) with explicit foreign keys, CHECK-constrained
enumerations, and unique constraints — the same 28-table shape as the root
`schema.sql`. Vector embeddings (`pgvector`, `document_chunks.embedding`)
exist only as a *retrieval aid* for a future search/recommendation feature
(Release 4) — never as the system of record for a fact, a claim, or a
recommendation. SQLAlchemy 2.x models plus Alembic migrations are the
executable source of truth after this implementation; `schema.sql` remains
the frozen, human-readable reference it was checked in as.

This gives the product exactly the properties `RESEARCH_PROTOCOL.md`
demands: conflicting evidence can coexist (`claim_evidence.relationship IN
('supports','contradicts','qualifies','context')`) instead of being
averaged away; every mutation is attributable (`audit_events`); a claim
cannot become `published` without a real evidence link
(`services/evidence.py`, enforced in the service layer *and* backed by the
relational shape that makes the check possible in the first place).

## Why Alembic migrations mirror `schema.sql` verbatim

`migrations/versions/0001_baseline_schema.py` is a statement-by-statement
copy of `schema.sql`'s DDL, not an ORM `autogenerate` diff. This makes the
migration trivially diffable against the frozen reference file — anyone
can `diff` the two side by side and see they match exactly — rather than
trusting that SQLAlchemy's autogenerate reproduced every CHECK constraint,
trigger, and index correctly.

## Documented deviations from `schema.sql`

All three are additive; none remove, narrow, or contradict anything in the
reference file.

### 1. `review_items.metadata jsonb NOT NULL DEFAULT '{}'::jsonb` (migration `0002`)

**Why:** `services/dedup.py`'s duplicate-candidate scanner needs to record
*which* other source a `dedup_candidate` review item is about, and the
similarity score that triggered it, so a reviewer sees that context
without re-running the scan. `schema.sql`'s `review_items` has no field
for this.

**Why JSONB and not new columns:** the payload is genuinely
supplemental/optional (only `dedup_candidate` items use it) and follows
the same `metadata jsonb` pattern `schema.sql` already uses on `sources`,
`source_snapshots`, `documents`, `funding_programs`, `research_jobs`, and
`audit_events`.

**What stays out of it:** every field a query needs to filter or sort on —
`entity_type`, `entity_id`, `review_type`, `status`, `priority`,
`assigned_to`, `decision_reason` — remains a plain, indexed column exactly
as in `schema.sql`. Nothing business-critical is hidden inside JSONB; see
`docs/DATA_DICTIONARY.md`'s `review_items` entry for the exact shape of
the metadata payload.

### 2. HNSW index on `document_chunks.embedding` (migration `0003`)

**Why HNSW and not IVFFlat:** IVFFlat's `lists` parameter needs to be
tuned against an existing row-count/distribution, and ideally the table
should already contain representative data before the index is built and
`ANALYZE`d. `document_chunks` is empty in this release (no ingestion
pipeline runs until Release 2), so there is no data to tune against yet.
HNSW builds incrementally with reasonable static defaults (`m=16,
ef_construction=64`) and doesn't need to be rebuilt once real data starts
arriving, making it the lower-risk choice to ship now rather than defer
index creation to a later migration.

**Operator class:** `vector_cosine_ops`, matching the cosine-similarity
ranking a future retrieval feature (Release 4) is expected to use.

### 3. Timezone-aware `datetime` mapping at the ORM base-class level

Not a schema change (every `schema.sql` timestamp column already is
`timestamptz`) but worth recording: `db/base.py` sets
`type_annotation_map = {datetime: DateTime(timezone=True)}` on the
declarative `Base`. Without it, SQLAlchemy infers a timezone-*naive*
`DateTime` from a bare `Mapped[datetime]` annotation, and asyncpg then
rejects binding a timezone-aware Python `datetime` (e.g.
`datetime.now(UTC)`) against it. This was caught by the integration test
suite (`test_review_and_audit.py`'s decision-recording test) before it
could reach any real deployment.

## Rejected alternatives

- **Native Postgres `ENUM` types** for the CHECK-constrained columns:
  rejected because `schema.sql` deliberately uses `text + CHECK` (adding a
  new allowed value to a native `ENUM` requires `ALTER TYPE ... ADD
  VALUE`, which cannot run inside a transaction in older Postgres and is
  generally more migration-friction than editing a CHECK list). The Python
  side still gets full type safety via `enum.StrEnum` mirrors, checked
  against the live CHECK constraints by
  `tests/unit/test_enum_constraint_lockstep.py`.
- **New lookup tables for `ai_patterns`/`outcome_types`/
  `capability_categories`:** considered and rejected for this release.
  `schema.sql` has no such tables, and RESEARCH_PROTOCOL.md's instruction
  that these vocabularies stay open is already satisfied by `use_cases`
  keeping them as free text/array columns — no `use_case` rows exist yet
  to justify governing that vocabulary with a table.
- **An extra `ix_sources_canonical_url` index:** considered and rejected.
  `schema.sql`'s `UNIQUE (canonical_url, publisher)` already indexes
  `canonical_url` as its leading column, which Postgres can use for a
  `canonical_url = ?` lookup; a second single-column index would be
  redundant without a concrete query plan proving otherwise.
