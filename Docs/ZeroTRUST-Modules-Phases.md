# ZeroTRUST — Module-Wise Implementation Plan
## Divided by Phase & Module

**Project:** ZeroTRUST — AI-Powered Misinformation Detection  
**Track:** AWS AI for Bharat Hackathon 2026  
**Doc Type:** Module Breakdown | **Date:** February 28, 2026

---

## Phase Overview

```
Phase 0 ── Foundation & Repo Setup                     (Day 1)
Phase 1 ── Data Layer & Infrastructure                 (Day 1–2)
Phase 2 ── API Gateway Service                         (Day 2–3)
Phase 3 ── Verification Engine Core                    (Day 3–4)
Phase 4 ── Multi-Agent System (6 Agents)               (Day 4–6)
Phase 5 ── Media Analysis Pipeline                     (Day 6–7)
Phase 6 ── Caching & Optimization                      (Day 7–8)
Phase 7 ── Frontend Clients                            (Day 8–10)
Phase 8 ── Integration, Testing & Demo Polish          (Day 10–12)
```

---

## PHASE 0 — Foundation & Repo Setup

### Module 0.1 — Monorepo Scaffold

| Field | Detail |
|-------|--------|
| **Purpose** | Create the repository structure all other modules build on |
| **Owner** | Full team |
| **Output** | Working monorepo with Docker Compose running locally |

**Directory structure to create:**
```
zerotrust-aws/
├── apps/
│   ├── api-gateway/
│   ├── verification-engine/
│   ├── media-analysis/
│   ├── web-portal/
│   ├── browser-extension/
│   └── mobile-app/
├── infrastructure/
├── scripts/
├── docs/
├── .env.local.example
└── docker-compose.yml
```

**Tasks:**
- [ ] `git init` + create GitHub repo + add `.gitignore`
- [ ] Bootstrap `api-gateway` with `npm init -y` + TypeScript config
- [ ] Bootstrap `verification-engine` with `python -m venv venv` + `requirements.txt`
- [ ] Bootstrap `web-portal` with `npm create vite@latest`
- [ ] Bootstrap `browser-extension` with Webpack + MV3 template
- [ ] Bootstrap `mobile-app` with `npx create-expo-app`
- [ ] Create root `docker-compose.yml` (Postgres + Redis + all 3 backend services)
- [ ] Create `.env.local.example` with all required keys documented

**Acceptance Criteria:**
- `docker-compose up` starts without errors
- All services return `{"status":"healthy"}` on `/health`

---

### Module 0.2 — Shared Types & API Contract

| Field | Detail |
|-------|--------|
| **Purpose** | Define the canonical TypeScript interfaces shared across web portal, extension, and mobile app |
| **Output** | `shared/types/verification.types.ts` used by all frontend clients |

**Types to define:**
```typescript
VerificationResult, VerificationRequest, SourceReference,
AgentVerdict, CredibilityCategory, ContentType
```

**Tasks:**
- [ ] Create `packages/shared-types/` with TypeScript interfaces (see IMPL-01 §7)
- [ ] Wire into `web-portal`, `browser-extension` via `tsconfig.json` path alias
- [ ] Create Python Pydantic models (`verification-engine/src/models/verification.py`)

---

## PHASE 1 — Data Layer & Infrastructure

### Module 1.1 — PostgreSQL Database

| Field | Detail |
|-------|--------|
| **Purpose** | Primary relational store — users, verifications, source credibility |
| **Tech** | PostgreSQL 15 via RDS (prod) / Docker (local) |
| **Inputs** | Verification results from Verification Engine |
| **Outputs** | Query results to API Gateway |

**Schema tables:**
```
users               — auth + subscription tier
verifications       — all verification results (permanent store)
sources             — source domain credibility registry
api_keys            — enterprise API key management
```

**Tasks:**
- [ ] Write `schema.prisma` with all 4 tables
- [ ] Write and test Prisma migrations (`npx prisma migrate dev`)
- [ ] Add indexes: `claim_hash`, `user_id`, `created_at DESC`
- [ ] Seed `sources` table with 50+ pre-rated domains (Tier 1–4)
- [ ] Write `scripts/seed-sources.py`

**Acceptance Criteria:**
- Prisma migrate runs without error
- `SELECT COUNT(*) FROM sources` returns ≥ 50 rows post-seed
- CRUD queries complete in < 50ms locally

---

### Module 1.2 — Redis Cache (Tier 1)

| Field | Detail |
|-------|--------|
| **Purpose** | Hot cache — 1-hour TTL, <5ms latency, ~60% hit rate |
| **Tech** | Redis 7 via ElastiCache (prod) / Docker (local) |
| **Key format** | `verify:{type}:{sha256_hash[:32]}` |

**Tasks:**
- [ ] Add Redis service to `docker-compose.yml` (maxmemory 256MB, allkeys-lru)
- [ ] Write `CacheService.ts` with `getRedis()`, `setRedis()`, `deleteRedis()`
- [ ] Implement SHA-256 claim normalization for cache key generation
- [ ] Set TTL: 3600s general, 86400s for trending claims
- [ ] Add Redis rate-limit store for `express-rate-limit`

