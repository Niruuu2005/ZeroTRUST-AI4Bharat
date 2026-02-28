# ZeroTRUST — Architecture Compliance & Readiness

**Reference:** `Docs/ZeroTRUST_Architecture_Diagrams.html`  
**Purpose:** Verify the codebase follows the documented architecture and whether it will work as expected.  
**Last updated:** February 28, 2026

---

## Summary

| Diagram | Architecture (HTML) | Codebase alignment | Will it work? |
|--------|----------------------|--------------------|----------------|
| **1 – System** | Clients → Edge → API Gateway → Compute → Data → External → Observability | Partial (see §1) | ✅ For text/URL flow |
| **2 – Multi-Agent** | Normalization → Manager → 6 agents → Credibility → Report | ✅ Aligned | ✅ Yes |
| **3 – Verification sequence** | Request → Cache check → VE → Bedrock → Agents → Store | ✅ Aligned | ✅ Yes |
| **4 – Media flow** | S3 → Lambda → AWS media + Forensic → Merge | ✅ Implemented (Textract, Transcribe, Rekognition; Lambda in repo) | ✅ Yes |
| **5 – AWS VPC** | Infra only (deploy target) | N/A in repo | ⚠️ When deployed per IMPL-02 |
| **6 – Caching** | Redis → DynamoDB → CloudFront → Full verify | ⚠️ Tier 3 = PG not CloudFront | ✅ Yes |

**Overall:** The **text/URL verification path** matches the architecture and will work as expected. **Media pipeline** and **edge/infra** (CloudFront, AWS API Gateway, Lambda, Neptune, Vector DB) are either missing or simplified in the prototype.

---

## 1. Diagram 1 – Full System Architecture

### 1.1 Intended (from HTML)

- **Client:** Web Portal (React), Browser Extension, Mobile App, Public API  
- **Edge:** CloudFront CDN, AWS WAF, Route 53  
- **API:** AWS API Gateway (REST, Auth, Rate-Limit, Routing)  
- **Compute:** API Service (Node/Express), Verification Engine (Python/FastAPI, LangGraph), Media Analysis (TF/PyTorch), Lambda  
- **AI:** AWS Bedrock (Claude, Llama, Mistral)  
- **Data:** Redis, DynamoDB, S3, Neptune, PostgreSQL, Vector DB  
- **AWS Media:** Textract, Transcribe, Rekognition  
- **External:** Search (Google·Bing), News, Fact-Check, Scientific, Social  
- **Observability:** CloudWatch  

### 1.2 Codebase reality

| Component | In diagram | In codebase | Match? |
|-----------|------------|-------------|--------|
| Web Portal | ✅ React | ✅ `apps/web-portal` (React + Vite) | ✅ |
| Browser Extension | ✅ | ✅ `apps/browser-extension` (Chrome MV3, verify text/URL) | ✅ |
| Mobile App | ✅ | ❌ No `mobile-app` app | ❌ |
| Public API | ✅ | ✅ Express exposes REST (`/api/v1/verify`, etc.) | ✅ |
| CloudFront / WAF / Route 53 | ✅ | ❌ Not in repo (deploy/infra) | ⚠️ |
| **API layer** | AWS API Gateway | **Express** (`apps/api-gateway`) as BFF/API | ⚠️ Different product, same role |
| API Service (Node) | ✅ | ✅ Express: JWT, **Zod validation**, cache-check, routes | ✅ |
| Verification Engine | ✅ Python/LangGraph | ✅ FastAPI + LangGraph in `apps/verification-engine` | ✅ |
| Media Analysis | ✅ | ✅ Full pipeline: Textract, Transcribe, Rekognition; `/analyze` with S3 URL | ✅ |
| Lambda | ✅ | ✅ `apps/lambda/media-trigger` (S3 Put → media-analysis) | ⚠️ Deploy separately |
| Bedrock | ✅ | ✅ `integrations/bedrock.py`, used by manager + agents | ✅ |
| Redis | ✅ | ✅ `CacheService` + `REDIS_URL` (Docker/ElastiCache) | ✅ |
| DynamoDB | ✅ | ✅ Tier 2 cache in `CacheService` (optional) | ✅ |
| S3 | ✅ | ✅ Presign: `POST /api/v1/media/presign` (when `S3_MEDIA_BUCKET` set); no server-side upload | ⚠️ |
| Neptune | ✅ | ❌ Not used | ❌ |
| PostgreSQL | ✅ | ✅ Prisma in api-gateway, schema + migrations | ✅ |
| Vector DB | ✅ | ❌ Not used | ❌ |
| Textract / Transcribe / Rekognition | ✅ | ✅ Used in `apps/media-analysis` (image OCR, audio transcript, video labels) | ✅ |
| External sources | ✅ | ✅ Via agents: DuckDuckGo, RSS, Reddit, PubMed, arXiv, scraper (in-house; diagram lists Google·Bing, etc.) | ✅ Different mix, same idea |
| CloudWatch | ✅ | ✅ Optional: set `CW_LOG_GROUP` for Winston → CloudWatch Logs | ⚠️ |

