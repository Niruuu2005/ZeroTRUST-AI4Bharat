# Design Document: ZeroTRUST Production Readiness

## Overview

This design document specifies the implementation of critical missing components to transform the ZeroTRUST system from a 45% complete prototype into a production-ready misinformation detection platform. The system will verify claims in under 5 seconds by orchestrating 6 specialized AI agents across 30-60 sources, achieving >0.7 agent confidence with comprehensive caching and AWS infrastructure.

### Current State

The system has solid foundations:
- PostgreSQL database with Prisma ORM (complete)
- Redis cache tier (complete)
- Express API Gateway skeleton (85% complete)
- FastAPI Verification Engine skeleton (70% complete)
- 6 specialist agents implemented (Research, News, Scientific, Social Media, Sentiment, Scraper)
- React web portal UI (75% complete)

### Critical Gaps

The following components block production readiness:
1. AWS Bedrock not configured - all LLM analysis returns mocks with 0.0 confidence
2. Manager Agent missing - cannot orchestrate specialist agents
3. API routes missing - frontend cannot communicate with backend
4. Credibility scoring not implemented - cannot calculate final scores
5. Evidence aggregation not implemented - cannot deduplicate sources
6. Report generation not implemented - cannot format results
7. Rate limiting not implemented - vulnerable to abuse
8. S3 media upload not implemented - cannot verify images/videos
9. DynamoDB cache tier not deployed - missing distributed caching
10. Test suite missing - 0% coverage, high regression risk

### Design Goals


1. Enable accurate AI analysis by configuring AWS Bedrock with proper credentials and model access
2. Implement Manager Agent using LangGraph to orchestrate the verification workflow
3. Implement credibility scoring algorithm with weighted formula (Evidence 40% + Consensus 30% + Reliability 30%)
4. Implement evidence aggregation with deduplication and stance analysis
5. Implement report generation with LLM-generated recommendations
6. Create RESTful API routes for verification, history, and authentication
7. Implement tier-based rate limiting to prevent abuse
8. Implement S3 presigned URL flow for media uploads
9. Deploy DynamoDB cache tier for distributed caching
10. Create comprehensive test suite with >70% coverage including property-based tests

### Success Criteria

- Verification time: <5 seconds for 90% of requests
- Sources consulted: 30-60 per verification
- Agent confidence: >0.7 average
- Cache hit rate: >80%
- Test coverage: >70%
- API uptime: >99.9%

## Architecture

### System Architecture

The ZeroTRUST system follows a microservices architecture with three main services:

```
┌─────────────┐
│   Clients   │ (Web Portal, Browser Extension, Mobile App)
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────────────────────────────┐
│              API Gateway (Express/TypeScript)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │   Auth   │  │  Verify  │  │  3-Tier Cache        │  │
│  │  Routes  │  │  Routes  │  │  Redis → DynamoDB    │  │
│  └──────────┘  └──────────┘  │  → PostgreSQL        │  │
│                               └──────────────────────┘  │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP
                   ▼
┌─────────────────────────────────────────────────────────┐
│        Verification Engine (FastAPI/Python)              │
│  ┌──────────────┐  ┌────────────────────────────────┐  │
│  │   Manager    │  │    6 Specialist Agents         │  │
│  │    Agent     │──│  Research, News, Scientific,   │  │
│  │  (LangGraph) │  │  Social, Sentiment, Scraper    │  │
│  └──────────────┘  └────────────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ Credibility  │  │   Evidence   │  │   Report    │  │
│  │   Scorer     │  │  Aggregator  │  │  Generator  │  │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│           External Services & AWS                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │   AWS    │  │ NewsAPI  │  │  Google  │  │Twitter │ │
│  │ Bedrock  │  │  GNews   │  │   CSE    │  │ Reddit │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Manager Agent Workflow (LangGraph)

The Manager Agent orchestrates the verification process through a state machine:

```
normalize_claim
      │
      ▼
analyze_claim_domain
      │
      ▼
select_agents
      │
      ▼
execute_agents (parallel)
      │
      ▼
aggregate_evidence
      │
      ▼
calculate_credibility
      │
      ▼
generate_report
```


### Cache Architecture

Three-tier caching strategy for optimal performance:

**Tier 1: Redis (In-Memory)**
- TTL: 1 hour
- Purpose: Hot cache for frequently accessed claims
- Latency: <10ms

**Tier 2: DynamoDB (Distributed)**
- TTL: 24 hours
- Purpose: Distributed cache for recent claims
- Latency: <50ms
- Auto-promotion to Tier 1 on hit

**Tier 3: PostgreSQL (Persistent)**
- TTL: 30 days
- Purpose: Historical data and long-term storage
- Latency: <200ms
- Auto-promotion to Tier 1 and Tier 2 on hit

### API Routes Architecture

**Authentication Routes** (`/api/v1/auth`)
- POST `/register` - Create new user account
- POST `/login` - Authenticate and receive JWT tokens
- POST `/refresh` - Refresh access token
- POST `/logout` - Revoke tokens

**Verification Routes** (`/api/v1/verify`)
- POST `/` - Submit claim for verification
- GET `/presigned-url` - Get S3 presigned URL for media upload

**History Routes** (`/api/v1/history`)
- GET `/` - Get paginated verification history
- GET `/:id` - Get specific verification by ID

## Components and Interfaces

### 1. AWS Bedrock Integration

**Purpose:** Enable LLM-based analysis for all agents

**Configuration:**
```typescript
// Environment variables required
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_DEFAULT_REGION=us-east-1

// Models to enable in AWS Console
- anthropic.claude-3-5-sonnet-20241022-v2:0 (primary)
- anthropic.claude-3-haiku-20240307-v1:0 (fallback)
- mistral.mistral-large-2402-v1:0 (fallback)
```

**Python Client:**
```python
import boto3
from botocore.config import Config

bedrock = boto3.client(
    'bedrock-runtime',
    region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
    config=Config(
        retries={'max_attempts': 3, 'mode': 'adaptive'}
    )
)

def invoke_model(prompt: str, model_id: str) -> dict:
    response = bedrock.invoke_model(
        modelId=model_id,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        })
    )
    return json.loads(response['body'].read())
