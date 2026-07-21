import type { ReviewItemRead, SourceRead } from "@/lib/api/types";

export function makeSource(overrides: Partial<SourceRead> = {}): SourceRead {
  return {
    id: "00000000-0000-0000-0000-000000000001",
    source_key: "TEST_SOURCE",
    title: "Test Source",
    publisher: "Test Publisher",
    original_url: "https://example.com/report",
    canonical_url: "https://example.com/report",
    source_type: "official_statistics",
    tier: "A",
    language_code: "de",
    geography_codes: ["DE"],
    jurisdiction_codes: [],
    topic_tags: ["adoption"],
    access_policy: "metadata_only",
    rights_status: "needs_review",
    tdm_opt_out_status: "unknown",
    licence_name: null,
    licence_url: null,
    refresh_interval_days: 90,
    last_verified_at: null,
    next_review_at: null,
    status: "registered",
    notes: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

export function makeReviewItem(overrides: Partial<ReviewItemRead> = {}): ReviewItemRead {
  return {
    id: "10000000-0000-0000-0000-000000000001",
    entity_type: "source",
    entity_id: "00000000-0000-0000-0000-000000000001",
    review_type: "rights_review",
    status: "open",
    priority: 3,
    assigned_to: null,
    decision_reason: null,
    due_at: null,
    decided_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}
