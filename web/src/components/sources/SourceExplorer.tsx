"use client";

import { useMemo, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import type { SourceRead } from "@/lib/api/types";

import { SourceFilters, type SourceFiltersValue } from "./SourceFilters";
import { SourceTable } from "./SourceTable";

const PAGE_SIZE = 20;
const EMPTY_FILTERS: SourceFiltersValue = {
  search: "",
  status: "",
  rightsStatus: "",
  accessPolicy: "",
  sourceType: "",
};

function matches(source: SourceRead, filters: SourceFiltersValue): boolean {
  if (filters.status && source.status !== filters.status) return false;
  if (filters.rightsStatus && source.rights_status !== filters.rightsStatus) return false;
  if (filters.accessPolicy && source.access_policy !== filters.accessPolicy) return false;
  if (filters.sourceType && source.source_type !== filters.sourceType) return false;
  if (filters.search.trim()) {
    const needle = filters.search.trim().toLowerCase();
    const haystack = `${source.title} ${source.source_key} ${source.publisher}`.toLowerCase();
    if (!haystack.includes(needle)) return false;
  }
  return true;
}

/**
 * Client-side filtering/pagination over an already-fetched, bounded list of
 * sources. The backend's GET /api/v1/sources only supports server-side
 * filtering by tier/source_type/topic/publisher/language/status/freshness —
 * it has no rights_status, access_policy, or free-text search parameters —
 * so those filters are applied here, in memory, against the full bounded
 * set the parent Server Component already fetched (see
 * listAllSourcesForStats in lib/api/sources.ts and its documented
 * truncation limit).
 */
export function SourceExplorer({ sources }: { sources: SourceRead[] }) {
  const [filters, setFilters] = useState<SourceFiltersValue>(EMPTY_FILTERS);
  const [page, setPage] = useState(0);

  const sourceTypeOptions = useMemo(
    () => Array.from(new Set(sources.map((s) => s.source_type))).sort(),
    [sources],
  );

  const filtered = useMemo(() => {
    const next = sources.filter((source) => matches(source, filters));
    return next;
  }, [sources, filters]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount - 1);
  const pageItems = filtered.slice(currentPage * PAGE_SIZE, currentPage * PAGE_SIZE + PAGE_SIZE);

  function handleFiltersChange(next: SourceFiltersValue) {
    setFilters(next);
    setPage(0);
  }

  return (
    <div className="space-y-4">
      <SourceFilters value={filters} onChange={handleFiltersChange} sourceTypeOptions={sourceTypeOptions} />

      <p className="text-sm text-slate-500 dark:text-slate-400" aria-live="polite">
        {filtered.length} von {sources.length} Quellen
      </p>

      {filtered.length === 0 ? (
        <EmptyState
          title="Keine Quellen gefunden"
          description="Passen Sie die Filter an oder setzen Sie die Suche zurück."
        />
      ) : (
        <>
          <SourceTable sources={pageItems} />
          {pageCount > 1 ? (
            <nav
              aria-label="Seitennavigation"
              className="flex items-center justify-between text-sm text-slate-600 dark:text-slate-300"
            >
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={currentPage === 0}
                className="rounded-md border border-slate-300 px-3 py-1.5 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700"
              >
                Zurück
              </button>
              <span>
                Seite {currentPage + 1} von {pageCount}
              </span>
              <button
                type="button"
                onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
                disabled={currentPage >= pageCount - 1}
                className="rounded-md border border-slate-300 px-3 py-1.5 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700"
              >
                Weiter
              </button>
            </nav>
          ) : null}
        </>
      )}
    </div>
  );
}
