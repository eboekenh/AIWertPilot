# Claude Code Master Prompt — Germany AI Knowledge Base

## How to use

Copy everything between `PROMPT START` and `PROMPT END` into Claude Code from the root of a new or existing Git repository. Place these companion files in the repository root first:

- `RESEARCH_PROTOCOL.md`
- `seed_sources.csv`
- `seed_claims.csv`
- `schema.sql`

The prompt deliberately asks Claude Code to build the research foundation before attempting the final recommendation application.

---

## PROMPT START

You are the principal engineer, data architect, and research-infrastructure engineer for a serious commercial product. Build a production-minded, Germany-focused AI transformation knowledge base. The working repository name is `de-ai-knowledge-base`.

This is not a demo, a generic chatbot, a Streamlit prototype, or a thin wrapper around an LLM. The long-term product will help German companies identify, assess, sequence, and implement AI use cases and find relevant training, regulation, funding, standards, case studies, and implementation guidance. Its defensible core must be a structured, versioned, source-grounded knowledge system.

### 1. Product context

The future application should be able to answer questions such as:

- Which AI use cases fit a German industrial SME with a given sector, process problem, data situation, company size, and risk profile?
- What evidence supports each recommendation?
- What data, skills, governance, security, and organizational capabilities are prerequisites?
- Which German or European training offerings close the identified capability gaps?
- Which regulations, standards, employee-participation topics, and funding programs may be relevant?
- What is known from real implementations, and what remains uncertain?
- Which next validation action should the company take before investing in a PoC or production deployment?

The system must never invent evidence. Every externally verifiable claim must be traceable to one or more sources and, where possible, a page, section, table, or stable locator. Facts, source statements, analyst interpretations, and product recommendations must remain separate data objects.

### 2. Primary users

Design the foundation for these future users:

1. Founder/research administrator curating the knowledge base.
2. AI and digital-transformation consultants working with multiple client companies.
3. Heads of Digitalization, Innovation, R&D, Engineering, Operations, Data/AI, or IT in German Mittelstand companies.
4. Reviewers from privacy, security, legal, works council, quality, and compliance functions.

Initial domain priority is German industrial Mittelstand: machinery, automotive suppliers, specialty chemicals, energy/environmental technology, industrial services, laboratories, testing, engineering, manufacturing, logistics, maintenance, and technical R&D. The model must remain extensible to other sectors.

### 3. Current assignment

Do not attempt to build the final recommendation product in one pass. In this run, implement **Foundation Release 1** completely and leave the repository ready for the next releases.

Foundation Release 1 consists of:

1. A clean, typed backend repository.
2. PostgreSQL + pgvector data model and migrations.
3. A source registry with provenance, rights/access metadata, freshness rules, and lifecycle status.
4. Import of the supplied `seed_sources.csv` with validation, canonical URL handling, and idempotency.
5. Core structured entities for sources, snapshots, documents, claims/evidence, industries, business processes, capabilities, use cases, case studies, training, regulations/obligations, funding programs, research jobs, review items, and audit events.
6. A deterministic command-line research workflow and a small API for source registration, listing, filtering, review, and freshness reporting.
7. Tests, documentation, sample data, and repeatable local setup.

Do not mass-crawl the internet in this release. Build the compliant ingestion boundary and source registry first.

### 4. Non-negotiable product principles

- **Evidence before generation:** no claim or recommendation without evidence links.
- **Structured data plus retrieval:** use relational records for facts and relationships; use embeddings only for discovery and retrieval, never as the system of record.
- **Deterministic business logic:** scoring, staleness, validation, and workflow transitions must be ordinary tested code, not LLM judgment.
- **Human approval:** LLM-extracted claims enter a staging/review state and cannot become published automatically.
- **Temporal truth:** store publication, observation, effective, retrieval, verification, and expiry dates separately.
- **Conflicting evidence is preserved:** do not average away disagreement. Allow evidence to support, contradict, qualify, or contextualize a claim.
- **Germany/EU specificity:** record jurisdiction, geography, company-size scope, sector, and language.
- **Copyright and access compliance:** a public URL is not permission to republish or retain an entire work.
- **Auditability:** every material mutation must record actor, timestamp, action, and before/after metadata where appropriate.
- **Provider independence:** do not couple the domain model to one LLM, embedding model, cloud, or storage vendor.
- **No fabricated seed content:** the supplied source catalog is a discovery registry, not proof that every page has been fully reviewed.