**Acceptance Criteria:**
- Second identical verification request returns `cached: true, cache_tier: "redis"`
- Redis memory usage stays under threshold with LRU eviction

---

### Module 1.3 — DynamoDB Tables (Tier 2 Cache)

| Field | Detail |
|-------|--------|
| **Purpose** | Warm cache — 24-hour TTL, <20ms latency, ~25% hit rate on Redis misses |
| **Tech** | DynamoDB on-demand (us-east-1) |

**Tables to create:**
```
zerotrust-claim-verifications   — PK: claim_hash, SK: created_at, TTL: 24h
zerotrust-user-sessions         — PK: session_id, TTL: 24h
```

**Tasks:**
- [ ] Create DynamoDB tables via AWS CLI (see IMPL-02 §7.2)
- [ ] Enable TTL attribute on both tables
- [ ] Write `CacheService.getDynamo()` + `CacheService.setDynamo()`
- [ ] Implement L2→L1 promotion: on DynamoDB hit, write back to Redis

**Acceptance Criteria:**
- Third request (after Redis TTL expires) returns `cache_tier: "dynamodb"`
- DynamoDB item has `ttl` attribute as epoch timestamp

---

### Module 1.4 — S3 Buckets

| Field | Detail |
|-------|--------|
| **Purpose** | Object storage for media uploads, ML models, static web portal |
| **Tech** | AWS S3 (us-east-1) |

**Three buckets:**
```
zerotrust-media-uploads-{account}   — user uploaded images/videos
zerotrust-models-{account}          — ML model artifacts (.h5, .pth)
zerotrust-static-{account}          — web portal build (React)
```

**Tasks:**
- [ ] Create 3 S3 buckets via AWS CLI (see IMPL-02 §8)
- [ ] Configure CORS on media bucket for pre-signed PUT uploads
- [ ] Block public access on all buckets
- [ ] Configure S3 → SQS event notification for media uploads

---

### Module 1.5 — SQS Queue (Media Pipeline Trigger)

| Field | Detail |
|-------|--------|
| **Purpose** | Decouple media upload from analysis — S3 event → SQS → Media Analysis ECS |
| **Tech** | AWS SQS Standard Queue |

**Tasks:**
- [ ] Create `zerotrust-media-queue` (visibility timeout 600s)
- [ ] Wire S3 bucket notification to SQS queue
- [ ] Write SQS consumer in `media-analysis/src/consumer.py`

---

## PHASE 2 — API Gateway Service

### Module 2.1 — Express App Bootstrap

| Field | Detail |
|-------|--------|
| **Purpose** | HTTP entry point for all client requests |
| **Tech** | Node.js 20 + Express 4.18 + TypeScript |
| **Port** | 3000 |
| **File** | `apps/api-gateway/src/app.ts` |

**Middleware stack (in order):**
```
trust proxy → helmet → CORS → compression → json body parser
→ request logger → rate limiter → routes → error handler
```

**Tasks:**
- [ ] Set up Express with TypeScript + `tsconfig.json`
- [ ] Add `helmet`, `cors`, `compression`, `express-rate-limit`
- [ ] Configure CORS allowlist: web portal, `chrome-extension://`, localhost (dev)
- [ ] Create `GET /health` endpoint
- [ ] Set `app.set('trust proxy', 1)` for ALB/CloudFront IP forwarding

---

### Module 2.2 — JWT Authentication

| Field | Detail |
|-------|--------|
| **Purpose** | Stateless auth — sign tokens on login, verify on protected routes |
| **Tech** | `jsonwebtoken` + Redis blocklist |

**Two middleware functions:**
- `authMiddleware` — required auth (reject 401 if missing/invalid)
- `optionalAuth` — attach user if token present, continue anonymous if not

**Token structure:**
```typescript
{ sub: userId, email, tier: 'free'|'pro'|'enterprise', jti: uuid, iat, exp }
```

**Tasks:**
- [ ] Implement `authMiddleware.ts` (see IMPL-03 §1.3)
- [ ] Implement `optionalAuth` for public `/verify` endpoint
- [ ] JWT revocation: on logout, write `blocked:jti:{jti}` to Redis with TTL = token expiry
- [ ] `POST /api/v1/auth/register` — hash password with bcrypt (cost 12), create user
- [ ] `POST /api/v1/auth/login` — verify, issue access (15m) + refresh (7d) tokens
- [ ] `POST /api/v1/auth/refresh` — validate refresh token, return new access token
- [ ] `POST /api/v1/auth/logout` — blocklist JTI in Redis

**Acceptance Criteria:**
- Login returns `{ accessToken, refreshToken }`
- Protected routes return `401` without valid token
- Revoked tokens rejected even before expiry

---

### Module 2.3 — Rate Limiting

