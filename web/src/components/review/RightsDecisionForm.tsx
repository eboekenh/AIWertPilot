"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import { ActionError } from "@/components/ui/ActionError";
import { FormField } from "@/components/ui/FormField";
import { inputClass, primaryButtonClass } from "@/components/ui/formClasses";
import { resolveRightsReview } from "@/lib/api/actions";
import {
  ACCESS_POLICIES,
  RIGHTS_STATUSES,
  TDM_OPT_OUT_STATUSES,
  type AccessPolicy,
  type ReviewItemRead,
  type RightsReviewDecisionResult,
  type RightsStatus,
  type TdmOptOutStatus,
} from "@/lib/api/types";
import { ACCESS_POLICY_META, RIGHTS_STATUS_META, metaOrFallback } from "@/lib/enums";
import { useActionResult } from "@/lib/useActionResult";

/**
 * Approves a rights_review item with an explicit reviewed outcome
 * (POST /api/v1/review-items/{id}/rights-decision) — the only way to
 * approve a rights_review on the backend. This form does not pre-validate
 * which rights_status/access_policy combinations are consistent
 * (domain/rights_policy.py on the backend is the sole authority there); an
 * invalid combination is rejected by the backend and shown via ActionError.
 */
export function RightsDecisionForm({ reviewItem }: { reviewItem: ReviewItemRead }) {
  const { execute, isPending, result } = useActionResult<RightsReviewDecisionResult>();
  const [showOptional, setShowOptional] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const tdmValue = String(form.get("tdm_opt_out_status") ?? "");
    const licenceName = String(form.get("licence_name") ?? "").trim();
    const licenceUrl = String(form.get("licence_url") ?? "").trim();

    execute(() =>
      resolveRightsReview(reviewItem.id, {
        rights_status: String(form.get("rights_status")) as RightsStatus,
        access_policy: String(form.get("access_policy")) as AccessPolicy,
        decision_reason: String(form.get("decision_reason") ?? "").trim(),
        tdm_opt_out_status: tdmValue ? (tdmValue as TdmOptOutStatus) : null,
        licence_name: licenceName || null,
        licence_url: licenceUrl || null,
      }),
    );
  }

  if (result?.ok) {
    return (
      <p className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
        Rechteprüfung abgeschlossen: {metaOrFallback(RIGHTS_STATUS_META, result.data.source.rights_status).label} /{" "}
        {metaOrFallback(ACCESS_POLICY_META, result.data.source.access_policy).label}.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3" aria-label="Rechteentscheidung">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <FormField label="Rechtestatus" htmlFor="rights-status">
          <select id="rights-status" name="rights_status" required className={inputClass}>
            {RIGHTS_STATUSES.map((status) => (
              <option key={status} value={status}>
                {metaOrFallback(RIGHTS_STATUS_META, status).label}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Zugriffsrichtlinie" htmlFor="rights-access-policy">
          <select id="rights-access-policy" name="access_policy" required className={inputClass}>
            {ACCESS_POLICIES.map((policy) => (
              <option key={policy} value={policy}>
                {metaOrFallback(ACCESS_POLICY_META, policy).label}
              </option>
            ))}
          </select>
        </FormField>
      </div>
      <FormField label="Begründung (erforderlich)" htmlFor="rights-reason">
        <textarea id="rights-reason" name="decision_reason" required rows={2} className={inputClass} />
      </FormField>

      <button
        type="button"
        onClick={() => setShowOptional((v) => !v)}
        className="text-xs font-medium text-slate-500 underline dark:text-slate-400"
      >
        {showOptional ? "Optionale Felder ausblenden" : "Optionale Felder anzeigen (TDM, Lizenz)"}
      </button>

      {showOptional ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <FormField label="TDM-Opt-out-Status" htmlFor="rights-tdm">
            <select id="rights-tdm" name="tdm_opt_out_status" defaultValue="" className={inputClass}>
              <option value="">— nicht angeben —</option>
              {TDM_OPT_OUT_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Lizenzname" htmlFor="rights-licence-name">
            <input id="rights-licence-name" name="licence_name" className={inputClass} />
          </FormField>
          <FormField label="Lizenz-URL" htmlFor="rights-licence-url">
            <input id="rights-licence-url" name="licence_url" type="url" className={inputClass} />
          </FormField>
        </div>
      ) : null}

      {result && !result.ok ? <ActionError error={result.error} /> : null}

      <button type="submit" disabled={isPending} className={primaryButtonClass}>
        {isPending ? "Wird gespeichert…" : "Rechteentscheidung speichern"}
      </button>
    </form>
  );
}
