# Data Dictionary

Authoritative reference DDL: root `schema.sql` (28 tables). This document
summarizes each table's purpose, critical fields, enumerations, and
relationships as implemented in `src/de_ai_kb/db/models/`. Every enumerated
`text ... CHECK (col IN (...))` column has a matching Python
`enum.StrEnum` in `src/de_ai_kb/domain/enums.py`, kept in lockstep by
`tests/unit/test_enum_constraint_lockstep.py`.

## Sources and documents (`db/models/sources.py`, `documents.py`)

### `sources`
Registry of external sources. Key fields: `source_key` (stable business
key, unique), `original_url` / `canonical_url` (both stored — see
`domain/url.py`), `tier` (`A`-`E`, RESEARCH_PROTOCOL.md §3),
`access_policy` (`metadata_only|short_evidence|full_text_allowed|blocked|
unknown`, default `metadata_only`), `rights_status`
(`needs_review|reviewed_allowed|reviewed_restricted|blocked`),
`tdm_opt_out_status`, `refresh_interval_days`, `status` (the 11-state
lifecycle: `discovered→registered→fetched→extracted→under_review→
approved→published`, plus `rejected|blocked|superseded|archived`; allowed
transitions are enforced in `domain/enums.SOURCE_STATUS_TRANSITIONS` and
`services/source_registry.py`, not just the DB CHECK). `UNIQUE
(canonical_url, publisher)`.

### `source_quality_evaluations`
Seven 0-5 component scores (`authority`, `method_transparency`, `recency`,
`geographic_relevance`, `scope_specificity`, `independence`,
`locatability`) plus a `derived_score` (0-100) and `rationale`. Multiple
evaluations per source over time; `superseded_at` marks a replaced
evaluation. A prioritization aid, never presented as proof (RESEARCH_
PROTOCOL.md §4).

### `source_snapshots`
Immutable retrieval records (enforced by the `prevent_snapshot_update()`
trigger — any `UPDATE` raises; the repository also exposes no `update()`
method as defense in depth). `retention_policy` governs how much of the
fetched content may be kept. `UNIQUE (source_id, sha256)`.

### `documents`
Bibliographic record derived from a snapshot: `document_type`, `authors`,
`publication_date`, `observed_from/to`, `effective_from/to`, `version_label`.

### `document_chunks`
Only for content the source's `access_policy` permits retaining.
`embedding vector(1536)` with an HNSW index (`ix_document_chunks_embedding_
hnsw`, cosine ops — see ADR-001) added in migration `0003`; empty in this
release (no ingestion pipeline runs yet). `UNIQUE (document_id,
chunk_index)`, `UNIQUE (document_id, text_sha256)`.

## Taxonomy (`db/models/taxonomy.py`)

### `industries`, `business_processes`, `capabilities`
Hierarchical (`parent_id` self-FK on the first two) reference tables, all
`slug`-unique. **Only `business_processes` is seeded** in this release —
the 19-item list from RESEARCH_PROTOCOL.md §5, via `de-ai-kb db
seed-taxonomy`. `industries` and `capabilities` ship with the table but no
rows, since the master prompt forbids inventing taxonomy content beyond
what the research protocol explicitly supplies.

## Organizations and evidence (`organizations.py`, `evidence.py`)

### `organizations`
Vendor/company records referenced by `case_studies` and
`training_providers`. `UNIQUE (name, country_code)`.

### `claims`
`claim_type`, `statement`, `normalized_value`/`normalized_unit`,
`confidence` (`unknown|low|medium|high`), `status` (`extracted→under_review
→approved→published`, plus `rejected|superseded|archived`). **No rows
exist in Foundation Release 1** — `seed_claims.csv` is validated
(`services/claims_validation.py`) but never imported, per the master
prompt §11.

### `claim_evidence`
Links a claim to a `document` (+ optional `chunk`), with `relationship`
(`supports|contradicts|qualifies|context`). `services/evidence.py`
enforces that a claim cannot transition to `published` without at least
one row here — the "evidence before generation" rule, tested in
`tests/integration/test_evidence.py`.

## Use cases and case studies (`use_cases.py`, `case_studies.py`)

### `use_cases`
`ai_pattern` and `expected_outcomes`/`required_data`/
`integration_dependencies` stay free text/array (not FK'd to a closed
enum) because RESEARCH_PROTOCOL.md §5 explicitly keeps the AI-pattern and
outcome-type vocabularies open. `maturity`
(`candidate|emerging|established|mature`), `lifecycle_status`.

### `use_case_industries` / `use_case_processes` / `use_case_capabilities` / `use_case_claims`
Many-to-many association tables with their own relationship/importance
qualifiers (`relevance`, `importance`, `relationship`). No `id` column —
composite primary keys, matching `schema.sql` exactly.

