import { apiFetch, buildQueryString } from "./client";
import { getApiBaseUrl } from "./config";
import type { FreshnessReportItemRead, Page, SourceListParams, SourceRead } from "./types";

/** GET /api/v1/sources — the real list/filter endpoint. Supports the exact
 * query parameters the backend router defines: tier, source_type, topic,
 * publisher, language, status, freshness, limit, offset. */
export async function listSources(params: SourceListParams = {}): Promise<Page<SourceRead>> {
  const qs = buildQueryString({
    tier: params.tier,
    source_type: params.source_type,
    topic: params.topic,
    publisher: params.publisher,
    language: params.language,
    status: params.status,
    freshness: params.freshness,
    limit: params.limit,
    offset: params.offset,
  });
  return apiFetch<Page<SourceRead>>(getApiBaseUrl(), `/api/v1/sources${qs}`);
}

/** GET /api/v1/sources/{id}. Throws ApiError with status 404 if the source
 * does not exist. */
export async function getSource(id: string): Promise<SourceRead> {
  return apiFetch<SourceRead>(getApiBaseUrl(), `/api/v1/sources/${encodeURIComponent(id)}`);
}

/** GET /api/v1/research/freshness. */
export async function getFreshnessReport(state?: string): Promise<FreshnessReportItemRead[]> {
  const qs = buildQueryString({ state });
  return apiFetch<FreshnessReportItemRead[]>(getApiBaseUrl(), `/api/v1/research/freshness${qs}`);
}

const MAX_AGGREGATE_PAGES = 10;
const AGGREGATE_PAGE_SIZE = 100;

export interface AggregatedSources {
  items: SourceRead[];
  total: number;
  /** True if `total` exceeded what this app is willing to fetch for
   * dashboard/review aggregation (MAX_AGGREGATE_PAGES * AGGREGATE_PAGE_SIZE
   * records) — the aggregated stats below then only reflect the first
   * `items.length` sources, not all of them. See web/README.md
   * "Known limitations". */
  truncated: boolean;
}

/**
 * Fetches all sources (bounded) for dashboard/review-workspace statistics.
 * There is no dedicated statistics endpoint on the backend, so this derives
 * real numbers from the actual list endpoint rather than inventing one —
 * per the phase scope, a backend statistics endpoint is not added solely
 * for this convenience.
 */
export async function listAllSourcesForStats(): Promise<AggregatedSources> {
  const items: SourceRead[] = [];
  let total = 0;
  for (let page = 0; page < MAX_AGGREGATE_PAGES; page += 1) {
    const offset = page * AGGREGATE_PAGE_SIZE;
    const result = await listSources({ limit: AGGREGATE_PAGE_SIZE, offset });
    total = result.total;
    items.push(...result.items);
    if (items.length >= total || result.items.length === 0) {
      break;
    }
  }
  return { items, total, truncated: items.length < total };
}