### 1.3 Verdict (Diagram 1)

- **Core path (text/URL):** Client → API Service (Express) → Redis/DynamoDB/PostgreSQL → Verification Engine → Bedrock + 6 agents → external sources is implemented and consistent with the diagram. Express acts as the “API Gateway” in the prototype; AWS API Gateway would sit in front in production.
- **Implemented in code:** Request validation (Zod on verify + auth), S3 presign (`POST /api/v1/media/presign`), trending (`GET /api/v1/trending`), optional CloudWatch Logs when `CW_LOG_GROUP` is set.
- **Gaps:** Mobile app, Neptune, Vector DB, edge (CloudFront/WAF). Lambda and media pipeline are implemented; extension is implemented.

---

## 2. Diagram 2 – Multi-Agent Engine (6 Parallel Agents)

### 2.1 Intended (from HTML)

- **Input:** User claim (text/URL/image/video/audio)  
- **Normalization:** Text Normalization, Metadata Extraction, Language Detection  
- **Manager:** AWS Bedrock (Claude 3.5) — Analyze claim, Select agents, Aggregate results, Generate verdict  
- **6 agents in parallel:** Research, News, Scientific, Social Media, Sentiment, Web Scraper  
- **Sources:** Google·Bing, Snopes·PolitiFact·etc., PubMed·arXiv·WHO·CDC, Twitter·Reddit, Live/archived web, AP·Reuters·BBC  
- **Engine:** Credibility Engine (weighted evidence, tiers, confidence) → Report Formatter → Trending → Output (score 0–100, verdict, evidence, citations, limitations)  

### 2.2 Codebase reality

| Element | In diagram | In codebase | Location |
|---------|------------|-------------|----------|
| Normalization | Text, Metadata, Language | ✅ | `normalization/`: `TextNormalizer`, `MetadataExtractor`, `LanguageDetector`; `NormalizationLayer.process()` |
| Manager (Bedrock) | Analyze, Select, Aggregate, Verdict | ✅ | `agents/manager.py`: LangGraph with nodes normalize → analyze_claim → select_agents → execute_agents → aggregate_evidence → calculate_credibility → generate_report |
| Research Agent | Google Scholar, Wikipedia, Academic | ✅ | DuckDuckGo web + Wikipedia (`integrations/duckduckgo_search`, `_wikipedia_search`) |
| News Agent | NewsAPI, AP, Reuters, BBC, Fact-Checkers | ✅ | RSS feeds + DuckDuckGo news (`integrations/rss_feeds`, `search_news`) |
| Scientific Agent | PubMed, CDC, WHO, arXiv, CrossRef | ✅ | PubMed E-utilities + arXiv (`_pubmed`, `_arxiv`) |
| Social Media Agent | Twitter, Reddit, CrowdTangle | ✅ | Reddit only (`_reddit`); no Twitter in-house |
| Sentiment Agent | Bias, Propaganda, Manipulation | ✅ | Regex patterns + Bedrock (`PROPAGANDA_PATTERNS`, LLM) |
| Web Scraper Agent | Content extraction, Context, Wayback | ✅ | httpx + BeautifulSoup (`_fetch`); no Wayback |
| Credibility Engine | Weighted evidence, tiers, confidence | ✅ | `services/scorer.py` (`CredibilityScorer`) |
| Report Formatter | Evidence trails, citations, limitations | ✅ | `services/report.py` (`ReportGenerator`) |
| Trending Fake News | Aggregator / Analytics | ✅ | `GET /api/v1/trending` (top claims by verification count, optional `limit`, `days`) |
| Output | Score 0–100, verdict, evidence, citations, limitations | ✅ | `VerificationResult` in `models/verification.py`, returned by manager |

### 2.3 Verdict (Diagram 2)

