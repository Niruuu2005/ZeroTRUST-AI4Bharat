# ZeroTRUST — Prototype Implementation Guide
## IMPL-01: System Overview, Architecture & Design Reference

**Project:** ZeroTRUST — AI-Powered Misinformation Detection  
**Track:** AWS AI for Bharat Hackathon 2026  
**Team Leader:** Pratik Jagdale | **Team:** ZeroTrust  
**Scope:** 🚧 PROTOTYPE — not production-hardened  
**Doc Version:** 4.0 (Diagram-Aligned) | **Date:** February 27, 2026

> **Document Series**
> | Doc | Title |
> |-----|-------|
> | **IMPL-01** | Master Overview, Architecture Reference ← *this file* |
> | **IMPL-02** | Infrastructure Setup (Local + Minimal AWS) |
> | **IMPL-03** | Backend Services — API Gateway, Verification Engine, Agents |
> | **IMPL-04** | Frontend — Web Portal, Browser Extension, Mobile App |
> | **IMPL-05** | Running the Prototype End-to-End |

> [!IMPORTANT]
> These docs target a **hackathon prototype** — demonstrable, functional, and fast to spin up. Production concerns (multi-account AWS, GuardDuty, SCP, provisioned Bedrock throughput, paid EKS etc.) are explicitly excluded unless noted.

---

## 1. What ZeroTRUST Does

ZeroTRUST takes any claim — a WhatsApp forward, a news headline, an image, a video — and returns a **Credibility Score (0–100)** within 5 seconds by running 6 AI agents in parallel against 30–60 real-world sources.

| Input type | Examples |
|-----------|---------|
| Text | "Vaccines cause autism", news headline |
| URL | https://whatsapp-forward.example.com/article |
| Image | Suspected deepfake photo, screenshot |
| Video | Viral clip |
| Audio | Speech deepfake |

---

## 2. Full System Architecture (Diagram 1)

> Source: `ZeroTRUST_Architecture_Diagrams.html` — Diagram 1

```
┌────────────────────────── CLIENT LAYER ──────────────────────────┐
│  🌐 Web Portal    🧩 Browser Extension    📱 Mobile    👩‍💻 API    │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ HTTPS
┌────────────────────── EDGE LAYER ────────────────────────────────┐
│  ☁️ CloudFront CDN + WAF       🌐 Route 53 DNS Health-check      │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────── API LAYER ─────────────────────────────────┐
│  🔀 AWS API Gateway (RESTful, Auth, Rate-Limit, Routing)         │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────── COMPUTE LAYER (ECS Fargate) ───────────────┐
│  ⚙️ API Service (Node.js)   🤖 Verification Engine (Python)      │
│  🎬 Media Analysis (TF/PyTorch GPU)   ⚡ AWS Lambda              │
└──────┬────────────────┬────────────────────────────┬─────────────┘
       │                │                            │
┌──────▼──────┐  ┌──────▼──────────────┐   ┌────────▼────────────┐
│ 🧠 Bedrock  │  │  💾 DATA LAYER      │   │ 🔬 AWS MEDIA SVCS   │
│ Claude 3.5  │  │  ⚡ Redis (Tier-1)  │   │ Textract / Transcribe│
│ Llama/Mistral│  │  📦 DynamoDB(Tier-2)│   │ Rekognition         │
│ Embeddings  │  │  ☁️ CloudFront(Tier-3)│  └─────────────────────┘
└─────────────┘  │  🐘 PostgreSQL(DB)  │
                 │  🕸️ Neptune (Graph) │
                 │  🔢 Vector DB       │
                 │  🪣 S3             │
                 └─────────────────────┘
                          │
                 ┌────────▼────────────┐
                 │ 🌍 EXTERNAL SOURCES │
                 │ Google · Bing       │
                 │ AP · Reuters · BBC  │
                 │ Snopes · PolitiFact │
                 │ PubMed · WHO · arXiv│
                 │ Twitter/X · Reddit  │
                 └─────────────────────┘
                          │
                 ┌────────▼────────────┐
                 │ 📊 OBSERVABILITY    │
                 │ AWS CloudWatch      │
                 └─────────────────────┘
```

---