| Field | Detail |
|-------|--------|
| **Purpose** | Prevent abuse of free tier and unauthenticated endpoints |
| **Tech** | `express-rate-limit` + `rate-limit-redis` |

**Rate limit tiers:**
| Tier | Limit | Window |
|------|-------|--------|
| Public (unauthenticated) | 10 req | per minute |
| Free user | 100 req | per day |
| Pro user | 5,000 req | per day |
| Enterprise | Unlimited | — |

**Tasks:**
- [ ] `publicRateLimit` middleware (see IMPL-03 §1.4)
- [ ] `userRateLimit` middleware — reads `req.user.tier` after `optionalAuth`
- [ ] Return `429` with `Retry-After` header on limit exceeded

---

### Module 2.4 — Verification Controller & 3-Tier Cache

| Field | Detail |
|-------|--------|
| **Purpose** | Cache-first verification: Redis → DynamoDB → CloudFront/PG → Full pipeline |
| **Key files** | `VerificationController.ts`, `VerificationService.ts`, `CacheService.ts` |

**Flow:**
```
POST /api/v1/verify
  → optionalAuth → publicRateLimit (or userRateLimit)
  → VerificationController.verify()
    → VerificationService.verify()
      → Tier 1: Redis lookup
      → Tier 2: DynamoDB lookup + L2→L1 promote
      → Tier 3: PostgreSQL lookup + backfill upper tiers
      → Full: HTTP POST to Verification Engine :8000
      → Write all tiers + persist to PostgreSQL
```

**Tasks:**
- [ ] `POST /api/v1/verify` — public + authenticated (see IMPL-03 §1.5)
- [ ] `GET /api/v1/verify/:id` — fetch result by ID from PostgreSQL
- [ ] `GET /api/v1/history` — paginated user verification history
- [ ] Cache key: `sha256(normalized_claim + ':' + type)[:32]`
- [ ] `GET /api/v1/verify/presign` — return S3 pre-signed URL for media upload
- [ ] Circuit breaker around Verification Engine call (opossum)

**Acceptance Criteria:**
- Cache hit returns in < 200ms
- Cache miss (full verify) returns in < 10s with valid VerificationResult JSON
- `cached: true, cache_tier: "redis"` on second identical request

---

## PHASE 3 — Verification Engine Core

### Module 3.1 — FastAPI App Bootstrap

| Field | Detail |
|-------|--------|
| **Purpose** | Python service that owns the agent pipeline |
| **Tech** | Python 3.11 + FastAPI 0.110 + Uvicorn |
| **Port** | 8000 |

**Tasks:**
- [ ] Create `apps/verification-engine/src/main.py` (see IMPL-03 §2.2)
- [ ] Register `POST /verify` router
- [ ] `GET /health` endpoint
- [ ] Uvicorn startup: `--workers 2` (local), `--workers 4` (ECS)
- [ ] Dockerfile (CPU-only for prototype — see IMPL-03 §8.2)

---

### Module 3.2 — Normalization Layer

> **Source:** Architecture Diagram 2 — runs before Manager Agent

| Field | Detail |
|-------|--------|
| **Purpose** | Pre-process every claim before LLM analysis |
| **Components** | `TextNormalizer`, `MetadataExtractor`, `LanguageDetector` |
| **File** | `apps/verification-engine/src/normalization/` |

**Three sub-modules:**

| Sub-module | What it does | Key output |
|------------|-------------|-----------|
| `TextNormalizer` | Strip HTML, unicode NFC, collapse whitespace | `normalized_content` |
| `MetadataExtractor` | Detect URLs, numbers, statistics, quotes, word count | `metadata: dict` |
| `LanguageDetector` | ISO 639-1 language code (en, hi, mr, ta…) | `language: str` |

**Tasks:**
- [ ] `TextNormalizer.normalize(text)` — strip HTML, fix unicode, collapse whitespace
- [ ] `TextNormalizer.to_cache_key(text)` — sorted token set for near-duplicate keys
- [ ] `MetadataExtractor.extract(content, type)` — regex patterns for stats, quotes, URLs
- [ ] `LanguageDetector.detect(text)` — `langdetect` library, fallback to `en`
- [ ] `NormalizationLayer.process(request)` — calls all three, returns enriched dict

**Acceptance Criteria:**
- `"  COVID-19 vaccines <b>cause</b>  autism  "` → `"covid-19 vaccines cause autism"`
- `"https://example.com"` → `metadata.is_url == True`
- Hindi text detected as `hi`

---

### Module 3.3 — Bedrock Integration

| Field | Detail |
|-------|--------|
| **Purpose** | Unified LLM caller with model fallback chain |
| **File** | `apps/verification-engine/src/integrations/bedrock.py` |
| **Models** | Claude 3.5 Sonnet → Llama 3.1 70B → Mistral Large (fallback) |

**Model config map:**
```python
'manager'  → Claude 3.5 Sonnet  (temp 0.3, max 4096 tokens)
'research' → Mistral Large 2407 (temp 0.4, max 2048 tokens)
'sentiment'→ Claude 3.5 Haiku   (temp 0.2, max 1024 tokens)
```

