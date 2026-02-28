# ZeroTRUST — Detailed Implementation Plan

**Source:** Gaps and recommendations from `Docs/ARCHITECTURE_COMPLIANCE_AND_READINESS.md`  
**Goal:** Implement all in-repo, code-level items that align the codebase with the architecture and fix known gaps.  
**Last updated:** February 28, 2026

---

## Scope: What Can Be Implemented in Code

| Item | From compliance doc | In repo? | Phase |
|------|--------------------|----------|--------|
| Request validation (Zod) | IMPLEMENTATION_STATUS: "no Zod validation on body" | ✅ API Gateway | 1 |
| Presign endpoint for S3 | "no presign endpoint for S3 uploads" | ✅ API Gateway | 1 |
| Trending endpoint | Diagram 2: "Trending Fake News" not implemented | ✅ API Gateway + PG | 1 |
| CloudWatch logs | "No direct integration (Winston → stdout)" | ✅ API Gateway logger | 1 |
| Media pipeline (full) | Diagram 4: S3 → Lambda → Textract/Transcribe/Rekognition | ✅ Implemented | 2 |
| Browser extension | Diagram 1 | ✅ `apps/browser-extension` (MV3) | 3 |
| Lambda (S3 trigger) | Diagram 4 | ✅ `apps/lambda/media-trigger` | 2 |
| Mobile app | Diagram 1 | ❌ Not implemented | 3 (optional) |
| Edge / VPC / AWS API Gateway | Diagrams 1 & 5 | Infra / deploy | Out of scope (IMPL-02) |

---

## Phase 1 — Quick Wins (API Gateway & Observability)

**Objective:** Harden the API, add architecture-mandated features that require no new apps or AWS media services.

### 1.1 Zod validation for request bodies

- **Why:** Consistent validation, clear 400 errors, single source of truth for types.
- **Where:** `apps/api-gateway/src/`
- **Tasks:**
  1. Add validators: `validators/verify.schema.ts`, `validators/auth.schema.ts`.
  2. Verify: `content` (string 10–10000), `type` (enum: text | url | image | video), `source` (optional string).
  3. Auth: register (email, password 8+), login (email, password), refresh (refreshToken).
  4. Use schemas in routes; on failure return `400` with `{ error: 'Validation failed', details: zodError.flatten() }`.
