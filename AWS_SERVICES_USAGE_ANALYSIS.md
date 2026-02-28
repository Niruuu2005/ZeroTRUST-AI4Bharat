# ZeroTRUST — AWS Services Usage Analysis (Prototype vs. Intended)

**Purpose:** Compare the **intended** use of each AWS service (from architecture/docs) with **actual usage** in the prototype codebase.  
**Scope:** Prototype only; production deployment may add more services.  
**Last updated:** February 28, 2026

---

## Summary Table

| AWS Service | Intended role | Used in prototype? | How / where | Verdict |
|-------------|----------------|---------------------|-------------|---------|
| **Bedrock** | Multi-agent LLM orchestration | ✅ Yes | Verification engine: manager, agents, report | Used properly |
| **Lambda** | Lightweight serverless (normalization, async) | ❌ No | — | Not used |
| **ECS Fargate** | Heavy processing (verification, API, media) | ⚠️ Deploy only | Docker Compose locally; ECS in IMPL-02 for prod | Pattern ready, not in app code |
| **API Gateway** | Public REST API | ⚠️ Replaced | Express (Node.js) app as “api-gateway” service | Custom API, not AWS API Gateway |
| **Textract** | OCR from images | ❌ No | Media-analysis is placeholder | Not used |
| **Transcribe** | Speech-to-text (audio/video) | ❌ No | Media-analysis is placeholder | Not used |
| **Rekognition** | Image/video analysis, deepfake/face | ❌ No | Media-analysis is placeholder | Not used |
| **S3** | Media uploads, reports, models | ❌ No | No S3 calls in any app | Not used |
| **DynamoDB** | Hot cache, cached verifications | ✅ Yes | API Gateway: Tier 2 cache (CacheService) | Used properly |
| **ElastiCache (Redis)** | In-memory cache (3-tier) | ✅ Yes | Redis via `REDIS_URL` (Docker locally; ElastiCache in prod) | Used properly |
| **Neptune** | Graph (claims, sources, entities) | ❌ No | No references in code | Not used |
| **CloudWatch** | Logs, metrics, alerts | ⚠️ Indirect | Winston → stdout; ECS/CloudWatch would collect | Not explicitly integrated |

---

## 1. LLM / AI orchestration — AWS Bedrock

**Intended:** Multi-agent LLM orchestration (Claude/Llama for manager + specialist agents).

**In prototype:**

- **Used:** Yes.
- **Where:** `apps/verification-engine/src/integrations/bedrock.py` + all agents and report generator.
- **Details:**
  - `boto3.client('bedrock-runtime')` in `us-east-1`.
  - Model mapping: **manager** → Claude 3.5 Sonnet, **research** → Mistral Large, **sentiment** → Claude 3.5 Haiku.
  - Fallback chain: Sonnet → Haiku → Mistral on throttle/errors.
  - `invoke_bedrock(config_key, prompt)` used from: manager (claim analysis), report (recommendation), research/news/scientific/social/sentiment/scraper agents (verdict/summary).
  - Graceful degradation: if Bedrock client fails (e.g. no AWS creds), returns mock JSON so pipeline still runs.

**Verdict:** Reused properly for multi-agent LLM orchestration. No Llama in code; docs mention it as optional fallback.

---

## 2. Serverless compute — AWS Lambda

**Intended:** Lightweight serverless for content normalization, pre/post-processing, async tasks.

**In prototype:**

- **Used:** No.
- **Where:** Not referenced in `apps/api-gateway` or `apps/verification-engine` or `apps/media-analysis`.
- **Details:** Normalization runs inside the verification-engine (Python) in-process. No Lambda handlers, no event triggers, no direct or indirect Lambda invocations.

**Verdict:** Not used. Prototype uses ECS/containers for all processing; Lambda is a future or production option.

---

## 3. Containers — AWS ECS Fargate

**Intended:** Runs heavy processing: multi-agent verification engine, API services, deepfake/media pipelines.

**In prototype:**

- **Used:** Only as deployment target in docs (IMPL-02), not in application code.
- **Where:** `docker-compose.yml` runs the same services locally (api-gateway, verification-engine, media-analysis). No ECS/Fargate SDK or config in repo.
- **Details:** Architecture is container-ready (Dockerfiles for api-gateway, verification-engine, media-analysis, web-portal). Fargate would run these images in AWS.

**Verdict:** Pattern is correct and ready for ECS Fargate; prototype runs the same stack via Docker Compose. Not “used” inside app code because it’s infrastructure.

---

## 4. API layer — AWS API Gateway

**Intended:** Exposes public REST API to web, extension, mobile, partners.

**In prototype:**

- **Used:** No. A custom API service is used instead.
- **Where:** `apps/api-gateway` is an **Express.js (Node.js)** app that implements the REST API (auth, verify, history, rate limit, 3-tier cache). Diagrams (e.g. IMPL-01) show “AWS API Gateway” at the edge; in the repo there is no AWS API Gateway configuration or usage.
- **Details:** All routes (`/api/v1/verify`, `/api/v1/auth/*`, `/api/v1/history`, `/health`) are implemented in Express. Production could put AWS API Gateway (or ALB + CloudFront) in front of this service.

**Verdict:** The **API layer** is implemented and used properly; the **implementation** is Express, not AWS API Gateway. So “AWS API Gateway” is not reused in the prototype.

---

## 5. OCR — AWS Textract

**Intended:** Extracts text from images (screenshots, scanned articles, documents).

**In prototype:**

- **Used:** No.
- **Where:** `apps/media-analysis` only exposes `/health` and `/analyze`; `/analyze` returns “not yet implemented.” No boto3 Textract or any OCR logic.

**Verdict:** Not used. Would belong in media-analysis when image pipeline is implemented.

---

