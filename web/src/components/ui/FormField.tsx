import type { ReactNode } from "react";

export function FormField({
  label,
  htmlFor,
  hint,
  children,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div>
      <label htmlFor={htmlFor} className="mb-1 block text-xs font-medium text-slate-600 dark:text-slate-400">
        {label}
      </label>
      {children}
      {hint ? <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{hint}</p> : null}
    </div>
  );
}
