"use server";

/**
 * Development-only write operations, implemented as Next.js Server Actions
 * so the backend's X-API-Key header is attached server-side and never sent
 * to, or embedded in, the browser bundle (see .env.example — DEV_API_KEY
 * is deliberately not a NEXT_PUBLIC_ variable).
 *
 * Every action re-checks isDevWritesEnabled() here, not just in the UI: a
 * Server Action is itself a callable server endpoint, so hiding the button
 * client-side is not a security boundary — this check, plus the backend's
 * own X-API-Key requirement, are the real boundaries.
 *
 * Only wraps endpoints that actually exist on the backend (see
 * src/de_ai_kb/api/routers/sources.py and review_items.py). Nothing here
 * simulates success or bypasses backend validation — every action forwards
 * to the real endpoint and returns exactly what it responded with.
 */

import { revalidatePath } from "next/cache";

import { ApiError, apiFetch } from "./client";
import { getApiBaseUrl, isDevWritesEnabled } from "./config";
import type {
  ActionResult,
  ReviewDecisionInput,
  ReviewItemRead,
  RightsReviewDecisionInput,
  RightsReviewDecisionResult,
  SourceBlockInput,
  SourceCreateInput,
  SourceRead,
  SourceTransitionInput,
  SourceUpdateInput,
} from "./types";

const DEV_WRITES_DISABLED_ERROR = {
  code: "dev_writes_disabled",
  message:
    "Schreibaktionen sind deaktiviert. Setzen Sie NEXT_PUBLIC_ENABLE_DEV_WRITES=true in einer lokalen Entwicklungsumgebung, um sie zu aktivieren.",
  details: {},
};

function devApiKey(): string {
  return process.env.DEV_API_KEY ?? "change-me-dev-key";
}

async function writeAction<T>(run: () => Promise<T>): Promise<ActionResult<T>> {
  if (!isDevWritesEnabled()) {
    return { ok: false, error: DEV_WRITES_DISABLED_ERROR };
  }
  try {
    const data = await run();
    return { ok: true, data };
  } catch (error) {
    if (error instanceof ApiError) {
      return { ok: false, error: { code: error.code, message: error.message, details: error.details } };
    }
    return {
      ok: false,
      error: {
        code: "unknown_error",
        message: "Ein unerwarteter Fehler ist aufgetreten.",
        details: {},
      },
    };
  }
}

function authHeaders(): Record<string, string> {
  return { "X-API-Key": devApiKey() };
}

/** POST /api/v1/sources. The input type has no status/rights_status/
 * access_policy fields — this action cannot send them even if a caller
 * tried to, because SourceCreateInput does not include them. */
export async function createSource(input: SourceCreateInput): Promise<ActionResult<SourceRead>> {
  const result = await writeAction(() =>
    apiFetch<SourceRead>(getApiBaseUrl(), "/api/v1/sources", {
      method: "POST",
      headers: authHeaders(),
      body: input,
    }),
  );
  if (result.ok) {
    revalidatePath("/sources");
    revalidatePath("/");
  }
  return result;
}

/** PATCH /api/v1/sources/{id} — generic metadata edits only. */
export async function updateSource(id: string, input: SourceUpdateInput): Promise<ActionResult<SourceRead>> {
  const result = await writeAction(() =>
    apiFetch<SourceRead>(getApiBaseUrl(), `/api/v1/sources/${encodeURIComponent(id)}`, {
      method: "PATCH",
      headers: authHeaders(),
      body: input,
    }),
  );
  if (result.ok) {
    revalidatePath(`/sources/${id}`);
    revalidatePath("/sources");
  }
  return result;
}

/** POST /api/v1/sources/{id}/transition. SourceTransitionInput's
 * new_status type excludes "blocked" at compile time; the backend rejects
 * it again at runtime regardless of what a caller sends. */
export async function transitionSource(
  id: string,
  input: SourceTransitionInput,
): Promise<ActionResult<SourceRead>> {
  const result = await writeAction(() =>
    apiFetch<SourceRead>(getApiBaseUrl(), `/api/v1/sources/${encodeURIComponent(id)}/transition`, {
      method: "POST",
      headers: authHeaders(),
      body: input,
    }),
  );
  if (result.ok) {
    revalidatePath(`/sources/${id}`);
    revalidatePath("/sources");
    revalidatePath("/review");
    revalidatePath("/");
  }
  return result;
}

/** POST /api/v1/sources/{id}/block. The backend rejects a blank/whitespace
 * reason (422) — this action does not duplicate that check, it relies on
 * the backend and surfaces whatever it returns. */
export async function blockSource(id: string, input: SourceBlockInput): Promise<ActionResult<SourceRead>> {
  const result = await writeAction(() =>
    apiFetch<SourceRead>(getApiBaseUrl(), `/api/v1/sources/${encodeURIComponent(id)}/block`, {
      method: "POST",
      headers: authHeaders(),
      body: input,
    }),
  );
  if (result.ok) {
    revalidatePath(`/sources/${id}`);
    revalidatePath("/sources");
    revalidatePath("/review");
    revalidatePath("/");
  }
  return result;
}

/** POST /api/v1/review-items/{id}/decision — for content_review and
 * dedup_candidate items, and non-approval outcomes of rights_review. The
 * backend itself rejects an attempt to approve a rights_review item here
 * (422); this action does not pre-validate that, it relies on the backend. */
export async function decideReviewItem(
  id: string,
  input: ReviewDecisionInput,
): Promise<ActionResult<ReviewItemRead>> {
  const result = await writeAction(() =>
    apiFetch<ReviewItemRead>(getApiBaseUrl(), `/api/v1/review-items/${encodeURIComponent(id)}/decision`, {
      method: "POST",
      headers: authHeaders(),
      body: input,
    }),
  );
  if (result.ok) {
    revalidatePath("/review");
    revalidatePath("/sources");
    revalidatePath("/");
  }
  return result;
}

/** POST /api/v1/review-items/{id}/rights-decision — the only way to
 * approve a rights_review item; applies the reviewed rights_status/
 * access_policy to the source atomically. This action does not duplicate
 * the backend's rights_status/access_policy consistency validation
 * (domain/rights_policy.py) — an invalid combination is rejected by the
 * backend and surfaced as-is. */
export async function resolveRightsReview(
  id: string,
  input: RightsReviewDecisionInput,
): Promise<ActionResult<RightsReviewDecisionResult>> {
  const result = await writeAction(() =>
    apiFetch<RightsReviewDecisionResult>(
      getApiBaseUrl(),
      `/api/v1/review-items/${encodeURIComponent(id)}/rights-decision`,
      {
        method: "POST",
        headers: authHeaders(),
        body: input,
      },
    ),
  );
  if (result.ok) {
    revalidatePath(`/sources/${result.data.source.id}`);
    revalidatePath("/sources");
    revalidatePath("/review");
    revalidatePath("/");
  }
  return result;
}
