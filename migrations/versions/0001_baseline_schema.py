"""Baseline schema - verbatim reproduction of schema.sql (28 tables).

This migration mirrors the root schema.sql reference DDL table-for-table,
index-for-index, trigger-for-trigger, with no deviations. Intentional
deviations from schema.sql are introduced only in later migrations
(0002, 0003) and documented in docs/ADR-001-architecture.md.

Revision ID: 0001
Revises:
Create Date: 2026-07-18

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Every statement below is copied verbatim (statement-by-statement) from the
# root schema.sql, in the same order it appears there.
_STATEMENTS: list[str] = [
    "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
    "CREATE EXTENSION IF NOT EXISTS vector;",
    """
    CREATE OR REPLACE FUNCTION set_updated_at()
    RETURNS trigger AS $$
    BEGIN
      NEW.updated_at = now();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """,
    # sources
    """
    CREATE TABLE sources (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      source_key text NOT NULL UNIQUE,
      title text NOT NULL,
      publisher text NOT NULL,
      original_url text NOT NULL,
      canonical_url text NOT NULL,
      source_type text NOT NULL,
      tier text NOT NULL CHECK (tier IN ('A', 'B', 'C', 'D', 'E')),
      language_code text NOT NULL DEFAULT 'de',
      geography_codes text[] NOT NULL DEFAULT '{}',
      jurisdiction_codes text[] NOT NULL DEFAULT '{}',
      topic_tags text[] NOT NULL DEFAULT '{}',
      access_policy text NOT NULL DEFAULT 'metadata_only'
        CHECK (access_policy IN ('metadata_only', 'short_evidence', 'full_text_allowed', 'blocked', 'unknown')),
      licence_name text,
      licence_url text,
      rights_status text NOT NULL DEFAULT 'needs_review'
        CHECK (rights_status IN ('needs_review', 'reviewed_allowed', 'reviewed_restricted', 'blocked')),
      tdm_opt_out_status text NOT NULL DEFAULT 'unknown'
        CHECK (tdm_opt_out_status IN ('unknown', 'not_found', 'reserved', 'not_applicable')),
      robots_reviewed_at timestamptz,
      terms_reviewed_at timestamptz,
      refresh_interval_days integer NOT NULL CHECK (refresh_interval_days > 0),
      last_discovered_at timestamptz,
      last_verified_at timestamptz,
      next_review_at timestamptz,
      status text NOT NULL DEFAULT 'registered'
        CHECK (status IN ('discovered', 'registered', 'fetched', 'extracted', 'under_review', 'approved', 'published', 'rejected', 'blocked', 'superseded', 'archived')),
      notes text,
      metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (canonical_url, publisher)
    );
    """,
    "CREATE INDEX ix_sources_status ON sources(status);",
    "CREATE INDEX ix_sources_publisher ON sources(publisher);",
    "CREATE INDEX ix_sources_type ON sources(source_type);",
    "CREATE INDEX ix_sources_tier ON sources(tier);",
    "CREATE INDEX ix_sources_next_review ON sources(next_review_at);",
    "CREATE INDEX ix_sources_topics_gin ON sources USING gin(topic_tags);",
    "CREATE INDEX ix_sources_metadata_gin ON sources USING gin(metadata);",
    """
    CREATE TRIGGER trg_sources_updated_at
    BEFORE UPDATE ON sources FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # source_quality_evaluations
    """
    CREATE TABLE source_quality_evaluations (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      source_id uuid NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
      authority smallint NOT NULL CHECK (authority BETWEEN 0 AND 5),
      method_transparency smallint NOT NULL CHECK (method_transparency BETWEEN 0 AND 5),
      recency smallint NOT NULL CHECK (recency BETWEEN 0 AND 5),
      geographic_relevance smallint NOT NULL CHECK (geographic_relevance BETWEEN 0 AND 5),
      scope_specificity smallint NOT NULL CHECK (scope_specificity BETWEEN 0 AND 5),
      independence smallint NOT NULL CHECK (independence BETWEEN 0 AND 5),
      locatability smallint NOT NULL CHECK (locatability BETWEEN 0 AND 5),
      derived_score numeric(5,2) NOT NULL CHECK (derived_score BETWEEN 0 AND 100),
      rationale text NOT NULL,
      evaluated_by text NOT NULL,
      evaluated_at timestamptz NOT NULL DEFAULT now(),
      superseded_at timestamptz
    );
    """,
    "CREATE INDEX ix_source_quality_source ON source_quality_evaluations(source_id, evaluated_at DESC);",
    # source_snapshots
    """
    CREATE TABLE source_snapshots (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      source_id uuid NOT NULL REFERENCES sources(id) ON DELETE RESTRICT,
      retrieved_at timestamptz NOT NULL,
      final_url text NOT NULL,
      http_status integer,
      etag text,
      last_modified text,
      media_type text,
      content_length bigint,
      sha256 text NOT NULL,
      storage_uri text,
      retention_policy text NOT NULL DEFAULT 'metadata_only'
        CHECK (retention_policy IN ('metadata_only', 'temporary', 'retained', 'blocked')),
      rights_decision text NOT NULL,
      fetcher_version text NOT NULL,
      parser_version text,
      metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (source_id, sha256)
    );
    """,
    "CREATE INDEX ix_source_snapshots_source ON source_snapshots(source_id, retrieved_at DESC);",
    """
    CREATE OR REPLACE FUNCTION prevent_snapshot_update()
    RETURNS trigger AS $$
    BEGIN
      RAISE EXCEPTION 'source_snapshots are immutable; create a new snapshot';
    END;
    $$ LANGUAGE plpgsql;
    """,
    """
    CREATE TRIGGER trg_source_snapshots_immutable
    BEFORE UPDATE ON source_snapshots FOR EACH ROW EXECUTE FUNCTION prevent_snapshot_update();
    """,
    # documents
    """
    CREATE TABLE documents (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      snapshot_id uuid NOT NULL REFERENCES source_snapshots(id) ON DELETE RESTRICT,
      title text NOT NULL,
      document_type text NOT NULL,
      authors text[] NOT NULL DEFAULT '{}',
      language_code text NOT NULL,
      publication_date date,
      observed_from date,
      observed_to date,
      effective_from date,
      effective_to date,
      version_label text,
      page_count integer CHECK (page_count IS NULL OR page_count > 0),
      external_identifier text,
      metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX ix_documents_snapshot ON documents(snapshot_id);",
    "CREATE INDEX ix_documents_publication_date ON documents(publication_date DESC);",
    # document_chunks
    """
    CREATE TABLE document_chunks (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
      chunk_index integer NOT NULL CHECK (chunk_index >= 0),
      page_number integer CHECK (page_number IS NULL OR page_number > 0),
      locator text,
      permitted_text text NOT NULL,
      text_sha256 text NOT NULL,
      embedding vector(1536),
      embedding_model text,
      embedding_dimensions integer,
      parser_version text NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (document_id, chunk_index),
      UNIQUE (document_id, text_sha256)
    );
    """,
    "CREATE INDEX ix_document_chunks_document ON document_chunks(document_id, chunk_index);",
    # industries
    """
    CREATE TABLE industries (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      name text NOT NULL,
      slug text NOT NULL UNIQUE,
      nace_code text,
      parent_id uuid REFERENCES industries(id) ON DELETE SET NULL,
      description text,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TRIGGER trg_industries_updated_at
    BEFORE UPDATE ON industries FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # business_processes
    """
    CREATE TABLE business_processes (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      name text NOT NULL,
      slug text NOT NULL UNIQUE,
      parent_id uuid REFERENCES business_processes(id) ON DELETE SET NULL,
      description text,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TRIGGER trg_business_processes_updated_at
    BEFORE UPDATE ON business_processes FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # capabilities
    """
    CREATE TABLE capabilities (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      name text NOT NULL,
      slug text NOT NULL UNIQUE,
      category text NOT NULL,
      description text,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TRIGGER trg_capabilities_updated_at
    BEFORE UPDATE ON capabilities FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # organizations
    """
    CREATE TABLE organizations (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      name text NOT NULL,
      organization_type text NOT NULL,
      country_code text,
      website_url text,
      industry_id uuid REFERENCES industries(id) ON DELETE SET NULL,
      employee_band text,
      metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (name, country_code)
    );
    """,
    """
    CREATE TRIGGER trg_organizations_updated_at
    BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # claims
    """
    CREATE TABLE claims (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      claim_type text NOT NULL,
      statement text NOT NULL,
      normalized_value numeric,
      normalized_unit text,
      geography_codes text[] NOT NULL DEFAULT '{}',
      jurisdiction_codes text[] NOT NULL DEFAULT '{}',
      industry_id uuid REFERENCES industries(id) ON DELETE SET NULL,
      company_size_scope text,
      sample_size integer CHECK (sample_size IS NULL OR sample_size >= 0),
      study_period_start date,
      study_period_end date,
      valid_from date,
      valid_to date,
      confidence text NOT NULL DEFAULT 'unknown'
        CHECK (confidence IN ('unknown', 'low', 'medium', 'high')),
      confidence_rationale text,
      status text NOT NULL DEFAULT 'under_review'
        CHECK (status IN ('extracted', 'under_review', 'approved', 'published', 'rejected', 'superseded', 'archived')),
      analyst_notes text,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX ix_claims_type_status ON claims(claim_type, status);",
    "CREATE INDEX ix_claims_statement_fts ON claims USING gin(to_tsvector('simple', statement));",
    """
    CREATE TRIGGER trg_claims_updated_at
    BEFORE UPDATE ON claims FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # claim_evidence
    """
    CREATE TABLE claim_evidence (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      claim_id uuid NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
      document_id uuid NOT NULL REFERENCES documents(id) ON DELETE RESTRICT,
      chunk_id uuid REFERENCES document_chunks(id) ON DELETE SET NULL,
      page_number integer CHECK (page_number IS NULL OR page_number > 0),
      locator text,
      evidence_summary text NOT NULL,
      short_quote text CHECK (short_quote IS NULL OR char_length(short_quote) <= 500),
      relationship text NOT NULL
        CHECK (relationship IN ('supports', 'contradicts', 'qualifies', 'context')),
      created_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (claim_id, document_id, locator, relationship)
    );
    """,
    "CREATE INDEX ix_claim_evidence_claim ON claim_evidence(claim_id);",
    "CREATE INDEX ix_claim_evidence_document ON claim_evidence(document_id);",
    # use_cases
    """
    CREATE TABLE use_cases (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      slug text NOT NULL UNIQUE,
      title text NOT NULL,
      summary text NOT NULL,
      business_problem text NOT NULL,
      ai_pattern text NOT NULL,
      human_role text,
      expected_outcomes text[] NOT NULL DEFAULT '{}',
      required_data text[] NOT NULL DEFAULT '{}',
      integration_dependencies text[] NOT NULL DEFAULT '{}',
      maturity text NOT NULL DEFAULT 'candidate'
        CHECK (maturity IN ('candidate', 'emerging', 'established', 'mature')),
      lifecycle_status text NOT NULL DEFAULT 'under_review'
        CHECK (lifecycle_status IN ('under_review', 'approved', 'published', 'superseded', 'archived')),
      limitations text,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX ix_use_cases_pattern ON use_cases(ai_pattern);",
    "CREATE INDEX ix_use_cases_fts ON use_cases USING gin(to_tsvector('simple', title || ' ' || summary || ' ' || business_problem));",
    """
    CREATE TRIGGER trg_use_cases_updated_at
    BEFORE UPDATE ON use_cases FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # use_case_industries
    """
    CREATE TABLE use_case_industries (
      use_case_id uuid NOT NULL REFERENCES use_cases(id) ON DELETE CASCADE,
      industry_id uuid NOT NULL REFERENCES industries(id) ON DELETE CASCADE,
      relevance text NOT NULL DEFAULT 'applicable'
        CHECK (relevance IN ('primary', 'applicable', 'conditional')),
      PRIMARY KEY (use_case_id, industry_id)
    );
    """,
    # use_case_processes
    """
    CREATE TABLE use_case_processes (
      use_case_id uuid NOT NULL REFERENCES use_cases(id) ON DELETE CASCADE,
      process_id uuid NOT NULL REFERENCES business_processes(id) ON DELETE CASCADE,
      PRIMARY KEY (use_case_id, process_id)
    );
    """,
    # use_case_capabilities
    """
    CREATE TABLE use_case_capabilities (
      use_case_id uuid NOT NULL REFERENCES use_cases(id) ON DELETE CASCADE,
      capability_id uuid NOT NULL REFERENCES capabilities(id) ON DELETE CASCADE,
      importance text NOT NULL CHECK (importance IN ('required', 'recommended', 'advanced')),
      minimum_level text,
      PRIMARY KEY (use_case_id, capability_id)
    );
    """,
    # use_case_claims
    """
    CREATE TABLE use_case_claims (
      use_case_id uuid NOT NULL REFERENCES use_cases(id) ON DELETE CASCADE,
      claim_id uuid NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
      relationship text NOT NULL CHECK (relationship IN ('benefit', 'prerequisite', 'risk', 'implementation', 'context')),
      PRIMARY KEY (use_case_id, claim_id, relationship)
    );
    """,
    # case_studies
    """
    CREATE TABLE case_studies (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      organization_id uuid REFERENCES organizations(id) ON DELETE SET NULL,
      use_case_id uuid NOT NULL REFERENCES use_cases(id) ON DELETE RESTRICT,
      title text NOT NULL,
      deployment_stage text NOT NULL
        CHECK (deployment_stage IN ('experiment', 'poc', 'pilot', 'production', 'scaled', 'unknown')),
      self_reported boolean NOT NULL DEFAULT true,
      baseline_summary text,
      intervention_summary text NOT NULL,
      outcome_summary text,
      measurement_period text,
      transferability_notes text,
      status text NOT NULL DEFAULT 'under_review'
        CHECK (status IN ('under_review', 'approved', 'published', 'rejected', 'superseded', 'archived')),
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TRIGGER trg_case_studies_updated_at
    BEFORE UPDATE ON case_studies FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # case_study_claims
    """
    CREATE TABLE case_study_claims (
      case_study_id uuid NOT NULL REFERENCES case_studies(id) ON DELETE CASCADE,
      claim_id uuid NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
      PRIMARY KEY (case_study_id, claim_id)
    );
    """,
    # training_providers
    """
    CREATE TABLE training_providers (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      name text NOT NULL,
      organization_id uuid REFERENCES organizations(id) ON DELETE SET NULL,
      official_url text NOT NULL,
      provider_type text,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (name, official_url)
    );
    """,
    """
    CREATE TRIGGER trg_training_providers_updated_at
    BEFORE UPDATE ON training_providers FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # training_offerings
    """
    CREATE TABLE training_offerings (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      provider_id uuid NOT NULL REFERENCES training_providers(id) ON DELETE RESTRICT,
      title text NOT NULL,
      official_url text NOT NULL,
      target_roles text[] NOT NULL DEFAULT '{}',
      level text,
      language_codes text[] NOT NULL DEFAULT '{}',
      format text,
      duration_minutes integer CHECK (duration_minutes IS NULL OR duration_minutes >= 0),
      location text,
      price_amount numeric CHECK (price_amount IS NULL OR price_amount >= 0),
      price_currency text,
      price_observed_at date,
      certificate text,
      prerequisites text,
      next_start_at timestamptz,
      last_verified_at timestamptz,
      status text NOT NULL DEFAULT 'under_review'
        CHECK (status IN ('under_review', 'active', 'inactive', 'stale', 'archived')),
      metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (provider_id, official_url)
    );
    """,
    "CREATE INDEX ix_training_offerings_status ON training_offerings(status, last_verified_at);",
    """
    CREATE TRIGGER trg_training_offerings_updated_at
    BEFORE UPDATE ON training_offerings FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # training_capabilities
    """
    CREATE TABLE training_capabilities (
      training_id uuid NOT NULL REFERENCES training_offerings(id) ON DELETE CASCADE,
      capability_id uuid NOT NULL REFERENCES capabilities(id) ON DELETE CASCADE,
      coverage text NOT NULL CHECK (coverage IN ('introductory', 'working', 'advanced')),
      PRIMARY KEY (training_id, capability_id)
    );
    """,
    # regulations
    """
    CREATE TABLE regulations (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      title text NOT NULL,
      official_identifier text,
      jurisdiction_code text NOT NULL,
      official_url text NOT NULL,
      status text NOT NULL,
      published_at date,
      effective_from date,
      effective_to date,
      authoritative_source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
      notes text,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (jurisdiction_code, official_identifier)
    );
    """,
    """
    CREATE TRIGGER trg_regulations_updated_at
    BEFORE UPDATE ON regulations FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # regulatory_obligations
    """
    CREATE TABLE regulatory_obligations (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      regulation_id uuid NOT NULL REFERENCES regulations(id) ON DELETE CASCADE,
      article_or_section text,
      affected_actor text NOT NULL,
      obligation_summary text NOT NULL,
      applies_from date,
      applies_to text,
      authoritative_claim_id uuid REFERENCES claims(id) ON DELETE SET NULL,
      status text NOT NULL DEFAULT 'under_review'
        CHECK (status IN ('under_review', 'approved', 'published', 'superseded', 'archived')),
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    """
    CREATE TRIGGER trg_regulatory_obligations_updated_at
    BEFORE UPDATE ON regulatory_obligations FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # use_case_obligations
    """
    CREATE TABLE use_case_obligations (
      use_case_id uuid NOT NULL REFERENCES use_cases(id) ON DELETE CASCADE,
      obligation_id uuid NOT NULL REFERENCES regulatory_obligations(id) ON DELETE CASCADE,
      relevance text NOT NULL CHECK (relevance IN ('possible', 'likely', 'context_only')),
      rationale text NOT NULL,
      PRIMARY KEY (use_case_id, obligation_id)
    );
    """,
    # funding_programs
    """
    CREATE TABLE funding_programs (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      title text NOT NULL,
      provider text NOT NULL,
      official_url text NOT NULL,
      geography_codes text[] NOT NULL DEFAULT '{}',
      applicant_types text[] NOT NULL DEFAULT '{}',
      company_size_scope text,
      funding_form text,
      funding_rate numeric,
      maximum_amount numeric,
      currency text,
      opens_at timestamptz,
      deadline_at timestamptz,
      eligibility_summary text,
      last_verified_at timestamptz,
      status text NOT NULL DEFAULT 'under_review'
        CHECK (status IN ('under_review', 'open', 'closed', 'paused', 'stale', 'archived')),
      source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (provider, official_url)
    );
    """,
    "CREATE INDEX ix_funding_deadline ON funding_programs(status, deadline_at);",
    """
    CREATE TRIGGER trg_funding_programs_updated_at
    BEFORE UPDATE ON funding_programs FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # research_jobs
    """
    CREATE TABLE research_jobs (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      job_type text NOT NULL,
      source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
      status text NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'blocked', 'cancelled')),
      requested_by text NOT NULL,
      started_at timestamptz,
      finished_at timestamptz,
      input jsonb NOT NULL DEFAULT '{}'::jsonb,
      output_summary jsonb NOT NULL DEFAULT '{}'::jsonb,
      error_code text,
      error_detail text,
      created_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX ix_research_jobs_status ON research_jobs(status, created_at);",
    # review_items
    """
    CREATE TABLE review_items (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      entity_type text NOT NULL,
      entity_id uuid NOT NULL,
      review_type text NOT NULL,
      status text NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'in_progress', 'approved', 'rejected', 'needs_changes', 'cancelled')),
      priority smallint NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
      assigned_to text,
      decision_reason text,
      due_at timestamptz,
      decided_at timestamptz,
      created_at timestamptz NOT NULL DEFAULT now(),
      updated_at timestamptz NOT NULL DEFAULT now(),
      UNIQUE (entity_type, entity_id, review_type, status)
    );
    """,
    "CREATE INDEX ix_review_items_queue ON review_items(status, priority, created_at);",
    """
    CREATE TRIGGER trg_review_items_updated_at
    BEFORE UPDATE ON review_items FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    # audit_events
    """
    CREATE TABLE audit_events (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
      actor_type text NOT NULL,
      actor_id text NOT NULL,
      action text NOT NULL,
      entity_type text NOT NULL,
      entity_id uuid,
      request_id text,
      before_state jsonb,
      after_state jsonb,
      metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      occurred_at timestamptz NOT NULL DEFAULT now()
    );
    """,
    "CREATE INDEX ix_audit_events_entity ON audit_events(entity_type, entity_id, occurred_at DESC);",
    "CREATE INDEX ix_audit_events_actor ON audit_events(actor_id, occurred_at DESC);",
]

# Tables in FK-safe drop order (children before parents) for downgrade().
_TABLES_DROP_ORDER: list[str] = [
    "audit_events",
    "review_items",
    "research_jobs",
    "funding_programs",
    "use_case_obligations",
    "regulatory_obligations",
    "regulations",
    "training_capabilities",
    "training_offerings",
    "training_providers",
    "case_study_claims",
    "case_studies",
    "use_case_claims",
    "use_case_capabilities",
    "use_case_processes",
    "use_case_industries",
    "use_cases",
    "claim_evidence",
    "claims",
    "organizations",
    "capabilities",
    "business_processes",
    "industries",
    "document_chunks",
    "documents",
    "source_snapshots",
    "source_quality_evaluations",
    "sources",
]


def upgrade() -> None:
    for statement in _STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    for table in _TABLES_DROP_ORDER:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS prevent_snapshot_update();")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")