## 6. Speech-to-text — AWS Transcribe

**Intended:** Converts audio/video speech (e.g. WhatsApp forwards, clips) to text for verification.

**In prototype:**

- **Used:** No.
- **Where:** No Transcribe client or job polling in any app. Media-analysis has no audio pipeline.

**Verdict:** Not used. Intended for future media/audio flow.

---

## 7. Image/Video analysis — AWS Rekognition

**Intended:** Image/video analysis, deepfake/media manipulation detection, object/face detection.

**In prototype:**

- **Used:** No.
- **Where:** No Rekognition client or API calls. Media-analysis is a stub.

**Verdict:** Not used. Would be used in media-analysis when image/video pipeline is built.

---

## 8. Object storage — AWS S3

**Intended:** Stores uploaded media (images, videos, audio), reports, archives, model artifacts.

**In prototype:**

- **Used:** No.
- **Where:** No S3 client, `getObject`, `putObject`, or presigned URL generation in api-gateway or media-analysis. Web portal “image/video” mode sends only a filename; no upload to S3.

**Verdict:** Not used. Needed for real media upload and for media-analysis to read objects (and for reports/artifacts if desired).

---

## 9. NoSQL DB — AWS DynamoDB

**Intended:** Fast key-value/NoSQL for hot metadata, cached verifications, trends, quick lookups.

**In prototype:**

- **Used:** Yes (Tier 2 cache).
- **Where:** `apps/api-gateway/src/services/CacheService.ts` and `VerificationService.ts`.
- **Details:**
  - Lazy-load of `@aws-sdk/client-dynamodb` and `@aws-sdk/util-dynamodb`; if import fails, DynamoDB is disabled (no crash).
  - Table name: `zerotrust-claim-verifications`. Key: `claim_hash` (partition key). Attributes: `result_json`, `ttl` (TTL enabled).
  - `getDynamo(key)` / `setDynamo(key, value)` used in verification flow: Tier 2 lookup after Redis miss; on hit, result is promoted to Redis and returned.
  - Region from `AWS_REGION` (default `us-east-1`).

**Verdict:** Reused properly for cached verifications. Optional for local dev (graceful skip).

---

## 10. In-memory cache — AWS ElastiCache (Redis)

**Intended:** Caching layer for 3-tier design (fast responses, high cache hit target).

**In prototype:**

- **Used:** Yes (Redis protocol; ElastiCache is the AWS-managed Redis).
- **Where:** `apps/api-gateway`: `config/redis.ts` (ioredis), `CacheService.ts` (Tier 1 get/set), `VerificationService.ts` (cache flow), rate-limit store, auth JWT blocklist.
- **Details:** `REDIS_URL` from env (e.g. `redis://redis:6379` in Docker; in AWS would be ElastiCache endpoint). No ElastiCache-specific API; standard Redis usage, so it works with ElastiCache.

**Verdict:** Used properly for Tier 1 cache, rate limiting, and auth. Prototype uses Docker Redis; production would use ElastiCache with the same interface.

---

## 11. Graph DB — AWS Neptune

**Intended:** Graph database for relationships between claims, sources, entities, misinformation networks.

**In prototype:**

- **Used:** No.
- **Where:** No Neptune client or Gremlin/SPARQL in any app. Docs (e.g. IMPL-02, Modules-Phases) mention Neptune as optional/future.

**Verdict:** Not used. Optional/future feature.

---

## 12. Monitoring & logs — AWS CloudWatch

**Intended:** Centralized logging, metrics, dashboards, alerts.

**In prototype:**

- **Used:** Not explicitly.
- **Where:** `apps/api-gateway` uses Winston logger with Console transport only (`utils/logger.ts`). No CloudWatch Logs agent, no PutLogEvents, no custom metrics. In ECS, stdout would typically be collected by the CloudWatch Logs driver, but the app does not send logs directly to CloudWatch.

**Verdict:** Logging is in place (Winston → stdout); CloudWatch is not integrated in code. Deployment (e.g. ECS task definition) can add CloudWatch Logs; metrics/alarms would be a separate step.

---

## 13. What’s used properly vs. missing

**Used and aligned with intent:**

- **Bedrock:** Multi-model, fallback, used by manager and all agents; mock when unavailable.
- **DynamoDB:** Tier 2 cache with correct key design and graceful disable.
- **Redis (ElastiCache-ready):** Tier 1 cache, rate limit, JWT blocklist; same code works with ElastiCache.

**Implemented but with a different service:**

- **API layer:** Implemented as Express “api-gateway” service; AWS API Gateway is not used in the prototype.
- **Containers:** Implemented with Docker/Compose; ECS Fargate is the intended production host (not in code).

**Not used in prototype (intended for production or future):**

- **Lambda:** No serverless functions; all logic in ECS services.
- **Textract, Transcribe, Rekognition:** Media pipeline not built; media-analysis is a stub.
- **S3:** No upload or object access; needed for media and optionally reports/models.
- **Neptune:** No graph usage.
- **CloudWatch:** No direct integration; only stdout logging.

---

## 14. Recommendations

1. **Keep as-is for prototype:** Bedrock, DynamoDB (optional), Redis. No change required for “used properly” services.
2. **When adding media pipeline:** Integrate Textract (OCR), Transcribe (STT), Rekognition (faces/objects) in media-analysis; add S3 upload (presigned URL in api-gateway) and S3 read in media-analysis.
3. **When moving to production:** Consider AWS API Gateway or ALB in front of Express; ensure ECS task definitions and CloudWatch Logs (and optional metrics) are configured; optionally add Lambda for small async tasks if desired.
4. **Optional later:** Neptune for claim/source/entity graph; CloudWatch metrics and alarms for latency, errors, cache hit rate.

---

*This analysis reflects the prototype codebase and docs as of the date above.*