### 5. Required technology choices

Use these defaults unless the existing repository has an equivalent, coherent stack that should be preserved:

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL 16
- pgvector
- `uv` for Python dependency and virtual-environment management
- pytest, pytest-asyncio, Ruff, and mypy
- Docker Compose for local PostgreSQL
- `httpx` behind an explicit fetcher interface for a later ingestion release
- structured JSON logging
- object-storage abstraction with a local development implementation and an S3-compatible interface, but no cloud credentials required

Do not introduce Redis, Kafka, Temporal, Kubernetes, or a frontend during this first release unless the existing repository already requires them. Design service boundaries so background orchestration and a Next.js admin interface can be added later.

All source code, identifiers, migrations, tests, and technical documentation should be in English. Knowledge records may be German or English and must store their language.

### 6. Repository structure

Use a structure close to the following, adapting only when justified:

```text
.
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── alembic.ini
├── migrations/
├── src/de_ai_kb/
│   ├── api/
│   ├── cli/
│   ├── core/
│   ├── db/
│   ├── domain/
│   ├── repositories/
│   ├── services/
│   ├── ingestion/
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── data/seed_sources.csv
└── docs/
    ├── IMPLEMENTATION_PLAN.md
    ├── DATA_DICTIONARY.md
    ├── RESEARCH_WORKFLOW.md
    ├── RIGHTS_AND_CONTENT_POLICY.md
    ├── ADR-001-architecture.md
    └── NEXT_RELEASES.md
```

Move or copy the supplied companion files into sensible repository locations while preserving their content and history. Treat `schema.sql` as a reference specification; Alembic migrations and SQLAlchemy models are the executable source of truth after implementation. Document any intentional deviation.

### 7. Minimum domain model

Implement UUID primary keys, UTC timestamps, constraints, indexes, and explicit relationships. Avoid opaque JSON blobs for core searchable fields; JSONB is acceptable for source-specific metadata and future extension.

At minimum model:

#### Sources and documents

- `sources`: stable key, title, publisher, canonical URL, source type, tier, language, jurisdiction/geography, topic tags, access policy, licence/rights status, TDM opt-out status, refresh interval, lifecycle status, verification dates, notes.
- `source_snapshots`: retrieval metadata, final URL, HTTP status, ETag, Last-Modified, media type, content hash, storage reference, rights decision, parser version. Snapshot rows must be immutable.
- `documents`: title, authors, document type, publication date, effective dates, version, language, page count, and source snapshot.
- `document_chunks`: only for content that policy allows the product to retain; include locator/page, checksum, permitted text, embedding-model metadata, and vector field.

#### Evidence

- `claims`: claim type, statement, normalized numeric value/unit when applicable, geography, sector/company-size scope, sample size, study period, validity period, confidence, status, and analyst notes.
- `claim_evidence`: claim, document/chunk, page/section/locator, a paraphrased evidence summary, an optional short quotation subject to rights policy, and relationship type (`supports`, `contradicts`, `qualifies`, `context`).
- A published claim must have at least one evidence link. Enforce this in the service layer and test it.

#### Taxonomy and product knowledge

- `industries`, preferably able to map to NACE codes.
- `business_processes` with hierarchical parent relationships.
- `capabilities` and skill categories.
- `use_cases` with problem, AI pattern, expected outcome types, data requirements, human role, maturity, and lifecycle status.
- many-to-many links among use cases, industries, processes, capabilities, claims, regulatory flags, trainings, and case studies.
- `organizations` and `case_studies`, keeping vendor-authored and independent evidence distinguishable.
- `training_providers`, `training_offerings`, and capability mappings. Store audience, level, language, format, duration, price/currency, certificate, location, prerequisites, next dates, and last verification date.
- `regulations`, `regulatory_obligations`, jurisdiction, effective dates, authoritative source, and non-legal-advice disclaimer metadata.
- `funding_programs` with eligibility, region, company-size applicability, funding form, amount/rate if known, deadlines, official source, and last verification date.

