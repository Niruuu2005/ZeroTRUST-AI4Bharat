# ZeroTRUST — AI-Powered Misinformation Detection for Bharat

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-FF9900?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-1C3C3C)](https://langchain-ai.github.io/langgraph/)

**A multi-agent, multi-modal fact-verification platform built for the Indian information ecosystem.**

[Overview](#overview) · [Architecture](#system-architecture) · [Agents](#multi-agent-pipeline) · [Services](#services) · [Getting Started](#getting-started) · [Configuration](#configuration) · [Deployment](#deployment)

</div>

---

## Overview

ZeroTRUST is a production-grade, open-source misinformation detection system that verifies text claims and media content (images, video, audio) using a coordinated pipeline of seven specialist AI agents backed by AWS Bedrock. It is purpose-built for the Indian context: supporting RSS feeds from major Indian newsrooms, academic sources in Hindi/English, and dedicated source-tier weighting for fact-checkers like AltNews, BoomLive, and AFP Bharat.

### What it does

| Input | What happens | Output |
|---|---|---|
| Text claim or URL | 7 agents search web, news, science, Reddit, and official fact-check databases in parallel | Credibility score (0–100), category, verdict, ranked sources |
| Image / Video / Audio (S3) | AWS Textract + Transcribe + Rekognition analyse content | Same structured `VerificationResult` with media evidence |
| Browser page content | Chrome extension submits highlighted text to the API | Inline trust badge rendered on any webpage |

### Core Design Principles

- **In-house first**: DuckDuckGo search, RSS feeds, and Reddit public APIs require zero third-party keys. The system works end-to-end with only AWS credentials.
- **India-first source tier**: Tier-1 sources explicitly include AltNews, BoomLive, The Wire, The Print, Scroll in, NDTV, and all major government/WHO/CDC domains.
- **No black box**: Every claim returns structured evidence per source, per agent, with stances and tier classifications — auditable by design.
- **Horizontal scalability**: Each service is independently Dockerised, stateless at the application layer, and designed for AWS ECS + ALB deployment.

---

## System Architecture

ZeroTRUST is a **polyglot microservices monorepo**. Services communicate over HTTP and share a PostgreSQL persistence layer and Redis cache.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Client Layer                                    │
│  ┌───────────────────┐   ┌─────────────────────────────────────────────┐   │
│  │  Chrome Extension  │   │           Next.js Web Portal (port 3001)    │   │
│  │  (popup.js)        │   │           apps/web-portal  (TypeScript)     │   │
│  └────────┬──────────┘   └───────────────────────┬─────────────────────┘   │
└───────────┼───────────────────────────────────────┼─────────────────────────┘
            │ HTTPS                                 │ HTTPS
            ▼                                       ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    API Gateway  (port 3000)                                │
│               apps/api-gateway — Node.js / Express / TypeScript           │
│                                                                           │
│  Routes:  /api/v1/verify  /api/v1/auth  /api/v1/history                  │
│           /api/v1/media   /api/v1/trending                                │
│                                                                           │
│  ┌──────────────────────────── VerificationService ─────────────────────┐ │
│  │  Cache Lookup                                                         │ │
│  │  ├─ Tier 1: Redis         (TTL: 1 h)   — sub-ms hot results          │ │
│  │  ├─ Tier 2: DynamoDB      (TTL: 24 h)  — warm cross-instance cache   │ │
│  │  └─ Tier 3: PostgreSQL    (TTL: 30 d)  — cold historical lookup      │ │
│  │                                                                       │ │
│  │  On cache miss → route to correct engine ───►                        │ │
│  │     text/url → Verification Engine (port 8000)                       │ │
│  │     image/video/audio → Media Analysis (port 8001)                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬────────────────────────────┬────────────────────┘
                           │                            │
              ┌────────────▼────────────┐  ┌───────────▼────────────────────┐
              │   Verification Engine   │  │      Media Analysis Service     │
              │     (port 8000)         │  │          (port 8001)            │
              │  apps/verification-     │  │  apps/media-analysis           │
              │  engine — Python/FastAPI│  │  Python / FastAPI               │
              │                         │  │                                 │
              │  LangGraph State Machine│  │  ┌──────────────────────────┐  │
              │  ┌─────────────────────┐│  │  │ AWS Textract  (OCR)      │  │
              │  │ normalize           ││  │  │ AWS Transcribe (speech)  │  │
              │  │ analyze_claim       ││  │  │ AWS Rekognition (labels/ │  │
              │  │ select_agents       ││  │  │   moderation / video)    │  │
              │  │ execute_agents ─────┼┼──┼──► Evidence Merge           │  │
              │  │ aggregate_evidence  ││  │  │ Credibility Score        │  │
              │  │ calculate_credib.   ││  │  └──────────────────────────┘  │
              │  │ generate_report     ││  │                                 │
              │  └─────────────────────┘│  └────────────────────────────────┘
              │                         │
              │  7 Specialist Agents    │        AWS Bedrock (Claude / Titan)
              │  (parallel execution)   │◄────────────────────────────────────
              └─────────────────────────┘
                            │
              ┌─────────────▼──────────────────────────┐
              │            Data Layer                   │
              │  PostgreSQL 15  (persistent store)       │
              │  Redis 7        (L1 cache, pub/sub)      │
              │  AWS DynamoDB   (L2 global cache)        │
              │  AWS S3         (media uploads)          │
              └────────────────────────────────────────-┘
```

### Repository Layout

```
ZeroTRUST-AI4Bharat/
├── apps/
│   ├── api-gateway/           # Node.js / Express gateway (TypeScript)
│   │   ├── src/
│   │   │   ├── routes/        # verify, auth, history, media, trending
│   │   │   ├── services/      # VerificationService, CacheService
│   │   │   ├── middleware/    # auth, rate-limit, error
│   │   │   ├── config/        # database (Prisma), redis
│   │   │   └── validators/    # Zod request schemas
│   │   └── prisma/            # Schema + migrations
│   │
│   ├── verification-engine/   # Python / FastAPI + LangGraph
│   │   └── src/
│   │       ├── agents/        # 7 specialist agents + manager
│   │       ├── integrations/  # bedrock, duckduckgo, rss_feeds, factcheck_api
│   │       ├── services/      # scorer, evidence aggregator, report generator
│   │       ├── models/        # Pydantic request/response models
│   │       ├── normalization/ # Text normalisation, language detection
│   │       └── routers/       # FastAPI route handlers
│   │
│   ├── media-analysis/        # Python / FastAPI — AWS media pipeline
│   │   └── src/
│   │       ├── aws_media.py   # Textract, Transcribe, Rekognition wrappers
│   │       ├── s3_utils.py    # S3 presigned URL helpers
│   │       └── evidence_merge.py  # Score computation from media evidence
│   │
│   ├── web-portal/            # Next.js 14 / React frontend
│   │   └── src/
│   │       ├── app/           # App Router pages
│   │       ├── components/    # Reusable UI components
│   │       └── lib/           # API client, auth helpers
│   │
│   ├── browser-extension/     # Chrome Manifest V3 extension
│   │   ├── manifest.json
│   │   ├── popup.html / popup.js / popup.css
│   │
│   └── lambda/
│       └── media-trigger/     # S3-event Lambda (trigger media analysis)
│
├── lambda-functions/verify/   # Standalone Lambda for serverless verify
├── scripts/                   # Model check, S3 scan utilities
├── aws-setup/                 # IAM, trust policies, CloudFormation helpers
├── docker-compose.yml         # Full local stack
├── .env.local.example         # Environment variable reference
└── package.json               # Monorepo workspace root
```

---

## Multi-Agent Pipeline

The **Verification Engine** implements a **LangGraph state machine** that orchestrates seven specialist agents to produce a structured, explainable verdict for every claim.

### Pipeline Execution Flow

```
Input Claim
    │
    ▼
┌─────────────┐
│  normalize  │  ← Text normalisation, language detection, URL/media flag
└──────┬──────┘
       ▼
┌──────────────┐
│ analyze_claim│  ← AWS Bedrock extracts: main_assertion, entities, domain, type
└──────┬───────┘
       ▼
┌──────────────┐
│ select_agents│  ← Domain-to-agent mapping (politics → news+social+research+factcheck)
└──────┬───────┘
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ execute_agents  (asyncio.gather — full parallel execution)           │
│                                                                      │
│  ┌─────────────┐ ┌──────────┐ ┌────────────┐ ┌────────────────────┐│
│  │  Research   │ │  News    │ │ Scientific │ │   Social Media     ││
│  │  Agent      │ │  Agent   │ │  Agent     │ │   Agent            ││
│  │ DuckDuckGo  │ │ RSS+DDG  │ │ PubMed +  │ │   Reddit (public   ││
│  │ + Wikipedia │ │  news    │ │   arXiv   │ │   JSON API)        ││
│  └─────────────┘ └──────────┘ └────────────┘ └────────────────────┘│
│  ┌─────────────┐ ┌──────────┐ ┌────────────────────────────────────┐│
│  │  Sentiment  │ │ Scraper  │ │         FactCheck Agent            ││
│  │  Agent      │ │  Agent   │ │  Google Fact Check API (Snopes,    ││
│  │ propaganda  │ │  URL     │ │  AltNews, BoomLive, PolitiFact,    ││
│  │  patterns   │ │  fetch   │ │  Reuters, BBC, AFP + 100 more)     ││
│  └─────────────┘ └──────────┘ └────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
       ▼
┌──────────────────┐
│ aggregate_evidence│  ← Deduplicate & rank sources across agents
└──────┬───────────┘
       ▼
┌─────────────────────┐
│ calculate_credibility│  ← Weighted formula (see Scoring section)
└──────┬──────────────┘
       ▼
┌───────────────┐
│ generate_report│  ← Recommendation, limitations, per-agent verdict map
└───────────────┘
       ▼
   VerificationResult (JSON)
```

### The Seven Agents

| # | Agent | Data Sources | Key Intel |
|---|---|---|---|
| 1 | **ResearchAgent** | DuckDuckGo Web Search, Wikipedia REST API | General web evidence; no API key required |
| 2 | **NewsAgent** | RSS feeds (BBC, Reuters, AP, NPR, The Hindu, Indian Express, NDTV, The Wire, …) + DuckDuckGo News | Timestamped news corpus; no API key required |
| 3 | **ScientificAgent** | PubMed E-utilities, arXiv Atom API | Peer-reviewed academic literature; free public APIs |
| 4 | **SocialMediaAgent** | Reddit public search JSON (`/search.json`) | Social sentiment & discussion; no API key required |
| 5 | **SentimentAgent** | Regex propaganda pattern detection + AWS Bedrock | Detects name-calling, loaded language, false urgency, bandwagon, ad hominem, appeal to fear |
| 6 | **ScraperAgent** | Direct HTTP fetch + BeautifulSoup | Analyses the content at a submitted URL directly |
| 7 | **FactCheckAgent** | Google Fact Check Explorer API | Aggregates verdicts from **Snopes, AltNews, BoomLive, PolitiFact, FactCheck.org, AFP, BBC Reality Check, Reuters Fact Check, and 100+ registered fact-checkers** |

> **Agent selection is domain-aware.** A `politics` claim runs news + social + research + sentiment + factcheck agents. A `health` or `science` claim automatically includes the scientific agent. A `URL` input activates the scraper agent. The manager always adds `sentiment` and `factcheck` to every pipeline run.

### Domain → Agent Routing

| Domain | Agents Activated |
|---|---|
| `politics` | news, social_media, research, sentiment, factcheck |
| `health` | scientific, news, research, factcheck, sentiment |
| `science` | scientific, research, factcheck, sentiment |
| `technology` | news, research, factcheck, sentiment |
| `climate` | scientific, news, research, factcheck, sentiment |
| `sports` | news, social_media, factcheck, sentiment |
| `entertainment` | news, social_media, factcheck, sentiment |
| `business` | news, research, factcheck, sentiment |
| `default` | research, news, social_media, factcheck, sentiment |

---

## Credibility Scoring

The **CredibilityScorer** implements a deterministic weighted formula. Every component is transparent and auditable.

### Standard Formula

```
Credibility Score = (Evidence Quality × 0.40)
                  + (Agent Consensus  × 0.30)
                  + (Source Reliability × 0.30)
```

| Component | Weight | Method |
|---|---|---|
| **Evidence Quality** | 40% | Sources weighted by tier and stance (supporting − contradicting). Tier weights: Tier-1 = 1.0, Tier-2 = 0.7, Tier-3 = 0.4, Tier-4 = 0.2 |
| **Agent Consensus** | 30% | % of agents whose dominant verdict matches the plurality verdict |
| **Source Reliability** | 30% | Average credibility score across all consulted sources |

### Official Fact-Check Anchor

When `FactCheckAgent` finds a match in the Google Fact Check Explorer database:

```
Blended Score = (Official Truth Score × 0.60) + (Standard Formula × 0.40)
```

This ensures that a professional human-reviewed verdict from organisations like Reuters or AltNews overrides purely inferred signals.

### Score → Category Mapping

| Score Range | Category |
|---|---|
| 85 – 100 | ✅ **Verified True** |
| 70 – 84 | 🟢 **Likely True** |
| 60 – 69 | 🟡 **Uncertain** |
| 40 – 59 | 🔴 **Likely False** |
| 0 – 39 | ❌ **Verified False** |

### Confidence Levels

| Level | Condition |
|---|---|
| `High` | Average agent confidence ≥ 0.8 **and** ≥ 30 sources consulted |
| `Medium` | Average agent confidence ≥ 0.6 **and** ≥ 15 sources consulted |
| `Low` | Everything else |

> A confidence penalty is applied when average agent confidence drops below 0.5 — up to a 50% penalty to prevent falsely confident low-signal verdicts.

---

## Source Tier System

All sources gathered by any agent are classified into four tiers that directly feed the scoring formula.

| Tier | Description | Example Sources |
|---|---|---|
| **Tier 1** | Official & dedicated fact-checkers, government health, wire services | BBC, Reuters, AP, NPR, PBS, AltNews, BoomLive, FactCheck.org, Snopes, PolitiFact, WHO, CDC, PubMed |
| **Tier 2** | Established mainstream press (national / international) | The Guardian, Washington Post, NYT, Bloomberg, NDTV, The Hindu, Indian Express, Hindustan Times, Times of India, The Print, The Wire, Scroll.in |
| **Tier 3** | Regional and mid-tier outlets | (configured at runtime) |
| **Tier 4** | User-generated, social media, unclassified | Reddit, blogs, unknown domains |

---

## Media Analysis Pipeline

The **Media Analysis Service** runs entirely on managed AWS AI services. It accepts an **S3 URL** (clients upload via pre-signed URL first) and returns the same `VerificationResult` shape as the text pipeline.

```
S3 URL  (image/video/audio)
         │
         ▼
┌────────────────────────────────────────────────────┐
│                 run_media_pipeline                  │
│                                                    │
│  image/* ──► AWS Textract     (OCR → text)          │
│           ──► AWS Rekognition (labels, moderation)  │
│                                                    │
│  audio/* ──► AWS Transcribe   (speech → text)       │
│                                                    │
│  video/* ──► AWS Rekognition  (label detection,     │
│              frame-by-frame moderation)             │
│                                                    │
└───────────────────────┬────────────────────────────┘
                        │ evidence dict
                        ▼
             compute_credibility_from_evidence()
                        │
                        ▼
             VerificationResult JSON
             (compatible with text pipeline cache)
```

---

## API Gateway

The API Gateway is the single public-facing entry point. It handles authentication, rate limiting, caching, and request routing.

**Base URL:** `http://localhost:3000` (dev) | `https://api.zerotrust.ai` (prod)

### Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/verify` | Optional JWT | Submit a claim for verification |
| `GET` | `/api/v1/history` | Required JWT | Paginated verification history |
| `GET` | `/api/v1/trending` | None | Top trending verified claims |
| `POST` | `/api/v1/auth/register` | None | User registration |
| `POST` | `/api/v1/auth/login` | None | Obtain JWT access + refresh token |
| `POST` | `/api/v1/auth/refresh` | None | Refresh access token |
| `POST` | `/api/v1/media/presign` | Optional JWT | Get S3 pre-signed upload URL |
| `GET` | `/health` | None | Gateway health probe |

### Three-Tier Cache Strategy

Every verification request hits cache layers before invoking a backend engine. This typically reduces p50 latency by **95%** for recently-seen claims.

```
Request
   │
   ├──► Redis GET   (Tier 1 — 1 h TTL)        → HIT: return immediately
   │
   ├──► DynamoDB GET (Tier 2 — 24 h TTL)       → HIT: promote to Redis, return
   │
   ├──► PostgreSQL GET (Tier 3 — 30 day window) → HIT: promote to Redis+Dynamo, return
   │
   └──► Cache MISS: invoke Verification Engine / Media Analysis
              │
              └──► Write-all: Redis + DynamoDB + PostgreSQL (non-blocking)
```

**Cache key construction:**  
Content is normalised (lowercased, stripped of HTML, punctuation removed, stop words filtered, tokens sorted) before being SHA-256 hashed. This ensures near-duplicate claims ("India won" vs. "India has won") share the same cache entry.

---

## Services

### API Gateway (`apps/api-gateway`)

- **Runtime:** Node.js 20, TypeScript 5
- **Framework:** Express 4 with `helmet`, `cors`, `compression`
- **ORM:** Prisma 5 → PostgreSQL 15
- **Auth:** JWT (access 15 min, refresh 7 days), `bcrypt` password hashing
- **Cache:** `ioredis` (Tier 1), `@aws-sdk/client-dynamodb` (Tier 2)
- **Validation:** Zod schemas on all request bodies

### Verification Engine (`apps/verification-engine`)

- **Runtime:** Python 3.11
- **Framework:** FastAPI + uvicorn
- **Orchestration:** LangGraph state graph (`StateGraph`, `TypedDict` state)
- **LLM:** AWS Bedrock (`anthropic.claude-3-haiku-20240307-v1:0` for speed, configurable per agent role)
- **HTTP client:** `httpx` (async)
- **Web parsing:** `BeautifulSoup4`
- **Feed parsing:** `feedparser`
- **Key integrations:** DuckDuckGo (duckduckgo-search), Wikipedia REST, PubMed E-utilities, arXiv Atom, Reddit JSON, Google Fact Check API

### Media Analysis Service (`apps/media-analysis`)

- **Runtime:** Python 3.11
- **Framework:** FastAPI + uvicorn
- **AWS Services:** `boto3` → Textract, Transcribe, Rekognition
- **Input:** S3 URLs only (ensures files are already in AWS for native service access)

### Web Portal (`apps/web-portal`)

- **Framework:** Next.js 14 (App Router, TypeScript)
- **Rendering:** SSR + client components
- **Auth:** Token-based via API calls to the gateway

### Browser Extension (`apps/browser-extension`)

- **Standard:** Chrome Manifest V3
- **Operation:** User highlights text → popup fetches `/api/v1/verify` → displays credibility badge inline
- No background service worker required for basic operation

---

## Getting Started

### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Docker Desktop | 4.x+ | Run the full stack locally |
| Docker Compose | 2.x+ | Service orchestration |
| Node.js | 20+ | API gateway / web portal development |
| Python | 3.11+ | Verification / media engine development |
| AWS Account | — | Bedrock LLM access (required for real verification) |

### 1. Clone & Configure

```bash
git clone https://github.com/Niruuu2005/ZeroTRUST-AI4Bharat.git
cd ZeroTRUST-AI4Bharat
cp .env.local.example .env.local
```

Open `.env.local` and fill in the minimum required values:

```env
# Required — database & cache
DATABASE_URL=postgresql://zerotrust:devpassword@localhost:5432/zerotrust_dev
REDIS_URL=redis://localhost:6379
JWT_SECRET=<generate with: openssl rand -hex 32>

# Required — AWS Bedrock (for LLM-powered verification)
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_DEFAULT_REGION=us-east-1
```

> All other keys (News API, GNews, Google CSE, Twitter, Reddit, PubMed) are **optional**. The system runs fully in-house without them.

### 2. Start the Full Stack

```bash
docker compose up --build
```

This starts five services:

| Container | Port | Service |
|---|---|---|
| `zt-postgres` | 5432 | PostgreSQL 15 |
| `zt-redis` | 6379 | Redis 7 |
| `zt-api` | 3000 | API Gateway |
| `zt-verification` | 8000 | Verification Engine |
| `zt-media` | 8001 | Media Analysis |
| `zt-web` | 3001 | Web Portal |

### 3. Verify Services are Healthy

```bash
curl http://localhost:3000/health
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### 4. Submit Your First Verification

```bash
curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"content": "5G towers cause COVID-19", "type": "text", "source": "twitter"}'
```

### 5. Install the Browser Extension

1. Open Chrome → `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select `apps/browser-extension/`
4. Point the extension to `http://localhost:3000` (configurable in `popup.js`)

---

## Configuration

### Environment Variables

#### API Gateway

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `REDIS_URL` | ✅ | — | Redis connection string |
| `JWT_SECRET` | ✅ | — | JWT signing secret (min 32 chars) |
| `JWT_ACCESS_EXPIRY` | — | `15m` | Access token lifetime |
| `JWT_REFRESH_EXPIRY` | — | `7d` | Refresh token lifetime |
| `VERIFICATION_ENGINE_URL` | — | `http://localhost:8000` | Verification Engine endpoint |
| `MEDIA_ENGINE_URL` | — | `http://localhost:8001` | Media Analysis endpoint |
| `S3_MEDIA_BUCKET` | — | — | S3 bucket for media uploads |
| `AWS_REGION` | — | `us-east-1` | AWS region |
| `RATE_LIMIT_PUBLIC` | — | `20` | Requests/minute for unauthenticated users |
| `CW_LOG_GROUP` | — | — | CloudWatch log group (optional) |

#### Verification Engine

| Variable | Required | Default | Description |
|---|---|---|---|
| `BEDROCK_REGION` | ✅ | `us-east-1` | Bedrock invocation region |
| `MAX_AGENT_TIMEOUT` | — | `10` | Per-agent timeout (seconds) |
| `MAX_SOURCES_PER_AGENT` | — | `20` | Max sources collected per agent |
| `NEWS_API_KEY` | — | — | NewsAPI.org key (optional) |
| `GNEWS_API_KEY` | — | — | GNews key (optional) |
| `GOOGLE_SEARCH_KEY` | — | — | Google Custom Search key (optional) |
| `GOOGLE_SEARCH_ENGINE_ID` | — | — | Google CSE ID (optional) |
| `TWITTER_BEARER_TOKEN` | — | — | Twitter API v2 Bearer token (optional) |
| `PUBMED_API_KEY` | — | — | PubMed API key for higher rate limits (optional) |

---

## Deployment

### AWS Architecture

For production, ZeroTRUST targets a standard AWS three-tier deployment:

```
Internet
    │
    ▼
Route 53 (DNS)
    │
    ▼
CloudFront CDN (static assets + API cache headers)
    │
    ▼
Application Load Balancer
    ├──► ECS Fargate — api-gateway   (auto-scaling)
    ├──► ECS Fargate — verification-engine
    ├──► ECS Fargate — media-analysis
    └──► ECS Fargate — web-portal
         │
         ├── RDS PostgreSQL (Multi-AZ)
         ├── ElastiCache Redis (cluster mode)
         ├── DynamoDB (on-demand, global tables optional)
         ├── S3 (media uploads, model artefacts)
         └── Bedrock (cross-regional inference)
```

### IAM Permissions

The verification engine and media analysis services require:

```json
{
  "bedrock:InvokeModel",
  "s3:GetObject",
  "s3:PutObject",
  "textract:DetectDocumentText",
  "transcribe:StartTranscriptionJob",
  "transcribe:GetTranscriptionJob",
  "rekognition:DetectLabels",
  "rekognition:DetectModerationLabels",
  "rekognition:StartLabelDetection",
  "rekognition:GetLabelDetection",
  "dynamodb:GetItem",
  "dynamodb:PutItem",
  "logs:CreateLogGroup",
  "logs:PutLogEvents"
}
```

Reference IAM trust and permission policies are in `aws-setup/` and `ec2-trust-policy.json` / `lambda-trust-policy.json`.

### EC2 Bootstrap

`ec2-userdata.sh` automates the full stack installation on a fresh Ubuntu EC2 instance — installs Docker, Docker Compose, pulls the repo, applies environment variables, and starts all services.

---

## Data Model

The primary `Verification` table (Prisma / PostgreSQL) stores every computed result:

```
Verification {
  id              String   (UUID)
  claimHash       String   (SHA-256, 32 chars — cache key)
  claimText       String
  claimType       String   (text | image | video | audio | url)
  credibilityScore Int     (0–100)
  category        String   (Verified True | Likely True | Uncertain | Likely False | Verified False)
  confidence      String   (High | Medium | Low)
  sourcesConsulted Int
  agentConsensus  String
  evidenceSummary Json
  sources         Json[]
  agentVerdicts   Json
  limitations     String[]
  recommendation  String
  processingTime  Float    (seconds)
  cached          Boolean
  sourcePlatform  String
  userId          String?  (null for anonymous)
  createdAt       DateTime
}
```

---

## Development

### Running Services Individually

**API Gateway (development hot-reload)**
```bash
cd apps/api-gateway
npm install
npx prisma generate
npx prisma migrate dev
npm run dev
```

**Verification Engine**
```bash
cd apps/verification-engine
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

**Media Analysis**
```bash
cd apps/media-analysis
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8001
```

**Web Portal**
```bash
cd apps/web-portal
npm install
npm run dev
```

### System Diagnostics

```bash
python diagnose_system.py
```

Checks all services, AWS credentials, Bedrock model access, database connectivity, and Redis availability. Useful before first run or after configuration changes.

### Model Availability Check

```bash
python scripts/quick-model-check.py
```

Lists available Claude / Titan models in your configured Bedrock region and validates that the configured model ID is accessible.

---

## Propagation Timing

| Cache Tier | Write | Invalidation |
|---|---|---|
| Redis (Tier 1) | Synchronous write after each verification | 1-hour TTL; evicts by LRU when at 256 MB limit |
| DynamoDB (Tier 2) | Non-blocking write via `Promise.allSettled` | 24-hour TTL via DynamoDB TTL attribute |
| PostgreSQL (Tier 3) | Non-blocking via `Promise.allSettled` | Queries filter to last 30 days via `createdAt` |

Results promoted from L2/L3 are immediately written back to L1 (Redis) to speed up subsequent lookups.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run the diagnostic script: `python diagnose_system.py`
5. Open a pull request with a clear description of what the change does

Please keep agent implementations idempotent and ensure any new data source is assigned an appropriate source tier classification.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgements

- **LangGraph** — graph-based multi-agent orchestration
- **AWS Bedrock** — serverless LLM inference (Claude family)
- **Google Fact Check Tools API** — official professional fact-checker database
- **AltNews & BoomLive** — India's leading independent fact-checking organisations, whose work informs the Tier-1 source classification
- **DuckDuckGo** — privacy-first search with a public scraping interface
- All PubMed, arXiv, and Wikipedia contributors whose open data powers the Scientific and Research agents

---

<div align="center">

Built with ❤️ for the Indian information ecosystem · **ZeroTRUST-AI4Bharat**

</div>
