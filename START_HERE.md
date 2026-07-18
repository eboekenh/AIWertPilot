# Start Here — Germany AI Knowledge Base

## What we are building first

The first product asset is not a chatbot. It is a reviewed, versioned evidence system containing:

- source registry
- documents and immutable snapshots
- claims linked to exact evidence
- AI use cases linked to industries and business processes
- implementation prerequisites and capability gaps
- case studies and measured outcomes
- training offerings
- regulation, standards, employee-participation, security, and privacy guidance
- funding programs

The application will later query this foundation to produce company-specific recommendations with explanations and citations.

## Files in this starter pack

- `CLAUDE_CODE_MASTER_PROMPT.md`: full build instruction for Claude Code
- `RESEARCH_PROTOCOL.md`: editorial, evidence, freshness, and rights rules
- `schema.sql`: detailed PostgreSQL reference model
- `seed_sources.csv`: 65 Germany/EU starting sources discovered and URL/scope-checked on 2026-07-18
- `seed_claims.csv`: 38 first-pass claims checked against source tables/pages, still awaiting formal import and editor approval

The seed rows are not yet “approved knowledge.” They are registered research candidates. Each still needs rights/access review and content review.

## Recommended working sequence

### Session 1 — Foundation Release 1

1. Create a new Git repository.
2. Put all four companion files in its root.
3. Open Claude Code from that repository.
4. Paste the entire section between `PROMPT START` and `PROMPT END` from `CLAUDE_CODE_MASTER_PROMPT.md`.
5. Let Claude Code inspect the repository, create the implementation plan, build the backend/database, import the source registry, and run the quality gates.
6. Do not ask it to crawl or build the final recommendation interface during this session.

The session is complete only when migrations, seed import, lint, typing, tests, and the API smoke test pass.

### Session 2 — Compliant ingestion

After Foundation Release 1 passes, give Claude Code this task:

```text
Implement Release 2 as defined in docs/NEXT_RELEASES.md and the original master specification.

Start with a domain-policy registry and ingest only an explicit allowlist of five sources. Implement robots/terms/licence review fields, per-domain rate limits, immutable HTTP snapshots, HTML and PDF parser provenance, content hashes, change detection, retries, and blocked-source handling. Unknown rights must remain metadata-only. Do not bypass access restrictions and do not use an LLM yet.

Add integration tests with saved public fixtures so the test suite does not depend on live websites. Run all existing and new quality gates. Report exactly which five sources were fetched, which remained metadata-only, and why.
```

### Session 3 — Assisted extraction and human review

```text
Implement Release 3 from docs/NEXT_RELEASES.md.

Add a provider-neutral extraction interface that converts permitted source content into candidate claims, use cases, case studies, training offerings, regulations, and funding records using strict JSON schemas. Record provider, model, prompt version, source snapshot, locator, and extraction timestamp. All candidates must enter a review queue; automatic publication is forbidden.

Build a minimal but production-quality reviewer interface or admin workflow showing source evidence beside extracted fields. Support edit, approve, reject, needs-changes, contradiction linking, and audit events. Tests must use a deterministic fake extractor. Do not create fake production facts.
```

### Session 4 — Knowledge application

Only after enough records are reviewed:

```text
Implement the first evidence-search and company-assessment application from Release 4.

Use relational filters and deterministic matching first; use vector retrieval only to find candidate evidence. Every recommendation must show why it matched, prerequisites, missing company information, evidence quality/freshness, citations, uncertainty, and the next validation action. Never let an LLM calculate business scores or invent ROI.
```

## First research batch

Review these source groups in order:

1. Destatis adoption, barriers, and SME definitions
2. EUR-Lex AI Act, European Commission implementation guidance, and Bundesnetzagentur
3. DSK privacy/RAG guidance and BSI security guidance
4. Mittelstand-Digital and Plattform Lernende Systeme implementation material
5. Fraunhofer industrial use-case publications
6. KI-Campus, Fraunhofer Academy, KURSNET, and mein NOW training catalogs
7. Official funding databases

For each source, capture:

- exact scope and methodology
- publication, study, effective, and retrieval dates
- rights/access decision
- claims with page/section/table locators
- limitations and commercial bias
- refresh interval
- conflicts with existing evidence

## Initial editorial targets

Do not optimize for record count alone. A useful first reviewed corpus would contain:

- 50–75 rights-classified sources
- 60 industrial use cases
- 30 case studies with clear deployment stage
- 75 current training offerings mapped to capabilities
- core German/EU regulatory and security guidance
- 20 current funding/support records

These are coverage targets, not an MVP boundary. The system remains a continuously maintained product asset.

## Important operating rule

Separate these four things in the database and in the UI:

1. what a source literally reports
2. the normalized claim extracted from it
3. the analyst's interpretation
4. the application's recommendation

This separation is what makes the future application trustworthy and defensible.
