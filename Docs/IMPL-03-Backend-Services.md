# ZeroTRUST — Backend Services Implementation
## IMPL-03: API Gateway, Verification Engine & Multi-Agent System (Prototype)

**Series:** IMPL-03 of 05  
**Scope:** 🚧 PROTOTYPE — emphasis on working code, not production scale

---

## Table of Contents

1. [Service 1: API Gateway (Node.js + Express)](#1-api-gateway)
2. [Service 2: Verification Engine (Python + FastAPI)](#2-verification-engine)
3. [Normalization Layer](#3-normalization-layer) ← from Diagram 2
4. [Manager Agent — LangGraph Orchestration](#4-manager-agent)
5. [Specialist Agent Implementations](#5-specialist-agents)
6. [Credibility Scorer](#6-credibility-scorer)
7. [Service 3: Media Analysis](#7-media-analysis-service)
8. [Dockerfiles](#8-dockerfiles)
9. [requirements.txt](#9-requirementstxt)

---

## 1. API Gateway

### 1.1 Project Structure

```
apps/api-gateway/
├── src/
│   ├── app.ts                   # Express app setup
│   ├── server.ts                # HTTP server
│   ├── config/
│   │   ├── index.ts             # Config from env
│   │   └── redis.ts             # Redis client
│   ├── routes/
│   │   ├── verify.routes.ts
│   │   ├── auth.routes.ts
│   │   └── history.routes.ts
│   ├── controllers/
│   │   ├── VerificationController.ts
│   │   └── AuthController.ts
│   ├── middleware/
│   │   ├── auth.middleware.ts
│   │   ├── rateLimit.middleware.ts
│   │   └── error.middleware.ts
│   ├── services/
│   │   ├── VerificationService.ts   # 3-tier cache logic
│   │   └── CacheService.ts
│   └── utils/
│       ├── logger.ts
│       └── validators.ts
├── prisma/
│   └── schema.prisma
├── Dockerfile
└── package.json
```

### 1.2 app.ts

```typescript
import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import compression from 'compression';
import { verifyRoutes } from './routes/verify.routes';
import { authRoutes } from './routes/auth.routes';
import { historyRoutes } from './routes/history.routes';
import { errorMiddleware } from './middleware/error.middleware';

const app = express();

app.set('trust proxy', 1);  // Behind ALB/CloudFront
app.use(helmet());
app.use(cors({
  origin: (origin, cb) => {
    const allowed = [
      'https://zerotrust.ai',
      /^chrome-extension:\/\//,
      ...(process.env.NODE_ENV === 'development'
        ? ['http://localhost:5173', 'http://localhost:3001']
        : [])
    ];
    const ok = !origin || allowed.some(p => typeof p === 'string' ? p === origin : p.test(origin));
    cb(ok ? null : new Error('CORS'), ok);
  },
  credentials: true
}));
app.use(compression());
app.use(express.json({ limit: '10mb' }));

app.get('/health', (_, res) => res.json({ status: 'healthy', time: new Date().toISOString() }));

app.use('/api/v1/verify',   verifyRoutes);
app.use('/api/v1/auth',     authRoutes);
app.use('/api/v1/history',  historyRoutes);

app.use(errorMiddleware);

export default app;
```

### 1.3 JWT Auth Middleware

```typescript
// src/middleware/auth.middleware.ts
import jwt from 'jsonwebtoken';
import { Request, Response, NextFunction } from 'express';
import { redisClient } from '../config/redis';

interface JWTPayload {
  sub: string; email: string; tier: 'free'|'pro'|'enterprise'; jti: string;
}

export async function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const header = req.headers.authorization;
  if (!header?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Authentication required' });
  }
  try {
    const payload = jwt.verify(header.slice(7), process.env.JWT_SECRET!) as JWTPayload;
    const revoked = await redisClient.exists(`blocked:jti:${payload.jti}`);
    if (revoked) return res.status(401).json({ error: 'Token revoked' });
    req.user = { id: payload.sub, email: payload.email, tier: payload.tier, jti: payload.jti };
    next();
  } catch {
    res.status(401).json({ error: 'Invalid or expired token' });
  }
}

export async function optionalAuth(req: Request, res: Response, next: NextFunction) {
  const header = req.headers.authorization;
  if (header?.startsWith('Bearer ')) {
    try {
      const payload = jwt.verify(header.slice(7), process.env.JWT_SECRET!) as JWTPayload;
      const revoked = await redisClient.exists(`blocked:jti:${payload.jti}`);
      if (!revoked) req.user = { id: payload.sub, email: payload.email, tier: payload.tier, jti: payload.jti };
    } catch { /* anonymous */ }
  }
  next();
}
```

### 1.4 Rate Limiting Middleware

```typescript
// src/middleware/rateLimit.middleware.ts
import { rateLimit } from 'express-rate-limit';
import { RedisStore } from 'rate-limit-redis';
import { redisClient } from '../config/redis';

export const publicRateLimit = rateLimit({
  store: new RedisStore({ sendCommand: (...args: any[]) => redisClient.sendCommand(args), prefix: 'rl:pub:' }),
  windowMs: 60 * 1000,
  max: parseInt(process.env.RATE_LIMIT_PUBLIC ?? '10'),
  standardHeaders: true,
  legacyHeaders: false,
  handler: (_, res) => res.status(429).json({ error: 'Rate limit exceeded. Try again in 60 seconds.' })
});

const TIER_DAILY_LIMITS = { free: 100, pro: 5000, enterprise: 999999 };

export function userRateLimit(req: any, res: any, next: any) {
  const tier = (req.user?.tier ?? 'free') as keyof typeof TIER_DAILY_LIMITS;
  return rateLimit({
    store: new RedisStore({
      sendCommand: (...args: any[]) => redisClient.sendCommand(args),
      prefix: `rl:${req.user?.id ?? 'anon'}:`
    }),
    windowMs: 24 * 60 * 60 * 1000,
    max: TIER_DAILY_LIMITS[tier],
    handler: (_, res) => res.status(429).json({ error: `Daily limit of ${TIER_DAILY_LIMITS[tier]} reached` })
  })(req, res, next);
}
```

### 1.5 Verification Service (3-Tier Cache Logic)

```typescript
// src/services/VerificationService.ts
import crypto from 'crypto';
import axios from 'axios';
import { prisma } from '../config/database';
import { CacheService } from './CacheService';
import { logger } from '../utils/logger';

export class VerificationService {
  private cache = new CacheService();

  async verify(content: string, type: string, source: string, userId: string) {
    const cacheKey = this.buildKey(content, type);

    // ── Tier 1: Redis ────────────────────────────────────────────────
    const redisHit = await this.cache.getRedis(cacheKey);
    if (redisHit) return { ...redisHit, cached: true, cache_tier: 'redis' };

    // ── Tier 2: DynamoDB ─────────────────────────────────────────────
    const dynamoHit = await this.cache.getDynamo(cacheKey);
    if (dynamoHit) {
      await this.cache.setRedis(cacheKey, dynamoHit, 3600);       // L2→L1 promote
      return { ...dynamoHit, cached: true, cache_tier: 'dynamodb' };
    }

    // ── Tier 3: CloudFront / PostgreSQL exact-hash ───────────────────
    const pgHit = await prisma.verification.findFirst({
      where: { claimHash: cacheKey, createdAt: { gte: new Date(Date.now() - 30 * 86400 * 1000) } }
    });
    if (pgHit) {
      const result = pgHit as any;
      await Promise.all([
        this.cache.setRedis(cacheKey, result, 1800),
        this.cache.setDynamo(cacheKey, result)
      ]);
      return { ...result, cached: true, cache_tier: 'cloudfront' };
    }

    // ── Full Verification ────────────────────────────────────────────
    logger.info('Cache miss — invoking verification engine', { key: cacheKey });
    const result = await axios.post(
      `${process.env.VERIFICATION_ENGINE_URL}/verify`,
      { content, type, source, user_id: userId },
      { timeout: 30000 }
    ).then(r => r.data);

    // Write to all tiers
    await Promise.allSettled([
      this.cache.setRedis(cacheKey, result, 3600),
      this.cache.setDynamo(cacheKey, result),
      prisma.verification.create({ data: {
        claimHash: cacheKey, claimText: content, claimType: type,
        credibilityScore: result.credibility_score, category: result.category,
        confidence: result.confidence, sourcesConsulted: result.sources_consulted,
        agentConsensus: result.agent_consensus, evidenceSummary: result.evidence_summary,
        sources: result.sources, agentVerdicts: result.agent_verdicts,
        limitations: result.limitations, recommendation: result.recommendation,
        processingTime: result.processing_time,
        userId: userId !== 'anonymous' ? userId : null,
        sourcePlatform: source, cached: false
      }})
    ]);

    return { ...result, cached: false };
  }

  private buildKey(content: string, type: string): string {
    const normalized = content.toLowerCase().trim().replace(/\s+/g, ' ');
    return crypto.createHash('sha256').update(`${normalized}:${type}`).digest('hex').slice(0, 32);
  }
}
```

---

## 2. Verification Engine

### 2.1 Project Structure

```
apps/verification-engine/
├── src/
│   ├── main.py                       # FastAPI app
│   ├── routers/verify.py             # POST /verify
│   ├── normalization/                # ← Diagram 2: Normalization Layer
│   │   ├── __init__.py
│   │   ├── text_normalizer.py
│   │   ├── metadata_extractor.py
│   │   └── language_detector.py
│   ├── agents/
│   │   ├── base.py
│   │   ├── manager.py               # LangGraph orchestrator
│   │   ├── research.py
│   │   ├── news.py
│   │   ├── scientific.py
│   │   ├── social_media.py
│   │   ├── sentiment.py
│   │   └── scraper.py
│   ├── services/
│   │   ├── credibility.py
│   │   ├── evidence.py
│   │   └── report.py
│   ├── integrations/
│   │   ├── bedrock.py
│   │   ├── news_apis.py
│   │   ├── search.py
│   │   ├── fact_check.py
│   │   ├── scientific_apis.py
│   │   └── social_apis.py
│   └── models/verification.py
```

### 2.2 main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.verify import router as verify_router

app = FastAPI(
    title="ZeroTRUST Verification Engine",
    version="2.0.0",
    docs_url="/docs" if __import__('os').getenv('ENVIRONMENT') != 'production' else None
)

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "verification-engine"}

app.include_router(verify_router, prefix="/verify")
```

### 2.3 Pydantic Models

```python
# src/models/verification.py
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class ClaimType(str, Enum):
    FACTUAL = "factual"; STATISTICAL = "statistical"; QUOTE = "quote"
    PREDICTION = "prediction"; OPINION = "opinion"; MIXED = "mixed"

class ContentType(str, Enum):
    TEXT = "text"; URL = "url"; IMAGE = "image"; VIDEO = "video"

class VerificationRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=10000)
    type: ContentType
    source: str
    user_id: str = "anonymous"
    priority: int = Field(default=5, ge=1, le=10)

class SourceReference(BaseModel):
    url: str; title: str; excerpt: str
    credibility_tier: str; credibility_score: float
    stance: str; source_type: str
    published_at: Optional[str] = None

class AgentVerdict(BaseModel):
    verdict: str; confidence: float; summary: str
    sources_count: int; error: Optional[str] = None

class VerificationResult(BaseModel):
    id: str
    credibility_score: int = Field(ge=0, le=100)
    category: str; confidence: str; claim_type: ClaimType
    sources_consulted: int; agent_consensus: str
    evidence_summary: dict; sources: list; agent_verdicts: dict
    limitations: list; recommendation: str
    processing_time: float; created_at: str
```

---

## 3. Normalization Layer

> From Architecture Diagram 2 — runs BEFORE the Manager Agent

```python
# src/normalization/__init__.py
from .text_normalizer import TextNormalizer
from .metadata_extractor import MetadataExtractor
from .language_detector import LanguageDetector

class NormalizationLayer:
    """Pre-processes claim before Manager Agent — Diagram 2: Normalization Layer."""

    def __init__(self):
        self.text_norm = TextNormalizer()
        self.meta_extract = MetadataExtractor()
        self.lang_detect = LanguageDetector()

    async def process(self, request: dict) -> dict:
        content = request['content']
        claim_type = request['type']

        normalized_text = self.text_norm.normalize(content)
        metadata = self.meta_extract.extract(content, claim_type)
        language = self.lang_detect.detect(content)

        return {
            **request,
            'normalized_content': normalized_text,
            'metadata': metadata,
            'language': language,
            'original_content': content
        }
```

```python
# src/normalization/text_normalizer.py
import re
import unicodedata

class TextNormalizer:
    """🔤 Text Normalization — strip HTML, fix unicode, normalize whitespace."""

    # Common stop words for cache key generation
    STOP_WORDS = frozenset([
        'a','an','the','is','are','was','were','be','been','being',
        'have','has','had','do','does','did','will','would','could',
        'should','may','might','shall','can','of','in','at','by','for',
        'with','about','as','from','that','this','it','its'
    ])

    def normalize(self, text: str) -> str:
        # Decode HTML entities
        import html
        text = html.unescape(text)
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Normalize unicode (NFC)
        text = unicodedata.normalize('NFC', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def to_cache_key(self, text: str) -> str:
        """Order-independent cache key (for near-duplicate detection)."""
        normalized = self.normalize(text).lower()
        import string
        normalized = normalized.translate(str.maketrans('', '', string.punctuation))
        tokens = [w for w in normalized.split() if w not in self.STOP_WORDS]
        canonical = ' '.join(sorted(tokens))
        return canonical
```

```python
# src/normalization/metadata_extractor.py
import re
from urllib.parse import urlparse

class MetadataExtractor:
    """🏷️ Metadata Extraction — entity hints, URL domain, claim markers."""

    def extract(self, content: str, claim_type: str) -> dict:
        metadata: dict = {
            'is_url': bool(re.match(r'https?://', content.strip())),
            'has_numbers': bool(re.search(r'\d+\.?\d*%?', content)),
            'has_quote_markers': bool(re.search(r'["\'"]', content)),
            'word_count': len(content.split()),
            'contains_statistics': bool(re.search(
                r'\d+\.?\d*\s*(%|percent|million|billion|crore|lakh)', content, re.I))
        }
        if metadata['is_url']:
            try:
                parsed = urlparse(content.strip())
                metadata['source_domain'] = parsed.netloc
            except Exception:
                pass
        return metadata
```

```python
# src/normalization/language_detector.py
import langdetect
from langdetect.lang_detect_exception import LangDetectException

class LanguageDetector:
    """🌐 Language Detection — ISO 639-1 code."""

    SUPPORTED = {'en', 'hi', 'mr', 'ta', 'te', 'bn', 'gu', 'kn', 'ml', 'pa'}

    def detect(self, text: str) -> str:
        try:
            lang = langdetect.detect(text[:200])
            return lang if lang in self.SUPPORTED else 'en'
        except LangDetectException:
            return 'en'
```

---

## 4. Manager Agent

```python
# src/agents/manager.py
import asyncio, json, time, uuid
from datetime import datetime
from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END
from normalization import NormalizationLayer
from integrations.bedrock import invoke_bedrock
from agents import research, news, scientific, social_media, sentiment, scraper
from services.credibility import CredibilityScorer
from services.evidence import EvidenceAggregator
from services.report import ReportGenerator
from models.verification import VerificationRequest, VerificationResult, ClaimType

AGENT_REGISTRY = {
    'research':     research.ResearchAgent(),
    'news':         news.NewsAgent(),
    'scientific':   scientific.ScientificAgent(),
    'social_media': social_media.SocialMediaAgent(),
    'sentiment':    sentiment.SentimentAgent(),
    'scraper':      scraper.ScraperAgent()
}

# Domain → agents map (from Diagram 2 context)
DOMAIN_AGENTS = {
    'politics':      ['news', 'social_media', 'research', 'sentiment'],
    'health':        ['scientific', 'news', 'research'],
    'science':       ['scientific', 'research'],
    'technology':    ['news', 'research'],
    'climate':       ['scientific', 'news', 'research'],
    'sports':        ['news', 'social_media'],
    'entertainment': ['news', 'social_media'],
    'business':      ['news', 'research'],
    'default':       ['research', 'news', 'social_media']
}

class AgentState(TypedDict):
    request: dict
    normalized: dict           # output of NormalizationLayer
    claim_analysis: dict
    selected_agents: list[str]
    agent_results: Annotated[Sequence[dict], operator.add]
    evidence: dict
    credibility: dict
    report: dict
    errors: Annotated[Sequence[str], operator.add]

class ManagerAgent:
    def __init__(self):
        self.normalizer = NormalizationLayer()   # ← Diagram 2: Normalization
        self.scorer    = CredibilityScorer()
        self.aggregator = EvidenceAggregator()
        self.reporter  = ReportGenerator()
        self.graph     = self._build_graph()

    def _build_graph(self):
        g = StateGraph(AgentState)
        g.add_node("normalize",            self._normalize_node)      # ← NEW from Diagram 2
        g.add_node("analyze_claim",        self._analyze_claim_node)
        g.add_node("select_agents",        self._select_agents_node)
        g.add_node("execute_agents",       self._execute_agents_node)
        g.add_node("aggregate_evidence",   self._aggregate_evidence_node)
        g.add_node("calculate_credibility", self._calculate_credibility_node)
        g.add_node("generate_report",      self._generate_report_node)

        g.set_entry_point("normalize")
        g.add_edge("normalize",            "analyze_claim")
        g.add_edge("analyze_claim",        "select_agents")
        g.add_edge("select_agents",        "execute_agents")
        g.add_edge("execute_agents",       "aggregate_evidence")
        g.add_edge("aggregate_evidence",   "calculate_credibility")
        g.add_edge("calculate_credibility", "generate_report")
        g.add_edge("generate_report",      END)
        return g.compile()

    async def verify(self, request: VerificationRequest) -> VerificationResult:
        start = time.time()
        initial: AgentState = {
            "request": request.model_dump(), "normalized": {},
            "claim_analysis": {}, "selected_agents": [],
            "agent_results": [], "evidence": {},
            "credibility": {}, "report": {}, "errors": []
        }
        final = await self.graph.ainvoke(initial)
        processing_time = time.time() - start

        return VerificationResult(
            id=str(uuid.uuid4()),
            credibility_score=final['credibility']['score'],
            category=final['credibility']['category'],
            confidence=final['credibility']['confidence'],
            claim_type=ClaimType(final['claim_analysis'].get('type', 'mixed')),
            sources_consulted=final['evidence'].get('total_sources', 0),
            agent_consensus=final['credibility']['consensus'],
            evidence_summary=final['evidence'].get('summary', {}),
            sources=final['evidence'].get('sources', []),
            agent_verdicts=final['report'].get('agent_verdicts', {}),
            limitations=final['report'].get('limitations', []),
            recommendation=final['report'].get('recommendation', ''),
            processing_time=processing_time,
            created_at=datetime.utcnow().isoformat()
        )

    # ── Node Implementations ──────────────────────────────────────────────────

    async def _normalize_node(self, state: AgentState) -> dict:
        """Diagram 2: Normalization Layer — text norm, metadata, language."""
        normalized = await self.normalizer.process(state['request'])
        return {"normalized": normalized}

    async def _analyze_claim_node(self, state: AgentState) -> dict:
        claim = state['normalized'].get('normalized_content', state['request']['content'])
        prompt = f"""Analyze this claim. Return ONLY valid JSON:
{{
  "main_assertion": "<one sentence>",
  "entities": ["<entity1>"],
  "type": "factual|statistical|quote|prediction|opinion|mixed",
  "domain": "politics|health|science|technology|climate|sports|entertainment|business|general",
  "verification_scope": "<what needs checking>"
}}
Claim: {claim}"""
        try:
            r = await invoke_bedrock('manager', prompt)
            analysis = json.loads(r.strip())
        except Exception as e:
            analysis = {"domain": "general", "type": "mixed", "entities": [], "error": str(e)}
        return {"claim_analysis": analysis}

    async def _select_agents_node(self, state: AgentState) -> dict:
        domain = state['claim_analysis'].get('domain', 'default')
        agents = set(DOMAIN_AGENTS.get(domain, DOMAIN_AGENTS['default']))
        agents.add('sentiment')    # always include manipulation detection
        meta = state['normalized'].get('metadata', {})
        if meta.get('is_url'):
            agents.add('scraper')
        if state['claim_analysis'].get('type') == 'statistical':
            agents.add('research')
        if state['claim_analysis'].get('domain') in ('health', 'science', 'climate'):
            agents.add('scientific')
        return {"selected_agents": list(agents)}

    async def _execute_agents_node(self, state: AgentState) -> dict:
        claim = state['normalized'].get('normalized_content', state['request']['content'])
        analysis = state['claim_analysis']
        TIMEOUT = float(__import__('os').getenv('MAX_AGENT_TIMEOUT', '10'))

        async def run(name: str):
            try:
                return await asyncio.wait_for(
                    AGENT_REGISTRY[name].investigate(claim, analysis), timeout=TIMEOUT)
            except asyncio.TimeoutError:
                return {"agent": name, "verdict": "insufficient", "confidence": 0.0,
                        "summary": f"Agent timed out ({TIMEOUT}s)", "sources": [], "error": "timeout"}
            except Exception as e:
                return {"agent": name, "verdict": "insufficient", "confidence": 0.0,
                        "summary": "Agent error", "sources": [], "error": str(e)[:200]}

        results = await asyncio.gather(*[run(n) for n in state['selected_agents']])
        return {"agent_results": list(results)}

    async def _aggregate_evidence_node(self, state: AgentState) -> dict:
        return {"evidence": self.aggregator.aggregate(state['agent_results'])}

    async def _calculate_credibility_node(self, state: AgentState) -> dict:
        return {"credibility": self.scorer.calculate(
            evidence=state['evidence'],
            agent_results=state['agent_results'],
            claim_analysis=state['claim_analysis']
        )}

    async def _generate_report_node(self, state: AgentState) -> dict:
        return {"report": self.reporter.generate(
            claim=state['request']['content'],
            analysis=state['claim_analysis'],
            evidence=state['evidence'],
            credibility=state['credibility'],
            agent_results=state['agent_results']
        )}
```

---

## 5. Specialist Agents

### 5.1 Base Agent

```python
# src/agents/base.py
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    async def investigate(self, claim: str, analysis: dict) -> dict:
        """Returns: {agent, verdict, confidence, summary, sources, evidence, error?}"""
        pass

    def _source(self, url, title, excerpt, tier, stance, source_type, published_at=None):
        tier_scores = {'tier_1': 0.95, 'tier_2': 0.80, 'tier_3': 0.60, 'tier_4': 0.35}
        return {
            "url": url, "title": title, "excerpt": excerpt,
            "credibility_tier": tier, "credibility_score": tier_scores.get(tier, 0.3),
            "stance": stance, "source_type": source_type, "published_at": published_at
        }
```

### 5.2 News Agent

```python
# src/agents/news.py
import asyncio, json, httpx
from agents.base import BaseAgent
from integrations.bedrock import invoke_bedrock
from integrations.news_apis import search_newsapi
from integrations.fact_check import search_factcheckers

TIER_1 = {'BBC', 'Reuters', 'Associated Press', 'NPR', 'PBS', 'The Economist', 'AltNews', 'Boomlive'}
TIER_2 = {'CNN', 'The Guardian', 'Washington Post', 'Bloomberg', 'NDTV', 'The Hindu', 'Indian Express'}

class NewsAgent(BaseAgent):
    async def investigate(self, claim: str, analysis: dict) -> dict:
        entities = analysis.get('entities', [])[:5]
        news_res, fc_res = await asyncio.gather(
            search_newsapi(entities), search_factcheckers(claim), return_exceptions=True)
        if isinstance(news_res, Exception): news_res = []
        if isinstance(fc_res, Exception): fc_res = []
        all_sources = news_res + fc_res
        if not all_sources:
            return {"agent":"news","verdict":"insufficient","confidence":0.0,
                    "summary":"No news sources found","sources":[],"evidence":{}}
        return await self._analyze(claim, all_sources)

    def _assess_tier(self, name: str) -> str:
        if name in TIER_1: return 'tier_1'
        if name in TIER_2: return 'tier_2'
        return 'tier_4'

    async def _analyze(self, claim: str, sources: list) -> dict:
        context = "\n".join([f"- {s.get('title','')} ({s.get('source_name','')}): {s.get('excerpt','')[:200]}"
                             for s in sources[:15]])
        prompt = f"""Analyze whether these news sources support or contradict this claim.
Claim: {claim}
Sources:
{context}
Return ONLY valid JSON:
{{"verdict":"supports|contradicts|mixed|insufficient","confidence":0.0,"summary":"<2 sentences>","evidence":{{"supporting":0,"contradicting":0,"neutral":0}}}}"""
        try:
            r = await invoke_bedrock('manager', prompt)
            parsed = json.loads(r.strip())
            return {"agent": "news", **parsed, "sources": sources[:20]}
        except:
            return {"agent":"news","verdict":"insufficient","confidence":0.0,
                    "summary":"Analysis failed","sources":sources[:5],"evidence":{}}
```

### 5.3 Scientific Agent

```python
# src/agents/scientific.py
import asyncio, json
from agents.base import BaseAgent
from integrations.bedrock import invoke_bedrock
from integrations.scientific_apis import search_pubmed, search_arxiv

class ScientificAgent(BaseAgent):
    async def investigate(self, claim: str, analysis: dict) -> dict:
        query = analysis.get('main_assertion', claim)[:200]
        pm_res, ax_res = await asyncio.gather(
            search_pubmed(query), search_arxiv(query), return_exceptions=True)
        papers = []
        if isinstance(pm_res, list): papers.extend(pm_res)
        if isinstance(ax_res, list): papers.extend(ax_res)
        if not papers:
            return {"agent":"scientific","verdict":"insufficient","confidence":0.2,
                    "summary":"No peer-reviewed sources found","sources":[],"evidence":{}}
        return await self._assess_consensus(claim, papers)

    async def _assess_consensus(self, claim: str, papers: list) -> dict:
        titles = "\n".join([f"- {p['title']} ({p.get('journal','')}, {p.get('year','')})"
                            for p in papers[:10]])
        prompt = f"""As a scientist, does the peer-reviewed literature support or contradict this claim?
Claim: {claim}
Relevant papers:
{titles}
Return ONLY JSON:
{{"verdict":"supports|contradicts|mixed|insufficient","confidence":0.0,"summary":"<2 sentences>","consensus_level":"strong_consensus|moderate_consensus|weak_consensus|divided|minority_view","evidence":{{"supporting":0,"contradicting":0,"neutral":0}}}}"""
        try:
            r = await invoke_bedrock('research', prompt)
            parsed = json.loads(r.strip())
            sources = [self._source(p.get('url',''), p['title'], p.get('abstract','')[:200],
                                    'tier_1', 'neutral', 'academic') for p in papers[:10]]
            return {"agent": "scientific", **parsed, "sources": sources}
        except:
            return {"agent":"scientific","verdict":"insufficient","confidence":0.0,
                    "summary":"Scientific analysis failed","sources":[],"evidence":{}}
```

### 5.4 Sentiment & Propaganda Agent

```python
# src/agents/sentiment.py
import re, json
from agents.base import BaseAgent
from integrations.bedrock import invoke_bedrock

PROPAGANDA_PATTERNS = {
    'name_calling':   r'\b(radical|extremist|terrorist|traitor|fascist)\b',
    'loaded_language': r'\b(devastating|catastrophic|explosive|shocking|outrageous)\b',
    'false_urgency':  r'\b(act now|urgent|immediate action|before it\'s too late)\b',
    'bandwagon':      r'\b(everyone knows|everyone is|millions are|join the)\b',
    'false_dilemma':  r'\b(either.*or|you\'re with us|no other choice)\b',
}

class SentimentAgent(BaseAgent):
    async def investigate(self, claim: str, analysis: dict) -> dict:
        detected = [t for t, p in PROPAGANDA_PATTERNS.items()
                    if re.search(p, claim.lower())]

        llm = await self._llm_analysis(claim, detected)
        manipulation_score = min(1.0,
            len(detected) * 0.15 +
            llm.get('manipulation_score', 0) * 0.85
        )
        verdict = ('contradicts' if manipulation_score > 0.6 else
                   'mixed'       if manipulation_score > 0.3 else 'supports')
        return {
            "agent": "sentiment",
            "verdict": verdict,
            "confidence": min(0.95, 0.6 + len(detected) * 0.06),
            "summary": llm.get('summary', f"Detected {len(detected)} manipulation technique(s)"),
            "sources": [],
            "evidence": {"supporting": 0, "contradicting": 1 if manipulation_score > 0.5 else 0, "neutral": 1},
            "manipulation_score": manipulation_score,
            "detected_techniques": detected
        }

    async def _llm_analysis(self, claim: str, techniques: list) -> dict:
        prompt = f"""Analyze for propaganda/manipulation techniques.
Claim: {claim}
Pre-detected techniques: {techniques}
Return ONLY JSON:
{{"manipulation_score":0.0,"techniques":[],"summary":"","is_emotionally_manipulative":false}}"""
        try:
            r = await invoke_bedrock('sentiment', prompt)
            return json.loads(r.strip())
        except:
            return {"manipulation_score": 0.0, "summary": "Manipulation analysis unavailable"}
```

---

## 6. Credibility Scorer

```python
# src/services/credibility.py

SOURCE_TIER_WEIGHTS  = {'tier_1': 1.0, 'tier_2': 0.8, 'tier_3': 0.5, 'tier_4': 0.2}
VERDICT_SCORES       = {
    'strongly_supports': 1.0, 'supports': 0.8, 'leans_support': 0.65,
    'mixed': 0.5, 'insufficient': 0.5,
    'leans_contradict': 0.35, 'contradicts': 0.2, 'strongly_contradicts': 0.0
}
AGENT_WEIGHTS        = {
    'news': 0.25, 'scientific': 0.25, 'research': 0.20,
    'social_media': 0.10, 'sentiment': 0.10, 'scraper': 0.10
}
SCORE_CATEGORIES = [
    (85, 'Verified True'), (70, 'Likely True'), (55, 'Mixed Evidence'),
    (40, 'Likely False'), (0, 'Verified False')
]

class CredibilityScorer:
    def calculate(self, evidence: dict, agent_results: list, claim_analysis: dict) -> dict:
        if not agent_results:
            return {"score": 50, "category": "Insufficient Evidence", "confidence": "Low", "consensus": "No agents run"}

        # 1. Evidence score
        ev = evidence.get('summary', {}); total_ev = max(sum(ev.values()), 1)
        evidence_score = max(0.0, (ev.get('supporting', 0) - ev.get('contradicting', 0) * 0.5) / total_ev)

        # 2. Agent consensus score
        weighted, total_w, verdicts = 0.0, 0.0, []
        for r in agent_results:
            w = AGENT_WEIGHTS.get(r.get('agent', ''), 0.1)
            s = VERDICT_SCORES.get(r.get('verdict', 'insufficient'), 0.5)
            weighted += s * w; total_w += w
            verdicts.append(r.get('verdict', 'insufficient'))
        consensus_score = weighted / max(total_w, 0.01)

        # 3. Source reliability
        sources = evidence.get('sources', [])
        reliability_score = self._reliability(sources)

        # 4. Confidence penalty
        avg_conf = sum(r.get('confidence', 0.5) for r in agent_results) / len(agent_results)
        penalty = 0.7 + avg_conf * 0.3

        # 5. Final score
        raw = (evidence_score * 0.40 + consensus_score * 0.30 + reliability_score * 0.30) * penalty
        score = int(min(100, max(0, raw * 100)))
        category = next(cat for threshold, cat in SCORE_CATEGORIES if score >= threshold)

        return {
            "score": score, "category": category,
            "confidence": "High" if avg_conf >= 0.8 and len(sources) >= 5 else
                          "Medium" if avg_conf >= 0.6 and len(sources) >= 3 else "Low",
            "consensus": self._describe_consensus(verdicts),
            "components": {
                "evidence_score": round(evidence_score, 3),
                "consensus_score": round(consensus_score, 3),
                "reliability_score": round(reliability_score, 3),
                "confidence_penalty": round(penalty, 3)
            }
        }

    def _reliability(self, sources: list) -> float:
        if not sources: return 0.3
        weighted = sum(s.get('credibility_score', 0.3) *
                       SOURCE_TIER_WEIGHTS.get(s.get('credibility_tier', 'tier_4'), 0.2)
                       for s in sources)
        total_w = sum(SOURCE_TIER_WEIGHTS.get(s.get('credibility_tier', 'tier_4'), 0.2) for s in sources)
        return weighted / max(total_w, 0.01)

    def _describe_consensus(self, verdicts: list) -> str:
        if not verdicts: return "No consensus"
        top = max(set(verdicts), key=verdicts.count)
        pct = (verdicts.count(top) / len(verdicts)) * 100
        if pct >= 80: return f"Strong consensus ({pct:.0f}%)"
        if pct >= 60: return f"Moderate consensus ({pct:.0f}%)"
        return f"Mixed opinions ({pct:.0f}%)"
```

---

## 7. Media Analysis Service

### 7.1 Image Deepfake Detector (XceptionNet + EfficientNet — Diagram 4)

```python
# apps/media-analysis/src/detectors/image.py
import asyncio
import numpy as np
from PIL import Image, ExifTags
import tensorflow as tf

class ImageDeepfakeDetector:
    """Ensemble: XceptionNet 35% + EfficientNet 35% + FFT 20% + EXIF 10%"""

    def __init__(self, model_dir: str):
        self.xception = tf.keras.models.load_model(f'{model_dir}/xception_deepfake_v2.h5')
        self.efficientnet = tf.keras.models.load_model(f'{model_dir}/efficientnet_b4_deepfake_v1.h5')

    async def analyze(self, image_path: str) -> dict:
        image = Image.open(image_path).convert('RGB')
        xc, ef, freq, meta = await asyncio.gather(
            asyncio.to_thread(self._xception_predict, image),
            asyncio.to_thread(self._efficientnet_predict, image),
            asyncio.to_thread(self._frequency_analysis, image),
            asyncio.to_thread(self._metadata_analysis, image_path)
        )
        prob = xc * 0.35 + ef * 0.35 + freq['score'] * 0.20 + meta['score'] * 0.10
        return {
            "manipulation_probability": float(prob),
            "is_likely_manipulated": prob > 0.70,
            "confidence": "High" if abs(prob - 0.5) > 0.3 else "Medium",
            "model_scores": {"xception": float(xc), "efficientnet": float(ef)},
            "frequency_analysis": freq, "metadata": meta,
            "recommendation": (
                "High probability of manipulation. Do not share without verification." if prob >= 0.85 else
                "Possible manipulation detected. Seek original source." if prob >= 0.70 else
                "Some anomalies detected. Use caution." if prob >= 0.50 else
                "No obvious manipulation detected, but verify source independently."
            )
        }

    def _xception_predict(self, img: Image.Image) -> float:
        arr = np.expand_dims(np.array(img.resize((299, 299))) / 255.0, axis=0)
        return float(self.xception.predict(arr, verbose=0)[0][1])

    def _efficientnet_predict(self, img: Image.Image) -> float:
        arr = np.expand_dims(np.array(img.resize((380, 380))) / 255.0, axis=0)
        return float(self.efficientnet.predict(arr, verbose=0)[0][1])

    def _frequency_analysis(self, img: Image.Image) -> dict:
        """FFT artifact detection — Diagram 4: Frequency Analysis."""
        gray = np.array(img.convert('L'), dtype=float)
        f = np.fft.fft2(gray); mag = np.abs(np.fft.fftshift(f))
        h, w = mag.shape
        center = mag[h//4:3*h//4, w//4:3*w//4]
        edge = mag.copy(); edge[h//4:3*h//4, w//4:3*w//4] = 0
        score = min(1.0, float(np.mean(edge) / (np.mean(center) + 1e-7)) * 2.0)
        return {"score": score, "has_artifacts": score > 0.6}

    def _metadata_analysis(self, path: str) -> dict:
        """EXIF metadata analysis — Diagram 4: Metadata Analyser."""
        inconsistencies = []
        try:
            img = Image.open(path)
            exif = {ExifTags.TAGS.get(k, k): str(v) for k, v in (img._getexif() or {}).items()}
            if exif.get('DateTime') != exif.get('DateTimeOriginal'):
                inconsistencies.append('Timestamp modified')
            for sw in ['Photoshop', 'GIMP', 'Lightroom']:
                if sw.lower() in str(exif.get('Software', '')).lower():
                    inconsistencies.append(f'Editing software detected: {sw}')
        except Exception:
            pass
        return {"inconsistencies": inconsistencies, "score": min(1.0, len(inconsistencies) * 0.35)}
```

### 7.2 Bedrock Integration

```python
# src/integrations/bedrock.py
import boto3
from botocore.config import Config
import os

bedrock = boto3.client(
    'bedrock-runtime',
    region_name=os.getenv('BEDROCK_REGION', 'us-east-1'),
    config=Config(retries={'max_attempts': 3, 'mode': 'adaptive'},
                  connect_timeout=5, read_timeout=60)
)

MODEL_CONFIGS = {
    'manager': {
        'modelId': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
        'inferenceConfig': {'maxTokens': 4096, 'temperature': 0.3, 'topP': 0.9}
    },
    'research': {
        'modelId': 'mistral.mistral-large-2407-v1:0',
        'inferenceConfig': {'maxTokens': 2048, 'temperature': 0.4, 'topP': 0.85}
    },
    'sentiment': {
        'modelId': 'anthropic.claude-3-5-haiku-20241022-v1:0',
        'inferenceConfig': {'maxTokens': 1024, 'temperature': 0.2}
    }
}

# Fallback chain: Claude 3.5 Sonnet → Llama 3.1 70B → Mistral Large
FALLBACK_CHAIN = [
    'anthropic.claude-3-5-sonnet-20241022-v2:0',
    'meta.llama3-1-70b-instruct-v1:0',
    'mistral.mistral-large-2407-v1:0'
]

async def invoke_bedrock(config_key: str, prompt: str) -> str:
    model_ids = [MODEL_CONFIGS[config_key]['modelId']] + FALLBACK_CHAIN
    for mid in model_ids:
        try:
            r = bedrock.converse(
                modelId=mid,
                messages=[{'role': 'user', 'content': [{'text': prompt}]}],
                inferenceConfig=MODEL_CONFIGS[config_key]['inferenceConfig']
            )
            return r['output']['message']['content'][0]['text']
        except bedrock.exceptions.ThrottlingException:
            continue
        except Exception:
            if mid == model_ids[-1]: raise
    raise RuntimeError("All Bedrock models failed")
```

---

## 8. Dockerfiles

### 8.1 API Gateway

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
RUN addgroup -S zerotrust && adduser -S zerotrust -G zerotrust
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
USER zerotrust
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/server.js"]
```

### 8.2 Verification Engine

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN adduser --no-create-home --disabled-password zerotrust
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm
COPY src/ ./src/
USER zerotrust
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### 8.3 Media Analysis (CPU — for prototype)

```dockerfile
# Dockerfile.cpu — no GPU needed for prototype demo
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg libgl1 && rm -rf /var/lib/apt/lists/*
RUN adduser --no-create-home --disabled-password zerotrust
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
USER zerotrust
EXPOSE 8001
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
```

---

## 9. requirements.txt

```
# Verification Engine
fastapi==0.110.0
uvicorn[standard]==0.28.0
pydantic==2.6.0
langchain==0.1.15
langgraph==0.0.60
boto3==1.34.50
httpx==0.27.0
redis==5.0.3
psycopg2-binary==2.9.9
sqlalchemy==2.0.28

# NLP / ML
transformers==4.38.2
torch==2.2.0
tensorflow-cpu==2.15.0   # Change to tensorflow==2.15.0 for GPU
Pillow==10.2.0
numpy==1.26.4
spacy==3.7.4
vaderSentiment==3.3.2
sentence-transformers==2.6.1

# Web scraping
beautifulsoup4==4.12.3
playwright==1.42.0

# Language detection
langdetect==1.0.9

# Observability
sentry-sdk==1.42.0

# ── API Gateway (package.json) ──
# express@4.18.x
# prisma@5.10.x
# jsonwebtoken
# zod
# axios
# winston
# express-rate-limit
# rate-limit-redis
# ioredis
# helmet
# compression
# cors
```