- **Fully aligned:** Normalization → Manager (Bedrock) → 6 agents in parallel → Credibility Engine → Report Formatter → output. Graph structure and data flow match the diagram.
- **Source mix:** Diagram names Google·Bing, NewsAPI, etc.; code uses in-house (DuckDuckGo, RSS, Reddit, PubMed, arXiv, scraper). Architecture is the same; only data sources differ.
- **Trending:** Implemented via `GET /api/v1/trending` (top claims by verification count over configurable `days`, optional `limit`).

---

## 3. Diagram 3 – End-to-End Verification Sequence

### 3.1 Intended (from HTML)

1. User → CloudFront → (WAF) → API Gateway → API Service  
2. API Service → Redis (Tier 1)  
3. **Cache HIT:** return cached result (<500ms)  
4. **Cache MISS:** API → Verification Engine → Bedrock (analyze) → dispatch 6 agents → external sources → Credibility Engine → API → store Redis + PostgreSQL + DynamoDB → response (<5s)  

### 3.2 Codebase reality

- **Request path:** `verify.routes.ts` → `VerificationService.verify()` → `buildCacheKey()` → `getRedis(key)` (Tier 1). **Matches.**
- **Cache HIT:** `if (t1) return { ...t1, cached: true, cache_tier: 'redis' }`. **Matches.**
- **Cache MISS:** Tier 2 DynamoDB → Tier 3 PostgreSQL (code uses PG as third tier; diagram 3 does not spell out Tier 3). Then `callVerificationEngine()` → HTTP POST to Verification Engine. **Matches.**
- **Verification Engine:** `routers/verify.py` → `ManagerAgent.verify()` → LangGraph (normalize → analyze_claim → select_agents → execute_agents → aggregate_evidence → calculate_credibility → generate_report) → Bedrock + 6 agents. **Matches.**
- **After full verify:** `setRedis`, `setDynamo`, `prisma.verification.create()`. **Matches.**

### 3.3 Verdict (Diagram 3)

- Sequence and responsibilities match the diagram. Text/URL verification will behave as described (cache hit fast, cache miss full pipeline with storage).

---

## 4. Diagram 4 – Media Verification Data Flow

### 4.1 Intended (from HTML)

- Image/Video/Audio → S3 upload (pre-signed) → Lambda (S3 event) → Textract, Transcribe, Rekognition + Forensic (Deepfake, Reverse Image, Metadata, FFT, A/V Sync) → Evidence Merger → Credibility → S3 + final report.  

### 4.2 Codebase reality

- **Media Analysis:** `apps/media-analysis/src/main.py` exposes `/health` and `POST /analyze`. `/analyze` accepts body `{ url: S3 URL, contentType }` and runs the full pipeline: Textract (image OCR), Rekognition (image labels/moderation, video labels with async poll), Transcribe (audio, async poll). Evidence is merged in `evidence_merge.py`; credibility score and VerificationResult-compatible response returned. Forensic (deepfake, reverse image) is a placeholder.
- **API Gateway:** `POST /api/v1/media/presign` returns a presigned S3 PUT URL when `S3_MEDIA_BUCKET` is set. When `type` is image/video/audio, `POST /api/v1/verify` routes to media-analysis (S3 URL or key), caches and stores the result.
- **Lambda:** `apps/lambda/media-trigger/handler.py` — on S3 Put, POSTs to Media Analysis `/analyze` with the object URL. Deploy separately with `MEDIA_ANALYSIS_URL`.

### 4.3 Verdict (Diagram 4)

- **Implemented.** Media-analysis runs Textract (image), Transcribe (audio, async poll), Rekognition (image + video async poll); evidence merged into credibility score. API Gateway routes `type=image|video|audio` to media-analysis; Lambda handler in repo for S3 trigger. Forensic (deepfake, reverse image) is placeholder.

---

## 5. Diagram 5 – AWS Infrastructure & VPC

- Purely deployment/network (VPC, subnets, ALB, ECS, RDS, ElastiCache, managed services).  
- Not encoded in application code; IMPL-02 describes how to deploy.  
- **Verdict:** N/A for “does the code follow the architecture”; when you deploy per IMPL-02, infra can match the diagram.

---

## 6. Diagram 6 – 3-Tier Caching Strategy

### 6.1 Intended (from HTML)