```

**Fallback Chain:**
1. Try Claude 3.5 Sonnet (best quality)
2. If throttled/unavailable, try Claude 3 Haiku (faster)
3. If still unavailable, try Mistral Large (alternative)
4. If all fail, return error with descriptive message

### 2. Manager Agent (LangGraph)

**Purpose:** Orchestrate the verification workflow through a state machine

**State Definition:**
```python
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    # Input
    claim: str
    claim_type: str
    source: str
    user_id: str
    
    # Normalization
    normalized_claim: str
    claim_hash: str
    metadata: Dict[str, Any]
    language: str
    
    # Analysis
    domain: str  # health, politics, science, general
    selected_agents: List[str]
    
    # Agent Results
    agent_results: List[Dict[str, Any]]
    
    # Aggregation
    all_sources: List[Dict[str, Any]]
    deduplicated_sources: List[Dict[str, Any]]
    evidence_summary: Dict[str, int]
    
    # Scoring
    credibility_score: int
    category: str
    confidence: str
    
    # Report
    final_report: Dict[str, Any]
    processing_time: float
```

**Node Functions:**


```python
async def normalize_claim(state: AgentState) -> AgentState:
    """Strip HTML, lowercase, remove stop words, generate hash"""
    normalizer = TextNormalizer()
    normalized = normalizer.normalize(state['claim'])
    metadata = MetadataExtractor().extract(state['claim'])
    language = LanguageDetector().detect(state['claim'])
    claim_hash = hashlib.sha256(normalized.encode()).hexdigest()[:32]
    
    return {
        **state,
        'normalized_claim': normalized,
        'claim_hash': claim_hash,
        'metadata': metadata,
        'language': language
    }

async def analyze_claim_domain(state: AgentState) -> AgentState:
    """Use LLM to classify claim domain"""
    prompt = f"Classify this claim into one domain: health, politics, science, or general.\nClaim: {state['claim']}"
    response = await invoke_bedrock(prompt, "claude-3-haiku")
    domain = response['content'][0]['text'].strip().lower()
    
    return {**state, 'domain': domain}

async def select_agents(state: AgentState) -> AgentState:
    """Select agents based on domain"""
    domain_mapping = {
        'health': ['research', 'scientific', 'news', 'sentiment'],
        'politics': ['news', 'social_media', 'sentiment', 'research'],
        'science': ['scientific', 'research', 'news', 'sentiment'],
        'general': ['research', 'news', 'social_media', 'sentiment', 'scraper']
    }
    selected = domain_mapping.get(state['domain'], ['research', 'news', 'sentiment'])
    
    return {**state, 'selected_agents': selected}

async def execute_agents(state: AgentState) -> AgentState:
    """Execute all selected agents in parallel with timeout"""
    agents = {
        'research': ResearchAgent(),
        'news': NewsAgent(),
        'scientific': ScientificAgent(),
        'social_media': SocialMediaAgent(),
        'sentiment': SentimentAgent(),
        'scraper': ScraperAgent()
    }
    
    tasks = [
        agents[name].investigate(state['claim'], state['metadata'])
        for name in state['selected_agents']
        if name in agents
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    agent_results = [r for r in results if not isinstance(r, Exception)]
    
    return {**state, 'agent_results': agent_results}

async def aggregate_evidence(state: AgentState) -> AgentState:
    """Deduplicate sources and calculate evidence summary"""
    aggregator = EvidenceAggregator()
    deduplicated = aggregator.deduplicate_sources(state['agent_results'])
    summary = aggregator.calculate_summary(deduplicated)
    
    return {
        **state,
        'deduplicated_sources': deduplicated,
        'evidence_summary': summary
    }

async def calculate_credibility(state: AgentState) -> AgentState:
    """Calculate credibility score using weighted formula"""
    scorer = CredibilityScorer()
    score, category, confidence = scorer.calculate(
        state['agent_results'],
        state['deduplicated_sources'],
        state['evidence_summary']
    )
    
    return {
        **state,
        'credibility_score': score,
        'category': category,
        'confidence': confidence
    }

async def generate_report(state: AgentState) -> AgentState:
    """Generate final report with LLM recommendation"""
    generator = ReportGenerator()
    report = await generator.generate(
        state['claim'],
        state['credibility_score'],
        state['category'],
        state['agent_results'],
        state['deduplicated_sources'],
        state['evidence_summary']
    )
    
    return {**state, 'final_report': report}
```

**Graph Construction:**
```python
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("normalize", normalize_claim)
workflow.add_node("analyze", analyze_claim_domain)
workflow.add_node("select", select_agents)
workflow.add_node("execute", execute_agents)
workflow.add_node("aggregate", aggregate_evidence)
workflow.add_node("score", calculate_credibility)
workflow.add_node("report", generate_report)

# Add edges
workflow.set_entry_point("normalize")
workflow.add_edge("normalize", "analyze")
workflow.add_edge("analyze", "select")
workflow.add_edge("select", "execute")
workflow.add_edge("execute", "aggregate")
workflow.add_edge("aggregate", "score")
workflow.add_edge("score", "report")
workflow.set_finish_point("report")

manager = workflow.compile()
```

### 3. Credibility Scoring Algorithm

**Purpose:** Calculate a 0-100 credibility score using weighted formula

**Formula:**
```
Credibility Score = (Evidence Quality × 0.4) + (Agent Consensus × 0.3) + (Source Reliability × 0.3)
```

**Component Calculations:**


**1. Evidence Quality (40%)**
```python
def calculate_evidence_quality(sources: List[Dict]) -> float:
    """Weight sources by tier and stance"""
    tier_weights = {'tier_1': 1.0, 'tier_2': 0.7, 'tier_3': 0.4, 'tier_4': 0.2}
    
    supporting_score = sum(
        tier_weights.get(s['credibility_tier'], 0.2)
        for s in sources if s['stance'] == 'supporting'
    )
    contradicting_score = sum(
        tier_weights.get(s['credibility_tier'], 0.2)
        for s in sources if s['stance'] == 'contradicting'
    )
    
    total_weight = supporting_score + contradicting_score
    if total_weight == 0:
        return 50.0  # neutral when no evidence
    
    # Higher supporting score = higher credibility
    return (supporting_score / total_weight) * 100
```

**2. Agent Consensus (30%)**
```python
def calculate_agent_consensus(agent_results: List[Dict]) -> float:
    """Calculate percentage of agents with matching verdicts"""
    verdicts = [r['verdict'] for r in agent_results if r['verdict'] != 'insufficient']
    
    if not verdicts:
        return 50.0  # neutral when no verdicts
    
    # Count most common verdict
    verdict_counts = {}
    for v in verdicts:
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
    
    max_count = max(verdict_counts.values())
    consensus_pct = (max_count / len(verdicts)) * 100
    
    # If most common verdict is 'supporting', high consensus = high score
    # If most common verdict is 'contradicting', high consensus = low score
    most_common = max(verdict_counts, key=verdict_counts.get)
    
    if most_common == 'supporting':
        return consensus_pct
    elif most_common == 'contradicting':
        return 100 - consensus_pct
    else:  # neutral
        return 50.0
```

**3. Source Reliability (30%)**
```python
def calculate_source_reliability(sources: List[Dict]) -> float:
    """Average credibility scores of all sources"""
    if not sources:
        return 50.0
    
    scores = [s['credibility_score'] * 100 for s in sources]
    return sum(scores) / len(scores)
```

**Confidence Penalty:**
```python
def apply_confidence_penalty(score: float, agent_results: List[Dict]) -> float:
    """Reduce score if agent confidence is low"""
    confidences = [r['confidence'] for r in agent_results if r['confidence'] > 0]
    
    if not confidences:
        return score * 0.5  # 50% penalty if no confidence
    
    avg_confidence = sum(confidences) / len(confidences)
    
    if avg_confidence < 0.5:
        penalty = 1 - (0.5 - avg_confidence)  # 0-50% penalty
        return score * penalty
    
    return score
```

**Category Mapping:**
```python
def map_score_to_category(score: int) -> str:
    if score >= 85:
        return "Verified True"
    elif score >= 70:
        return "Likely True"
    elif score >= 60:
        return "Uncertain"
    elif score >= 40:
        return "Likely False"
    else:
        return "Verified False"
```

**Confidence Level:**
```python
def calculate_confidence_level(agent_results: List[Dict], sources: List[Dict]) -> str:
    confidences = [r['confidence'] for r in agent_results if r['confidence'] > 0]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    
    source_count = len(sources)
    
    if avg_confidence >= 0.8 and source_count >= 30:
        return "High"
    elif avg_confidence >= 0.6 and source_count >= 15:
        return "Medium"
    else:
        return "Low"
```

### 4. Evidence Aggregator

**Purpose:** Deduplicate sources and calculate evidence statistics

**Deduplication Algorithm:**
```python
def deduplicate_sources(agent_results: List[Dict]) -> List[Dict]:
    """Remove duplicate sources by normalized URL"""
    seen_urls = set()
    unique_sources = []
    
    for result in agent_results:
        for source in result.get('sources', []):
            # Normalize URL (remove query params, fragments, trailing slash)
            url = source['url']
            normalized_url = normalize_url(url)
            
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_sources.append(source)
    
    return unique_sources

def normalize_url(url: str) -> str:
    """Normalize URL for deduplication"""
    from urllib.parse import urlparse, urlunparse
    
    parsed = urlparse(url)
    # Remove query params and fragment
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc.lower(),
        parsed.path.rstrip('/'),
        '', '', ''
    ))
    return normalized
