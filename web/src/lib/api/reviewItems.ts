import { apiFetch, buildQueryString } from "./client";
import { getApiBaseUrl } from "./config";
import type { Page, ReviewItemListParams, ReviewItemRead } from "./types";

/** GET /api/v1/review-items — supports status, review_type, entity_type,
 * limit, offset (the exact query parameters the backend router defines). */
export async function listReviewItems(params: ReviewItemListParams = {}): Promise<Page<ReviewItemRead>> {
  const qs = buildQueryString({
    status: params.status,
    review_type: params.review_type,
    entity_type: params.entity_type,
    limit: params.limit,
    offset: params.offset,
  });
  return apiFetch<Page<ReviewItemRead>>(getApiBaseUrl(), `/api/v1/review-items${qs}`);
}

const MAX_AGGREGATE_PAGES = 10;
const AGGREGATE_PAGE_SIZE = 100;

export interface AggregatedReviewItems {
  items: ReviewItemRead[];
  total: number;
  truncated: boolean;
}

/** Fetches all review items matching `params` (bounded) — used by the
 * review workspace, which needs the full open-item set to group by source,
 * not just one page. See listAllSourcesForStats for the same bounded-page
 * pattern and its documented limitation. */
export async function listAllReviewItems(
  params: Omit<ReviewItemListParams, "limit" | "offset"> = {},
): Promise<AggregatedReviewItems> {
  const items: ReviewItemRead[] = [];
  let total = 0;
  for (let page = 0; page < MAX_AGGREGATE_PAGES; page += 1) {
    const offset = page * AGGREGATE_PAGE_SIZE;
    const result = await listReviewItems({ ...params, limit: AGGREGATE_PAGE_SIZE, offset });
    total = result.total;
    items.push(...result.items);
    if (items.length >= total || result.items.length === 0) {
      break;
    }
  }
  return { items, total, truncated: items.length < total };
}
