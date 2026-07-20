import { PageHeader } from "@/components/layout/PageHeader";
import { SourceCreateForm } from "@/components/sources/SourceCreateForm";
import { SourceExplorer } from "@/components/sources/SourceExplorer";
import { DevWritesNotice } from "@/components/ui/DevWritesNotice";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { ApiError } from "@/lib/api/client";
import { isDevWritesEnabled } from "@/lib/api/config";
import { listAllSourcesForStats } from "@/lib/api/sources";

export const dynamic = "force-dynamic";

export default async function SourcesPage() {
  const devWritesEnabled = isDevWritesEnabled();

  let sourcesResult: Awaited<ReturnType<typeof listAllSourcesForStats>>;
  try {
    sourcesResult = await listAllSourcesForStats();
  } catch (error) {
    const message =
      error instanceof ApiError ? error.message : "Unbekannter Fehler beim Laden der Quellen.";
    return (
      <>
        <PageHeader title="Quellen" description="Registrierte Quellen durchsuchen und filtern." />
        <ErrorState message={message} />
      </>
    );
  }

  return (
    <>
      <PageHeader title="Quellen" description="Registrierte Quellen durchsuchen und filtern." />

      <details className="mb-6 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <summary className="cursor-pointer text-sm font-semibold text-slate-900 dark:text-slate-100">
          Neue Quelle registrieren
        </summary>
        <div className="mt-4">
          {devWritesEnabled ? <SourceCreateForm /> : <DevWritesNotice />}
        </div>
      </details>

      {sourcesResult.truncated ? (
        <p className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
          Hinweis: Es werden nur die ersten {sourcesResult.items.length} von {sourcesResult.total} Quellen
          geladen. Suche, Filter und Kennzahlen auf dieser Seite beziehen sich nur auf diese geladene
          Teilmenge. Details siehe web/README.md.
        </p>
      ) : null}

      {sourcesResult.total === 0 ? (
        <EmptyState
          title="Noch keine Quellen registriert"
          description="Importieren Sie seed_sources.csv über die Backend-CLI oder nutzen Sie das Formular oben."
        />
      ) : (
        <SourceExplorer sources={sourcesResult.items} />
      )}
    </>
  );
}
