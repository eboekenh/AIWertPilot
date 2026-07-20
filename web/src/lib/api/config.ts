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
 * write controls are hidden unless this is explicitly "true". This flag
 * only gates UI visibility; the backend's X-API-Key check (performed
 * server-side in src/lib/api/actions.ts) remains the actual authorization
 * boundary.
 */
export function isDevWritesEnabled(): boolean {
  return process.env.NEXT_PUBLIC_ENABLE_DEV_WRITES === "true";
}
