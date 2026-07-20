# AIWertPilot — Frontend (Foundation Phase 1)

An internal **evidence and source-review interface** for the AIWertPilot
backend (`../README.md`). This is not the final AI recommendation product —
it is a foundation for browsing, filtering, and reviewing the sources the
backend already tracks, and for safely exercising the backend's real write
endpoints in local development.

Everything on screen comes from the real backend API. Nothing here fetches,
crawls, calls an LLM, or fabricates data. Mocked data is used only inside
tests (`src/test/`).

## Requirements

- **Node.js 20 or newer** (developed and tested against Node 22). Next.js
  16 requires Node ≥ 20.
- **npm** (this project uses npm, not pnpm/yarn/bun).
- A running AIWertPilot backend — see `../README.md` for how to start
  PostgreSQL/pgvector and the FastAPI server.

## Setup

```bash
cd web
npm install
cp .env.example .env.local
```

Edit `.env.local` as needed (see "Environment variables" below). Next.js
loads `.env.local` automatically; it is git-ignored.

## Running the full stack locally

1. **Database** (from the repo root, one of the two documented paths in
   `../README.md`):

   ```bash
   docker compose up -d db
   # or, if no Docker daemon is available:
   service postgresql start
   ```

2. **Backend** (from the repo root):

   ```bash
   cp .env.example .env   # if not already done
   # Allow the local Next.js dev server to call the API directly if needed:
   echo 'CORS_ALLOWED_ORIGINS=http://localhost:3000' >> .env
   uv sync
   uv run alembic upgrade head
   uv run de-ai-kb sources import --file data/seed_sources.csv
   uv run uvicorn de_ai_kb.main:app --reload
   ```

   The backend listens on `http://localhost:8000` by default.

3. **Frontend** (from `web/`):

   ```bash
   npm run dev
   ```

   Open `http://localhost:3000`.

## Environment variables

### Frontend (`web/.env.example` → `web/.env.local`)

| Variable | Purpose | Default |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL, no trailing slash. Public — used by server-side data fetches, which run server-to-server and never expose this beyond "which API to call". | `http://localhost:8000` |
| `NEXT_PUBLIC_ENABLE_DEV_WRITES` | Set to exactly `true` to show write controls (create source, transition, block, rights/review decisions). **Never set this against a shared or production backend.** | `false` |
| `DEV_API_KEY` | The backend's development `X-API-Key`. **Not** prefixed with `NEXT_PUBLIC_` — read only by server-side Server Actions (`src/lib/api/actions.ts`), never sent to or bundled into the browser. Only needed when `NEXT_PUBLIC_ENABLE_DEV_WRITES=true`. | `change-me-dev-key` |

### Backend (relevant to this frontend — see `../.env.example` for the full list)

| Variable | Purpose | Default |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed browser origins. Empty/unset disables CORS entirely (restrictive by default). Add `http://localhost:3000` for local frontend development / direct browser API access. | *(empty)* |
| `DEV_API_KEY` | Must match the frontend's `DEV_API_KEY` for dev-write requests to succeed. | `change-me-dev-key` |

## How the frontend talks to the backend

- **Reads** (dashboard, source list, source detail, review workspace) are
  plain `fetch` calls made from **React Server Components**, running on the
  Next.js server, not the browser. This is server-to-server traffic — it
  does not go through the browser's CORS machinery at all, and needs no
  authentication (every read endpoint this app uses is unauthenticated on
  the backend). The backend's CORS setting exists for direct
  browser-to-API use (e.g. hitting the API from a browser console, or a
  future purely client-side view) rather than because this app's own reads
  require it.
- **Writes** (create source, transition, block, review/rights decisions)
  are **Next.js Server Actions** (`"use server"`, in `src/lib/api/actions.ts`).
  A client component (a form) calls the Server Action directly; the action
  runs on the Next.js server, attaches the backend's `X-API-Key` header
  from `process.env.DEV_API_KEY`, and forwards the request. The API key is
  never sent to, or present in, the browser bundle. Every action
  independently re-checks `NEXT_PUBLIC_ENABLE_DEV_WRITES` server-side
  (`isDevWritesEnabled()`) — hiding the button client-side is not treated
  as the security boundary, since a Server Action is itself a callable
  endpoint.
- Every write action returns a typed `ActionResult<T>`
  (`{ ok: true, data } | { ok: false, error }`) instead of throwing, so a
  rejected write (a backend validation error, a disabled dev-writes flag,
  a network failure) is always renderable inline, never an uncaught
  exception.

## Development-only write controls

Write controls (registering a source, changing its status, blocking it,
and resolving review/rights decisions) are **hidden and disabled by
default**. To enable them locally:

```bash
# web/.env.local
NEXT_PUBLIC_ENABLE_DEV_WRITES=true
DEV_API_KEY=<same value as the backend's .env DEV_API_KEY>
```

Restart `npm run dev` after changing this. With it enabled:

- The "Neue Quelle registrieren" panel on `/sources` becomes usable.
- Each source detail page (`/sources/[id]`) shows status-transition,
  block, and review-decision controls.

Every write control only exposes fields the real backend contract
accepts:

- **Source creation** never offers `status`, `rights_status`, or
  `access_policy` — those fields do not exist on the form or in the
  request type (`SourceCreateInput`) at all. The backend always assigns
  the safe initial values (`registered` / `needs_review` / `metadata_only`)
  itself.
- **Status transitions** never offer `blocked` as a target — blocking is a
  dedicated, separately audited workflow with its own mandatory-reason
  form.
- **Blocking** requires a non-blank reason; the confirm button stays
  disabled until one is entered.
- **Rights decisions** and **generic review decisions** submit exactly
  what `RightsReviewDecisionInput` / `ReviewDecisionInput` allow. Neither
  form re-implements the backend's transition-table or
  rights/access-policy consistency rules — an invalid request is rejected
  by the backend and its message is shown via the shared `ActionError`
  component.

## Keeping types in sync with the backend

`src/lib/api/types.ts` is a hand-derived TypeScript mirror of:

- `../src/de_ai_kb/api/schemas/sources.py`
- `../src/de_ai_kb/api/schemas/review_items.py`
- `../src/de_ai_kb/api/schemas/common.py`
- `../src/de_ai_kb/domain/enums.py` (value sets only — mirrored again,
  with German display labels, in `src/lib/enums.ts`)

There is no OpenAPI-generation step in this phase. If a backend schema or
enum changes, update `types.ts` (and `enums.ts` for label/tone changes) to
match by hand, and re-run `npm run typecheck`.

## Commands

```bash
npm run dev         # start the dev server (http://localhost:3000)
npm run build        # production build
npm run start         # run a production build (after `npm run build`)
npm run lint          # ESLint (flat config, next/core-web-vitals + next/typescript)
npm run typecheck     # tsc --noEmit (strict mode)
npm run test           # Vitest, single run
npm run test:watch    # Vitest, watch mode
```

## Testing

Vitest + React Testing Library (`jsdom` environment). Tests live under
`src/test/`, mirroring the structure of `src/lib` and `src/components`.
Server Actions (`src/lib/api/actions.ts`) are mocked in component tests
(`vi.mock("@/lib/api/actions")`) since outside a real Next.js build a
`"use server"` file is just a plain module — mocking keeps these tests
fast, deterministic, and free of real network calls.

Coverage includes: the typed fetch client's success/error/network-failure
handling, source filtering (search/status/rights/access-policy/type),
badge label rendering (incl. fallback for unrecognized values),
loading/empty/error states, dev-write visibility gating (hidden by default,
shown only when explicitly enabled), source-creation payloads never
containing the forbidden lifecycle/rights fields, transition controls
never offering "blocked", block requiring a non-blank reason, and backend
validation errors being surfaced to the user.

## Real backend endpoints this app uses

See `../README.md`'s "API endpoints" table for the authoritative list. In
short: `GET /health`, `GET/POST /api/v1/sources`, `GET/PATCH
/api/v1/sources/{id}` *(PATCH not yet exposed in the UI — see
limitations)*, `POST /api/v1/sources/{id}/transition`, `POST
/api/v1/sources/{id}/block`, `GET /api/v1/research/freshness`, `GET
/api/v1/review-items`, `POST /api/v1/review-items/{id}/decision`, `POST
/api/v1/review-items/{id}/rights-decision`.

## Known limitations (Foundation Phase 1)

- **Bounded client-side aggregation.** The backend's list endpoints only
  support `limit`/`offset` pagination server-side; they have no
  `rights_status`, `access_policy`, or free-text search query parameters,
  and there is no dedicated statistics endpoint. The dashboard, source
  list, and review workspace therefore fetch up to 1000 sources /
  1000 review items (10 pages of 100, the backend's max page size) once
  and derive statistics, filtering, and pagination from that bounded set
  in memory. Beyond that size, figures are based on the first N records
  fetched, not the full dataset — a `truncated` flag is tracked in
  `lib/api/sources.ts` / `lib/api/reviewItems.ts` and surfaced as a notice
  on the dashboard. A real seed import (`data/seed_sources.csv`, 65 rows)
  is far under this limit.
- **No block/transition reason display.** The backend records status-
  transition and block reasons in `audit_events`, but exposes no read
  endpoint for that table. The UI therefore cannot show *why* a source was
  blocked or transitioned, only its current state — this is a backend gap,
  not a frontend omission.
- **No snapshots, documents, or evidence/claims.** These exist in the
  database schema but have no API routes yet (Release 2/3 scope per the
  backend's own `docs/NEXT_RELEASES.md`). The source detail page notes
  this explicitly rather than showing an empty section that implies a bug.
- **No generic metadata-edit UI.** `PATCH /api/v1/sources/{id}` (editing
  title/publisher/tier/topic_tags/refresh_interval_days/notes) is a real,
  supported backend endpoint but has no form in this phase — only
  creation, transition, block, and review/rights decisions are wired up.
- **No authentication.** The dev-write `X-API-Key` model is explicitly
  development-only (see backend `CLAUDE.md`/`docs/`); this frontend does
  not add any authentication of its own, and must never be pointed at a
  shared or production backend with dev writes enabled.
- **Filters/pagination are not URL-synced** on `/sources` — they reset on
  page reload. Deliberately deferred to keep this phase's scope focused;
  the underlying data flow (bounded fetch → client filter/paginate) would
  support adding `useSearchParams` synchronization later without a
  redesign.