#### Research operations

- `research_jobs`, `review_items`, and `audit_events`.
- Review state machine: `discovered -> registered -> fetched -> extracted -> under_review -> approved -> published`, with `rejected`, `blocked`, `superseded`, and `archived` paths where applicable.
- Do not allow invalid state transitions.

Use the supplied `schema.sql` and `RESEARCH_PROTOCOL.md` as the detailed starting point.

### 8. Source-quality and freshness behavior

Implement transparent, configurable scoring dimensions rather than a single unexplained score:

- authority
- methodological transparency
- recency
- Germany/EU relevance
- sector/company-size specificity
- independence/commercial-bias risk
- reproducibility/locatability

Store both the component values and the derived display score. Do not let the score imply truth; it is a review aid.

Implement freshness calculation from source category and configured refresh interval. Initial defaults:

- laws, regulatory guidance, deadlines, and funding calls: 7–14 days
- active training offerings and prices: 30 days
- vendor/product pages: 30 days
- statistics and market reports: 90 days
- research guidance and standards metadata: 180 days
- evergreen methodology: 365 days

Individual records may override defaults. Expose `fresh`, `due_soon`, `stale`, and `unknown` states.

### 9. Rights and content policy

Create and enforce a conservative policy layer:

- Never bypass authentication, paywalls, CAPTCHAs, robots controls, or technical restrictions.
- Record whether robots.txt, terms, licensing, machine-readable TDM reservation, and database rights require review.
- Do not assume that indexing, embedding, retaining, or redistributing full text is allowed merely because a URL is public.
- Default unknown-rights sources to metadata, URL, bibliographic facts, analyst-written paraphrases, and minimal locators only.
- Retain full text/chunks only when an explicit licence, public-domain status, owner permission, or reviewed legal basis permits it.
- Never expose full copyrighted reports through the API.
- Do not store personal data unless strictly necessary; do not ingest contact lists or sensitive personal data.
- Add a takedown/block mechanism and retain the reason in the audit trail.

This is an engineering policy, not legal advice. Flag unresolved cases for qualified legal review. Reference, but do not over-interpret, German UrhG §44b and applicable EU copyright/database rules.

### 10. API and CLI for Foundation Release 1

Implement at least:

#### API

- `GET /health`
- `GET /api/v1/sources` with pagination and filters for tier, type, topic, publisher, language, status, and freshness
- `POST /api/v1/sources` with validation and duplicate detection
- `GET /api/v1/sources/{id}`
- `PATCH /api/v1/sources/{id}` for reviewable metadata
- `GET /api/v1/research/freshness`
- `GET /api/v1/review-items`
- `POST /api/v1/review-items/{id}/decision`

Protect write routes behind a simple development API-key dependency that can later be replaced by proper authentication. Never hardcode the key; document it in `.env.example`.

#### CLI

- initialize/check database
- run migrations
- import `seed_sources.csv`
- validate source registry
- show duplicates
- show stale/due-soon records
- export a review CSV

Imports must support dry-run, produce a structured summary, reject malformed rows with useful reasons, and be idempotent. Canonicalize URLs carefully without destroying meaningful query parameters. Store the originally supplied URL as well as the canonical URL.

### 11. Seed-source semantics

The supplied `seed_sources.csv` contains source-discovery records verified at URL/scope level on 2026-07-18. Importing a row must not mark its content as reviewed, approved, or legally ingestible. Map its initial state to `registered` or equivalent and create follow-up review items for rights/access review and content review.

