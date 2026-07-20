import type { ReactNode } from "react";

import { Card } from "@/components/ui/Card";

export function DistributionCard({
  title,
  counts,
  renderBadge,
}: {
  title: string;
  counts: Record<string, number>;
  renderBadge: (value: string) => ReactNode;
}) {
  const entries = Object.entries(counts).sort(([, a], [, b]) => b - a);

  return (
    <Card>
      <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
      {entries.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Keine Daten.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {entries.map(([value, count]) => (
            <li key={value} className="flex items-center justify-between gap-3 text-sm">
              {renderBadge(value)}
              <span className="font-medium text-slate-700 dark:text-slate-200">{count}</span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export function countBy<T>(items: T[], keyOf: (item: T) => string): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const item of items) {
    const key = keyOf(item);
    counts[key] = (counts[key] ?? 0) + 1;
  }
  return counts;
}
