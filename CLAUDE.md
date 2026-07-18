# AIWertPilot — Germany AI Knowledge Base

## What this repository is

A structured, versioned, source-grounded evidence system (Foundation Release 1
of a Germany-focused AI transformation knowledge base). It is not a chatbot,
not a thin LLM wrapper, and does not yet contain the recommendation
application. See `START_HERE.md` and the `PROMPT START`/`PROMPT END` block in
`CLAUDE_CODE_MASTER_PROMPT.md` for the authoritative product and engineering
specification, and `RESEARCH_PROTOCOL.md` for editorial/evidence rules.

## Durable rules

- **Never modify, delete, or rename** the six root specification/seed files:
  `START_HERE.md`, `CLAUDE_CODE_MASTER_PROMPT.md`, `RESEARCH_PROTOCOL.md`,
  `schema.sql`, `seed_sources.csv`, `seed_claims.csv`. Runtime/operational
  copies live under `data/`.
- `schema.sql` is the reference DDL. Alembic migrations and SQLAlchemy models
  in `src/de_ai_kb/db/models/` are the executable source of truth; any
  deviation from `schema.sql` must be documented in `docs/ADR-001-architecture.md`.
- Evidence before generation: no claim or recommendation may exist without a
  linked evidence record. A published claim requires at least one
  `claim_evidence` row — enforced in the service layer, not just the DB.
- Deterministic business logic only: scoring, freshness, and workflow
  transitions are plain tested code, not LLM judgment.
- `seed_claims.csv` is a worksheet. It is validated but never imported into
  `claims`/`claim_evidence` in Foundation Release 1.
- Do not crawl external websites, add a real LLM integration, or build the
  final recommendation UI in this release.
- Do not fabricate use cases, claims, statistics, legal conclusions, training
  facts, or prices.
- Source snapshots are immutable once created (enforced by a DB trigger).
- Write API routes require the `X-API-Key` development header; never
  hardcode the key — it comes from `.env`.

## Commands

```bash
uv sync
uv run ruff check .
uv run mypy src
uv run pytest
docker compose config
uv run alembic upgrade head
uv run de-ai-kb sources import --file data/seed_sources.csv --dry-run
```

See `README.md` for full local setup and `docs/IMPLEMENTATION_PLAN.md` for
what is implemented vs. deferred.
