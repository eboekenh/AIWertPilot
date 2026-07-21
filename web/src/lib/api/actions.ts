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
 * Every argument is treated as untrusted runtime input, not just as the
 * TypeScript type in its signature (see validate.ts) — it is re-validated
 * and explicitly reconstructed before ever being forwarded to the backend,
 * and a forbidden/extra field or malformed value is rejected locally
 * without making a backend request at all.
 *
 * Only wraps endpoints that actually exist on the backend (see
 * src/de_ai_kb/api/routers/sources.py and review_items.py). Nothing here
 * simulates success or bypasses backend validation — every action forwards
 * to the real endpoint and returns exactly what it responded with; none of
 * it duplicates the backend's own business-rule validation (state
 * transition table, rights/access-policy consistency), which remains the
 * backend's sole authority.
 */

import { revalidatePath } from "next/cache";

import { ApiError, apiFetch } from "./client";
import { DevWritesConfigError, getApiBaseUrl, isDevWritesEnabled, resolveDevApiKey } from "./config";
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
import {
  ValidationError,
  validateReviewDecisionInput,
  validateRightsReviewDecisionInput,
  validateSourceBlockInput,
  validateSourceCreateInput,
  validateSourceTransitionInput,
  validateSourceUpdateInput,
} from "./validate";

const DEV_WRITES_DISABLED_ERROR = {
  code: "dev_writes_disabled",
  message:
    "Schreibaktionen sind deaktiviert. Setzen Sie ENABLE_DEV_WRITES=true in einer lokalen Entwicklungsumgebung, um sie zu aktivieren.",
  details: {},
};

/**
 * Central plumbing shared by every write action below:
 *  1. Refuse outright if dev-writes are disabled — no validation, no
 *     backend call.
 *  2. Runtime-validate/reconstruct the raw input; a forbidden field or
 *     malformed value is rejected here, before any backend request.
 *  3. Resolve a real DEV_API_KEY; fail closed (no backend request) if it
 *     is missing, blank, or still the shipped placeholder.
 *  4. Only then call the backend, translating any ApiError into the same
 *     ActionResult shape as every other failure mode.
 */
async function writeAction<TInput, TOutput>(
  rawInput: unknown,
  validate: (input: unknown) => TInput,
  call: (input: TInput, apiKey: string) => Promise<TOutput>,
): Promise<ActionResult<TOutput>> {
  if (!isDevWritesEnabled()) {
    return { ok: false, error: DEV_WRITES_DISABLED_ERROR };
  }

  let validated: TInput;
  try {
    validated = validate(rawInput);
  } catch (error) {
    if (error instanceof ValidationError) {
      return { ok: false, error: { code: "validation_failed", message: error.message, details: error.details } };
    }
    throw error;
  }

  let apiKey: string;
  try {
    apiKey = resolveDevApiKey();
  } catch (error) {
    if (error instanceof DevWritesConfigError) {
      return { ok: false, error: { code: "configuration_error", message: error.message, details: {} } };
    }
    throw error;
  }

  try {
    const data = await call(validated, apiKey);
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

/** POST /api/v1/sources. validateSourceCreateInput allowlists exactly the
 * backend's SourceCreate fields — status/rights_status/access_policy are
 * rejected before any request is made, regardless of what is passed in. */
export async function createSource(input: SourceCreateInput): Promise<ActionResult<SourceRead>> {
  const result = await writeAction(input, validateSourceCreateInput, (validated, apiKey) =>
    apiFetch<SourceRead>(getApiBaseUrl(), "/api/v1/sources", {
      method: "POST",
      headers: { "X-API-Key": apiKey },
      body: validated,
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
  const result = await writeAction(input, validateSourceUpdateInput, (validated, apiKey) =>
    apiFetch<SourceRead>(getApiBaseUrl(), `/api/v1/sources/${encodeURIComponent(id)}`, {
      method: "PATCH",
      headers: { "X-API-Key": apiKey },
      body: validated,
    }),
  );
  if (result.ok) {
    revalidatePath(`/sources/${id}`);
    revalidatePath("/sources");
  }
  return result;
}

/** POST /api/v1/sources/{id}/transition. validateSourceTransitionInput
 * rejects new_status="blocked" locally (the backend rejects it again
 * regardless), plus any unrecognized status value or forbidden field. */
export async function transitionSource(
  id: string,
  input: SourceTransitionInput,
): Promise<ActionResult<SourceRead>> {
  const result = await writeAction(input, validateSourceTransitionInput, (validated, apiKey) =>
    apiFetch<SourceRead>(getApiBaseUrl(), `/api/v1/sources/${encodeURIComponent(id)}/transition`, {
      method: "POST",
      headers: { "X-API-Key": apiKey },
      body: validated,
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

/** POST /api/v1/sources/{id}/block. validateSourceBlockInput rejects a
 * blank/whitespace-only reason locally; the backend enforces the same
 * rule again independently. */
export async function blockSource(id: string, input: SourceBlockInput): Promise<ActionResult<SourceRead>> {
  const result = await writeAction(input, validateSourceBlockInput, (validated, apiKey) =>
    apiFetch<SourceRead>(getApiBaseUrl(), `/api/v1/sources/${encodeURIComponent(id)}/block`, {
      method: "POST",
      headers: { "X-API-Key": apiKey },
      body: validated,
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
  const result = await writeAction(input, validateReviewDecisionInput, (validated, apiKey) =>
    apiFetch<ReviewItemRead>(getApiBaseUrl(), `/api/v1/review-items/${encodeURIComponent(id)}/decision`, {
      method: "POST",
      headers: { "X-API-Key": apiKey },
      body: validated,
    }),
  );
  if (result.ok) {
    revalidatePath("/review");
    revalidatePath("/sources");
    revalidatePath(`/sources/${result.data.entity_id}`);
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
  const result = await writeAction(input, validateRightsReviewDecisionInput, (validated, apiKey) =>
    apiFetch<RightsReviewDecisionResult>(
      getApiBaseUrl(),
      `/api/v1/review-items/${encodeURIComponent(id)}/rights-decision`,
      {
        method: "POST",
        headers: { "X-API-Key": apiKey },
        body: validated,
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
