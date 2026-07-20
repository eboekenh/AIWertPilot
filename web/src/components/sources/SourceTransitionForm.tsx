"use client";

import type { FormEvent } from "react";

import { ActionError } from "@/components/ui/ActionError";
import { FormField } from "@/components/ui/FormField";
import { inputClass, primaryButtonClass } from "@/components/ui/formClasses";
import { transitionSource } from "@/lib/api/actions";
import type { SourceRead, SourceStatus } from "@/lib/api/types";
import { SOURCE_STATUS_META, metaOrFallback } from "@/lib/enums";
import { allowedTransitionTargets } from "@/lib/transitions";
import { useActionResult } from "@/lib/useActionResult";

export function SourceTransitionForm({ source }: { source: SourceRead }) {
  const { execute, isPending, result } = useActionResult<SourceRead>();
  const options = allowedTransitionTargets(source.status);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const newStatus = String(form.get("new_status")) as Exclude<SourceStatus, "blocked">;
    const reason = String(form.get("reason") ?? "").trim();

    execute(() => transitionSource(source.id, { new_status: newStatus, reason: reason || null }));
  }

  if (options.length === 0) {
    return (
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Aus dem aktuellen Status (&quot;{metaOrFallback(SOURCE_STATUS_META, source.status).label}&quot;) sind
        keine weiteren Statusübergänge möglich.
      </p>
    );
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