- **Acceptance:** POST /api/v1/verify and /auth/* reject invalid bodies with 400 and structured details.

### 1.2 S3 presigned URL endpoint

- **Why:** Architecture (Diagram 4) expects client → S3 upload via presigned URL; API should issue the URL.
- **Where:** `apps/api-gateway/src/routes/media.routes.ts`, `services/PresignService.ts` (or inline).
- **Tasks:**
  1. Add dependency: `@aws-sdk/client-s3`.
  2. Env: `S3_MEDIA_BUCKET`, `AWS_REGION` (optional; default us-east-1).
  3. New route: `POST /api/v1/media/presign` body: `{ key?: string, contentType: string, extension?: string }`. Key default: `uploads/{uuid}.{ext}`.
  4. Return `{ uploadUrl, key, expiresIn }`. If bucket not configured, return `503` with message "Media upload not configured".
- **Acceptance:** When S3_MEDIA_BUCKET is set, client receives a valid PUT URL; without bucket, 503.

### 1.3 Trending claims endpoint

- **Why:** Diagram 2 — "Trending Fake News" aggregator; product value for high-volume/repeated claims.
- **Where:** `apps/api-gateway/src/routes/trending.routes.ts`, use Prisma (raw or groupBy).
- **Tasks:**
  1. `GET /api/v1/trending?limit=20&days=7`.
  2. Query: last N days, group by `claimHash` (and claimText for display), count verifications, order by count desc, limit.
  3. Return array of `{ claimHash, claimText, count, lastSeen, sampleVerificationId?, category?, credibilityScore? }` (sample = one recent verification for that claim).
- **Acceptance:** Returns top recurring claims in the time window; no auth required (public analytics).

### 1.4 Optional CloudWatch Logs

- **Why:** Diagram 1 — Observability via CloudWatch; production logs in one place.
- **Where:** `apps/api-gateway/src/utils/logger.ts`.
- **Tasks:**
  1. Add optional transport when `CW_LOG_GROUP` (and optionally `AWS_REGION`) are set.
  2. Use `winston-cloudwatch` or custom transport with `@aws-sdk/client-cloudwatch-logs` (PutLogEvents). Prefer minimal dependency: custom transport that batches and sends.
  3. Do not break local dev: if CW vars not set, logger remains console-only.
- **Acceptance:** In AWS env with CW_LOG_GROUP set, logs appear in CloudWatch; locally unchanged.

---

## Phase 2 — Media Pipeline (Implemented)

**Objective:** Full Diagram 4 pipeline: S3 URL → Textract / Transcribe / Rekognition → evidence merge → credibility.

### 2.1 Media-analysis: full pipeline

- **Where:** `apps/media-analysis/src/` — `main.py`, `aws_media.py`, `s3_utils.py`, `evidence_merge.py`
- **Implemented:** `POST /analyze` with body `{ url: S3 URL, contentType }`. Runs Textract (image OCR), Rekognition (image labels/moderation, video labels with async poll), Transcribe (audio, async poll). Merges evidence, computes credibility score, returns VerificationResult-compatible shape.
- **Acceptance:** ✅ Image (sync), audio/video (async poll with timeout). S3 URL required (upload via presign first).

### 2.2 API Gateway: route image/video/audio to media-analysis

- **Where:** `apps/api-gateway/src/services/VerificationService.ts`
- **Implemented:** When `type` is `image` | `video` | `audio`, build S3 URL from content (or use content as URL), call `MEDIA_ENGINE_URL/analyze`, cache and store result like text/URL verifications.
- **Acceptance:** ✅ POST /api/v1/verify with type=image and content=S3 key or URL returns media analysis result.

---

## Phase 3 — Clients

- **Browser extension:** ✅ Implemented in `apps/browser-extension` (Chrome MV3). Popup: paste claim (text/URL), verify, show score/category/recommendation. API URL configurable via storage.
- **Lambda (S3 trigger):** ✅ Implemented in `apps/lambda/media-trigger/handler.py`. On S3 Put, POST to Media Analysis `/analyze` with object URL. Deploy with MEDIA_ANALYSIS_URL env.
- **Mobile app:** ❌ Not implemented (React Native would be new app).
- **Neptune / Vector DB:** Backlog; not required for Diagram 2/3/6 compliance.

---

## Implementation Order (Phase 1)

1. **Zod** — validators + wire in verify + auth routes.  
2. **Presign** — S3 client + env + route + app mount.  
3. **Trending** — route + Prisma raw/groupBy + app mount.  
4. **CloudWatch** — optional logger transport + env.  
5. **Docs** — Update ARCHITECTURE_COMPLIANCE_AND_READINESS.md to mark "Trending", "Presign", "Zod", "CloudWatch" as done where applicable.

---

## Files to Create or Modify (Phase 1)

| File | Action |
|------|--------|
| `apps/api-gateway/src/validators/verify.schema.ts` | Create |
| `apps/api-gateway/src/validators/auth.schema.ts` | Create |
| `apps/api-gateway/src/validators/index.ts` | Create (re-export) |
| `apps/api-gateway/src/routes/verify.routes.ts` | Use Zod, central error format |
| `apps/api-gateway/src/routes/auth.routes.ts` | Use Zod |
| `apps/api-gateway/src/routes/media.routes.ts` | Create (presign) |
| `apps/api-gateway/src/routes/trending.routes.ts` | Create |
| `apps/api-gateway/src/app.ts` | Mount /api/v1/media, /api/v1/trending |
| `apps/api-gateway/src/utils/logger.ts` | Optional CloudWatch transport |
| `apps/api-gateway/package.json` | Add @aws-sdk/client-s3; optional winston-cloudwatch |
| `.env.local.example` | Add S3_MEDIA_BUCKET, CW_LOG_GROUP |
| `Docs/ARCHITECTURE_COMPLIANCE_AND_READINESS.md` | Update §1.2 table and §8 |

---

## Success Criteria (Phase 1 Complete)

- [x] POST /api/v1/verify with invalid body returns 400 with Zod details.  
- [x] POST /api/v1/auth/register and /login with invalid body return 400 with Zod details.  
- [x] POST /api/v1/media/presign returns uploadUrl when S3_MEDIA_BUCKET set, else 503.  
- [x] GET /api/v1/trending?limit=20&days=7 returns array of trending claims.  
- [x] With CW_LOG_GROUP set, logs appear in CloudWatch; without, console only.  
- [x] ARCHITECTURE_COMPLIANCE_AND_READINESS.md updated to reflect implemented items.

**Phase 1 implemented:** February 28, 2026. See code: `apps/api-gateway/src/validators/`, `routes/media.routes.ts`, `routes/trending.routes.ts`, `utils/cloudwatch-transport.ts`, `utils/logger.ts`; `apps/media-analysis` structured stub.
