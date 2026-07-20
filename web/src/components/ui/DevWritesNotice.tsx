/** Shown wherever write controls would otherwise appear, so it's clear
 * *why* they're hidden rather than the UI silently looking incomplete. */
export function DevWritesNotice() {
  return (
    <p className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
      Schreibaktionen sind deaktiviert. Setzen Sie{" "}
      <code className="rounded bg-slate-200 px-1 py-0.5 dark:bg-slate-800">ENABLE_DEV_WRITES=true</code>{" "}
      in einer lokalen Entwicklungsumgebung, um sie anzuzeigen.
    </p>
  );
}