## 3. Multi-Agent Engine (Diagram 2)

> Source: `ZeroTRUST_Architecture_Diagrams.html` — Diagram 2

```
📥 User Claim Input (Text · URL · Image · Video · Audio)
        │
        ▼
┌────────────────────────────────────────────┐
│  NORMALIZATION LAYER                       │
│  🔤 Text Normalization                     │
│  🏷️ Metadata Extraction                   │
│  🌐 Language Detection                    │
└────────────────────────┬───────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────┐
│  🧠 MANAGER AGENT (AWS Bedrock — Claude 3.5)│
│  ① Analyze Claim                           │
│  ② Select Agents (domain-based)            │
│  ③ Aggregate Results                       │
│  ④ Generate Verdict                        │
└────────┬────────┬────────┬────────┬────────┘
         │        │        │        │
   ──────6 SPECIALIST AGENTS IN PARALLEL──────
    🔍 Research  📰 News  🔬 Scientific
    📣 Social    😤 Sentiment  🕷️ Scraper
         │        │        │        │
         └────────┴────────┴────────┘
                         │
                         ▼
              30–60 sources queried simultaneously
                         │
                         ▼
┌────────────────────────────────────────────┐
│  CREDIBILITY & REPORTING ENGINE            │
│  ⚖️ Weighted Evidence Aggregation          │
│  📋 Report Formatter + Source Citations    │
│  📊 Trending Fake News Tracker             │
└────────────────────────┬───────────────────┘
                         │
                         ▼
📤 Final Output: Score 0–100 · Verdict · Evidence · Citations · Limitations
```

### 3.1 Agent → Source Mapping

| Agent | Sources Queried |
|-------|----------------|
| 🔍 Research Agent | Google · Bing · Wikipedia · Academic DBs |
| 📰 News Agent | NewsAPI · AP · Reuters · BBC · CNN · Fact-Checkers |
| 🔬 Scientific Agent | PubMed · CDC · WHO · arXiv · CrossRef |
| 📣 Social Media Agent | Twitter/X · Reddit · Facebook CrowdTangle |
| 😤 Sentiment Agent | Google · Bing · Twitter/X (bias detection) |
| 🕷️ Scraper Agent | Live web pages · Wayback Machine |

---

## 4. Verification Sequence (Diagram 3)

> Source: `ZeroTRUST_Architecture_Diagrams.html` — Diagram 3

```
User → CloudFront → WAF → API Gateway → API Service
                                              │
                                    ┌─ Redis Cache check ─┐
                                    │                      │
                               ✅ HIT (~90%)         ❌ MISS
                             Return < 500ms          │
                                              Verification Engine
                                                    │
                                         Bedrock: Analyze (Claude 3.5)
                                                    │
                                    Dispatch 6 agents simultaneously
                                                    │
                                         Query 30–60 ext. sources
                                                    │
                                        Agent verdicts → Credibility Engine
                                                    │
                                       Score → API Service → Cache (TTL 1hr)
                                                    │
                                       Persist to PostgreSQL + DynamoDB
                                                    │
                                              User < 5 seconds
```

---

## 5. Media Verification Flow (Diagram 4)

> Source: `ZeroTRUST_Architecture_Diagrams.html` — Diagram 4

```
🖼️ Image / 🎬 Video / 🎙️ Audio
        │
        ▼ (Pre-signed URL)
   S3 Upload → Lambda Trigger
        │
   ┌────┴──────────────────┐
   │  AWS Media Intelligence │
   │  📄 Textract (OCR)     │
   │  🎙️ Transcribe (STT)   │
   │  👁️ Rekognition        │
   └────────────┬───────────┘
                │
   ┌────────────▼───────────────────────────┐
   │  Forensic Analysis Engine (ECS task)   │
   │  🔍 Deepfake: XceptionNet + EfficientNet│
   │  🔄 Reverse Image Search               │
   │  📋 Metadata Analysis (EXIF)           │
   │  〰️ Frequency Analysis (FFT)           │
   │  🔊 A/V Sync Check (video only)        │
   └────────────┬───────────────────────────┘
                │
   ┌────────────▼───────────┐
   │  Evidence Merger        │
   │  Unified Credibility ⚖️ │
   └────────────┬────────────┘
                │
   S3 Result Store + Final Report to User
```

