"use client";

import { useState } from "react";

import { ReviewItemStatusBadge, ReviewTypeBadge } from "@/components/badges/ReviewItemStatusBadge";
import { Card } from "@/components/ui/Card";
import { DevWritesNotice } from "@/components/ui/DevWritesNotice";
import { REVIEW_TYPE_RIGHTS, type ReviewItemRead } from "@/lib/api/types";
import { formatDateTime } from "@/lib/format";

import { ReviewDecisionForm } from "./ReviewDecisionForm";
import { RightsDecisionForm } from "./RightsDecisionForm";

const OPEN_STATUSES = new Set(["open", "in_progress", "needs_changes"]);

function ReviewItemCard({ reviewItem, devWritesEnabled }: { reviewItem: ReviewItemRead; devWritesEnabled: boolean }) {
  const [showAlternative, setShowAlternative] = useState(false);
  const isOpen = OPEN_STATUSES.has(reviewItem.status);
  const isRights = reviewItem.review_type === REVIEW_TYPE_RIGHTS;

  return (
    <Card>
      <div className="flex flex-wrap items-center gap-2">
        <ReviewTypeBadge reviewType={reviewItem.review_type} />
        <ReviewItemStatusBadge status={reviewItem.status} />
      </div>
      <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400">
        <dt>Erstellt</dt>
        <dd>{formatDateTime(reviewItem.created_at)}</dd>
        {reviewItem.decided_at ? (
          <>
            <dt>Entschieden</dt>
            <dd>{formatDateTime(reviewItem.decided_at)}</dd>
          </>
        ) : null}
      </dl>
      {reviewItem.decision_reason ? (
        <p className="mt-2 text-sm text-slate-700 dark:text-slate-200">
          <span className="font-medium">Begründung:</span> {reviewItem.decision_reason}
        </p>
      ) : null}

      {isOpen ? (
        devWritesEnabled ? (
          <div className="mt-4 border-t border-slate-200 pt-4 dark:border-slate-800">
            {isRights && !showAlternative ? (
              <>
                <RightsDecisionForm reviewItem={reviewItem} />
                <button
                  type="button"
                  onClick={() => setShowAlternative(true)}
                  className="mt-3 text-xs font-medium text-slate-500 underline dark:text-slate-400"
                >
                  Stattdessen ablehnen / Änderungen anfordern / abbrechen
                </button>
              </>
            ) : (
              <>
                <ReviewDecisionForm reviewItem={reviewItem} />
                {isRights ? (
                  <button
                    type="button"
                    onClick={() => setShowAlternative(false)}
                    className="mt-3 text-xs font-medium text-slate-500 underline dark:text-slate-400"
                  >
                    Zurück zur Rechteentscheidung
                  </button>
                ) : null}
              </>
            )}
          </div>
        ) : (
          <div className="mt-4 border-t border-slate-200 pt-4 dark:border-slate-800">
            <DevWritesNotice />
          </div>
        )
      ) : null}
    </Card>
  );
}

export function ReviewActionPanel({
  reviewItems,
  devWritesEnabled,
}: {
  reviewItems: ReviewItemRead[];
  devWritesEnabled: boolean;
}) {
  if (reviewItems.length === 0) {
    return <p className="text-sm text-slate-500 dark:text-slate-400">Keine Prüfaufgaben für diese Quelle.</p>;
  }

  return (
    <div className="space-y-3">
      {reviewItems.map((item) => (
        <ReviewItemCard key={item.id} reviewItem={item} devWritesEnabled={devWritesEnabled} />
      ))}
    </div>
  );
}
