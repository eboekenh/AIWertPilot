"use client";

import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

export interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  pending?: boolean;
  /** Confirm is disabled while this is true — used e.g. to require a
   * non-blank reason before a destructive action can be confirmed. */
  confirmDisabled?: boolean;
  /** Extra form content rendered between the description and the action
   * buttons (e.g. a mandatory reason field for blocking a source). */
  children?: ReactNode;
  onConfirm: () => void;
  onCancel: () => void;
}

/** Accessible confirmation dialog: focuses the confirm button on open,
 * closes on Escape, and traps neither pointer clicks inside the panel nor
 * background scroll beyond a simple overlay — kept intentionally simple
 * for this internal tool rather than pulling in a dialog library. */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Bestätigen",
  cancelLabel = "Abbrechen",
  destructive = false,
  pending = false,
  confirmDisabled = false,
  children,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const confirmRef = useRef<HTMLButtonElement>(null);

  // Only on the open/close transition, not on every render: callers
  // typically pass a fresh onCancel closure each render (e.g. a
  // component-local `close` function), and re-focusing the confirm button
  // on every such render would repeatedly steal focus away from any input
  // inside the dialog while the user is still typing into it.
  useEffect(() => {
    if (!open) return;
    confirmRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onCancel]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
      onClick={onCancel}
    >
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby={description ? "confirm-dialog-description" : undefined}
        className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl dark:bg-slate-900"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="confirm-dialog-title" className="text-base font-semibold text-slate-900 dark:text-slate-100">
          {title}
        </h2>
        {description ? (
          <p id="confirm-dialog-description" className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            {description}
          </p>
        ) : null}
        {children ? <div className="mt-4">{children}</div> : null}
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            {cancelLabel}
          </button>
          <button
            ref={confirmRef}
            type="button"
            onClick={onConfirm}
            disabled={pending || confirmDisabled}
            className={`rounded-md px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60 ${
              destructive ? "bg-rose-600 hover:bg-rose-700" : "bg-slate-900 hover:bg-slate-800"
            }`}
          >
            {pending ? "Wird ausgeführt…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
