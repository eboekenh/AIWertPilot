import { Card } from "@/components/ui/Card";
import { DevWritesNotice } from "@/components/ui/DevWritesNotice";
import type { SourceRead } from "@/lib/api/types";

import { SourceBlockDialog } from "./SourceBlockDialog";
import { SourceTransitionForm } from "./SourceTransitionForm";

export function SourceActionsPanel({
  source,
  devWritesEnabled,
}: {
  source: SourceRead;
  devWritesEnabled: boolean;
}) {
  if (!devWritesEnabled) {
    return (
      <Card>
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Statusaktionen</h2>
        <div className="mt-3">
          <DevWritesNotice />
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Status ändern</h2>
        <div className="mt-3">
          <SourceTransitionForm source={source} />
        </div>
      </Card>
      <Card>
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Sperren</h2>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Nur für Takedown-Fälle. Erfordert eine Begründung und wird protokolliert.
        </p>
        <div className="mt-3">
          <SourceBlockDialog source={source} />
        </div>
      </Card>
    </div>
  );
}
