# Germany AI Knowledge Base — Research and Quality Protocol

Version: 0.1  
Research cut-off for the seed catalog: 2026-07-18  
Status: Operational starting specification; not legal advice

## 1. Mission

Build a living, traceable knowledge base that supports evidence-based AI adoption decisions by German companies. The system should connect company problems and processes to AI use cases, prerequisites, implementation evidence, measurable outcomes, risks, regulation, standards, training, and funding.

The goal is not to archive “the whole internet.” The goal is controlled coverage of a defined source universe, with explicit quality, freshness, rights, and evidence rules.

## 2. Scope

### Initial geography

- Germany as the primary market
- European Union where law, standards, funding, or comparative evidence affects German companies
- International frameworks only when directly useful in Germany and clearly labelled

### Initial company segment

- SMEs and mid-market organizations, with company-size scope retained exactly as defined by each source
- Initial domain priority: industrial R&D, engineering, machinery, automotive suppliers, specialty chemicals, energy/environment, laboratories, testing, production, maintenance, quality, logistics, and industrial services

### Knowledge domains

1. AI adoption statistics and barriers
2. Use cases and business processes
3. Case studies and measured outcomes
4. Data and technical prerequisites
5. Organizational readiness and change
6. Skills, roles, and training offerings
7. AI Act, privacy, employee participation, security, and standards
8. Funding and support programs
9. Implementation methods, lifecycle stages, and failure patterns
10. Vendors and tools, explicitly labelled as commercial evidence

## 3. Source tiers

| Tier | Source class | Examples | Default treatment |
|---|---|---|---|
| A | Authoritative law, regulator, official statistics | EUR-Lex, Bundesnetzagentur, Destatis, BSI, DSK | Eligible as primary evidence after content review |
| B | Public research and standards bodies | Fraunhofer, DFKI, Plattform Lernende Systeme, DIN, ISO, ENISA, NIST | Strong evidence; method and edition must be recorded |
| C | Industry associations and public support networks | Bitkom, VDMA, VCI, ZVEI, IHK, Mittelstand-Digital | Useful sector evidence; survey scope and institutional position must be explicit |
| D | Named company, vendor, consultancy, or training provider | Company case studies, product pages, course catalogs | Commercial/self-reported; never presented as independent validation |
| E | News, commentary, directories, community content | Trade press, blogs, aggregators | Discovery/context only unless independently corroborated |

Tier is not a truth score. A well-documented Tier D case can be useful, while an old Tier A page may be stale or out of scope.

## 4. Quality dimensions

Score each dimension from 0 to 5 and retain the components:

- `authority`: responsibility or expertise of the publisher
- `method_transparency`: sample, method, definitions, and limitations disclosed
- `recency`: current enough for the claim type
- `geographic_relevance`: Germany/EU applicability
- `scope_specificity`: relevant sector, process, and company-size detail
- `independence`: distance from direct commercial interest
- `locatability`: stable URL, page/section/table, version, and reproducible citation

The UI may derive a weighted display score, but must also show all components and limitations. Quality scoring is a prioritization aid, not proof.

## 5. Core taxonomy

### Business processes

- Strategy and innovation
- Research and development
- Product and systems engineering
- Software development and testing
- Production planning and scheduling
- Manufacturing and assembly
- Quality assurance and inspection
- Asset maintenance and reliability
- Supply chain and logistics
- Procurement
- Energy and sustainability
- Technical service and field support
- Knowledge and document management
- Sales and marketing
- Customer service
- Finance and controlling
- Human resources and learning
- Legal, privacy, governance, and compliance
- IT operations and cybersecurity

Support parent/child relationships; do not encode this list as a closed enumeration.

### AI patterns

- classification and regression
- forecasting
- anomaly and novelty detection
- optimization and decision support
- computer vision
- natural-language processing and information extraction
- semantic search and retrieval-augmented generation
- generative content or code assistance
- agents and workflow automation
- robotics and autonomous systems
- recommender and personalization systems
- simulation, digital twins, and surrogate models

### Outcome types

- cost reduction
- cycle-time reduction
- quality or yield improvement
- downtime reduction
- revenue or conversion improvement
- risk reduction
- compliance improvement
- energy/resource reduction
- employee enablement or safety
- customer experience

### Capability categories

- AI literacy
- problem framing and process analysis
- data literacy and data governance
- data engineering and integration
- statistics and machine learning
- generative AI, RAG, and evaluation
- MLOps/LLMOps and monitoring
- software architecture and cloud/platform operations
- security and privacy
- AI governance and AI Act literacy
- human factors, UX, and change management
- domain-specific expertise
- product management and value measurement

## 6. Record types and minimum evidence

### Claim

Every claim records:

- exact analyst-written statement
- claim type
- geography and jurisdiction
- sector and company-size scope
- population/sample and methodology when relevant
- observation/study period
- publication date
- valid/effective period where relevant
- normalized value and unit where relevant
- source relationship: supports, contradicts, qualifies, or contextualizes
- source locator and evidence summary
- review status and reviewer

Statistics without their population definition must not be compared directly. For example, results for companies with 10+ employees and 20+ employees are distinct observations, not a trend unless methodology is aligned.

### Use case

Every approved use case should eventually include:

- business problem and process
- affected roles
- AI pattern and human role
- required input data and minimum data conditions
- integration dependencies
- outcome hypotheses and candidate KPIs
- implementation stage/maturity
- operational and change prerequisites
- failure modes and uncertainty
- relevant risk/regulatory flags
- evidence links and case studies

Do not assign a universal ROI to a use case. Benefits are context-dependent and should be represented as sourced observations or scenario inputs.

### Case study

Record separately:

- implementing organization and sector
- publisher and whether the evidence is self-reported
- baseline, intervention, measured outcome, unit, and measurement period
- deployment stage: experiment, PoC, pilot, production, or scaled
- technology/vendor where publicly disclosed
- caveats, missing information, and transferability notes

“Successful implementation” without baseline, metric, or production status is marketing evidence, not a measured outcome.

### Training offering

Record:

- provider and official URL
- title, learning outcomes, capability mappings
- target roles and level
- language, format, duration, location
- price and currency only with observation date
- certificate/assessment
- prerequisites and schedule
- licence if content itself is retained
- last verification and freshness state

Courses and prices are dynamic. A stale listing must not be recommended as currently available.

### Regulation or obligation

Record the authoritative legal source separately from explanatory guidance. Store jurisdiction, article/section, affected actor, effective date, status, and official guidance. Product output must use “may apply” and route users to official guidance or professional advice rather than offer a binding legal determination.

### Funding program

Record official program source, target applicants, geography, funding form, rate/amount, deadlines, eligible activities, open/closed status, last verification, and an explicit “verify before applying” notice.

## 7. Research workflow

```text
discover -> register -> rights review -> fetch -> parse -> extract -> deduplicate
        -> evidence review -> approve -> publish -> monitor -> supersede/archive
```

### Discover

- Search by source category, sector, process, and knowledge gap.
- Prefer official indexes and publication catalogs over isolated search results.
- Record discovery query/date and parent index where useful.

### Register

- Store original and canonical URL, publisher, title, type, tier, language, topics, and expected refresh interval.
- Registration means “candidate known,” not “content verified.”

### Rights review

- Check access conditions, licence, terms, robots controls, TDM reservation, and database-right risk.
- Allowed retention must be an explicit field: metadata only, short evidence only, full text allowed, or blocked.
- Unknown defaults to metadata/URL plus original analyst paraphrase.

### Fetch and snapshot

- Fetch only allowed sources, with an identified user agent and per-domain rate limits.
- Preserve retrieval metadata and checksum.
- Snapshots are immutable; a changed source creates a new snapshot.

### Extract

- Parser and optional LLM output always records software/model/prompt version.
- Extraction creates candidates, never published facts.
- Reject output that lacks a locator or cannot be reconciled with the source.

### Review

- Compare candidate to the source.
- Correct scope, dates, units, and evidence relationship.
- Separate claim, inference, and recommendation.
- Record reviewer and decision reason.

### Publish

- A published claim has evidence.
- A recommendation has an explanation and cites approved knowledge records.
- Stale or superseded evidence is visibly labelled.

## 8. Conflict and uncertainty rules

- Preserve conflicting claims as separate records.
- Check methodology, population, dates, definitions, geography, and deployment stage before treating findings as inconsistent.
- Do not average incompatible statistics.
- Use confidence levels only with a written rationale.
- Record `unknown` instead of guessing.
- Recommendations must expose the largest evidence or data gap and the next validation action.

## 9. Freshness defaults

| Record/source class | Review interval |
|---|---:|
| Active law/guidance implementation, deadlines, funding calls | 7–14 days |
| Training availability, prices, events | 30 days |
| Vendor/product pages | 30 days |
| Market/adoption statistics | 90 days |
| Research guidance and standards metadata | 180 days |
| Stable methodology | 365 days |

Store overrides per record. Freshness states are `fresh`, `due_soon`, `stale`, and `unknown`.

## 10. Copyright, database, privacy, and access boundaries

- Do not bypass paywalls, authentication, CAPTCHAs, technical measures, or site restrictions.
- A public page is not automatically licensed for full-text storage, embedding, redistribution, or commercial reuse.
- Rights holders may reserve text-and-data-mining rights; database collections may have separate protection.
- Default to bibliographic metadata, factual fields, stable links, short lawful evidence, and analyst-written paraphrases.
- Retain or distribute full text only after explicit licence/permission or reviewed legal basis.
- Never reproduce paid standards. Store standard metadata and point to the official publisher.
- Avoid personal data. Do not collect contact databases, private profiles, or sensitive data.
- Maintain block/takedown, deletion, and audit procedures.
- Legal uncertainty goes to qualified German/EU counsel; the software does not decide it.

Relevant starting references include German UrhG §44b, Directive (EU) 2019/790, and EU database-protection rules. These references do not themselves authorize a particular ingestion action.

## 11. Research waves

### Wave 1 — authoritative landscape

Official statistics, AI Act and German implementation, privacy, security, employee participation, standards, public support networks, and major training indexes.

Output target: 50–75 registered sources, all rights/freshness classified.

### Wave 2 — industrial use-case evidence

Research each priority business process across machinery, automotive suppliers, chemicals, energy/environment, industrial services, laboratories/testing, manufacturing, logistics, and maintenance.

Output target: 60 approved use-case records and at least 30 production/pilot case studies. Prefer measured outcomes; explicitly tag evidence gaps.

### Wave 3 — capability and training graph

Map use-case prerequisites to roles/capabilities and verified German/European training offerings.

Output target: 75 current training offerings across AI literacy, data, GenAI/RAG, MLOps, security/privacy, governance, and change.

### Wave 4 — implementation and value evidence

Collect lifecycle methods, failure patterns, cost components, time-to-value observations, and KPI definitions. Do not create universal benchmarks until comparable samples exist.

### Wave 5 — funding, vendors, and continuous monitoring

Add official funding calls and commercial products with explicit bias and freshness labels. Implement scheduled change detection and review queues.

## 12. Publication quality gates

A record may be published only when:

- required fields are complete
- its source and rights status are known
- dates, scope, and units are normalized
- evidence is locatable
- commercial/self-reported evidence is labelled
- conflicts and limitations are retained
- a reviewer has approved it
- the audit event exists

The initial `seed_sources.csv` passes discovery-level URL verification only. It does not pass these publication gates.