---

## 6. 3-Tier Caching Strategy (Diagram 6)

> Source: `ZeroTRUST_Architecture_Diagrams.html` — Diagram 6

The cache uses **SHA-256 hash of the normalized claim** as the cache key.

```
Incoming Request (SHA-256 hash key)
        │
        ▼
 TIER 1 — ⚡ Redis (ElastiCache)
   TTL: 1 hour  |  Latency: <5ms  |  ~60% hit rate
        │ MISS
        ▼
 TIER 2 — 📦 DynamoDB
   TTL: 24 hours  |  Latency: <20ms  |  ~25% hit rate
   → On HIT: promote back to Redis (L2→L1)
        │ MISS
        ▼
 TIER 3 — ☁️ CloudFront Edge Cache
   TTL: 30 days (popular/trending claims)  |  Latency: <50ms  |  ~5%
   → On HIT: fill Redis + DynamoDB
        │ MISS (~10% of all requests)
        ▼
 🤖 Full Verification Pipeline (6 agents, 30–60 sources, ~3–5 sec)
        │
        ▼
 💾 Write to: Redis + DynamoDB + CloudFront + PostgreSQL (permanent)
```

> [!NOTE]
> **PostgreSQL is NOT a cache tier** — it is the permanent/archival store, written to after full verification regardless of cache state. CloudFront edge is Tier 3, not PostgreSQL.

---

## 7. API Design — Core Endpoints (Prototype Scope)

### 7.1 Endpoints Required for Prototype Demo

```
POST   /api/v1/verify           # Main verification (anonymous + authenticated)
GET    /api/v1/verify/:id        # Fetch result by ID
POST   /api/v1/auth/login        # JWT login
POST   /api/v1/auth/register     # Register user
GET    /api/v1/history           # User's verification history
GET    /health                   # Health check
```

> [!NOTE]
> Prototype can skip: bulk API, job polling, admin endpoints, Stripe, analytics. These are noted in IMPL-03 as "post-prototype."

### 7.2 Verification Request Schema

```typescript
interface VerifyRequest {
  content: string;         // min 10, max 10000 chars
  type: 'text' | 'url' | 'image' | 'video';
  source: 'web_portal' | 'extension' | 'mobile_app' | 'api';
}
```

### 7.3 Verification Response Schema

```typescript
interface VerifyResponse {
  id: string;                  // UUID
  credibility_score: number;   // 0–100
  category: CredibilityCategory;
  confidence: 'High' | 'Medium' | 'Low';
  claim_type: string;          // factual | statistical | quote | prediction | opinion | mixed
  sources_consulted: number;
  agent_consensus: string;     // e.g., "Strong consensus (87%)"
  evidence_summary: {
    supporting: number;
    contradicting: number;
    neutral: number;
  };
  sources: SourceReference[];
  agent_verdicts: Record<string, AgentVerdict>;
  limitations: string[];
  recommendation: string;
  processing_time: number;     // seconds
  cached: boolean;
  cache_tier?: 'redis' | 'dynamodb' | 'cloudfront';
  created_at: string;
}
```

---

## 8. Credibility Score Design

### 8.1 Weighted Formula

```
CredibilityScore = clamp(0, 100,
  floor(
    (
      EvidenceScore    × 0.40  +   // supporting vs contradicting ratio
      ConsensusScore   × 0.30  +   // agent agreement
      ReliabilityScore × 0.30      // source tier weighting
    ) × ConfidencePenalty × 100
  )
)

ConfidencePenalty = 0.7 + (avg_agent_confidence × 0.3)  → range: 0.7–1.0
```

**Agent Weights in ConsensusScore:**

| Agent | Weight | Why |
|-------|--------|-----|
| News Agent | 0.25 | Fact-checkers + Tier-1 outlets |
| Scientific Agent | 0.25 | Peer-reviewed sources |
| Research Agent | 0.20 | Broad web consensus |
| Social Media Agent | 0.10 | Context signal, not authority |
| Sentiment Agent | 0.10 | Manipulation modifier |
| Scraper Agent | 0.10 | Site-level credibility |

### 8.2 Score → Category → UI Color