- Request → **Tier 1 Redis** (1 hr, <5ms) → HIT return / MISS → **Tier 2 DynamoDB** (24 hr, <20ms) → HIT (promote to L1) / MISS → **Tier 3 CloudFront** (30 days, edge) → HIT / MISS → Full verification → write Redis + DynamoDB + CloudFront + PostgreSQL.  

### 6.2 Codebase reality

- **Tier 1 (Redis):** Implemented. TTL 1 hour (3600s), `getRedis` / `setRedis`. **Matches.**  
- **Tier 2 (DynamoDB):** Implemented. `getDynamo` / `setDynamo`, on HIT we `setRedis` (L2→L1 promotion). **Matches.**  
- **Tier 3:** Diagram = CloudFront edge cache. Code = **PostgreSQL** (“last 30 days” `getPgCache`). So Tier 3 is “warm DB cache” in code, not edge CDN. Same idea (third layer before full verify), different technology.  
- **Full verify:** Then write Redis + DynamoDB + PostgreSQL. No CloudFront write in app. **Matches except Tier 3 = PG not CloudFront.**  

### 6.3 Verdict (Diagram 6)

- Caching logic and promotion match; Tier 3 is implemented as PostgreSQL instead of CloudFront. Behavior is correct for the prototype; CloudFront can be added at the edge in production.

---

## 7. Will It Work as Expected?

### 7.1 What will work

- **Text and URL verification:** End-to-end flow matches Diagrams 2 and 3: request → API Service → 3-tier cache (Redis → DynamoDB → PG) → on miss, Verification Engine → Normalization → Manager (Bedrock) → 6 agents in parallel (DuckDuckGo, RSS, Reddit, PubMed, arXiv, sentiment, scraper) → Credibility + Report → store and return.  
- **Caching:** Cache hits and L2→L1 promotion behave as in Diagram 6 (with Tier 3 as PG).  
- **Output:** Score 0–100, category, evidence, sources, limitations, recommendation as in the architecture.  

### 7.2 What will not work (or is simplified)

- **Media (image/video/audio):** Full pipeline implemented (Textract, Transcribe, Rekognition); forensic (deepfake, reverse image) is placeholder. Presign + media-analysis + optional Lambda S3 trigger.
- **Browser extension:** Implemented; mobile app not in repo.
- **Edge (CloudFront, WAF, Route 53):** Not in repo; local/dev uses Express only.  
- **AWS API Gateway:** Replaced by Express in code; diagram’s “API Gateway” role is fulfilled by Express.  
- **Lambda, Neptune, Vector DB, full media pipeline:** Not in app; no impact on text/URL verification. S3 and CloudWatch are used (presign endpoint; optional CloudWatch Logs when `CW_LOG_GROUP` set).  

### 7.3 Is the codebase “proper and as needed”?

- **For the architecture described in the diagrams:**  
  - **Yes** for the **multi-agent verification path** (Diagram 2), **verification sequence** (Diagram 3), and **caching strategy** (Diagram 6 with Tier 3 = PG).  
  - **Partially** for **system architecture** (Diagram 1): core compute, data (Redis, DynamoDB, PG), Bedrock, Zod validation, presign, trending, optional CloudWatch, media pipeline, browser extension, Lambda handler (in repo) are in place; mobile app, edge (CloudFront/WAF), Neptune, Vector DB are out of scope.  
  - **Yes** for **media flow** (Diagram 4), with forensic as placeholder.  

- **For “will it work as expected”:**  
  - **Text/URL:** Yes, it will work as expected for verification and caching.  
  - **Media:** Yes; image/audio/video via media-analysis (S3 URL). Forensic steps placeholder.  

---

## 8. Recommendations

1. **Implemented (Phase 1):** Zod validation on verify/auth bodies; S3 presign (`POST /api/v1/media/presign`), Trending (`GET /api/v1/trending`), optional CloudWatch Logs when `CW_LOG_GROUP` is set. Details: `Docs/IMPLEMENTATION_PLAN.md`.  
2. **When implementing full media:** Follow Diagram 4: client uploads via presigned URL, Lambda or ECS pipeline, Textract/Transcribe/Rekognition + forensic, evidence merger, then same credibility/report path.  
3. **When deploying to AWS:** Use IMPL-02 to align with Diagram 5; put CloudFront (and optionally AWS API Gateway) in front of the existing Express service so the full Diagram 1 flow is satisfied in production.

---

*This document is the single place to check “does the code follow the architecture and will it work?” against `ZeroTRUST_Architecture_Diagrams.html`.*
