import type { ApiErrorEnvelope } from "./types";

/**
 * Typed error thrown for every non-2xx backend response and for network
 * failures. `message` is always safe to show a user (either the backend's
 * own message, which is already user-facing text, or a generic German
 * fallback — never a raw exception string or stack trace).
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: Record<string, unknown>;

  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

interface ApiFetchOptions {
  method?: "GET" | "POST" | "PATCH";
  headers?: Record<string, string>;
  body?: unknown;
  cache?: RequestCache;
  signal?: AbortSignal;
}

function safeJsonParse(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

function isErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as { error?: unknown }).error === "object"
  );
}

/**
 * Fetch JSON from `${baseUrl}${path}`, throwing a typed ApiError for any
 * non-2xx response or network failure. Defaults to `cache: "no-store"`
 * since this is a live review tool — data must never be silently served
 * stale from Next.js's fetch cache.
 */
export async function apiFetch<T>(baseUrl: string, path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { method = "GET", headers = {}, body, cache = "no-store", signal } = options;

  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      method,
      headers: {
        Accept: "application/json",
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      cache,
      signal,
    });
  } catch (cause) {
    throw new ApiError(0, "network_error", "Der Server ist nicht erreichbar. Läuft das Backend?", {
      cause: cause instanceof Error ? cause.message : String(cause),
    });
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  const json = text.length > 0 ? safeJsonParse(text) : undefined;

  if (!response.ok) {
    if (isErrorEnvelope(json)) {
      throw new ApiError(response.status, json.error.code, json.error.message, json.error.details ?? {});
    }
    throw new ApiError(
      response.status,
      "unknown_error",
      `Unerwarteter Serverfehler (Status ${response.status}).`,
      {},
    );
  }

  return json as T;
}

/** Builds a query string from a params object, dropping undefined/empty
 * values so filters that aren't set are simply omitted (matching how the
 * backend's optional query parameters behave). */
export function buildQueryString(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}