```

**Evidence Summary:**
```python
def calculate_summary(sources: List[Dict]) -> Dict[str, int]:
    """Count sources by stance"""
    summary = {
        'supporting': 0,
        'contradicting': 0,
        'neutral': 0
    }
    
    for source in sources:
        stance = source.get('stance', 'neutral')
        summary[stance] = summary.get(stance, 0) + 1
    
    return summary
```

**Agent Coverage:**
```python
def calculate_agent_coverage(agent_results: List[Dict]) -> Dict[str, Any]:
    """Calculate agent participation statistics"""
    total_agents = len(agent_results)
    successful_agents = len([r for r in agent_results if r['verdict'] != 'insufficient'])
    failed_agents = total_agents - successful_agents
    
    return {
        'total': total_agents,
        'successful': successful_agents,
        'failed': failed_agents,
        'success_rate': (successful_agents / total_agents * 100) if total_agents > 0 else 0
    }
```

### 5. Report Generator

**Purpose:** Format final verification report with LLM-generated recommendation


**Report Structure:**
```python
{
    "id": "uuid",
    "credibility_score": 75,
    "category": "Likely True",
    "confidence": "Medium",
    "sources_consulted": 42,
    "agent_consensus": "Strong consensus (83%)",
    "evidence_summary": {
        "supporting": 28,
        "contradicting": 10,
        "neutral": 4
    },
    "sources": [...],  # Deduplicated, sorted by credibility
    "agent_verdicts": {
        "research": {...},
        "news": {...},
        "scientific": {...},
        "social_media": {...},
        "sentiment": {...}
    },
    "limitations": [
        "Limited social media data due to API rate limits",
        "No fact-checker sources available"
    ],
    "recommendation": "LLM-generated paragraph...",
    "processing_time": 4.23,
    "created_at": "2026-02-28T12:00:00Z"
}
```

**Limitation Auto-Generation:**
```python
def generate_limitations(agent_results: List[Dict], sources: List[Dict]) -> List[str]:
    """Automatically generate limitation notes"""
    limitations = []
    
    # Check source count
    if len(sources) < 30:
        limitations.append(f"Only {len(sources)} sources consulted (target: 30-60)")
    
    # Check failed agents
    failed = [r['agent'] for r in agent_results if r['verdict'] == 'insufficient']
    if failed:
        limitations.append(f"Agents failed: {', '.join(failed)}")
    
    # Check low confidence
    confidences = [r['confidence'] for r in agent_results if r['confidence'] > 0]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0
    if avg_conf < 0.5:
        limitations.append(f"Low agent confidence (avg: {avg_conf:.2f})")
    
    # Check missing source types
    source_types = set(s['source_type'] for s in sources)
    if 'fact_checker' not in source_types:
        limitations.append("No fact-checker sources available")
    
    return limitations
