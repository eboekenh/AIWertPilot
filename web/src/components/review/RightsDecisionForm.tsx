"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import { ActionError } from "@/components/ui/ActionError";
import { FormField } from "@/components/ui/FormField";
import { inputClass, primaryButtonClass } from "@/components/ui/formClasses";
import { resolveRightsReview } from "@/lib/api/actions";
import {
  TDM_OPT_OUT_STATUSES,
  type AccessPolicy,
  type ReviewItemRead,
  type RightsReviewDecisionResult,
  type RightsStatus,
  type TdmOptOutStatus,
} from "@/lib/api/types";
import { ACCESS_POLICY_META, RIGHTS_STATUS_META, metaOrFallback } from "@/lib/enums";
import { COMPLETED_RIGHTS_STATUSES, allowedAccessPoliciesFor } from "@/lib/transitions";
import { useActionResult } from "@/lib/useActionResult";

const DEFAULT_RIGHTS_STATUS = COMPLETED_RIGHTS_STATUSES[0];
const DEFAULT_ACCESS_POLICY = allowedAccessPoliciesFor(DEFAULT_RIGHTS_STATUS)[0];

/**
 * Approves a rights_review item with an explicit reviewed outcome
 * (POST /api/v1/review-items/{id}/rights-decision) — the only way to
 * approve a rights_review on the backend.
 *
 * rights_status and access_policy are controlled here (not read from
 * FormData like the rest of the form) so that changing rights_status
 * always re-narrows the access_policy options to
 * domain/rights_policy.py's allowed pairs and resets the selection to a
 * valid one — an inconsistent combination can never be selected through
 * this UI, by construction, not just by chance. This still does not
 * replace the backend's own validation: the backend re-checks the pair
 * independently and remains the sole authority (see lib/transitions.ts).
 * "needs_review" is never offered as an outcome — it means "not yet
 * reviewed", never a completed decision.
 */
export function RightsDecisionForm({ reviewItem }: { reviewItem: ReviewItemRead }) {
  const { execute, isPending, result } = useActionResult<RightsReviewDecisionResult>();
  const [showOptional, setShowOptional] = useState(false);
  const [rightsStatus, setRightsStatus] = useState<Exclude<RightsStatus, "needs_review">>(DEFAULT_RIGHTS_STATUS);
  const [accessPolicy, setAccessPolicy] = useState<AccessPolicy>(DEFAULT_ACCESS_POLICY);

  const accessPolicyOptions = allowedAccessPoliciesFor(rightsStatus);

  function handleRightsStatusChange(next: string) {
    const nextStatus = next as Exclude<RightsStatus, "needs_review">;
    setRightsStatus(nextStatus);
    // Always land on a valid pair for the new rights_status — never leave
    // a combination selected that domain/rights_policy.py would reject.
    const nextOptions = allowedAccessPoliciesFor(nextStatus);
    if (!nextOptions.includes(accessPolicy)) {
      setAccessPolicy(nextOptions[0]);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const tdmValue = String(form.get("tdm_opt_out_status") ?? "");
    const licenceName = String(form.get("licence_name") ?? "").trim();
    const licenceUrl = String(form.get("licence_url") ?? "").trim();

    execute(() =>
      resolveRightsReview(reviewItem.id, {
        rights_status: rightsStatus,
        access_policy: accessPolicy,
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
          <select
            id="rights-status"
            name="rights_status"
            required
            value={rightsStatus}
            onChange={(event) => handleRightsStatusChange(event.target.value)}
            className={inputClass}
          >
            {COMPLETED_RIGHTS_STATUSES.map((status) => (
              <option key={status} value={status}>
                {metaOrFallback(RIGHTS_STATUS_META, status).label}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Zugriffsrichtlinie" htmlFor="rights-access-policy">
          <select
            id="rights-access-policy"
            name="access_policy"
            required
            value={accessPolicy}
            onChange={(event) => setAccessPolicy(event.target.value as AccessPolicy)}
            className={inputClass}
          >
            {accessPolicyOptions.map((policy) => (
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
