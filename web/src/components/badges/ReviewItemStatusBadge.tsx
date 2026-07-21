import { Badge } from "@/components/ui/Badge";
import { REVIEW_ITEM_STATUS_META, REVIEW_TYPE_META, metaOrFallback } from "@/lib/enums";

/** Renders a review_items.status value. */
export function ReviewItemStatusBadge({ status }: { status: string }) {
  const meta = metaOrFallback(REVIEW_ITEM_STATUS_META, status);
  return <Badge label={meta.label} tone={meta.tone} title={`Status: ${status}`} />;
}

/** Renders a review_items.review_type value (free text on the backend —
 * rights_review/content_review/dedup_candidate are the values this app
 * knows about; anything else falls back to the raw value). */
export function ReviewTypeBadge({ reviewType }: { reviewType: string }) {
  const meta = metaOrFallback(REVIEW_TYPE_META, reviewType);
  return <Badge label={meta.label} tone={meta.tone} title={`Prüfungsart: ${reviewType}`} />;
}
