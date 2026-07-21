import type { ReactNode } from "react";

/** Actionable error state. `message` must already be a safe, user-facing
 * string (e.g. ApiError.message) — never render a raw exception or stack
 * trace here. */
export function ErrorState({
  title = "Etwas ist schiefgelaufen",
  message,
  action,
}: {
  title?: string;
  message: string;
  action?: ReactNode;
}) {
  return (
    <div
      role="alert"
      className="rounded-lg border border-rose-300 bg-rose-50 p-6 dark:border-rose-800 dark:bg-rose-950/40"
    >
      <p className="text-sm font-semibold text-rose-800 dark:text-rose-200">{title}</p>
      <p className="mt-1 text-sm text-rose-700 dark:text-rose-300">{message}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
