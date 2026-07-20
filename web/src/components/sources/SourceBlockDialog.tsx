"use client";

import { useState } from "react";

import { ActionError } from "@/components/ui/ActionError";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { dangerButtonClass, inputClass } from "@/components/ui/formClasses";
import { blockSource } from "@/lib/api/actions";
import type { SourceRead } from "@/lib/api/types";
import { useActionResult } from "@/lib/useActionResult";

/** Blocking (takedown) is a dedicated, separately audited workflow — the
 * backend's POST /sources/{id}/block, not the generic transition endpoint.
 * A non-blank reason is mandatory: the confirm button stays disabled until
 * the reason field has non-whitespace content, mirroring (not replacing)
 * the backend's own non-blank check. */
export function SourceBlockDialog({ source }: { source: SourceRead }) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const { execute, isPending, result, reset } = useActionResult<SourceRead>();

  function close() {
    setOpen(false);
    setReason("");
    reset();
  }

  function handleConfirm() {
    execute(() => blockSource(source.id, { reason: reason.trim() }));
  }

  if (source.status === "blocked") {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Diese Quelle ist bereits gesperrt.</p>;
  }

  return (
    <>
      <button type="button" onClick={() => setOpen(true)} className={dangerButtonClass}>
        Quelle sperren
      </button>
      {result?.ok ? (
        <p className="mt-2 text-sm font-medium text-emerald-700 dark:text-emerald-300">
          Quelle wurde gesperrt.
        </p>
      ) : null}
      <ConfirmDialog
        open={open}
        title="Quelle sperren"
        description={`„${source.title}“ wird gesperrt (Status: gesperrt). Dieser Schritt wird protokolliert.`}
        confirmLabel="Sperren"
        destructive
        pending={isPending}
        confirmDisabled={reason.trim().length === 0}
        onConfirm={handleConfirm}
        onCancel={close}
      >
        <label htmlFor="block-reason" className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
          Begründung (erforderlich)
        </label>
        <textarea
          id="block-reason"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          rows={3}
          required
          className={inputClass}
        />
        {result && !result.ok ? (
          <div className="mt-2">
            <ActionError error={result.error} />
          </div>
        ) : null}
      </ConfirmDialog>
    </>
  );
}