```

**LLM Recommendation:**
```python
async def generate_recommendation(
    claim: str,
    score: int,
    category: str,
    evidence_summary: Dict[str, int]
) -> str:
    """Generate recommendation using LLM"""
    prompt = f"""
Based on the verification results, provide a brief recommendation (2-3 sentences) for users.

Claim: {claim}
Credibility Score: {score}/100
Category: {category}
Evidence: {evidence_summary['supporting']} supporting, {evidence_summary['contradicting']} contradicting

Focus on:
1. Whether the claim should be trusted
2. What additional verification might be needed
3. Any important caveats
"""
    
    response = await invoke_bedrock(prompt, "claude-3-haiku")
    return response['content'][0]['text'].strip()
```

### 6. API Routes Implementation

**Authentication Routes:**
```typescript
// apps/api-gateway/src/routes/auth.routes.ts
import { Router } from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { prisma } from '../config/database';
import { redis } from '../config/redis';

const router = Router();

router.post('/register', async (req, res) => {
    const { email, password } = req.body;
    
    // Validate input
    if (!email || !password) {
        return res.status(400).json({ error: 'Email and password required' });
    }
    
    // Check if user exists
    const existing = await prisma.user.findUnique({ where: { email } });
    if (existing) {
        return res.status(409).json({ error: 'Email already registered' });
    }
    
    // Hash password
    const passwordHash = await bcrypt.hash(password, 10);
    
    // Create user
    const user = await prisma.user.create({
        data: { email, passwordHash, subscriptionTier: 'free' }
    });
    
    res.status(201).json({
        message: 'Registration successful',
        user: { id: user.id, email: user.email, tier: user.subscriptionTier }
    });
});

router.post('/login', async (req, res) => {
    const { email, password } = req.body;
    
    // Find user
    const user = await prisma.user.findUnique({ where: { email } });
    if (!user) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    // Verify password
    const valid = await bcrypt.compare(password, user.passwordHash);
    if (!valid) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    // Generate tokens
    const accessToken = jwt.sign(
        { sub: user.id, email: user.email, tier: user.subscriptionTier },
        process.env.JWT_SECRET!,
        { expiresIn: '15m' }
    );
    
    const refreshToken = jwt.sign(
        { sub: user.id, type: 'refresh' },
        process.env.JWT_SECRET!,
        { expiresIn: '7d' }
    );
    
    res.json({
        accessToken,
        refreshToken,
        user: { id: user.id, email: user.email, tier: user.subscriptionTier }
    });
});

router.post('/refresh', async (req, res) => {
    const { refreshToken } = req.body;
    
    try {
        const payload = jwt.verify(refreshToken, process.env.JWT_SECRET!) as any;
        
        if (payload.type !== 'refresh') {
            return res.status(401).json({ error: 'Invalid token type' });
        }
        
        // Check if token is revoked
        const revoked = await redis.get(`revoked:${refreshToken}`);
        if (revoked) {
            return res.status(401).json({ error: 'Token revoked' });
        }
        
        // Get user
        const user = await prisma.user.findUnique({ where: { id: payload.sub } });
        if (!user) {
            return res.status(401).json({ error: 'User not found' });
        }
        
        // Generate new access token
        const accessToken = jwt.sign(
            { sub: user.id, email: user.email, tier: user.subscriptionTier },
            process.env.JWT_SECRET!,
            { expiresIn: '15m' }
        );
        
        res.json({ accessToken });
    } catch (err) {
        res.status(401).json({ error: 'Invalid token' });
    }
});

router.post('/logout', async (req, res) => {
    const { refreshToken } = req.body;
    
    // Revoke refresh token
    await redis.setex(`revoked:${refreshToken}`, 7 * 24 * 60 * 60, '1');
    
    res.json({ message: 'Logged out successfully' });
});

export default router;
```

**Verification Routes:**
```typescript
// apps/api-gateway/src/routes/verify.routes.ts
import { Router } from 'express';
import { authMiddleware, optionalAuth } from '../middleware/auth.middleware';
import { VerificationService } from '../services/VerificationService';

const router = Router();
const verificationService = new VerificationService();

router.post('/', optionalAuth, async (req, res) => {
    try {
        const { content, type, source } = req.body;
        const userId = req.user?.id ?? 'anonymous';
        
        // Validate input
        if (!content || !type) {
            return res.status(400).json({ error: 'Content and type required' });
        }
        
        // Verify claim
        const result = await verificationService.verify(content, type, source ?? 'api', userId);
        
        res.json(result);
    } catch (err: any) {
        res.status(500).json({ error: err.message });
    }
});

router.get('/presigned-url', authMiddleware, async (req, res) => {
    try {
        const { filename, contentType } = req.query;
        
        if (!filename || !contentType) {
            return res.status(400).json({ error: 'Filename and contentType required' });
        }
        
        // Generate presigned URL
        const { getSignedUrl } = await import('@aws-sdk/s3-request-presigner');
        const { S3Client, PutObjectCommand } = await import('@aws-sdk/client-s3');
        
        const s3 = new S3Client({ region: process.env.AWS_REGION });
        const key = `uploads/${req.user!.id}/${Date.now()}-${filename}`;
        
        const command = new PutObjectCommand({
            Bucket: process.env.S3_MEDIA_BUCKET,
            Key: key,
            ContentType: contentType as string
        });
        
        const url = await getSignedUrl(s3, command, { expiresIn: 900 }); // 15 minutes
        
        res.json({ url, key });
    } catch (err: any) {
        res.status(500).json({ error: err.message });
    }
});

export default router;
```

**History Routes:**
```typescript
// apps/api-gateway/src/routes/history.routes.ts
import { Router } from 'express';
import { authMiddleware } from '../middleware/auth.middleware';
import { VerificationService } from '../services/VerificationService';

const router = Router();
const verificationService = new VerificationService();

router.get('/', authMiddleware, async (req, res) => {
    try {
        const page = parseInt(req.query.page as string) || 1;
        const limit = parseInt(req.query.limit as string) || 20;
        
        const result = await verificationService.getHistory(req.user!.id, page, limit);
        
        res.json(result);
    } catch (err: any) {
        res.status(500).json({ error: err.message });
    }
});

router.get('/:id', authMiddleware, async (req, res) => {
    try {
        const verification = await verificationService.getById(req.params.id);
        
        if (!verification) {
            return res.status(404).json({ error: 'Verification not found' });
        }
        
        if (verification.userId !== req.user!.id) {
            return res.status(403).json({ error: 'Access denied' });
        }
        
        res.json(verification);
    } catch (err: any) {
        res.status(500).json({ error: err.message });
    }
});