### `case_studies`
`deployment_stage` (`experiment|poc|pilot|production|scaled|unknown`),
`self_reported` (boolean, defaults `true` — vendor/self-reported evidence
must never be silently treated as independent), `baseline_summary` /
`intervention_summary` / `outcome_summary`.

## Training (`training.py`)

`training_providers` → `training_offerings` (price + `price_observed_at`,
`last_verified_at`, `status`) → `training_capabilities` (coverage:
`introductory|working|advanced`). No rows this release.

## Regulation (`regulation.py`)

`regulations` (authoritative legal source, `authoritative_source_id` → a
Tier-A/B `sources` row) → `regulatory_obligations` (per-article summaries,
`authoritative_claim_id` optionally linking a supporting claim) →
`use_case_obligations` (relevance: `possible|likely|context_only`, with a
mandatory `rationale`). No rows this release.

## Funding (`funding.py`)

`funding_programs`: geography/applicant-type arrays, funding form/rate,
deadlines, `last_verified_at`, `status`
(`under_review|open|closed|paused|stale|archived`). No rows this release.

## Research operations (`ops.py`)

### `research_jobs`
Placeholder for future scheduled/queued ingestion work
(`queued|running|succeeded|failed|blocked|cancelled`). Not populated by
anything in this release (no ingestion pipeline yet).

### `review_items`
The review queue. `entity_type`/`entity_id` point at any reviewable
record; `review_type` is free text (not CHECK-constrained — new review
categories may be added later without a migration). This release creates
two kinds: `rights_review` and `content_review` (exactly two per
successfully imported source, created atomically with the source insert —
see `services/review.py::create_standard_source_review_items`), and
`dedup_candidate` (from `services/dedup.py`, never more than one open item
per source at a time because of the `UNIQUE(entity_type, entity_id,
review_type, status)` constraint). `status`
(`open→in_progress→approved|rejected|needs_changes|cancelled`), transitions
enforced by `domain/enums.REVIEW_ITEM_STATUS_TRANSITIONS`.

**Deviation:** `metadata jsonb NOT NULL DEFAULT '{}'` (migration `0002`,
not in `schema.sql`). Holds only supplemental, non-searchable context for
a review item — currently just the dedup-candidate payload
`{"counterpart_source_id", "similarity_score", "reason"}`. All primary,
filterable/searchable fields (`entity_type`, `entity_id`, `review_type`,
`status`, `priority`, `assigned_to`, `decision_reason`) remain plain
columns exactly as in `schema.sql`; nothing business-critical is hidden
inside this JSONB column.

### `audit_events`
Append-only. `actor_type`/`actor_id`, `action`, `entity_type`/`entity_id`,
`before_state`/`after_state` (JSONB), `metadata`. Written by
`services/audit.py::AuditService.record(...)` in the same transaction as
every mutation it documents — never a separate async/eventual write.

## Enumerations quick reference

| Column | Enum (domain/enums.py) |
|---|---|
| `sources.tier` | `SourceTier` |
| `sources.access_policy` | `AccessPolicy` |
| `sources.rights_status` | `RightsStatus` |
| `sources.tdm_opt_out_status` | `TdmOptOutStatus` |
| `sources.status` | `SourceStatus` |
| `source_snapshots.retention_policy` | `SnapshotRetentionPolicy` |
| `claims.confidence` | `ClaimConfidence` |
| `claims.status` | `ClaimStatus` |
| `claim_evidence.relationship` | `EvidenceRelationship` |
| `use_cases.maturity` | `UseCaseMaturity` |
| `use_cases.lifecycle_status` | `LifecycleStatus` |
| `use_case_industries.relevance` | `UseCaseIndustryRelevance` |
| `use_case_capabilities.importance` | `UseCaseCapabilityImportance` |
| `use_case_claims.relationship` | `UseCaseClaimRelationship` |
| `case_studies.deployment_stage` | `DeploymentStage` |
| `case_studies.status` | `CaseStudyStatus` |
| `training_offerings.status` | `TrainingOfferingStatus` |
| `training_capabilities.coverage` | `TrainingCoverage` |
| `regulatory_obligations.status` | `RegulatoryObligationStatus` |
| `use_case_obligations.relevance` | `UseCaseObligationRelevance` |
| `funding_programs.status` | `FundingProgramStatus` |
| `research_jobs.status` | `ResearchJobStatus` |
| `review_items.status` | `ReviewItemStatus` |
| (computed, not a column) | `FreshnessState` (`fresh|due_soon|stale|unknown`) |