The supplied `seed_claims.csv` is a first-pass evidence worksheet. Preserve and validate it, but do not publish or import it as approved claims in Foundation Release 1 because the corresponding snapshots/documents and formal evidence links do not exist yet. Document the Release 2/3 import path that will create source snapshots, documents, evidence locators, under-review claims, and reviewer tasks in one transaction.

Deduplicate using canonical URL plus publisher/title similarity, but never merge automatically when records may represent different versions or editions. Produce merge candidates for review.

### 12. Tests and quality gates

Provide meaningful tests for at least:

- URL canonicalization and duplicate detection
- seed import idempotency
- CSV validation and error reporting
- source status transitions
- freshness calculation at boundary dates
- source-quality component validation
- published-claim evidence requirement
- immutable snapshot behavior
- review decisions and audit events
- API pagination/filtering
- development write-route authorization

Integration tests may use a dedicated PostgreSQL container. Do not silently replace PostgreSQL behavior with SQLite in tests where types, constraints, arrays, JSONB, or pgvector matter.

Required commands must pass:

```bash
uv sync
uv run ruff check .
uv run mypy src
uv run pytest
docker compose config
```

Also provide a smoke-test sequence for starting PostgreSQL, applying migrations, importing seeds, starting the API, and querying `/health` and `/api/v1/sources`.

### 13. Documentation requirements

Write:

- `README.md`: exact local setup, commands, architecture summary, and current limitations.
- `docs/IMPLEMENTATION_PLAN.md`: completed and deferred work, with decision rationale.
- `docs/DATA_DICTIONARY.md`: every table/entity, critical field, enumeration, and relationship.
- `docs/RESEARCH_WORKFLOW.md`: discovery-to-publication workflow and reviewer responsibilities.
- `docs/RIGHTS_AND_CONTENT_POLICY.md`: operational policy and escalation cases.
- `docs/ADR-001-architecture.md`: why relational evidence graph + optional vector retrieval was chosen.
- `docs/NEXT_RELEASES.md`: sequenced plan for compliant fetching/parsing, extraction/review UI, knowledge search, company assessment, use-case matching, and training-roadmap generation.

### 14. Future-release boundaries

Architect for, but do not implement prematurely:

#### Release 2 — compliant ingestion

- domain allowlist and per-domain policy
- robots/terms/licence review records
- rate-limited HTML/PDF fetchers
- immutable snapshots and parser provenance
- PDF/HTML extraction
- change detection
- retry/dead-letter workflow

#### Release 3 — assisted extraction and review

- provider-neutral LLM interface
- strict JSON-schema extraction
- prompt/model/version provenance
- claim/case-study/training candidate creation
- side-by-side source review
- approve/reject/edit workflow
- no automatic publication

#### Release 4 — knowledge application

- evidence search
- company readiness profile
- use-case matching
- capability-gap analysis
- training and funding matching
- recommendation explanations with citations
- deterministic scoring and uncertainty

#### Release 5 — commercial product controls

- multi-tenancy, RBAC, SSO, tenant isolation
- client workspaces
- evidence-backed decision reports
- monitoring, backups, retention, deletion, security review, and EU deployment

### 15. Execution behavior

Work autonomously on normal reversible implementation decisions. Do not ask broad preference questions that are already answered here. Stop and ask only if the repository contains conflicting existing architecture, credentials would be required, or an irreversible/destructive action is necessary.

At the start:

1. Inspect the repository without deleting or overwriting unrelated work.
2. Summarize the current state in a few lines.
3. Create or update `docs/IMPLEMENTATION_PLAN.md` with a checklist.
4. Implement Foundation Release 1 in small coherent steps.
5. Run all quality gates and fix failures.
6. Do not create Git commits unless explicitly asked.

At the end, report:

- what was implemented
- important architectural decisions
- exact commands run and their outcomes
- seed import counts: inserted, unchanged, rejected, and review items created
- known limitations
- the single best next task for Release 2

Do not claim completion if migrations, tests, lint, or type checks are failing. Do not insert made-up use cases, prices, statistics, legal conclusions, or training facts merely to make the UI look populated.

Begin now with repository inspection and Foundation Release 1.

## PROMPT END