export default router;
```

### 7. Rate Limiting

**Purpose:** Prevent abuse with tier-based rate limiting


**Implementation:**
```typescript
// apps/api-gateway/src/middleware/rateLimit.middleware.ts
import { Request, Response, NextFunction } from 'express';
import { redis } from '../config/redis';

const RATE_LIMITS = {
    public: { requests: 10, window: 60 },        // 10 req/min
    free: { requests: 100, window: 86400 },      // 100 req/day
    pro: { requests: 5000, window: 86400 },      // 5000 req/day
    enterprise: { requests: -1, window: 0 }      // unlimited
};

export async function rateLimitMiddleware(req: Request, res: Response, next: NextFunction) {
    try {
        const tier = req.user?.tier ?? 'public';
        const userId = req.user?.id ?? req.ip;
        
        const limit = RATE_LIMITS[tier as keyof typeof RATE_LIMITS];
        
        // Enterprise has no limits
        if (limit.requests === -1) {
            return next();
        }
        
        const key = `ratelimit:${tier}:${userId}`;
        const current = await redis.get(key);
        
        if (current && parseInt(current) >= limit.requests) {
            return res.status(429).json({
                error: 'Rate limit exceeded',
                limit: limit.requests,
                window: limit.window,
                retryAfter: await redis.ttl(key)
            });
        }
        
        // Increment counter
        const count = await redis.incr(key);
        if (count === 1) {
            await redis.expire(key, limit.window);
        }
        
        // Add rate limit headers
        res.setHeader('X-RateLimit-Limit', limit.requests);
        res.setHeader('X-RateLimit-Remaining', Math.max(0, limit.requests - count));
        res.setHeader('X-RateLimit-Reset', Date.now() + (limit.window * 1000));
        
        next();
    } catch (err) {
        // If rate limiting fails, allow request (fail open)
        next();
    }
}
```

## Data Models

### AgentState (LangGraph)
```python
class AgentState(TypedDict):
    # Input
    claim: str
    claim_type: str
    source: str
    user_id: str
    
    # Normalization
    normalized_claim: str
    claim_hash: str
    metadata: Dict[str, Any]
    language: str
    
    # Analysis
    domain: str
    selected_agents: List[str]
    
    # Agent Results
    agent_results: List[Dict[str, Any]]
    
    # Aggregation
    all_sources: List[Dict[str, Any]]
    deduplicated_sources: List[Dict[str, Any]]
    evidence_summary: Dict[str, int]
    
    # Scoring
    credibility_score: int
    category: str
    confidence: str
    
    # Report
    final_report: Dict[str, Any]
    processing_time: float
```

### AgentResult
```python
{
    "agent": str,                    # Agent name
    "verdict": str,                  # supporting/contradicting/neutral/insufficient
    "confidence": float,             # 0.0-1.0
    "summary": str,                  # Brief summary of findings
    "sources": List[Source],         # Sources consulted
    "evidence": {                    # Evidence counts
        "supporting": int,
        "contradicting": int,
        "neutral": int
    },
    "error": Optional[str]           # Error message if failed
}
```

### Source
```python
{
    "url": str,
    "title": str,
    "excerpt": str,                  # Max 300 chars
    "credibility_tier": str,         # tier_1/tier_2/tier_3/tier_4
    "credibility_score": float,      # 0.0-1.0
    "stance": str,                   # supporting/contradicting/neutral
    "source_type": str,              # news/academic/social/fact_checker/general
    "published_at": Optional[str]    # ISO 8601 timestamp
}
```

### VerificationResult
```typescript
{
    id: string;
    credibility_score: number;       // 0-100
    category: string;                // Verified True/Likely True/Uncertain/Likely False/Verified False
    confidence: string;              // High/Medium/Low
    sources_consulted: number;
    agent_consensus: string;         // e.g., "Strong consensus (83%)"
    evidence_summary: {
        supporting: number;
        contradicting: number;
        neutral: number;
    };
    sources: Source[];
    agent_verdicts: Record<string, AgentResult>;
    limitations: string[];
    recommendation: string;
    processing_time: number;         // seconds
    cached: boolean;
    cache_tier?: string;             // redis/dynamodb/cloudfront
    created_at: string;              // ISO 8601
}
```

### Database Schema (Prisma)
```prisma
model User {
  id                String   @id @default(uuid())
  email             String   @unique
  passwordHash      String
  subscriptionTier  String   @default("free")  // free/pro/enterprise
  createdAt         DateTime @default(now())
  verifications     Verification[]
}

model Verification {
  id                String   @id @default(uuid())
  claimHash         String   @db.VarChar(32)
  claimText         String   @db.Text
  claimType         String   @db.VarChar(20)
  credibilityScore  Int
  category          String   @db.VarChar(50)
  confidence        String   @db.VarChar(20)
  sourcesConsulted  Int
  agentConsensus    String?  @db.VarChar(100)
  evidenceSummary   Json
  sources           Json
  agentVerdicts     Json
  limitations       String[]
  recommendation    String?  @db.Text
  processingTime    Float?
  cached            Boolean  @default(false)
  sourcePlatform    String   @db.VarChar(50)
  userId            String?
  user              User?    @relation(fields: [userId], references: [id])
  createdAt         DateTime @default(now())
  
  @@index([claimHash])
  @@index([userId])
  @@index([createdAt])
}
```

### DynamoDB Schema
```typescript
{
    TableName: 'zerotrust-claim-verifications',
    KeySchema: [
        { AttributeName: 'claim_hash', KeyType: 'HASH' }
    ],
    AttributeDefinitions: [
        { AttributeName: 'claim_hash', AttributeType: 'S' }
    ],
    BillingMode: 'PAY_PER_REQUEST',
    TimeToLiveSpecification: {
        Enabled: true,
        AttributeName: 'ttl'
    }
}
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Bedrock Integration with Fallback Chain

*For any* agent LLM request, when AWS Bedrock is invoked, the system should either return a valid response from one of the models in the fallback chain (Claude 3.5 Sonnet → Haiku → Mistral Large) or return an error after exhausting all options.

**Validates: Requirements 1.2, 1.3, 1.4**

### Property 2: Agent Source Consultation

