# ZeroTRUST — Frontend Integration Log

**Branch:** `frontend`  
**Period:** March 7, 2026  
**Engineer:** GitHub Copilot (assisted)

This document records every change made from the initial frontend migration through to the complete backend wiring and bug-fix pass.

---

## Table of Contents

1. [Starting Point — What Existed](#1-starting-point--what-existed)
2. [Step 1 — Frontend Migration (Vite → Next.js)](#2-step-1--frontend-migration-vite--nextjs)
3. [Step 2 — Phase 1: API Client Foundation](#3-step-2--phase-1-api-client-foundation)
4. [Step 3 — Phase 2: Wire /verify to Real Backend](#4-step-3--phase-2-wire-verify-to-real-backend)
5. [Step 4 — Full Workspace Audit](#5-step-4--full-workspace-audit)
6. [Step 5 — Bug Fix Pass (All 8 Bugs)](#6-step-5--bug-fix-pass-all-8-bugs)
7. [Current State Summary](#7-current-state-summary)
8. [Remaining Work](#8-remaining-work)

---

## 1. Starting Point — What Existed

### Repo Structure (before this branch)
The `main` branch contained a fully-implemented backend with a **Vite/React 18** web portal that had no connection to it:

```
apps/
  api-gateway/        ← Express/TypeScript, fully implemented
  verification-engine/ ← FastAPI/Python, LangGraph pipeline, fully implemented
  media-analysis/      ← FastAPI/Python, AWS Textract/Transcribe/Rekognition
  web-portal/          ← Vite + React 18 + Tailwind 3 (OLD, disconnected)
  browser-extension/   ← Chrome MV3 extension (simple popup)
```

### Old `web-portal` Stack
| Property | Value |
|---|---|
| Framework | Vite 5 + React 18 |
| Styling | Tailwind CSS 3 |
| State | Zustand |
| Entry | `index.html` + `src/main.tsx` |
| Port | `5173` (Vite default) |
| Backend connection | **None** — all hardcoded mock data |

### Separate Frontend (`ZeroTrustFrontend/` folder)
A fully designed Next.js 16 frontend existed in a separate workspace folder with:
- Full App Router page structure (13 routes)
- Hero section with file upload + text/URL input
- Animated verification result page
- Three.js WebGL background
- Browser extension source
- Zero backend wiring

---

## 2. Step 1 — Frontend Migration (Vite → Next.js)

**Commit:** `fd5c847`  
**Branch created:** `frontend`

### What was removed from `apps/web-portal/`
| File/Dir | Reason |
|---|---|
| `src/App.tsx` | Vite SPA root — replaced by Next.js App Router |
| `src/main.tsx` | Vite entry point |
| `src/index.css` | Replaced by `src/app/globals.css` |
| `src/store/authStore.ts` | Zustand auth store — replaced by `lib/auth.ts` |
| `src/store/verificationStore.ts` | Zustand verify store — replaced by `lib/api.ts` |
| `src/components/` (all 7) | Vite-era components replaced by new ones |
| `index.html` | Vite entry HTML — not needed in Next.js |
| `vite.config.ts` | Build config replaced by `next.config.ts` |
| `tailwind.config.js` | Tailwind 3 config replaced by Tailwind 4 CSS-first config |
| `postcss.config.js` | Replaced by `postcss.config.mjs` |
| `tsconfig.node.json` | Vite-specific TS config |
| `nginx.conf` | Obsolete — Next.js serves itself |
| `build_out.txt` | Build artifact log |
| `package-lock.json` | Regenerated for new deps |

### What was added to `apps/web-portal/`
All files copied from `ZeroTrustFrontend/` (excluding `node_modules`, `.next`, build artifacts):

```
apps/web-portal/
  src/
    app/
      layout.tsx             ← Root layout: Geist fonts, HyperspeedBackground
      page.tsx               ← Homepage: Hero + AgentsSection
      globals.css            ← Tailwind 4 directives + glass-card utility
      verify/page.tsx        ← Verification result page (still mocked at this point)
      about/page.tsx
      changelog/page.tsx
      contact/page.tsx
      demo/page.tsx          ← Redirects to /verify with preset claim
      docs/page.tsx
      docs/api/page.tsx      ← API reference (had wrong data — fixed later)
      extension/page.tsx
      how-it-works/page.tsx
      privacy/page.tsx
      research/page.tsx
      terms/page.tsx
      use-cases/page.tsx
    components/
      layout/
        Navbar.tsx
        Footer.tsx
        Hero.tsx             ← Input modes: text/url/image/video/audio
        AgentsSection.tsx    ← 6 agent cards with animated reveal
        HyperspeedBackground.tsx ← Three.js WebGL persistent layer
        PageTransition.tsx
      ui/
        InstallModal.tsx     ← Chrome extension install steps modal
        ProcessingTracker.tsx (unused)
        ResultPreview.tsx    (unused)
    lib/
      fileStore.ts           ← In-memory singleton for pending file uploads
  extension/                 ← Full MV3 browser extension source
    background/background.js
    content/content.js + content.css
    popup/popup.html + popup.js + popup.css
    sidebar/sidebar.html + sidebar.js + sidebar.css
    icons/
    manifest.json
  public/
    logo-transparent.png
    zerotrust-extension.zip  ← Packaged extension for InstallModal download
  next.config.ts
  next-env.d.ts
  postcss.config.mjs
  eslint.config.mjs
  tsconfig.json
  package.json               ← Next.js 16.1.6 / React 19 / Tailwind 4
  .gitignore
  README.md
```

### Dockerfile Updated
Old Dockerfile used nginx to serve a Vite static build. Replaced with a **4-stage Next.js standalone build**:

```dockerfile
# Stage 1: base  — node:20-alpine
# Stage 2: deps  — npm install
# Stage 3: builder — npm run build (standalone output)
# Stage 4: runner — copies .next/standalone + .next/static, runs node server.js
```

### `next.config.ts` — Added `output: 'standalone'`
Required so the Docker runner stage can copy only the minimal server files without `node_modules`.

### `docker-compose.yml` — Updated `web-portal` service
| Before | After |
|---|---|
| Port `5173:5173` | Port `3001:3000` |
| `VITE_API_BASE_URL` | `NEXT_PUBLIC_API_URL` |
| `command: npm run dev -- --host 0.0.0.0` | Removed (production image) |
| No volume mounts removed | (dev volumes removed — prod build) |

---

## 3. Step 2 — Phase 1: API Client Foundation

**Commit:** `39a9d12` (included with Phase 2)

### `.env.local` — Fixed API URL
```diff
- NEXT_PUBLIC_API_URL=http://localhost:8000   ← was pointing at verification engine
+ NEXT_PUBLIC_API_URL=http://localhost:3000   ← correct: API gateway
```

### `src/lib/auth.ts` — New File
Token store helpers for localStorage (SSR-safe with `typeof window` guard):

```typescript
tokenStore.setTokens({ accessToken, refreshToken, user })
tokenStore.getAccessToken()      // → string | null
tokenStore.getRefreshToken()     // → string | null
tokenStore.getUser()             // → AuthUser | null
tokenStore.setAccessToken(token) // used by silent refresh
tokenStore.isAuthenticated()     // → boolean
tokenStore.clear()               // on logout
```

Exported types: `AuthUser { id, email, tier }`, `TokenSet { accessToken, refreshToken, user }`.

### `src/lib/api.ts` — New File
Central typed fetch wrapper for all backend endpoints.

**Key behaviors:**
- Attaches `Authorization: Bearer <token>` automatically from `tokenStore`
- On **401**: calls `POST /api/v1/auth/refresh` silently, retries original request once
- Deduplicates concurrent refresh calls via a shared `Promise`
- Throws `ApiError(status, message, details?)` on non-2xx responses
- `204 No Content` returns `undefined`

**Exported API modules:**

| Module | Methods | Endpoint(s) |
|---|---|---|
| `authApi` | `register()`, `login()` (auto-stores tokens), `logout()` (auto-clears) | `POST /api/v1/auth/*` |
| `verifyApi` | `submit(payload)`, `getById(id)` | `POST /api/v1/verify`, `GET /api/v1/verify/:id` |
| `historyApi` | `list(page, limit)` | `GET /api/v1/history` |
| `trendingApi` | `list(limit, days)` | `GET /api/v1/trending` |
| `mediaApi` | `uploadFile(file)` → presign → S3 PUT → returns `{ s3Url, key }` | `POST /api/v1/media/presign` + direct S3 |

**Exported types** (matching backend shapes exactly):
- `VerificationResult` — `confidence: 'Low'|'Moderate'|'High'` (not `number`)
- `VerificationSource`, `EvidenceSummary`, `AgentVerdict`
- `PaginatedHistory`, `TrendingResult`, `PresignResponse`

---

## 4. Step 3 — Phase 2: Wire /verify to Real Backend

**Commit:** `39a9d12`

### `src/app/verify/page.tsx` — Major Update

#### Interface fix
Removed the old inline `VerificationResult` interface (had `confidence: number` and was missing 6 fields). Now imports the correct type from `@/lib/api`.

```typescript
// Before (wrong):
interface VerificationResult {
  confidence: number;  // ← WRONG, backend sends 'Low'|'Moderate'|'High'
  // missing: limitations, recommendation, claim_type, cache_tier, agent_consensus
}

// After (correct):
import { verifyApi, mediaApi, ApiError, type VerificationResult } from '@/lib/api';
```

#### `fetchResults` — Mock replaced with real API calls

**Text/URL flow:**
```typescript
data = await verifyApi.submit({
  content: query,
  type: mode as 'text' | 'url',
  source: source || undefined,
});
```

**Media file flow (image/video/audio):**
```typescript
const pending = fileStore.get();                    // get File object
const { s3Url } = await mediaApi.uploadFile(file); // presign → PUT to S3
data = await verifyApi.submit({
  content: s3Url,
  type: pending.mode as 'image' | 'video' | 'audio',
});
fileStore.clear();
```

**Error handling:**
```typescript
} catch (err) {
  if (err instanceof ApiError) setError(err.message);
  else setError('Verification failed. Please check your connection and try again.');
}
```

#### Display improvements

| Section | Before | After |
|---|---|---|
| Badges row | `processing_time` + `sources_consulted` | + `confidence` badge + `⚡ cache_tier` badge (when cached) |
| Evidence summary | `JSON.stringify(obj)` raw dump | `recommendation` as italic blockquote + 3 stat cards: Supporting / Contradicting / Neutral |
| Agent verdicts | Plain string verdict only | Object verdicts: `verdict` + `summary` blurb below each agent |
| Verdict color logic | `includes('support')` only | Also matches `includes('true')` for "Verified True" |
| Limitations | Not rendered | New section with amber `AlertCircle` per item |

---

## 5. Step 4 — Full Workspace Audit

After the core wiring was complete, a full audit was run across the entire workspace. The audit identified:

- **12 confirmed working areas** (full backend, all 5 routes, 3-tier cache, verification engine pipeline, media analysis, Docker setup)
- **9 bugs** (documented below)
- **5 missing features** (auth UI, history page, trending page, extension zip, docs stubs)
- **2 dead code files** (`ProcessingTracker.tsx`, `ResultPreview.tsx`)

---

## 6. Step 5 — Bug Fix Pass (All 8 Bugs)

**Commit:** `b041fdb`

> Note: Bug 9 (InstallModal download button) was already resolved — `public/zerotrust-extension.zip` exists and the modal's CTA already links to `/zerotrust-extension.zip`.

### B1 — Extension Background: Wrong Host + Wrong Path + Wrong Field
**File:** `apps/web-portal/extension/background/background.js`

```diff
- const DEFAULT_API_BASE = 'http://localhost:8000';
+ const DEFAULT_API_BASE = 'http://localhost:3000';

- const res = await fetch(`${apiBase}/verify`, ...
+ const res = await fetch(`${apiBase}/api/v1/verify`, ...

- body = { type: payload.type, query: payload.query }
+ body = { type: payload.type, content: payload.query }
```

**Impact:** Every context-menu and keyboard-shortcut verification was hitting the Python verification engine directly at the wrong port, on a non-existent path, bypassing API gateway auth and caching.

---

### B2 — Simple Extension Popup: SyntaxError (`await` in non-`async`)
**File:** `apps/browser-extension/popup.js`

```diff
- $('settings').addEventListener('click', (e) => {
+ $('settings').addEventListener('click', async (e) => {
```

**Impact:** Browser JavaScript parser rejects the file. The popup refuses to open entirely when clicking the extension icon.

---

### B3 — E2E Tests: Stale Vite Port
**File:** `tests/e2e/claim-verification.spec.ts`

```diff
- const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
+ const BASE_URL = process.env.BASE_URL || 'http://localhost:3001';
```

**Impact:** All Playwright E2E browser tests fail immediately — Playwright navigates to port 5173 where nothing is running.

---

### B4 — Docs API Reference: Wrong URL + Wrong Schema
**File:** `apps/web-portal/src/app/docs/api/page.tsx`

| Before | After |
|---|---|
| Base URL: `http://localhost:8000` | `http://localhost:3000/api/v1` |
| Path: `/verify` | `/api/v1/verify` |
| Request field: `"query": "string"` | `"content": "string"` |
| `"confidence": 0.94` (number) | `"confidence": "High"` (string enum) |
| `"category": "Highly Credible Content"` | Real enum values |
| Single endpoint | Added `/api/v1/media/presign` endpoint |
| Missing fields | Added `limitations`, `recommendation`, `cache_tier`, `agent_verdicts` as objects |

**Impact:** Developers and external integrators reading the API docs would implement incorrect request bodies and misparse response fields.

---

### B5 — Docker: `NEXT_PUBLIC_API_URL` Baked at Wrong Time
**Files:** `apps/web-portal/Dockerfile` + `docker-compose.yml`

`NEXT_PUBLIC_*` variables in Next.js are **inlined at build time** by the compiler (they become literal strings in the JS bundle). Setting them only as runtime `environment:` in docker-compose has no effect — the build step already ran without them.

**Dockerfile change:**
```dockerfile
# builder stage — before RUN npm run build
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
```

**docker-compose.yml change:**
```yaml
web-portal:
  build:
    context: apps/web-portal
    args:
      NEXT_PUBLIC_API_URL: http://api-gateway:3000   # ← passed to ARG
  environment:
    NEXT_PUBLIC_API_URL: http://api-gateway:3000     # ← kept for reference
```

**Impact:** In Docker, the web portal would silently call `http://localhost:3000` (from `.env.local`) from the *user's browser*, which either fails (production) or hits an unintended service.

---

### B6 — Local Dev: Port Clash Between API Gateway and Web Portal
**File:** `apps/web-portal/package.json`

```diff
- "dev": "next dev"
+ "dev": "next dev -p 3001"
```

**Impact:** Running `npm run dev` in `web-portal/` and the API gateway simultaneously would both bind to port 3000. The second to start would crash or silently fail.

---

### B7 — API Gateway CORS: Stale Vite Origin
**File:** `apps/api-gateway/src/app.ts`

```diff
const ALLOWED_ORIGINS = [
  'https://zerotrust.ai',
- 'http://localhost:5173',   ← Vite (stale, never matches anymore)
+ 'http://localhost:3000',   ← local Next.js dev (if run without -p flag)
  'http://localhost:3001',
];
```

**Impact:** If a developer runs `next dev` without `-p 3001`, the browser at `localhost:3000` would be blocked by CORS when calling the API gateway. Also cleans up the dead Vite origin.

---

### B8 — Media Analysis: Missing CORS Middleware
**File:** `apps/media-analysis/src/main.py`

```python
# Added after app = FastAPI(...)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://zerotrust.ai",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**Impact:** Direct browser access to the media analysis service (e.g., health checks, debugging) would be CORS-blocked. The service is primarily called server-to-server by the API gateway, but the missing middleware is a correctness issue.

---

## 7. Current State Summary

### Git Log (`frontend` branch)
```
b041fdb  fix: resolve all 8 bugs from audit
39a9d12  feat: wire /verify page to real backend API
35c4df4  (earlier commit)
fd5c847  feat: replace Vite web-portal with Next.js 16 frontend
8373e57  (origin/main) chore: remove gitignored directories
```

### What Works End-to-End
| Feature | Status |
|---|---|
| Homepage (Hero + AgentsSection + WebGL bg) | ✅ |
| Text/URL claim verification → API gateway → LangGraph pipeline | ✅ |
| Media file verification → presign → S3 → media analysis | ✅ |
| Result display: score, category, confidence, cache badge | ✅ |
| Result display: evidence stat cards (supporting/contradicting/neutral) | ✅ |
| Result display: recommendation blockquote | ✅ |
| Result display: agent verdicts with summaries | ✅ |
| Result display: limitations list | ✅ |
| Download JSON report | ✅ |
| Share URL copy | ✅ |
| Re-verify inline form | ✅ |
| All content pages (about, docs, extension, research, etc.) | ✅ |
| InstallModal with zip download | ✅ |
| Browser extension (web-portal/extension/) — correct API routing | ✅ |
| Browser extension (browser-extension/) — SyntaxError fixed | ✅ |
| E2E test port | ✅ |
| Docker build with correct API URL | ✅ |
| Local dev on port 3001 | ✅ |
| API gateway CORS for localhost:3000/3001 | ✅ |
| Media analysis CORS middleware | ✅ |

### Tech Stack (final)
| Layer | Technology |
|---|---|
| Frontend framework | Next.js 16.1.6 (App Router) |
| UI library | React 19.2.3 |
| Styling | Tailwind CSS 4 (CSS-first config) |
| Animation | Framer Motion 12 |
| 3D background | Three.js + Postprocessing |
| Icons | Lucide React |
| API client | Native `fetch` (no Axios) |
| Token storage | `localStorage` via `tokenStore` |
| API gateway | Express/TypeScript (Node 20) |
| Auth | JWT (15m access / 7d refresh) + Redis JTI blocklist |
| Cache | Redis → DynamoDB → PostgreSQL (3-tier) |
| Verification | FastAPI + LangGraph + AWS Bedrock (Claude 3.5 Sonnet) |
| Media analysis | FastAPI + Textract + Transcribe + Rekognition |
| ORM | Prisma (PostgreSQL) |
| Containers | Docker Compose (5 services) |

---

## 8. Remaining Work

### Priority 2 — Auth UI
No login or register pages exist. The `authApi` module in `api.ts` is fully coded but unreachable from the UI.

- **Create** `src/app/login/page.tsx` — email/password form → `authApi.login()`
- **Create** `src/app/register/page.tsx` — email/password form → `authApi.register()`
- **Update** `src/components/layout/Navbar.tsx`:
  - Currently has a `<div className="w-9" />` spacer where a login button should go
  - Show **Login / Register** buttons when `!tokenStore.isAuthenticated()`
  - Show user email + **Logout** button when authenticated

### Priority 3 — History Page
- **Create** `src/app/history/page.tsx` → `GET /api/v1/history` (requires JWT)
- **Create** `src/app/verify/[id]/page.tsx` → `GET /api/v1/verify/:id` (share-link landing)
- Add **History** link to Navbar (visible when logged in)

### Priority 4 — Trending
- Add trending claims section on homepage or create `src/app/trending/page.tsx`
- Uses `GET /api/v1/trending` (no auth required)

### Priority 5 — Polish
- Wire `ProcessingTracker.tsx` and `ResultPreview.tsx` into the UI or delete them
- Complete the 5 stub doc sections (`/docs` page)
- Add a real preprint link on `/research`

### Known Non-Issues
| Item | Why it's fine |
|---|---|
| `Source` DB table empty | No endpoint writes to it yet; credibility scoring gracefully falls back to defaults |
| `authApi.logout()` 401 on expired token | Acceptable — `tokenStore.clear()` still runs in the `finally` block, so the user is always logged out client-side |
| `NEXT_PUBLIC_API_URL` not in git | `.env.local` is correctly gitignored; set it per-environment |
