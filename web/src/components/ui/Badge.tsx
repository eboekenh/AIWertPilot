import type { Tone } from "@/lib/enums";

const TONE_CLASSES: Record<Tone, string> = {
  neutral:
    "bg-slate-100 text-slate-700 ring-slate-300 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-600",
  info: "bg-sky-100 text-sky-800 ring-sky-300 dark:bg-sky-900/40 dark:text-sky-200 dark:ring-sky-700",
  warning:
    "bg-amber-100 text-amber-800 ring-amber-300 dark:bg-amber-900/40 dark:text-amber-200 dark:ring-amber-700",
  success:
    "bg-emerald-100 text-emerald-800 ring-emerald-300 dark:bg-emerald-900/40 dark:text-emerald-200 dark:ring-emerald-700",
  danger: "bg-rose-100 text-rose-800 ring-rose-300 dark:bg-rose-900/40 dark:text-rose-200 dark:ring-rose-700",
};

export interface BadgeProps {
  label: string;
  tone: Tone;
  title?: string;
}

/** Generic status pill. Always renders a text label, never color alone —
 * status must remain understandable without relying on color perception. */
export function Badge({ label, tone, title }: BadgeProps) {
  return (
    <span
      title={title}
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset whitespace-nowrap ${TONE_CLASSES[tone]}`}
    >
      {label}
    </span>
  );
}
