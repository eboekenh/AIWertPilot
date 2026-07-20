/**
 * Frontend mirrors of the backend's state-transition tables
 * (src/de_ai_kb/domain/enums.py: SOURCE_STATUS_TRANSITIONS,
 * REVIEW_ITEM_STATUS_TRANSITIONS) and rights/access-policy consistency
 * rules (src/de_ai_kb/domain/rights_policy.py:
 * ALLOWED_ACCESS_POLICIES_BY_RIGHTS_STATUS).
 *
 * These exist ONLY to decide which options a dropdown offers, so the UI
 * doesn't invite a user to attempt something the backend will certainly
 * reject. They are never used to accept, reject, or validate a request —
 * the backend independently re-validates every transition and combination
 * (see src/lib/api/validate.ts's own comment on this same boundary) and
 * remains the sole authority. If this mirror ever drifts out of sync with
 * the backend, the backend still rejects an invalid request; the only
 * consequence is the UI briefly offering (or withholding) the wrong
 * option. Keep this in sync by hand when the backend files above change —
 * see web/README.md "Keeping types in sync with the backend".
 */

import type { AccessPolicy, ReviewItemStatus, RightsStatus, SourceStatus } from "./api/types";

export const SOURCE_STATUS_TRANSITIONS: Record<SourceStatus, readonly SourceStatus[]> = {
  discovered: ["registered", "rejected", "blocked"],
  registered: ["fetched", "rejected", "blocked", "superseded", "archived"],
  fetched: ["extracted", "rejected", "blocked", "superseded"],
  extracted: ["under_review", "rejected", "blocked", "superseded"],
  under_review: ["approved", "rejected", "blocked", "superseded"],
  approved: ["published", "blocked", "superseded"],
  published: ["superseded", "archived", "blocked"],
  rejected: ["archived", "registered"],
  blocked: ["archived"],
  superseded: ["archived"],
  archived: [],
};

/** SOURCE_STATUS_TRANSITIONS[currentStatus], minus "blocked". Blocking is
 * always a dedicated workflow (SourceBlockDialog) with its own
 * mandatory-reason confirmation, never a generic transition target. */
export function allowedTransitionTargets(currentStatus: string): SourceStatus[] {
  const targets = SOURCE_STATUS_TRANSITIONS[currentStatus as SourceStatus] ?? [];
  return targets.filter((status) => status !== "blocked");
}

export const REVIEW_ITEM_STATUS_TRANSITIONS: Record<ReviewItemStatus, readonly ReviewItemStatus[]> = {
  open: ["in_progress", "approved", "rejected", "needs_changes", "cancelled"],
  in_progress: ["approved", "rejected", "needs_changes", "cancelled"],
  needs_changes: ["in_progress", "approved", "rejected", "cancelled"],
  approved: [],
  rejected: [],
  cancelled: [],
};

/** REVIEW_ITEM_STATUS_TRANSITIONS[currentStatus], with "approved" excluded
 * whenever reviewType is "rights_review" — approving a rights_review
 * always requires the dedicated rights-decision workflow
 * (RightsDecisionForm / POST .../rights-decision), never the generic
 * decision endpoint (the backend rejects an attempt to do so with 422
 * regardless of what this function returns). */
export function allowedReviewDecisionTargets(currentStatus: string, reviewType: string): ReviewItemStatus[] {
  const targets = REVIEW_ITEM_STATUS_TRANSITIONS[currentStatus as ReviewItemStatus] ?? [];
  if (reviewType === "rights_review") {
    return targets.filter((status) => status !== "approved");
  }
  return [...targets];
}

/** rights_status values a completed rights review may resolve to.
 * "needs_review" is deliberately absent: it means "not yet reviewed" and
 * can never be the *outcome* of a review decision. */
export const COMPLETED_RIGHTS_STATUSES: readonly Exclude<RightsStatus, "needs_review">[] = [
  "reviewed_allowed",
  "reviewed_restricted",
  "blocked",
];

/** Mirrors domain/rights_policy.py's ALLOWED_ACCESS_POLICIES_BY_RIGHTS_STATUS:
 * "blocked" only ever pairs with access_policy="blocked" (a blocked rights
 * result must never permit any retention), and "reviewed_restricted"
 * excludes "full_text_allowed" (restricted rights must not grant full-text
 * retention). */
const ALLOWED_ACCESS_POLICIES_BY_RIGHTS_STATUS: Record<
  Exclude<RightsStatus, "needs_review">,
  readonly AccessPolicy[]
> = {
  reviewed_allowed: ["metadata_only", "short_evidence", "full_text_allowed"],
  reviewed_restricted: ["metadata_only", "short_evidence"],
  blocked: ["blocked"],
};

export function allowedAccessPoliciesFor(rightsStatus: string): readonly AccessPolicy[] {
  return ALLOWED_ACCESS_POLICIES_BY_RIGHTS_STATUS[rightsStatus as Exclude<RightsStatus, "needs_review">] ?? [];
}