**Tasks:**
- [ ] `boto3.client('bedrock-runtime', region='us-east-1')` with adaptive retry
- [ ] `invoke_bedrock(config_key, prompt)` — calls `bedrock.converse()` API
- [ ] Fallback chain on `ThrottlingException`: cycle through `FALLBACK_CHAIN`
- [ ] Test with real prompt → verify JSON response extracted from `content[0]['text']`

---

### Module 3.4 — LangGraph Agent Graph

| Field | Detail |
|-------|--------|
| **Purpose** | State machine that orchestrates the full verification pipeline |
| **Tech** | LangGraph 0.0.60 |
| **File** | `apps/verification-engine/src/agents/manager.py` |

**Graph nodes (in sequence):**

```
normalize → analyze_claim → select_agents → execute_agents
→ aggregate_evidence → calculate_credibility → generate_report
```

**AgentState TypedDict fields:**
```python
request, normalized, claim_analysis, selected_agents,
agent_results (Annotated[Sequence, add]), evidence,
credibility, report, errors (Annotated[Sequence, add])
```

**Tasks:**
- [ ] Define `AgentState` TypedDict
- [ ] Implement all 7 node functions (see IMPL-03 §4)
- [ ] Wire `StateGraph` with `add_edge` / `set_entry_point`
- [ ] `graph.compile()` → `graph.ainvoke(initial_state)`
- [ ] Expose `ManagerAgent.verify(request)` → returns `VerificationResult`

**Acceptance Criteria:**
- Graph compiles without error
- `ainvoke` returns all expected keys in final state
- Missing/failed agents don't crash the graph (graceful degradation)

---

## PHASE 4 — Multi-Agent System (6 Agents)

> All agents implement `BaseAgent.investigate(claim, analysis) → dict`
> All run in **parallel** via `asyncio.gather` in `execute_agents` node

---

### Module 4.1 — Research Agent

| Field | Detail |
|-------|--------|
| **Purpose** | Broad web + academic DB search |
| **Sources** | Google Custom Search, Bing, Wikipedia, Academic DBs |
| **File** | `agents/research.py` |

**Tasks:**
- [ ] `integrations/search.py` — `search_google(query)` via Google Custom Search API
- [ ] `integrations/search.py` — `search_bing(query)` via Bing Search API (fallback)
- [ ] Wikipedia API call for entity disambiguation
- [ ] Deduplicate results by URL
- [ ] LLM call (Mistral Large) to assess coverage → `{verdict, confidence, summary}`

---

### Module 4.2 — News Agent

| Field | Detail |
|-------|--------|
| **Purpose** | Professional journalism + dedicated fact-checker APIs |
| **Sources** | NewsAPI, GNews, AP, Reuters, BBC, Snopes, PolitiFact, AltNews, Boomlive |
| **File** | `agents/news.py` |

**Tasks:**
- [ ] `integrations/news_apis.py` — `search_newsapi(entities)`, `search_gnews(query)`
- [ ] `integrations/fact_check.py` — `search_factcheckers(claim)` (Snopes, PolitiFact)
- [ ] Source tier assessment: `TIER_1 = {BBC, Reuters, AP, AltNews, Boomlive}`
- [ ] LLM analysis of news coverage (see IMPL-03 §5.2)
- [ ] Extract `factcheck_verdict` from fact-checker results

---

### Module 4.3 — Scientific Agent

| Field | Detail |
|-------|--------|
| **Purpose** | Peer-reviewed literature search |
| **Sources** | PubMed, arXiv, WHO, CDC, CrossRef |
| **File** | `agents/scientific.py` |

**Tasks:**
- [ ] `integrations/scientific_apis.py` — `search_pubmed(query)` via E-utilities API
- [ ] `integrations/scientific_apis.py` — `search_arxiv(query)` via arXiv API
- [ ] LLM consensus assessment → `{consensus_level, verdict, confidence}`
- [ ] Map `consensus_level`: `strong_consensus` / `moderate_consensus` / `divided` etc.
- [ ] Always set `credibility_tier: 'tier_1'` for peer-reviewed hits

---

### Module 4.4 — Social Media Agent

| Field | Detail |
|-------|--------|
| **Purpose** | Viral spread context + community reaction |
| **Sources** | Twitter/X (Bearer token), Reddit (OAuth), Facebook CrowdTangle |
| **File** | `agents/social_media.py` |

**Tasks:**
- [ ] `integrations/social_apis.py` — Twitter v2 recent search (Bearer token)
- [ ] `integrations/social_apis.py` — Reddit search via `httpx` (no OAuth needed for public)
- [ ] Extract engagement metrics (retweets, upvotes) as viral signal
- [ ] LLM analysis — distinguish community consensus from brigading/bots
- [ ] Weight: `tier_4` (social media is context, not authority)

---

### Module 4.5 — Sentiment & Manipulation Agent

