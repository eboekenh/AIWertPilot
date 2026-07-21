import { Badge } from "@/components/ui/Badge";
import { SOURCE_STATUS_META, metaOrFallback } from "@/lib/enums";

/** Renders a source's lifecycle status (sources.status). */
export function StatusBadge({ status }: { status: string }) {
  const meta = metaOrFallback(SOURCE_STATUS_META, status);
  return <Badge label={meta.label} tone={meta.tone} title={`Status: ${status}`} />;
}
