/** Accessible loading indicator for a content region. Server Components in
 * this app mostly load data before rendering (no client-side spinner
 * needed for the initial page load), so this is used inside
 * <Suspense fallback> boundaries and by client components that trigger a
 * refetch (e.g. after a write action). */
export function LoadingState({ label = "Wird geladen…" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-3 rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
      <span
        aria-hidden="true"
        className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600 dark:border-slate-600 dark:border-t-slate-300"
      />
      <span>{label}</span>
    </div>
  );
}
