import { Card } from "./Card";

export function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: number | string;
  hint?: string;
}) {
  return (
    <Card>
      <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-1 text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{hint}</p> : null}
    </Card>
  );
}
