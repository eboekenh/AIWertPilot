import Link from "next/link";

import { RightsBadge } from "@/components/badges/RightsBadge";
import { ReviewTypeBadge } from "@/components/badges/ReviewItemStatusBadge";
import { StatusBadge } from "@/components/badges/StatusBadge";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Stat } from "@/components/ui/Stat";
import { ApiError } from "@/lib/api/client";
import { listAllReviewItems } from "@/lib/api/reviewItems";
import { listAllSourcesForStats } from "@/lib/api/sources";
import type { ReviewItemRead, SourceRead } from "@/lib/api/types";

export const dynamic = "force-dynamic";

const OPEN_REVIEW_STATUSES = new Set(["open", "in_progress", "needs_changes"]);

function SourceRow({ source, openItems }: { source: SourceRead; openItems: ReviewItemRead[] }) {
  return (
    <li className="flex flex-wrap items-center justify-between gap-3 py-3">
      <div>
        <Link
          href={`/sources/${source.id}`}
          className="font-medium text-slate-900 hover:underline dark:text-slate-100"
        >
          {source.title}
        </Link>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <span>{source.source_key}</span>
          <StatusBadge status={source.status} />
          {openItems.map((item) => (
            <ReviewTypeBadge key={item.id} reviewType={item.review_type} />
          ))}
        </div>
      </div>
      <Link
        href={`/sources/${source.id}`}
        className="shrink-0 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        Prüfen
      </Link>
    </li>
  );
}

export default async function ReviewWorkspacePage() {
  let sourcesResult: Awaited<ReturnType<typeof listAllSourcesForStats>>;
  let openReviewItemsResult: Awaited<ReturnType<typeof listAllReviewItems>>;

  try {
    [sourcesResult, openReviewItemsResult] = await Promise.all([
      listAllSourcesForStats(),
      listAllReviewItems({ entity_type: "source" }),
    ]);
  } catch (error) {
    const message =
      error instanceof ApiError ? error.message : "Unbekannter Fehler beim Laden der Prüfungsübersicht.";
    return (
      <>
        <PageHeader title="Prüfung" description="Quellen, die eine Entscheidung benötigen." />
        <ErrorState message={message} />
      </>
    );
  }

  const sourceById = new Map(sourcesResult.items.map((source) => [source.id, source]));
  const openItems = openReviewItemsResult.items.filter((item) => OPEN_REVIEW_STATUSES.has(item.status));

  const openItemsBySource = new Map<string, ReviewItemRead[]>();
  for (const item of openItems) {
    const list = openItemsBySource.get(item.entity_id) ?? [];
    list.push(item);
    openItemsBySource.set(item.entity_id, list);
  }

  const sourcesWithOpenItems = Array.from(openItemsBySource.entries())
    .map(([sourceId, items]) => ({ source: sourceById.get(sourceId), items }))
    .filter((entry): entry is { source: SourceRead; items: ReviewItemRead[] } => entry.source !== undefined)
    .sort((a, b) => a.source.title.localeCompare(b.source.title));

  const underReview = sourcesResult.items
    .filter((source) => source.status === "under_review")
    .sort((a, b) => a.title.localeCompare(b.title));

  const blocked = sourcesResult.items
    .filter((source) => source.status === "blocked")
    .sort((a, b) => a.title.localeCompare(b.title));

  const openRightsCount = openItems.filter((item) => item.review_type === "rights_review").length;
  const openContentCount = openItems.filter((item) => item.review_type === "content_review").length;

  return (
    <>
      <PageHeader
        title="Prüfung"
        description="Quellen, die noch eine Entscheidung benötigen. Die eigentliche Entscheidung wird auf der jeweiligen Quellenseite getroffen — diese Übersicht ändert nichts am Backend-Status selbst."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Offene Rechteprüfungen" value={openRightsCount} />
        <Stat label="Offene Inhaltsprüfungen" value={openContentCount} />
        <Stat label="Wartet auf Freigabe" value={underReview.length} hint="Status: In Prüfung" />
        <Stat label="Gesperrt" value={blocked.length} />
      </div>

      <section aria-labelledby="open-items-heading" className="mt-8">
        <h2 id="open-items-heading" className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
          Quellen mit offenen Prüfaufgaben
        </h2>
        <Card>
          {sourcesWithOpenItems.length === 0 ? (
            <EmptyState
              title="Keine offenen Prüfaufgaben"
              description="Alle Rechte- und Inhaltsprüfungen sind derzeit entschieden."
            />
          ) : (
            <ul className="divide-y divide-slate-200 dark:divide-slate-800">
              {sourcesWithOpenItems.map(({ source, items }) => (
                <SourceRow key={source.id} source={source} openItems={items} />
              ))}
            </ul>
          )}
        </Card>
      </section>

      <section aria-labelledby="under-review-heading" className="mt-8">
        <h2 id="under-review-heading" className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
          Wartet auf Freigabe
        </h2>
        <Card>
          {underReview.length === 0 ? (
            <EmptyState title="Keine Quellen in Prüfung" />
          ) : (
            <ul className="divide-y divide-slate-200 dark:divide-slate-800">
              {underReview.map((source) => (
                <SourceRow key={source.id} source={source} openItems={openItemsBySource.get(source.id) ?? []} />
              ))}
            </ul>
          )}
        </Card>
      </section>

      <section aria-labelledby="blocked-heading" className="mt-8">
        <h2 id="blocked-heading" className="mb-3 text-sm font-semibold text-slate-900 dark:text-slate-100">
          Gesperrte Quellen
        </h2>
        <Card>
          {blocked.length === 0 ? (
            <EmptyState title="Keine gesperrten Quellen" />
          ) : (
            <ul className="divide-y divide-slate-200 dark:divide-slate-800">
              {blocked.map((source) => (
                <li key={source.id} className="flex items-center justify-between gap-3 py-3">
                  <div>
                    <Link
                      href={`/sources/${source.id}`}
                      className="font-medium text-slate-900 hover:underline dark:text-slate-100"
                    >
                      {source.title}
                    </Link>
                    <div className="mt-1 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                      <span>{source.source_key}</span>
                      <RightsBadge rightsStatus={source.rights_status} />
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <p className="mt-2 text-xs text-slate-400 dark:text-slate-500">
          Sperrgründe werden im Backend-Audit-Log erfasst, aber derzeit über keinen Lese-Endpunkt
          bereitgestellt und können hier daher nicht angezeigt werden.
        </p>
      </section>
    </>
  );
}
