"use client";

import type { FormEvent } from "react";

import { ActionError } from "@/components/ui/ActionError";
import { FormField } from "@/components/ui/FormField";
import { inputClass, primaryButtonClass } from "@/components/ui/formClasses";
import { decideReviewItem } from "@/lib/api/actions";
import { REVIEW_ITEM_STATUSES, REVIEW_TYPE_RIGHTS, type ReviewItemRead, type ReviewItemStatus } from "@/lib/api/types";
import { REVIEW_ITEM_STATUS_META, metaOrFallback } from "@/lib/enums";
import { useActionResult } from "@/lib/useActionResult";

/**
 * Generic review decision (POST /api/v1/review-items/{id}/decision) — used
 * for content_review, dedup_candidate, and non-approval outcomes of a
 * rights_review. For a rights_review item, "approved" is left out of the
 * options as a UI convenience pointing the user at the dedicated
 * rights-decision form (RightsDecisionForm) instead; the backend enforces
 * this rejection itself regardless of what this form offers.
 */
export function ReviewDecisionForm({ reviewItem }: { reviewItem: ReviewItemRead }) {
  const { execute, isPending, result } = useActionResult<ReviewItemRead>();
  const options =
    reviewItem.review_type === REVIEW_TYPE_RIGHTS
      ? REVIEW_ITEM_STATUSES.filter((status) => status !== "approved")
      : REVIEW_ITEM_STATUSES;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const reason = String(form.get("decision_reason") ?? "").trim();

    execute(() =>
      decideReviewItem(reviewItem.id, {
        status: String(form.get("status")) as ReviewItemStatus,
        decision_reason: reason || null,
      }),
    );
  }

  if (result?.ok) {
    return (
      <p className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
        Entscheidung gespeichert: {metaOrFallback(REVIEW_ITEM_STATUS_META, result.data.status).label}.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3" aria-label="Prüfungsentscheidung">
      <FormField label="Entscheidung" htmlFor={`decision-status-${reviewItem.id}`}>
        <select id={`decision-status-${reviewItem.id}`} name="status" required className={inputClass}>
          {options.map((status) => (
            <option key={status} value={status}>
              {metaOrFallback(REVIEW_ITEM_STATUS_META, status).label}
            </option>
          ))}
        </select>
      </FormField>
      <FormField label="Begründung (optional)" htmlFor={`decision-reason-${reviewItem.id}`}>
        <input id={`decision-reason-${reviewItem.id}`} name="decision_reason" className={inputClass} />
      </FormField>

      {result && !result.ok ? <ActionError error={result.error} /> : null}

      <button type="submit" disabled={isPending} className={primaryButtonClass}>
        {isPending ? "Wird gespeichert…" : "Entscheidung speichern"}
      </button>
    </form>
  );
}
