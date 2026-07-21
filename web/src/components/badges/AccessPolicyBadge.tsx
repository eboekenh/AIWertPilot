import { Badge } from "@/components/ui/Badge";
import { ACCESS_POLICY_META, metaOrFallback } from "@/lib/enums";

/** Renders a source's access_policy. */
export function AccessPolicyBadge({ accessPolicy }: { accessPolicy: string }) {
  const meta = metaOrFallback(ACCESS_POLICY_META, accessPolicy);
  return <Badge label={meta.label} tone={meta.tone} title={`Zugriffsrichtlinie: ${accessPolicy}`} />;
}