*For any* claim verification, each selected agent should consult its configured external APIs and return between 0 and its maximum source count (Research: 10, News: 20, Social Media: 15), with the total sources consulted tracked correctly.

**Validates: Requirements 2.1, 2.2, 2.3, 2.6**

### Property 3: External API Error Resilience

*For any* external API failure during verification, the system should log the error, continue processing with remaining sources, and not fail the entire verification.

**Validates: Requirements 2.4, 14.1**

### Property 4: Manager Agent Workflow Completeness

*For any* verification request, the Manager Agent should execute all workflow steps in order (normalize → analyze → select → execute → aggregate → score → report) and produce a complete report even if individual agents fail.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

### Property 5: Credibility Score Formula Correctness

*For any* set of agent results and sources, the credibility score should be calculated as: (Evidence Quality × 0.4) + (Agent Consensus × 0.3) + (Source Reliability × 0.3), with each component correctly weighted and the final score in the range [0, 100].

**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

### Property 6: Score-to-Category Mapping

*For any* credibility score in the range [0, 100], the system should map it to exactly one category: "Verified False" (0-39), "Likely False" (40-59), "Uncertain" (60-69), "Likely True" (70-84), or "Verified True" (85-100).

**Validates: Requirements 4.5, 4.6, 4.7, 4.8, 4.9**

### Property 7: Confidence Penalty Application

*For any* agent result set where the average confidence is below 0.5, the system should apply a proportional penalty to the credibility score, reducing it by up to 50%.

**Validates: Requirements 4.10**

### Property 8: Source Deduplication by URL

*For any* list of sources from multiple agents, the evidence aggregator should deduplicate sources by normalized URL (ignoring query params, fragments, and case), ensuring each unique source appears exactly once in the final list.

**Validates: Requirements 5.1**

### Property 9: Evidence Stance Counting

*For any* deduplicated source list, the evidence summary should correctly count sources by stance (supporting/contradicting/neutral), with the sum of all stance counts equaling the total number of sources.

**Validates: Requirements 5.2**

### Property 10: Source Sorting by Credibility

*For any* deduplicated source list, the sources should be sorted in descending order by credibility_score, with higher-credibility sources appearing first.

**Validates: Requirements 5.3**

### Property 11: Agent Verdict Preservation

*For any* verification, all agent verdicts with their confidence scores should be preserved in the final report without loss or modification during aggregation.

**Validates: Requirements 5.5**

### Property 12: Report Schema Completeness

*For any* generated report, it should contain all required fields: credibility_score, category, confidence, sources_consulted, agent_consensus, evidence_summary, sources, agent_verdicts, limitations, recommendation, and processing_time.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.7**

### Property 13: Report Serialization Round Trip

*For any* verification result, serializing it to JSON and then deserializing should produce an equivalent object with all fields preserved.

**Validates: Requirements 6.8**

### Property 14: Limitation Auto-Generation

*For any* verification with fewer than 30 sources consulted, the report should include a limitation note stating the actual number of sources consulted.

**Validates: Requirements 2.7, 6.6**

### Property 15: Authentication Token Round Trip

*For any* valid user credentials, logging in should produce JWT tokens that can be used to access protected endpoints, and logging out should revoke those tokens, preventing further access.

**Validates: Requirements 7.4, 7.6**

### Property 16: Verification API Request Validation

*For any* POST request to /api/v1/verify, the API Gateway should validate that content and type fields are present, returning 400 if missing, or forward to Verification Engine if valid.

**Validates: Requirements 7.1, 7.7**

### Property 17: History Pagination Correctness

*For any* user with N verifications, requesting page P with limit L should return exactly min(L, N - (P-1)*L) items, with correct total count and page calculations.

**Validates: Requirements 7.2**

### Property 18: Rate Limiting by Tier

*For any* user tier (public: 10/min, free: 100/day, pro: 5000/day, enterprise: unlimited), the system should enforce the correct rate limit, returning 429 when exceeded and allowing requests within the limit.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7**

### Property 19: S3 Presigned URL Generation

*For any* authenticated media upload request, the API Gateway should generate a presigned S3 URL with 15-minute expiration that allows uploading the specified file type.

**Validates: Requirements 9.1, 9.2**

### Property 20: Media File Validation

*For any* media upload request, the system should enforce file size limits (10MB for images, 100MB for videos) and validate file types (JPEG/PNG/GIF for images, MP4/MOV for videos), rejecting invalid uploads.

**Validates: Requirements 9.6, 9.7**

### Property 21: Cache Tier Waterfall

*For any* claim verification, the system should check caches in order (Redis → DynamoDB → PostgreSQL), returning from the first hit, and promoting lower-tier hits to higher tiers asynchronously.

**Validates: Requirements 10.1, 10.2, 10.3**

### Property 22: Cache Fallback Resilience

*For any* cache tier failure (Redis, DynamoDB, or PostgreSQL), the system should fall back to the next tier without failing the entire verification request.

**Validates: Requirements 10.7, 14.4**

### Property 23: Text Normalization Idempotence

*For any* claim text, normalizing it twice should produce the same result as normalizing it once, and the generated Claim_Hash should be identical for equivalent normalized text.

**Validates: Requirements 13.1, 13.2, 13.3, 13.4, 13.7**

### Property 24: Metadata Extraction Completeness

*For any* claim text containing URLs, statistics, or quotes, the metadata extractor should identify and extract all such elements into the metadata dictionary.

**Validates: Requirements 13.5**

### Property 25: Language Detection Accuracy

*For any* claim text in a supported language, the language detector should return a valid ISO 639-1 language code.

**Validates: Requirements 13.6**

### Property 26: Agent Timeout Enforcement

*For any* agent execution, if the agent does not complete within 10 seconds, the Manager Agent should timeout the agent and include a timeout note in the report.

**Validates: Requirements 14.2**

### Property 27: Database Retry with Exponential Backoff

*For any* database connection failure, the system should retry up to 3 times with exponential backoff, and return a 503 error with descriptive message if all retries fail.

**Validates: Requirements 14.5, 14.6**

### Property 28: Circuit Breaker for External Dependencies

*For any* external dependency (API, database, cache) that fails repeatedly, the circuit breaker should open after a threshold of failures, preventing further requests for a cooldown period.

