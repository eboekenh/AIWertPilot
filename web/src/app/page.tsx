import Link from "next/link";

import { AccessPolicyBadge } from "@/components/badges/AccessPolicyBadge";
import { FreshnessBadge } from "@/components/badges/FreshnessBadge";
import { RightsBadge } from "@/components/badges/RightsBadge";
import { StatusBadge } from "@/components/badges/StatusBadge";
import { countBy, DistributionCard } from "@/components/dashboard/DistributionCard";
import { PageHeader } from "@/components/layout/PageHeader";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Stat } from "@/components/ui/Stat";
import { ApiError } from "@/lib/api/client";
import { listAllReviewItems } from "@/lib/api/reviewItems";
import { getFreshnessReport, listAllSourcesForStats } from "@/lib/api/sources";
import { formatDateTime } from "@/lib/format";
import { isOpenReviewItemStatus } from "@/lib/reviewStatus";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let sourcesResult: Awaited<ReturnType<typeof listAllSourcesForStats>>;
  let freshnessItems: Awaited<ReturnType<typeof getFreshnessReport>>;
  let openReviewItems: Awaited<ReturnType<typeof listAllReviewItems>>;

  try {
    [sourcesResult, freshnessItems, openReviewItems] = await Promise.all([
      listAllSourcesForStats(),
      getFreshnessReport(),
      // No status filter: "needs review" must count open, in_progress, AND
      // needs_changes items (see lib/reviewStatus.ts) — filtered below,
      // consistently with the review workspace.
      listAllReviewItems({ entity_type: "source" }),
    ]);
  } catch (error) {
    const message =
      error instanceof ApiError ? error.message : "Unbekannter Fehler beim Laden der Übersicht.";
    return (
      <>
        <PageHeader title="Übersicht" description="Kennzahlen aus dem AIWertPilot-Backend." />
        <ErrorState message={message} />
      </>
    );
  }

  const { items, total, truncated } = sourcesResult;

  if (total === 0) {
    return (
      <>
        <PageHeader title="Übersicht" description="Kennzahlen aus dem AIWertPilot-Backend." />
        <EmptyState
          title="Noch keine Quellen registriert"
          description="Importieren Sie seed_sources.csv über die Backend-CLI oder registrieren Sie eine Quelle, um loszulegen."
          action={
            <Link href="/sources" className="text-sm font-medium text-slate-900 underline dark:text-slate-100">
              Zu den Quellen
            </Link>
          }
        />
      </>
    );
  }

  const statusCounts = countBy(items, (s) => s.status);
  const rightsCounts = countBy(items, (s) => s.rights_status);
  const accessCounts = countBy(items, (s) => s.access_policy);
  const freshnessCounts = countBy(freshnessItems, (f) => f.freshness_state);

  const blockedCount = statusCounts.blocked ?? 0;
  const publishedCount = statusCounts.published ?? 0;
  const openReviewItemsList = openReviewItems.items.filter((item) => isOpenReviewItemStatus(item.status));
  const sourcesNeedingReview = new Set(openReviewItemsList.map((item) => item.entity_id)).size;

  const recentlyUpdated = [...items]
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
    .slice(0, 8);

  const reviewItemsTruncated = openReviewItems.truncated;

  return (
    <>
      <PageHeader
        title="Übersicht"
        description={`Kennzahlen aus ${total} registrierten Quellen.`}
      />

      {truncated || reviewItemsTruncated ? (
        <p className="mb-6 rounded-lg border border-amber-300 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
          Hinweis:{" "}
          {truncated
            ? `Diese Kennzahlen basieren auf den ersten ${items.length} von ${total} Quellen`
            : null}
          {truncated && reviewItemsTruncated ? " und " : null}
          {reviewItemsTruncated
            ? `auf den ersten ${openReviewItems.items.length} von ${openReviewItems.total} Prüfaufgaben`
            : null}{" "}
          — bei sehr vielen Datensätzen werden nicht alle für die Übersicht geladen. Details siehe
          web/README.md.
        </p>
      ) : null}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Quellen gesamt" value={total} />
        <Stat
          label="Prüfung erforderlich"
          value={sourcesNeedingReview}
          hint="Quellen mit offener Rechte- oder Inhaltsprüfung"
        />
        <Stat label="Gesperrt" value={blockedCount} />
        <Stat label="Veröffentlicht" value={publishedCount} />
      </div>

      <section aria-labelledby="distribution-heading" className="mt-8">
        <h2 id="distribution-heading" className="sr-only">
          Verteilungen
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <DistributionCard
            title="Status-Verteilung"
            counts={statusCounts}
            renderBadge={(value) => <StatusBadge status={value} />}
          />
          <DistributionCard
            title="Rechtestatus-Verteilung"
            counts={rightsCounts}
            renderBadge={(value) => <RightsBadge rightsStatus={value} />}
          />
          <DistributionCard
            title="Zugriffsrichtlinie"
            counts={accessCounts}
            renderBadge={(value) => <AccessPolicyBadge accessPolicy={value} />}
          />
          <DistributionCard
            title="Aktualität"
            counts={freshnessCounts}
            renderBadge={(value) => <FreshnessBadge freshnessState={value} />}
          />
        </div>
      </section>

      <section aria-labelledby="recent-heading" className="mt-8">
        <h2 id="recent-heading" className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
          Zuletzt aktualisiert
        </h2>
        <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
            <thead className="bg-slate-50 dark:bg-slate-900">
              <tr>
                <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300">
                  Quelle
                </th>
                <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300">
                  Status
                </th>
                <th scope="col" className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300">
                  Aktualisiert
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {recentlyUpdated.map((source) => (
                <tr key={source.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/60">
                  <td className="px-4 py-3">
                    <Link
                      href={`/sources/${source.id}`}
                      className="font-medium text-slate-900 hover:underline dark:text-slate-100"
                    >
                      {source.title}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={source.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                    {formatDateTime(source.updated_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
