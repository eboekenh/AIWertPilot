/**
 * review_items.status values that represent "not yet decided" (the
 * backend's REVIEW_ITEM_STATUS_TRANSITIONS treats "open", "in_progress",
 * and "needs_changes" as all having further legal transitions, while
 * "approved"/"rejected"/"cancelled" are terminal — see
 * src/de_ai_kb/domain/enums.py). Kept in exactly one place so the
 * dashboard and review workspace can never silently disagree about what
 * counts as "still needs a decision" — e.g. a source whose content_review
 * was sent back with needs_changes must count as needing review on both
 * pages, not just on one of them.
 */
export const OPEN_REVIEW_ITEM_STATUSES = ["open", "in_progress", "needs_changes"] as const;

export function isOpenReviewItemStatus(status: string): boolean {
  return (OPEN_REVIEW_ITEM_STATUSES as readonly string[]).includes(status);
}
