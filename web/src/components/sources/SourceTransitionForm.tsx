"use client";

import type { FormEvent } from "react";

import { ActionError } from "@/components/ui/ActionError";
import { FormField } from "@/components/ui/FormField";
import { inputClass, primaryButtonClass } from "@/components/ui/formClasses";
import { transitionSource } from "@/lib/api/actions";
import { SOURCE_STATUSES, type SourceRead, type SourceStatus } from "@/lib/api/types";
import { SOURCE_STATUS_META, metaOrFallback } from "@/lib/enums";
import { useActionResult } from "@/lib/useActionResult";

/** SOURCE_STATUSES minus "blocked" (blocking is a dedicated, separately
 * audited workflow — see SourceBlockDialog) and minus the source's current
 * status. The backend independently rejects new_status="blocked" here and
 * remains the sole authority on which transitions are actually valid from
 * the current status; this form does not reproduce that transition table,
 * it just avoids offering the one status that can never be sent here. */
function transitionableStatuses(current: string): SourceStatus[] {
  return SOURCE_STATUSES.filter((status) => status !== "blocked" && status !== current);
}

export function SourceTransitionForm({ source }: { source: SourceRead }) {
  const { execute, isPending, result } = useActionResult<SourceRead>();
  const options = transitionableStatuses(source.status);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const newStatus = String(form.get("new_status")) as Exclude<SourceStatus, "blocked">;
    const reason = String(form.get("reason") ?? "").trim();

    execute(() => transitionSource(source.id, { new_status: newStatus, reason: reason || null }));
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3" aria-label="Statusübergang">
      <FormField label="Neuer Status" htmlFor="transition-status">
        <select id="transition-status" name="new_status" required className={inputClass}>
          {options.map((status) => (
            <option key={status} value={status}>
              {metaOrFallback(SOURCE_STATUS_META, status).label}
            </option>
          ))}
        </select>
      </FormField>
      <FormField label="Begründung (optional)" htmlFor="transition-reason">
        <input id="transition-reason" name="reason" className={inputClass} />
      </FormField>

      {result && !result.ok ? <ActionError error={result.error} /> : null}
      {result?.ok ? (
        <p className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
          Status geändert zu &quot;{metaOrFallback(SOURCE_STATUS_META, result.data.status).label}&quot;.
        </p>
      ) : null}

      <button type="submit" disabled={isPending} className={primaryButtonClass}>
        {isPending ? "Wird übertragen…" : "Status ändern"}
      </button>
    </form>
  );
}
