/**
 * TypeScript mirrors of the backend's Pydantic v2 schemas
 * (src/de_ai_kb/api/schemas/*.py) and enums (src/de_ai_kb/domain/enums.py).
 *
 * These are hand-derived from the actual backend source, not guessed and
 * not generated from an OpenAPI spec. If the backend schemas change, these
 * types must be updated to match — see web/README.md "Keeping types in
 * sync with the backend" for the exact files to diff against.
 *
 * Every field here corresponds 1:1 to a field the backend actually returns
 * or accepts today. Nothing here is aspirational.
 */

// --- Enums (src/de_ai_kb/domain/enums.py) -----------------------------------
// Kept centrally in this one file (plus lib/enums.ts for display labels) so
// there is exactly one place these value sets can drift from the backend,
// rather than being re-typed ad hoc across components.

export const SOURCE_TIERS = ["A", "B", "C", "D", "E"] as const;
export type SourceTier = (typeof SOURCE_TIERS)[number];

export const ACCESS_POLICIES = [
  "metadata_only",
  "short_evidence",
  "full_text_allowed",
  "blocked",
  "unknown",
] as const;
export type AccessPolicy = (typeof ACCESS_POLICIES)[number];

export const RIGHTS_STATUSES = [
  "needs_review",
  "reviewed_allowed",
  "reviewed_restricted",
  "blocked",
] as const;
export type RightsStatus = (typeof RIGHTS_STATUSES)[number];

export const TDM_OPT_OUT_STATUSES = ["unknown", "not_found", "reserved", "not_applicable"] as const;
export type TdmOptOutStatus = (typeof TDM_OPT_OUT_STATUSES)[number];

export const SOURCE_STATUSES = [
  "discovered",
  "registered",
  "fetched",
  "extracted",
  "under_review",
  "approved",
  "published",
  "rejected",
  "blocked",
  "superseded",
  "archived",
] as const;
export type SourceStatus = (typeof SOURCE_STATUSES)[number];

export const REVIEW_ITEM_STATUSES = [
  "open",
  "in_progress",
  "approved",
  "rejected",
  "needs_changes",
  "cancelled",
] as const;
export type ReviewItemStatus = (typeof REVIEW_ITEM_STATUSES)[number];

export const FRESHNESS_STATES = ["fresh", "due_soon", "stale", "unknown"] as const;
export type FreshnessState = (typeof FRESHNESS_STATES)[number];

/** review_items.review_type is free text on the backend (not an enum) —
 * these are the two values every source registration creates today. */
export const REVIEW_TYPE_RIGHTS = "rights_review";
export const REVIEW_TYPE_CONTENT = "content_review";
export const REVIEW_TYPE_DEDUP_CANDIDATE = "dedup_candidate";

// --- Common envelopes (src/de_ai_kb/api/schemas/common.py) ------------------

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

export interface ApiErrorEnvelope {
  error: ApiErrorDetail;
}

/** Discriminated result returned by every Server Action in
 * src/lib/api/actions.ts, so a failed write (backend validation error,
 * disabled dev-writes, network failure) is a normal return value a
 * component can render inline — never an uncaught exception. */
export type ActionResult<T> = { ok: true; data: T } | { ok: false; error: ApiErrorDetail };

// --- Sources (src/de_ai_kb/api/schemas/sources.py) --------------------------

export interface SourceRead {
  id: string;
  source_key: string;
  title: string;
  publisher: string;
  original_url: string;
  canonical_url: string;
  source_type: string;
  tier: string;
  language_code: string;
  geography_codes: string[];
  jurisdiction_codes: string[];
  topic_tags: string[];
  access_policy: string;
  rights_status: string;
  tdm_opt_out_status: string;
  licence_name: string | null;
  licence_url: string | null;
  refresh_interval_days: number;
  last_verified_at: string | null;
  next_review_at: string | null;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

/** Fields accepted by POST /api/v1/sources. Deliberately excludes
 * status/rights_status/access_policy — SourceCreate on the backend has no
 * such fields at all (extra="forbid"); every new source always starts at
 * status=registered/rights_status=needs_review/access_policy=metadata_only. */
export interface SourceCreateInput {
  source_key: string;
  title: string;
  publisher: string;
  original_url: string;
  source_type: string;
  tier: SourceTier;
  language_code?: string;
  geography_codes?: string[];
  jurisdiction_codes?: string[];
  topic_tags?: string[];
  refresh_interval_days?: number;
  notes?: string | null;
}

/** Fields accepted by PATCH /api/v1/sources/{id}. Deliberately excludes
 * status/rights_status/access_policy — those require the dedicated
 * transition/block/rights-decision workflows below. */
export interface SourceUpdateInput {
  title?: string;
  publisher?: string;
  tier?: SourceTier;
  topic_tags?: string[];
  refresh_interval_days?: number;
  notes?: string | null;
}

/** POST /api/v1/sources/{id}/transition. new_status="blocked" is rejected
 * by the backend (422) — use SourceBlockInput / blockSource instead. */
export interface SourceTransitionInput {
  new_status: Exclude<SourceStatus, "blocked">;
  reason?: string | null;
}

/** POST /api/v1/sources/{id}/block. reason is mandatory and must be
 * non-blank (enforced by the backend at both the schema and service layer). */
export interface SourceBlockInput {
  reason: string;
}

export interface FreshnessReportItemRead {
  source_id: string;
  source_key: string;
  title: string;
  status: string;
  last_verified_at: string | null;
  refresh_interval_days: number;
  freshness_state: FreshnessState;
}

// --- Review items (src/de_ai_kb/api/schemas/review_items.py) ----------------

export interface ReviewItemRead {
  id: string;
  entity_type: string;
  entity_id: string;
  review_type: string;
  status: string;
  priority: number;
  assigned_to: string | null;
  decision_reason: string | null;
  due_at: string | null;
  decided_at: string | null;
  created_at: string;
  updated_at: string;
}

/** POST /api/v1/review-items/{id}/decision. The backend rejects
 * status="approved" for a rights_review item (422) — use
 * RightsReviewDecisionInput / resolveRightsReview instead. */
export interface ReviewDecisionInput {
  status: Exclude<ReviewItemStatus, "approved"> | "approved";
  decision_reason?: string | null;
}

/** POST /api/v1/review-items/{id}/rights-decision. decision_reason must be
 * non-blank; rights_status/access_policy must form a valid pair (validated
 * by the backend's domain/rights_policy.py) or the request is rejected
 * with 422 and neither the review item nor the source is changed. */
export interface RightsReviewDecisionInput {
  rights_status: RightsStatus;
  access_policy: AccessPolicy;
  decision_reason: string;
  tdm_opt_out_status?: TdmOptOutStatus | null;
  licence_name?: string | null;
  licence_url?: string | null;
}

export interface RightsReviewDecisionResult {
  review_item: ReviewItemRead;
  source: SourceRead;
}

// --- List filters (mirror the real query parameters the backend accepts) ---

export interface SourceListParams {
  tier?: string;
  source_type?: string;
  topic?: string;
  publisher?: string;
  language?: string;
  status?: string;
  freshness?: FreshnessState;
  limit?: number;
  offset?: number;
}

export interface ReviewItemListParams {
  status?: string;
  review_type?: string;
  entity_type?: string;
  limit?: number;
  offset?: number;
}