| Score | Category | Color | Hex |
|-------|----------|-------|-----|
| 85–100 | Verified True | Dark Green | `#16a34a` |
| 70–84 | Likely True | Light Green | `#22c55e` |
| 55–69 | Mixed Evidence | Yellow | `#eab308` |
| 40–54 | Likely False | Orange | `#f97316` |
| 0–39 | Verified False | Red | `#dc2626` |
| N/A | Insufficient Evidence | Gray | `#6b7280` |

---

## 9. Technology Stack (Prototype)

### 9.1 Backend

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| API Gateway | Node.js + Express | 20 LTS / 4.18 | JWT auth, rate-limit, cache-check |
| Verification Engine | Python + FastAPI | 3.11 / 0.110 | LangGraph agent system |
| Agent Orchestration | LangGraph | 0.0.60 | State-machine agents |
| LLM integration | LangChain | 0.1.15 | Prompt templates, tools |
| Task queue | Celery + Redis | 5.3.6 | Async/bulk jobs |
| ORM | Prisma | 5.10 | TypeScript-native DB access |
| Validation | Zod | — | Input schemas |

### 9.2 AI/ML

| Model | Purpose | Source |
|-------|---------|--------|
| Claude 3.5 Sonnet | Manager agent, claim analysis, report gen | AWS Bedrock |
| Claude 3.5 Haiku | Sentiment, fast classification | AWS Bedrock |
| Mistral Large 2407 | Research summarization | AWS Bedrock |
| Amazon Titan Embed G1 | Semantic search (384-dim) | AWS Bedrock |
| XceptionNet + EfficientNet-B4 | Image deepfake detection | Custom TF |
| 3D-CNN + Bi-LSTM | Video deepfake | Custom PyTorch |
| RoBERTa-base fine-tuned | Propaganda detection | Hugging Face |

### 9.3 Frontend

| Client | Stack |
|--------|-------|
| Web Portal | React 18 + Vite 5 + Tailwind CSS + Framer Motion + Zustand |
| Browser Extension | Chrome MV3 + React 18 (popup) |
| Mobile App | React Native 0.73 + Expo |

### 9.4 AWS Services (Prototype Subset)

| Service | Purpose | Prototype Config |
|---------|---------|-----------------|
| AWS Bedrock | LLM inference | On-demand, us-east-1, pay-per-token |
| ECS Fargate | Container compute | Single task per service, no min-max scaling |
| RDS PostgreSQL | Primary DB | db.t3.medium, Single-AZ, 20GB |
| ElastiCache Redis | Cache Tier 1 | cache.t3.micro, single node |
| DynamoDB | Cache Tier 2 | On-demand, ap-south-1 |
| S3 | Media uploads + static | 3 buckets, standard storage |
| CloudFront | CDN + Cache Tier 3 | Default cert, standard PriceClass |
| SQS | Async media queue | Standard queue |
| Lambda | S3 event triggers | Python 3.11, ARM64 |
| Textract / Transcribe / Rekognition | Media intelligence | Pay-per-use |
| Neptune | Graph DB (claims-entities-sources) | db.t3.medium |
| CloudWatch | Logging + metrics | Default settings |

---

## 10. Glossary

| Term | Definition |
|------|-----------|
| Agent | Autonomous LLM-backed module querying specific data sources |
| Claim | Verifiable assertion of fact submitted for analysis |
| Credibility Score | 0–100 integer representing evidence-weighted truth probability |
| Manager Agent | Orchestrator that parses claims, selects agents, synthesizes results |
| Normalization Layer | Pre-processing before Manager Agent: text normalization, metadata extraction, language detection |
| Cache Tier 1 | Redis — hot cache, 1hr TTL, <5ms latency |
| Cache Tier 2 | DynamoDB — warm cache, 24hr TTL, <20ms |
| Cache Tier 3 | CloudFront edge — popular claims, 30d TTL, <50ms |
| Permanent Store | PostgreSQL — written regardless of cache, no TTL |
| Deepfake | Algorithmically manipulated or synthesized media |
| ELA | Error Level Analysis — JPEG compression inconsistency detection |
| FFT | Fast Fourier Transform — frequency artifact detection for image forensics |