**Validates: Requirements 14.7**

### Property 29: Parallel Agent Execution

*For any* set of selected agents, the Manager Agent should execute all agents concurrently (not sequentially), with all agents starting within a short time window of each other.

**Validates: Requirements 15.3**

### Property 30: Cache Compression Round Trip

*For any* verification result, compressing it for cache storage and then decompressing should produce an equivalent object with all fields preserved.

**Validates: Requirements 15.5**


## Error Handling

### Error Categories

**1. External API Errors**
- Network timeouts
- Rate limiting (429)
- Authentication failures (401, 403)
- Service unavailable (503)
- Invalid responses

**Strategy:** Log error, continue with other sources, include limitation note in report

**2. AWS Service Errors**
- Bedrock throttling
- S3 access denied
- DynamoDB provisioned throughput exceeded
- Secrets Manager unavailable

**Strategy:** Implement fallback chains, retry with exponential backoff, graceful degradation

**3. Database Errors**
- Connection failures
- Query timeouts
- Constraint violations
- Deadlocks

**Strategy:** Retry with exponential backoff (max 3 attempts), connection pooling, circuit breaker

**4. Validation Errors**
- Missing required fields
- Invalid data types
- Out-of-range values
- Malformed URLs

**Strategy:** Return 400 with descriptive error message, validate early in request pipeline

**5. Authentication Errors**
- Invalid credentials
- Expired tokens
- Revoked tokens
- Missing authorization header

**Strategy:** Return 401 with clear error message, implement token refresh flow

**6. Rate Limiting Errors**
- Quota exceeded
- Too many requests

**Strategy:** Return 429 with Retry-After header, track limits in Redis

### Error Response Format

```typescript
{
    "error": string,           // Human-readable error message
    "code": string,            // Machine-readable error code
    "details"?: any,           // Additional error context
    "timestamp": string,       // ISO 8601 timestamp
    "request_id": string       // Unique request identifier for debugging
}
```

### Retry Strategy

**Exponential Backoff Formula:**
```
delay = base_delay * (2 ^ attempt) + random_jitter
```

**Configuration:**
- Base delay: 100ms
- Max attempts: 3
- Max delay: 5000ms
- Jitter: ±25%

**Example:**
- Attempt 1: 100ms + jitter
- Attempt 2: 200ms + jitter
- Attempt 3: 400ms + jitter

### Circuit Breaker

**States:**
- **Closed:** Normal operation, requests pass through
- **Open:** Too many failures, requests fail fast
- **Half-Open:** Testing if service recovered

**Configuration:**
- Failure threshold: 5 failures in 60 seconds
- Open duration: 30 seconds
- Half-open test requests: 3

**Implementation:**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'closed'
    
    async def call(self, func, *args, **kwargs):
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'half-open'
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = await func(*args, **kwargs)
            if self.state == 'half-open':
                self.state = 'closed'
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = 'open'
            raise e
```

### Logging Strategy

**Log Levels:**
- **ERROR:** System errors requiring immediate attention
- **WARN:** Degraded functionality, fallbacks activated
- **INFO:** Normal operations, verification requests
- **DEBUG:** Detailed execution traces (development only)

**Structured Logging Format:**
```json
{
    "timestamp": "2026-02-28T12:00:00Z",
    "level": "ERROR",
    "service": "verification-engine",
    "message": "External API failed",
    "context": {
        "agent": "news",
        "api": "newsapi",
        "error": "Rate limit exceeded",
        "claim_hash": "abc123..."
    },
    "request_id": "req-xyz789"
}
```

## Testing Strategy

### Testing Approach

The ZeroTRUST system requires a dual testing approach combining unit tests for specific examples and property-based tests for universal correctness guarantees.

**Unit Tests:**
- Specific examples and edge cases
- Integration points between components
- Error conditions and boundary values
- Authentication flows
- API endpoint behavior

**Property-Based Tests:**
- Universal properties across all inputs
- Comprehensive input coverage through randomization
- Invariants and mathematical properties
- Round-trip properties (serialization, normalization)
- Minimum 100 iterations per property test

### Test Coverage Goals

**Target: >70% code coverage across all services**

**Priority 1 (Must Have):**
- Authentication flows: 100%
- Verification workflow: 90%
- Credibility scoring: 100%
- Evidence aggregation: 100%
- Cache tier waterfall: 90%

**Priority 2 (Should Have):**
- Individual agents: 80%
- API routes: 85%
- Rate limiting: 90%
- Error handling: 75%

**Priority 3 (Nice to Have):**
- Normalization layer: 80%
- Report generation: 75%
- Media upload flow: 70%

### Property-Based Testing Framework

**Python (Verification Engine):**
- Framework: Hypothesis
- Configuration: 100 iterations minimum
- Strategies: Custom generators for claims, sources, agent results

**TypeScript (API Gateway):**
- Framework: fast-check
- Configuration: 100 iterations minimum
- Strategies: Custom arbitraries for requests, tokens, cache keys

### Test Organization

**Directory Structure:**
```
tests/
├── unit/
│   ├── agents/
│   │   ├── test_research_agent.py
│   │   ├── test_news_agent.py
│   │   └── ...
│   ├── services/
│   │   ├── test_credibility_scorer.py
│   │   ├── test_evidence_aggregator.py
│   │   └── test_report_generator.py
│   └── api/
│       ├── test_auth_routes.ts
│       ├── test_verify_routes.ts
│       └── test_history_routes.ts
├── property/
│   ├── test_credibility_scoring_properties.py
│   ├── test_evidence_aggregation_properties.py
│   ├── test_cache_waterfall_properties.ts
│   └── test_normalization_properties.py
├── integration/
│   ├── test_verification_flow.py
│   ├── test_auth_flow.ts
│   └── test_cache_tiers.ts
└── e2e/
    ├── test_claim_verification.spec.ts
    └── test_media_upload.spec.ts
```

### Property Test Examples

**Property 1: Credibility Score Formula**
```python
from hypothesis import given, strategies as st

@given(
    sources=st.lists(st.builds(Source), min_size=1, max_size=100),
    agent_results=st.lists(st.builds(AgentResult), min_size=1, max_size=6)
)
def test_credibility_score_in_range(sources, agent_results):
    """Property: Credibility score should always be in [0, 100]"""
    scorer = CredibilityScorer()
    score, _, _ = scorer.calculate(agent_results, sources, {})
    
    assert 0 <= score <= 100, f"Score {score} out of range"