| Field | Detail |
|-------|--------|
| **Purpose** | Detect emotional manipulation, propaganda techniques, bias |
| **Sources** | Claim text only (no external API needed) |
| **File** | `agents/sentiment.py` |

**18 propaganda patterns (regex-based):**
```
name_calling, loaded_language, false_urgency, bandwagon,
cherry_picking, false_dilemma, ad_hominem, appeal_to_fear,
appeal_to_authority, repetition, transfer, card_stacking…
```

**Tasks:**
- [ ] `PROPAGANDA_PATTERNS` dict — 18 regex patterns (see IMPL-03 §5.4)
- [ ] Score: `len(detected) × 0.15 + llm_score × 0.85`
- [ ] LLM call (Claude Haiku) for deep analysis → `manipulation_score`, `techniques`
- [ ] Verdict: `contradicts` if manipulation_score > 0.6, `mixed` if > 0.3, else `supports`
- [ ] Always return `sources: []` (no external sources, text-only analysis)

---

### Module 4.6 — Web Scraper Agent

| Field | Detail |
|-------|--------|
| **Purpose** | Fetch and analyze source URL content directly |
| **Sources** | Live web pages, Wayback Machine archive |
| **File** | `agents/scraper.py` |

**Tasks:**
- [ ] `playwright.async_api` — headless Chromium page fetch
- [ ] `BeautifulSoup4` — extract article title, body, author, date
- [ ] Wayback Machine API — fetch archived version if live page fails
- [ ] Assess source domain credibility via `sources` table lookup
- [ ] Triggered automatically when `metadata.is_url == True`

---

### Module 4.7 — Evidence Aggregator

| Field | Detail |
|-------|--------|
| **Purpose** | Merge all 6 agent results into unified evidence object |
| **File** | `services/evidence.py` |

**Output structure:**
```python
{
  "sources": [...all sources deduped by URL...],
  "summary": {"supporting": N, "contradicting": N, "neutral": N},
  "total_sources": N,
  "agent_coverage": {"news": 12, "scientific": 5, ...}
}
```

**Tasks:**
- [ ] Collect all `sources` arrays from agent results
- [ ] Deduplicate by URL (keep highest credibility_score on duplicate)
- [ ] Count stance totals across all sources
- [ ] Sort sources by `credibility_score DESC`

---

### Module 4.8 — Report Generator

| Field | Detail |
|-------|--------|
| **Purpose** | Generate human-readable recommendation + limitations |
| **File** | `services/report.py` |

**Output structure:**
```python
{
  "agent_verdicts": {agent_name: AgentVerdict, ...},
  "limitations": ["list of transparency disclosures"],
  "recommendation": "One paragraph human-readable guidance"
}
```

**Tasks:**
- [ ] Map agent result dicts → `AgentVerdict` Pydantic models
- [ ] Auto-generate `limitations` based on: low agent confidence, few sources, agent errors
- [ ] LLM call (Claude Sonnet) to generate `recommendation` paragraph
- [ ] Include `cached:false` agents as explicit limitations

---

## PHASE 5 — Media Analysis Pipeline

### Module 5.1 — Media Analysis FastAPI Service

| Field | Detail |
|-------|--------|
| **Purpose** | Separate service handling image/video/audio deepfake detection |
| **Tech** | Python 3.11 + FastAPI + TensorFlow (CPU) + PyTorch |
| **Port** | 8001 |
| **File** | `apps/media-analysis/src/main.py` |

**Tasks:**
- [ ] FastAPI app with `POST /analyze` endpoint
- [ ] `GET /health` endpoint
- [ ] SQS consumer loop: poll `zerotrust-media-queue`, process, write result to PostgreSQL
- [ ] Load ML models at startup from `MODEL_DIR` env var
- [ ] CPU-only Dockerfile for prototype (see IMPL-03 §8.3)

---

### Module 5.2 — Image Deepfake Detector

> **Source:** Diagram 4 — Forensic Analysis Engine

| Field | Detail |
|-------|--------|
| **Purpose** | Ensemble detection: XceptionNet + EfficientNet + FFT + EXIF |
| **File** | `detectors/image.py` |
| **Accuracy** | XceptionNet: 91.8%, EfficientNet-B4: ensemble improves to ~94% |

**Ensemble weights:**
```
XceptionNet (299×299)     × 0.35
EfficientNet-B4 (380×380) × 0.35
FFT Frequency Analysis     × 0.20
EXIF Metadata Analysis     × 0.10
```

**Sub-modules:**

| Sub-module | Diagram 4 node | Implementation |
|-----------|---------------|----------------|
| `_xception_predict` | Deepfake Detector | Load `.h5`, predict class[1] (fake probability) |
| `_efficientnet_predict` | Deepfake Detector | Load `.h5`, predict class[1] |
| `_frequency_analysis` | Frequency Analysis | FFT → high-freq/center-freq ratio |
| `_metadata_analysis` | Metadata Analyser | EXIF: timestamp mismatch + editing software detection |

