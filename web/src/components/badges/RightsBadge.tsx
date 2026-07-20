import { Badge } from "@/components/ui/Badge";
import { RIGHTS_STATUS_META, metaOrFallback } from "@/lib/enums";

/** Renders a source's rights_status. */
export function RightsBadge({ rightsStatus }: { rightsStatus: string }) {
  const meta = metaOrFallback(RIGHTS_STATUS_META, rightsStatus);
  return <Badge label={meta.label} tone={meta.tone} title={`Rechtestatus: ${rightsStatus}`} />;
}