```

**Property 2: Source Deduplication**
```python
@given(
    agent_results=st.lists(
        st.builds(AgentResult, sources=st.lists(st.builds(Source))),
        min_size=1,
        max_size=6
    )
)
def test_source_deduplication_removes_duplicates(agent_results):
    """Property: Deduplicated sources should have unique normalized URLs"""
    aggregator = EvidenceAggregator()
    deduplicated = aggregator.deduplicate_sources(agent_results)
    
    urls = [normalize_url(s['url']) for s in deduplicated]
    assert len(urls) == len(set(urls)), "Duplicate URLs found after deduplication"
```

**Property 3: Cache Tier Waterfall**
```typescript
import fc from 'fast-check';

test('Property: Cache waterfall should check tiers in order', async () => {
    await fc.assert(
        fc.asyncProperty(
            fc.string(),  // claim content
            fc.constantFrom('text', 'url'),  // claim type
            async (content, type) => {
                const service = new VerificationService();
                const key = buildCacheKey(content, type);
                
                // Clear all caches
                await clearAllCaches(key);
                
                // Mock verification result
                const mockResult = generateMockResult();
                mockVerificationEngine(mockResult);
                
                // First call should miss all caches
                const result1 = await service.verify(content, type, 'api', 'test-user');
                expect(result1.cached).toBe(false);
                
                // Second call should hit Redis (Tier 1)
                const result2 = await service.verify(content, type, 'api', 'test-user');
                expect(result2.cached).toBe(true);
                expect(result2.cache_tier).toBe('redis');
            }
        ),
        { numRuns: 100 }
    );
});
```

**Property 4: Text Normalization Idempotence**
```python
@given(st.text(min_size=1, max_size=1000))
def test_normalization_idempotence(text):
    """Property: Normalizing twice should equal normalizing once"""
    normalizer = TextNormalizer()
    
    normalized_once = normalizer.normalize(text)
    normalized_twice = normalizer.normalize(normalized_once)
    
    assert normalized_once == normalized_twice, "Normalization not idempotent"
```

**Property 5: Score-to-Category Mapping**
```python
@given(st.integers(min_value=0, max_value=100))
def test_score_category_mapping(score):
    """Property: Every score should map to exactly one category"""
    category = map_score_to_category(score)
    
    expected_categories = {
        range(0, 40): "Verified False",
        range(40, 60): "Likely False",
        range(60, 70): "Uncertain",
        range(70, 85): "Likely True",
        range(85, 101): "Verified True"
    }
    
    expected = next(cat for rng, cat in expected_categories.items() if score in rng)
    assert category == expected, f"Score {score} mapped to {category}, expected {expected}"
```

### Integration Test Examples

**Test: Complete Verification Flow**
```python
async def test_complete_verification_flow():
    """Integration test: End-to-end verification"""
    # Setup
    claim = "COVID-19 vaccines are safe and effective"
    
    # Execute
    manager = ManagerAgent()
    result = await manager.verify(claim, 'text', 'api', 'test-user')
    
    # Assert
    assert result['credibility_score'] >= 0
    assert result['credibility_score'] <= 100
    assert result['category'] in [
        "Verified False", "Likely False", "Uncertain",
        "Likely True", "Verified True"
    ]
    assert len(result['sources']) > 0
    assert len(result['agent_verdicts']) > 0
    assert 'recommendation' in result
```

**Test: Authentication Flow**
```typescript
describe('Authentication Flow', () => {
    it('should register, login, refresh, and logout', async () => {
        // Register
        const registerRes = await request(app)
            .post('/api/v1/auth/register')
            .send({ email: 'test@example.com', password: 'SecurePass123!' });
        expect(registerRes.status).toBe(201);
        
        // Login
        const loginRes = await request(app)
            .post('/api/v1/auth/login')
            .send({ email: 'test@example.com', password: 'SecurePass123!' });
        expect(loginRes.status).toBe(200);
        expect(loginRes.body).toHaveProperty('accessToken');
        expect(loginRes.body).toHaveProperty('refreshToken');
        
        const { accessToken, refreshToken } = loginRes.body;
        
        // Access protected route
        const historyRes = await request(app)
            .get('/api/v1/history')
            .set('Authorization', `Bearer ${accessToken}`);
        expect(historyRes.status).toBe(200);
        
        // Refresh token
        const refreshRes = await request(app)
            .post('/api/v1/auth/refresh')
            .send({ refreshToken });
        expect(refreshRes.status).toBe(200);
        expect(refreshRes.body).toHaveProperty('accessToken');
        
        // Logout
        const logoutRes = await request(app)
            .post('/api/v1/auth/logout')
            .send({ refreshToken });
        expect(logoutRes.status).toBe(200);
        
        // Verify token is revoked
        const revokedRes = await request(app)
            .post('/api/v1/auth/refresh')
            .send({ refreshToken });
        expect(revokedRes.status).toBe(401);
    });
});
```

### CI/CD Integration

**GitHub Actions Workflow:**
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          npm install
          cd apps/verification-engine && pip install -r requirements.txt
      
      - name: Run API Gateway tests
        run: |
          cd apps/api-gateway
          npm test -- --coverage
      
      - name: Run Verification Engine tests
        run: |
          cd apps/verification-engine
          pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./apps/api-gateway/coverage/lcov.info,./apps/verification-engine/coverage.xml
      
      - name: Check coverage threshold
        run: |
          # Fail if coverage < 70%
          npm run coverage:check
```

### Test Execution Commands

**Run all tests:**
```bash
# API Gateway
cd apps/api-gateway
npm test

# Verification Engine
cd apps/verification-engine
pytest

# E2E tests
npm run test:e2e
```

**Run property tests only:**
```bash
# Python
pytest tests/property/

# TypeScript
npm test -- --testPathPattern=property
```

**Run with coverage:**
```bash
# API Gateway
npm test -- --coverage

# Verification Engine
pytest --cov=src --cov-report=html
```

**Run specific test file:**
```bash
# Python
pytest tests/unit/services/test_credibility_scorer.py -v

# TypeScript
npm test -- test_auth_routes.ts
```