**Tasks:**
- [ ] `ImageDeepfakeDetector.__init__` — load both TF models at startup
- [ ] `analyze(image_path)` — `asyncio.gather` all 4 sub-analyses
- [ ] Threshold: `> 0.70` = `is_likely_manipulated: True`
- [ ] Return `manipulation_probability`, `model_scores`, `frequency_analysis`, `metadata`
- [ ] Fallback: if models not loaded, return `{"available": false}`

---

### Module 5.3 — Video Deepfake Detector

> **Source:** Diagram 4 — includes A/V Sync Check

| Field | Detail |
|-------|--------|
| **Purpose** | Frame-by-frame spatial + temporal analysis |
| **Tech** | PyTorch + MTCNN (face detection) + Bi-LSTM |
| **File** | `detectors/video.py` |

**Analysis pipeline:**
```
FFmpeg → extract every 3rd frame
→ MTCNN → detect faces per frame
→ EfficientNet-B4 → spatial features per frame
→ Bi-LSTM (256 units) → temporal consistency
→ Self-attention → weight inconsistent frames
→ A/V Sync Check → audio-video alignment
→ Weighted ensemble → final probability
```

**Tasks:**
- [ ] `VideoDeepfakeDetector.__init__` — load `.pth` model
- [ ] `extract_frames(video_path, every_n=3)` via `ffmpeg-python`
- [ ] Face detection per frame (MTCNN)
- [ ] Spatial features via EfficientNet backbone
- [ ] Temporal features via Bi-LSTM
- [ ] A/V sync check using `librosa` + `opencv` alignment score
- [ ] Return result with `frames_analyzed`, `faces_detected`, `temporal_score`

---

### Module 5.4 — AWS Media Services Integration

> **Source:** Diagram 4 — AWS Media Intelligence block

| Field | Detail |
|-------|--------|
| **Purpose** | Extract text (OCR), speech (STT), faces/objects from media |
| **Services** | AWS Textract, AWS Transcribe, AWS Rekognition |

**Tasks:**
- [ ] `textract_extract_text(s3_key)` — detect document text in image
- [ ] `transcribe_audio(s3_key)` — start + poll transcription job
- [ ] `rekognition_detect_faces(s3_key)` — face detection for face-swap detection
- [ ] Extract text from images, feed to Verification Engine as claim text
- [ ] Merge AWS results + forensic results in `EvidenceMerger`

---

### Module 5.5 — Evidence Merger (Media)

> **Source:** Diagram 4 — Result Merging block

| Field | Detail |
|-------|--------|
| **Purpose** | Combine AWS media intelligence + forensic analysis → unified credibility score |
| **File** | `services/media_merger.py` |

**Tasks:**
- [ ] Accept: `aws_results` (Textract + Transcribe + Rekognition) + `forensic_results`
- [ ] Weight: forensic score 60%, AWS signals 40%
- [ ] Generate unified credibility score (image/video-specific categories)
- [ ] Write final result to PostgreSQL + Redis

---

## PHASE 6 — Caching & Optimization

### Module 6.1 — Cache Key Normalization

| Field | Detail |
|-------|--------|
| **Purpose** | Ensure semantically similar claims hit the same cache entry |
| **File** | `api-gateway/src/utils/cacheKey.ts`, `verification-engine/src/normalization/text_normalizer.py` |

**Algorithm:**
```
1. lowercase + trim
2. strip HTML + punctuation
3. remove stop words
4. sort tokens alphabetically
5. SHA-256 → hex[:32]
```

**Tasks:**
- [ ] Implement same normalization in TypeScript (API Gateway) and Python (Verification Engine)
- [ ] Unit test: 10 semantically equivalent phrases → same cache key
- [ ] Unit test: 10 distinct claims → different cache keys

---

### Module 6.2 — 3-Tier Cache Flow

> **Source:** Architecture Diagram 6

| Tier | Store | TTL | Action on HIT |
|------|-------|-----|---------------|
| 1 | Redis | 1 hour | Return immediately |
| 2 | DynamoDB | 24 hours | Promote to Redis, return |
| 3 | CloudFront/PostgreSQL | 30 days (popular) | Backfill Redis + DynamoDB, return |
| — | Full verification | — | Write all tiers + PostgreSQL |

**Tasks:**
- [ ] `VerificationService.verify()` implements exact 4-step waterfall (see IMPL-03 §1.5)
- [ ] After full verification, `Promise.allSettled([setRedis, setDynamo, prisma.create])`
- [ ] Trending claims get 24h Redis TTL instead of 1h
- [ ] `cache_tier` field in response: `"redis"`, `"dynamodb"`, `"cloudfront"`, or absent

---

### Module 6.3 — Trending Claims Tracker

| Field | Detail |
|-------|--------|
| **Purpose** | Track which claims are being verified frequently; maintain top-N trending lists |
| **Tech** | Redis Sorted Sets + DynamoDB |

