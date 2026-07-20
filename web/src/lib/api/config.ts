/** Backend base URL. No hard-coded production URL — must be configured via
 * NEXT_PUBLIC_API_BASE_URL (see .env.example). Falls back to the local
 * backend default only so `npm run dev` works out of the box without a
 * .env.local file. */
export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (configured && configured.trim().length > 0) {
    return configured.replace(/\/+$/, "");
  }
  return "http://localhost:8000";
}

/**
 * Whether development-only write controls (source creation, transitions,
 * blocking, rights decisions) are visible and usable. Defaults to false —
 * write controls are hidden unless this is explicitly "true".
 *
 * Deliberately a plain server-only env var, not NEXT_PUBLIC_ENABLE_DEV_WRITES:
 * this flag is only ever read from React Server Components (to decide what
 * to render) and Server Actions (to decide whether to accept a write) —
 * never from client-side code — so there is no reason for its value to be
 * inlined into the browser bundle at all. The backend's X-API-Key check
 * (see resolveDevApiKey below and src/lib/api/actions.ts) remains the
 * actual authorization boundary regardless of this flag.
 */
export function isDevWritesEnabled(): boolean {
  return process.env.ENABLE_DEV_WRITES === "true";
}

/** Known placeholder values that must never be treated as a real API key —
 * "change-me-dev-key" is the literal default shipped in both this app's
 * and the backend's .env.example files. */
const PLACEHOLDER_DEV_API_KEYS = new Set(["change-me-dev-key"]);

export class DevWritesConfigError extends Error {}

/**
 * Resolves the backend's development X-API-Key from process.env.DEV_API_KEY,
 * failing closed (throwing, never returning a usable-looking value) if it is
 * missing, blank, or still the shipped placeholder. There is no fallback —
 * a caller that wants writes enabled must configure a real key.
 */
export function resolveDevApiKey(): string {
  const key = process.env.DEV_API_KEY?.trim();
  if (!key || PLACEHOLDER_DEV_API_KEYS.has(key)) {
    throw new DevWritesConfigError(
      'DEV_API_KEY ist nicht gesetzt oder verwendet noch den Platzhalterwert "change-me-dev-key". ' +
        "Schreibaktionen bleiben deaktiviert, bis ein echter Wert konfiguriert ist.",
    );
  }
  return key;
}
