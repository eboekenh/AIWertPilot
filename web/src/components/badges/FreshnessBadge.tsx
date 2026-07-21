import { Badge } from "@/components/ui/Badge";
import { FRESHNESS_STATE_META, metaOrFallback } from "@/lib/enums";

/** Renders a freshness_state value computed by the backend
 * (domain/freshness.py) — never computed client-side, so it always
 * matches what the backend's own freshness/dedup/CLI tooling would say. */
export function FreshnessBadge({ freshnessState }: { freshnessState: string }) {
  const meta = metaOrFallback(FRESHNESS_STATE_META, freshnessState);
  return <Badge label={meta.label} tone={meta.tone} title={`Aktualität: ${freshnessState}`} />;
}
