# AIWertPilot — Germany AI Knowledge Base

Foundation Release 1 of a structured, versioned, source-grounded evidence
system for German AI transformation decisions. This is a typed backend
(FastAPI + SQLAlchemy + PostgreSQL/pgvector), not a chatbot and not the
final recommendation product. See the six root specification files
(`START_HERE.md`, `CLAUDE_CODE_MASTER_PROMPT.md`, `RESEARCH_PROTOCOL.md`,
`schema.sql`, `seed_sources.csv`, `seed_claims.csv`) for the authoritative
product/engineering spec and editorial rules — they are never modified by
the application.

## Architecture summary

```
api/        FastAPI routers + Pydantic v2 schemas (HTTP boundary only)
cli/        Typer CLI — same services as the API, no duplicated logic
services/   Business rules, transactions, policy enforcement, audit emission
repositories/  Thin CRUD per aggregate, no business rules
db/models/  SQLAlchemy 2.x ORM, one module per schema.sql table group
domain/     Pure functions and enums: URL canonicalization, freshness, enums
ingestion/  Fetcher + object-storage interfaces only (no live fetching yet)
```

`schema.sql` (root, untouched) is the reference DDL. Alembic migrations
under `migrations/versions/` plus the SQLAlchemy models under
`src/de_ai_kb/db/models/` are the executable source of truth. Migration
`0001_baseline_schema.py` reproduces `schema.sql` verbatim (28 tables,
triggers, indexes); migrations `0002` and `0003` add the two documented,
additive deviations described in `docs/ADR-001-architecture.md`.

## Local setup

### Option A — Docker Compose (documented normal path)

```bash
cp .env.example .env
docker compose up -d db
uv sync
uv run alembic upgrade head
uv run de-ai-kb db seed-taxonomy
uv run de-ai-kb sources import --file data/seed_sources.csv --dry-run
uv run de-ai-kb sources import --file data/seed_sources.csv
uv run uvicorn de_ai_kb.main:app --reload
```

### Option B — local PostgreSQL 16 (fallback, used when a Docker daemon is
not available, e.g. this project's cloud development sandbox)

```bash
apt-get install -y postgresql-16-pgvector
service postgresql start
# create the de_ai_kb role/database and de_ai_kb_test database once:
su postgres -c "psql -c \"CREATE ROLE de_ai_kb LOGIN PASSWORD 'de_ai_kb'\""
su postgres -c "psql -c \"CREATE DATABASE de_ai_kb OWNER de_ai_kb\""
su postgres -c "psql -c \"CREATE DATABASE de_ai_kb_test OWNER de_ai_kb\""
cp .env.example .env   # defaults already point at localhost:5432
uv sync
uv run alembic upgrade head
```

Both paths converge on the same `DATABASE_URL`/`TEST_DATABASE_URL` design;
the integration test suite never falls back to SQLite (array/JSONB/pgvector/
CHECK-constraint behavior must be exercised against real PostgreSQL).

## Commands

```bash
uv sync
uv run ruff check .
uv run mypy src
uv run pytest
docker compose config
uv run alembic upgrade head
uv run de-ai-kb sources import --file data/seed_sources.csv --dry-run
uv run de-ai-kb claims validate --file data/seed_claims.csv
```

## API endpoints

| Method & path | Purpose | Auth |
|---|---|---|
| `GET /health` | Liveness check | none |
| `GET /api/v1/sources` | List/filter sources (tier, type, topic, publisher, language, status, freshness) | none |
| `POST /api/v1/sources` | Register a new source (also creates its 2 standard review items); always starts `status=registered`/`rights_status=needs_review`/`access_policy=metadata_only` — those fields cannot be set at creation, unknown/protected fields return `422` | `X-API-Key` |
| `GET /api/v1/sources/{id}` | Fetch one source | none |
| `PATCH /api/v1/sources/{id}` | Edit generic metadata only (`title`, `publisher`, `tier`, `topic_tags`, `refresh_interval_days`, `notes`) — cannot change `status`, `rights_status`, or `access_policy`; unknown/protected fields return `422` | `X-API-Key` |
| `POST /api/v1/sources/{id}/transition` | Change lifecycle `status`; invalid transitions return `409`; rejects `new_status=blocked` (`422`, use `/block`); `fetched`/`approved`/`published` require the matching review items to be approved first (`422` if not) | `X-API-Key` |
| `POST /api/v1/sources/{id}/block` | Takedown/block; a non-blank `reason` is mandatory | `X-API-Key` |
| `GET /api/v1/research/freshness` | Freshness report | none |
| `GET /api/v1/review-items` | List/filter review items | none |
| `POST /api/v1/review-items/{id}/decision` | Generic decision for non-rights review items; rejects an attempt to approve a `rights_review` item | `X-API-Key` |
| `POST /api/v1/review-items/{id}/rights-decision` | Approve a `rights_review` item with an explicit reviewed `rights_status`/`access_policy` (and optional `tdm_opt_out_status`/`licence_name`/`licence_url`), applied to the source atomically | `X-API-Key` |

## CLI commands

```bash
uv run de-ai-kb db check|init|migrate|seed-taxonomy
uv run de-ai-kb sources import --file data/seed_sources.csv [--dry-run]
uv run de-ai-kb sources validate --file data/seed_sources.csv
uv run de-ai-kb sources duplicates
uv run de-ai-kb sources stale [--state fresh|due_soon|stale|unknown|all]
uv run de-ai-kb sources transition <source-key-or-id> --status <status> [--reason <reason>]
uv run de-ai-kb sources block <source-key-or-id> --reason <reason>
uv run de-ai-kb review export --out review_items_export.csv
uv run de-ai-kb claims validate --file data/seed_claims.csv
```

There is currently no CLI command for the rights-review resolution
workflow — use `POST /api/v1/review-items/{id}/rights-decision`.

## Current limitations (Foundation Release 1)

- No crawling/fetching implementation — `ingestion/` defines interfaces only.
- No LLM extraction — claim/use-case candidates are not generated.
- `seed_claims.csv` is validated but never imported into `claims`/
  `claim_evidence`; see `docs/NEXT_RELEASES.md` for the Release 2/3 import
  path.
- No recommendation UI or frontend.
- Object storage ships a local-filesystem implementation only; the
  S3-compatible interface has no real S3/MinIO backend wired up yet.

See `docs/IMPLEMENTATION_PLAN.md` for the full completed/deferred checklist.
