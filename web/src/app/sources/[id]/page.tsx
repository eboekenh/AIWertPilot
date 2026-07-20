import { notFound } from "next/navigation";

import { AccessPolicyBadge } from "@/components/badges/AccessPolicyBadge";
import { FreshnessBadge } from "@/components/badges/FreshnessBadge";
import { RightsBadge } from "@/components/badges/RightsBadge";
import { StatusBadge } from "@/components/badges/StatusBadge";
import { PageHeader } from "@/components/layout/PageHeader";
import { ReviewActionPanel } from "@/components/review/ReviewActionPanel";
import { SourceActionsPanel } from "@/components/sources/SourceActionsPanel";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { ApiError } from "@/lib/api/client";
import { isDevWritesEnabled } from "@/lib/api/config";
import { listAllReviewItems } from "@/lib/api/reviewItems";
import { getFreshnessReport, getSource } from "@/lib/api/sources";
import { formatDateTime } from "@/lib/format";

export const dynamic = "force-dynamic";

function ExternalLink({ href }: { href: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="break-all text-slate-700 underline hover:text-slate-900 dark:text-slate-300 dark:hover:text-slate-100"
    >
      {href}
    </a>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</dt>
      <dd className="mt-0.5 text-sm text-slate-800 dark:text-slate-200">{children}</dd>
    </div>
  );
}

export default async function SourceDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const devWritesEnabled = isDevWritesEnabled();

  let source;
  try {
    source = await getSource(id);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    const message =
      error instanceof ApiError ? error.message : "Unbekannter Fehler beim Laden der Quelle.";
    return (
      <>
        <PageHeader title="Quelle" />
        <ErrorState message={message} />
      </>
    );
  }

  let reviewItems: Awaited<ReturnType<typeof listAllReviewItems>>["items"] = [];
  let freshness: Awaited<ReturnType<typeof getFreshnessReport>>[number] | undefined;
  let reviewSectionError: string | null = null;
  try {
    const [reviewItemsResult, freshnessItems] = await Promise.all([
      listAllReviewItems({ entity_type: "source" }),
      getFreshnessReport(),
    ]);
    reviewItems = reviewItemsResult.items.filter((item) => item.entity_id === source.id);
    freshness = freshnessItems.find((item) => item.source_id === source.id);
  } catch (error) {
    reviewSectionError =
      error instanceof ApiError
        ? error.message
        : "Unbekannter Fehler beim Laden der Prüfaufgaben und Aktualitätsdaten.";
  }

  return (
    <>
      <PageHeader
        title={source.title}
        description={`${source.source_key} · ${source.publisher}`}
        actions={
          <>
            <StatusBadge status={source.status} />
            <RightsBadge rightsStatus={source.rights_status} />
            <AccessPolicyBadge accessPolicy={source.access_policy} />
            {freshness ? <FreshnessBadge freshnessState={freshness.freshness_state} /> : null}
          </>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Metadaten</h2>
            <dl className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Quellentyp">{source.source_type}</Field>
              <Field label="Tier">{source.tier}</Field>
              <Field label="Sprache">{source.language_code}</Field>
              <Field label="Prüfintervall">{source.refresh_interval_days} Tage</Field>
              <Field label="Regionen">
                {source.geography_codes.length > 0 ? source.geography_codes.join(", ") : "—"}
              </Field>
              <Field label="Rechtsräume">
                {source.jurisdiction_codes.length > 0 ? source.jurisdiction_codes.join(", ") : "—"}
              </Field>
              <Field label="Themen">
                {source.topic_tags.length > 0 ? source.topic_tags.join(", ") : "—"}
              </Field>
              <Field label="TDM-Opt-out-Status">{source.tdm_opt_out_status}</Field>
              <Field label="Lizenzname">{source.licence_name ?? "—"}</Field>
              <Field label="Lizenz-URL">
                {source.licence_url ? <ExternalLink href={source.licence_url} /> : "—"}
              </Field>
              <Field label="Zuletzt geprüft">{formatDateTime(source.last_verified_at)}</Field>
              <Field label="Nächste Prüfung">{formatDateTime(source.next_review_at)}</Field>
              <Field label="Registriert">{formatDateTime(source.created_at)}</Field>
              <Field label="Aktualisiert">{formatDateTime(source.updated_at)}</Field>
            </dl>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Original-URL">
                <ExternalLink href={source.original_url} />
              </Field>
              <Field label="Kanonische URL">
                <ExternalLink href={source.canonical_url} />
              </Field>
            </div>
            {source.notes ? (
              <div className="mt-4">
                <Field label="Notizen">{source.notes}</Field>
              </div>
            ) : null}
          </Card>

          <Card>
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">Prüfaufgaben</h2>
            <div className="mt-4">
              {reviewSectionError ? (
                <ErrorState message={reviewSectionError} />
              ) : (
                <ReviewActionPanel reviewItems={reviewItems} devWritesEnabled={devWritesEnabled} />
              )}
            </div>
          </Card>

          <p className="text-xs text-slate-400 dark:text-slate-500">
            Snapshots, Dokumente und Belege (Claims) sind in dieser Version des Backends noch nicht über
            die API verfügbar und werden daher hier nicht angezeigt.
          </p>
        </div>

        <div>
          <SourceActionsPanel source={source} devWritesEnabled={devWritesEnabled} />
        </div>
      </div>
    </>
  );
}
