# Next Releases

Sequenced plan per `CLAUDE_CODE_MASTER_PROMPT.md` §14 and `START_HERE.md`'s
session outline. Each release builds on the relational foundation shipped
in Foundation Release 1 without altering it destructively.

## Release 2 — Compliant ingestion

- A domain-policy/allowlist registry (which hosts may be fetched, at what
  rate) — a new table, not a repurposing of anything in `schema.sql`.
- A real implementation of the `Fetcher` protocol
  (`src/de_ai_kb/ingestion/fetcher.py`) using `httpx`, honoring robots.txt,
  per-domain rate limits, and an identified user agent.
- Populate `source_snapshots` for real (immutability already enforced —
  nothing to change there) and `documents`/`document_chunks` via HTML/PDF
  parsers, recording `parser_version` and a content hash for change
  detection.
- Retry/dead-letter handling via `research_jobs` (table already modeled,
  unused this release).
- Fixture-based integration tests (saved HTML/PDF snapshots) so the suite
  never depends on live websites, per `START_HERE.md`'s Session 2 brief.
- Start with the five sources named in the Session 2 prompt; report
  exactly which were fetched vs. remained metadata-only, and why.

## Release 3 — Assisted extraction and human review

- A provider-neutral extraction interface (strict JSON-schema output per
  extraction type: claim, use case, case study, training offering,
  regulation, funding program), recording provider/model/prompt-version/
  source-snapshot/locator/timestamp on every candidate.
- **The `seed_claims.csv` import path this release unlocks:** for each of
  the 38 worksheet rows, once its `source_key` has a real `source_snapshots`
  → `documents` chain (from Release 2), a single transaction should: locate
  or create the `documents` row the claim's `locator` refers to, insert the
  `claims` row with `status='extracted'` (not `published`), insert a
  `claim_evidence` row linking them with the worksheet's implied
  relationship (default `supports` unless the row's `notes` say otherwise,
  e.g. the Destatis/Bitkom non-comparability notes already present in the
  CSV), and create a `review_type='content_review'` item pointing at the
  new claim. This is exactly the "candidates enter a review queue, never
  auto-published" rule from `RESEARCH_PROTOCOL.md` §7 — Foundation Release
  1 deliberately stops short of it because the document/snapshot chain
  doesn't exist yet.
- A minimal reviewer UI or admin workflow: source evidence next to the
  extracted field, edit/approve/reject/needs-changes, contradiction
  linking (`claim_evidence.relationship='contradicts'` already modeled).
- Tests against a deterministic fake extractor — no live LLM calls in CI.

## Release 4 — Knowledge application

- Evidence search and company-readiness profiling: relational filters and
  deterministic matching first; `document_chunks.embedding` (HNSW index
  already in place, see ADR-001) used only to find *candidate* evidence,
  never to compute a score.
- Use-case matching, capability-gap analysis, training/funding matching —
  all deterministic code against the now-populated `use_cases`,
  `capabilities`, `training_offerings`, `funding_programs` tables.
- Every recommendation must show why it matched, prerequisites, missing
  company information, evidence quality/freshness (the
  `source_quality_evaluations` components and `domain/freshness.py` states
  already exist for this), citations, uncertainty, and the next validation
  action. No LLM calculates a business score or invents an ROI figure.

## Release 5 — Commercial product controls

- Multi-tenancy, RBAC, SSO, tenant isolation.
- Client workspaces; evidence-backed decision reports as a deliverable
  artifact.
- Monitoring, backups, retention/deletion workflows, a security review,
  and EU-region deployment specifics.
- Replace the Foundation Release 1 dev-only `X-API-Key` header with real
  authentication — it was always documented as a placeholder
  (`.env.example`, `docs/RIGHTS_AND_CONTENT_POLICY.md` makes no claims
  about it being production auth).

## Single best next task

Build the Release 2 domain-allowlist table and the real `Fetcher`
implementation against exactly five sources from `data/seed_sources.csv`
(prioritize Tier A: Destatis, Bundesnetzagentur, EUR-Lex, BSI, DSK), with
fixture-backed integration tests. This is the smallest slice that turns
the compliant-ingestion boundary from an interface into working code
without yet touching extraction or the review UI.