**Tasks:**
- [ ] On every verification hit, `ZINCRBY trending:{category} 1 {claim_hash}`
- [ ] `GET /api/v1/trending` — return top 10 per category from Redis sorted set
- [ ] Expire trending sets every 1 hour (re-compute from DynamoDB)
- [ ] Pre-warm cache for top trending claims on startup

---

## PHASE 7 — Frontend Clients

### Module 7.1 — Web Portal (React)

| Field | Detail |
|-------|--------|
| **Purpose** | Primary user interface for claim verification |
| **Tech** | React 18 + Vite 5 + Tailwind CSS + Framer Motion + Zustand |
| **URL** | https://zerotrust.ai (or CloudFront domain for prototype) |

**Pages:**

| Page | Route | Description |
|------|-------|-------------|
| Home | `/` | Landing page with hero, feature cards, demo CTA |
| Verify | `/verify` | Main claim input + results display |
| History | `/history` | Authenticated user's past verifications |
| About | `/about` | How it works, architecture overview |

**Components:**

| Component | Purpose |
|-----------|---------|
| `ClaimInput` | 4-tab input (text/url/image/video) with drag-drop |
| `CredibilityScore` | Animated SVG ring gauge 0–100 with color coding |
| `EvidenceSummary` | Supporting/contradicting/neutral bar chart |
| `SourceList` | Paginated table with credibility tier badges |
| `AgentBreakdown` | Accordion showing each agent's verdict and sources |
| `LimitationsList` | Transparency disclosures |

**Tasks:**
- [ ] `ClaimInput.tsx` — 4 mode tabs, text area, file drag-drop, URL input
- [ ] `CredibilityScore.tsx` — animated SVG gauge + evidence bars (Framer Motion)
- [ ] `SourceList.tsx` — sortable table, tier badges, stance icons, excerpt expand
- [ ] `AgentBreakdown.tsx` — accordion per agent with confidence badge
- [ ] `useVerification.ts` hook — calls API, manages loading/error/progress state
- [ ] `authStore.ts` (Zustand) — token, user, login/logout actions
- [ ] `verificationStore.ts` (Zustand) — current result, history, loading state
- [ ] Auth pages: Login, Register with form validation (React Hook Form + Zod)

**Acceptance Criteria:**
- Lighthouse Performance ≥ 90 (Vite production build)
- Results visible within 5s of submitting a cache-miss claim
- All 4 input modes functional (text, URL, image, video)

---

### Module 7.2 — Browser Extension (Chrome MV3)

| Field | Detail |
|-------|--------|
| **Purpose** | One-click fact-check from any webpage via context menu |
| **Tech** | Manifest V3 + React popup + content script overlay |
| **Clients** | Chrome, Edge, Brave |

**Three components:**

| Component | Tech | Purpose |
|-----------|------|---------|
| `background.js` (Service Worker) | TypeScript | Context menu, API calls, local cache (chrome.storage) |
| `content-script.js` | TypeScript | Inject floating overlay with verification result |
| `popup.html` + `Popup.tsx` | React | Extension popup for manual input |

**Tasks:**
- [ ] `manifest.json` — MV3, context menu permission, host_permissions for API
- [ ] Service worker: `chrome.contextMenus` → trigger verify on selected text
- [ ] Service worker: call `/api/v1/verify` with Bearer token if signed in
- [ ] Service worker: SHA-256 local cache (`chrome.storage.local`, 24h TTL)
- [ ] Content script: inject floating overlay with loading + result (see IMPL-04 §2.3)
- [ ] Popup: text input + quick result display + link to full web portal

**Acceptance Criteria:**
- Right-click selected text → overlay appears with loading spinner → result in <5s
- Cached claim: result appears in <1s from local cache
- Extension loads unpacked in Chrome Dev mode without errors

---

### Module 7.3 — Mobile App (React Native)

| Field | Detail |
|-------|--------|
| **Purpose** | iOS + Android client for on-the-go fact checking + Share Sheet integration |
| **Tech** | React Native 0.73 + Expo + React Navigation |

**Screens:**

| Screen | Purpose |
|--------|---------|
| `VerifyScreen` | Text input + camera/gallery input |
| `ResultsScreen` | Full verification result with credibility gauge |
| `HistoryScreen` | Past verifications list |
| `SettingsScreen` | Auth, notifications, language |

**Tasks:**
- [ ] `AppNavigator.tsx` — Tab navigator (Verify, History, Settings) + Stack for Results
- [ ] `VerifyScreen.tsx` — text input + image picker (expo-image-picker) + camera
- [ ] `ResultsScreen.tsx` — credibility gauge using React Native SVG + evidence breakdown
- [ ] Share Sheet: register as share target so users can share WhatsApp messages directly
- [ ] Push notifications via Expo Notifications (`sendVerificationAlert`)
- [ ] Offline mode: show cached results from AsyncStorage

---

## PHASE 8 — Integration, Testing & Demo Polish

### Module 8.1 — Backend Integration Tests

| Field | Detail |
|-------|--------|
| **Purpose** | Verify all services work together end-to-end |
| **Tech** | pytest (Python) + Jest (TypeScript) + httpx |

