"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { FormEvent } from "react";

import { ActionError } from "@/components/ui/ActionError";
import { Card } from "@/components/ui/Card";
import { FormField } from "@/components/ui/FormField";
import { inputClass, primaryButtonClass } from "@/components/ui/formClasses";
import { createSource } from "@/lib/api/actions";
import { SOURCE_TIERS, type SourceRead } from "@/lib/api/types";
import { useActionResult } from "@/lib/useActionResult";

function splitList(raw: string): string[] {
  return raw
    .split(",")
    .map((part) => part.trim())
    .filter((part) => part.length > 0);
}

/**
 * Registers a new source via POST /api/v1/sources. Only fields present on
 * the backend's SourceCreate contract are collected — there is no field
 * for status, rights_status, or access_policy anywhere in this form, so
 * there is nothing to strip before submitting: the request body literally
 * cannot contain them. The backend assigns the safe initial values
 * (registered / needs_review / metadata_only) itself.
 */
export function SourceCreateForm() {
  const router = useRouter();
  const { execute, isPending, result, reset } = useActionResult<SourceRead>();
  const [formKey, setFormKey] = useState(0);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const refreshDays = Number(form.get("refresh_interval_days"));

    execute(() =>
      createSource({
        source_key: String(form.get("source_key") ?? "").trim(),
        title: String(form.get("title") ?? "").trim(),
        publisher: String(form.get("publisher") ?? "").trim(),
        original_url: String(form.get("original_url") ?? "").trim(),
        source_type: String(form.get("source_type") ?? "").trim(),
        tier: String(form.get("tier") ?? "A") as (typeof SOURCE_TIERS)[number],
        language_code: String(form.get("language_code") ?? "de").trim() || "de",
        topic_tags: splitList(String(form.get("topic_tags") ?? "")),
        geography_codes: splitList(String(form.get("geography_codes") ?? "")),
        refresh_interval_days: Number.isFinite(refreshDays) && refreshDays > 0 ? refreshDays : 90,
        notes: String(form.get("notes") ?? "").trim() || null,
      }),
    );
  }

  if (result?.ok) {
    return (
      <Card>
        <p className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
          Quelle &quot;{result.data.title}&quot; wurde registriert (Status: registriert, Rechtestatus:
          Prüfung erforderlich).
        </p>
        <div className="mt-3 flex gap-3">
          <button
            type="button"
            onClick={() => router.push(`/sources/${result.data.id}`)}
            className={primaryButtonClass}
          >
            Zur Quelle
          </button>
          <button
            type="button"
            onClick={() => {
              // reset() clears the stored ActionResult — without it,
              // `result?.ok` below stays true forever and this success
              // view would never give way back to an empty form.
              reset();
              setFormKey((k) => k + 1);
            }}
            className="text-sm font-medium text-slate-600 underline dark:text-slate-300"
          >
            Weitere Quelle anlegen
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <form key={formKey} onSubmit={handleSubmit} className="space-y-4" aria-label="Neue Quelle registrieren">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormField label="Quellenschlüssel (source_key)" htmlFor="create-source-key">
            <input id="create-source-key" name="source_key" required className={inputClass} />
          </FormField>
          <FormField label="Titel" htmlFor="create-title">
            <input id="create-title" name="title" required className={inputClass} />
          </FormField>
          <FormField label="Verlag / Herausgeber" htmlFor="create-publisher">
            <input id="create-publisher" name="publisher" required className={inputClass} />
          </FormField>
          <FormField label="URL" htmlFor="create-url">
            <input id="create-url" name="original_url" type="url" required className={inputClass} />
          </FormField>
          <FormField label="Quellentyp" htmlFor="create-source-type" hint="z. B. official_statistics, industry_report">
            <input id="create-source-type" name="source_type" required className={inputClass} />
          </FormField>
          <FormField label="Tier" htmlFor="create-tier">
            <select id="create-tier" name="tier" defaultValue="A" className={inputClass}>
              {SOURCE_TIERS.map((tier) => (
                <option key={tier} value={tier}>
                  {tier}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Sprachcode" htmlFor="create-language">
            <input id="create-language" name="language_code" defaultValue="de" className={inputClass} />
          </FormField>
          <FormField label="Prüfintervall (Tage)" htmlFor="create-refresh">
            <input
              id="create-refresh"
              name="refresh_interval_days"
              type="number"
              min={1}
              defaultValue={90}
              className={inputClass}
            />
          </FormField>
          <FormField label="Themen (kommagetrennt)" htmlFor="create-topics">
            <input id="create-topics" name="topic_tags" className={inputClass} />
          </FormField>
          <FormField label="Regionen (kommagetrennt)" htmlFor="create-geo">
            <input id="create-geo" name="geography_codes" placeholder="DE, EU" className={inputClass} />
          </FormField>
        </div>
        <FormField label="Notizen" htmlFor="create-notes">
          <textarea id="create-notes" name="notes" rows={3} className={inputClass} />
        </FormField>

        {result && !result.ok ? <ActionError error={result.error} /> : null}

        <button type="submit" disabled={isPending} className={primaryButtonClass}>
          {isPending ? "Wird gespeichert…" : "Quelle registrieren"}
        </button>
      </form>
    </Card>
  );
}