**Test cases to write:**

| Test | Expected |
|------|---------|
| POST /verify (text) | 200, credibility_score 0–100, sources > 0 |
| POST /verify (text) — second request | cached: true, cache_tier: redis |
| POST /verify (url) | 200, scraper agent in agent_verdicts |
| POST /verify (health domain) | scientific agent present |
| POST /auth/register + login + protected route | JWT flow works |
| POST /verify — rate limit exceeded | 429 with Retry-After |
| POST /verify — Bedrock times out | Graceful fallback, no 500 |

**Tasks:**
- [ ] `tests/test_verification.py` — pytest + httpx against running stack
- [ ] `tests/test_agents.py` — test each agent individually with mock claims
- [ ] `tests/test_cache.py` — validate 3-tier cache hit sequence
- [ ] `apps/api-gateway/src/__tests__/auth.test.ts` — Jest auth flow
- [ ] GitHub Actions CI (optional for prototype): run tests on push to main

---

### Module 8.2 — End-to-End Demo Test

**Test 5 claim archetypes (see IMPL-05 §7.2):**

| Claim | Expected Score | Expected Category |
|-------|---------------|-------------------|
| "COVID vaccines contain microchips" | ~8 | Verified False |
| "India launched Chandrayaan-3 in 2023" | ~91 | Verified True |
| "5G towers cause cancer" | ~30 | Verified False |
| "Vitamin C cures cancer" | ~25 | Likely False |
| "India's GDP grew 8.2% in 2024" | ~78 | Likely True |

**Tasks:**
- [ ] Run all 5 claims, verify category matches expected
- [ ] Re-run all 5 — verify all return `cached: true`
- [ ] Record response times — all < 6s (cache miss), all < 500ms (cache hit)

---

### Module 8.3 — Web Portal Polish

**Tasks:**
- [ ] Dark mode toggle (CSS variables swap)
- [ ] Responsive layout (mobile breakpoints)
- [ ] Error states: API down, rate limit exceeded, empty results
- [ ] Loading skeleton while verifying
- [ ] Copy result link button (share verification URL)
- [ ] "How it works" animated diagram on homepage

---

### Module 8.4 — Neptune Graph DB (Optional — Bonus)

| Field | Detail |
|-------|--------|
| **Purpose** | Graph connecting claims ↔ entities ↔ sources (as shown in Diagram 1) |
| **Tech** | AWS Neptune (Gremlin API) |
| **Priority** | Post-core — implement if time permits |

**Tasks:**
- [ ] Provision Neptune `db.t3.medium` (see IMPL-02 §5)
- [ ] Schema: Vertices = Claim, Entity, Source; Edges = mentions, cites, contradicts
- [ ] After each verification, write graph edges for claim entities + sources
- [ ] `GET /api/v1/claims/:id/related` — return related claims via graph traversal

---

### Module 8.5 — Deployment to AWS (Prototype)

| Field | Detail |
|-------|--------|
| **Purpose** | Get a public URL for the hackathon demo |
| **Sequence** | Follow IMPL-05 Option C |

**Steps:**
- [ ] Run `scripts/setup-vpc.sh` (VPC, subnets, security groups)
- [ ] Run `scripts/setup-managed.sh` (RDS, Redis, DynamoDB, S3, SQS)
- [ ] Run `scripts/setup-ssm.sh` (store all API keys)
- [ ] Build + push Docker images to ECR
- [ ] Create ECS cluster + 3 services (api-gateway, verification-engine, media-analysis)
- [ ] Configure ALB + CloudFront distribution
- [ ] Deploy web portal to S3 + invalidate CloudFront cache
- [ ] Smoke test all 5 demo claims against live URL

---

## Summary Table

| Phase | Modules | Days | Deliverable |
|-------|---------|------|-------------|
| 0 — Foundation | 0.1, 0.2 | Day 1 | Monorepo + shared types |
| 1 — Data Layer | 1.1–1.5 | Day 1–2 | PostgreSQL + Redis + DynamoDB + S3 + SQS |
| 2 — API Gateway | 2.1–2.4 | Day 2–3 | Working REST API with auth + cache |
| 3 — Verification Engine | 3.1–3.4 | Day 3–4 | FastAPI + Normalization + Bedrock + LangGraph |
| 4 — 6 Agents | 4.1–4.8 | Day 4–6 | All 6 agents + evidence aggregation + report gen |
| 5 — Media Analysis | 5.1–5.5 | Day 6–7 | Deepfake detection + AWS Media Services |
| 6 — Caching | 6.1–6.3 | Day 7–8 | 3-tier cache + trending |
| 7 — Frontend | 7.1–7.3 | Day 8–10 | Web portal + Extension + Mobile app |
| 8 — Polish & Deploy | 8.1–8.5 | Day 10–12 | End-to-end tests + AWS deploy + demo |

**Total modules: 26**  
**Total estimated time: 12 days (hackathon sprint)**
