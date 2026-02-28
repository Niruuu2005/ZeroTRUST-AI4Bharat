# ZeroTRUST — Prototype Run Guide
## IMPL-05: End-to-End Prototype Setup, Testing & Demo

**Series:** IMPL-05 of 05  
**Scope:** 🚧 PROTOTYPE — get the demo running step by step

---

## Table of Contents

1. [Prerequisites Checklist](#1-prerequisites-checklist)
2. [Option A: Run Entirely Local](#2-option-a-run-entirely-local)
3. [Option B: Local + AWS Bedrock](#3-option-b-local--aws-bedrock)
4. [Option C: Full AWS Prototype Deploy](#4-option-c-full-aws-prototype-deploy)
5. [Testing the Prototype](#5-testing-the-prototype)
6. [Known Prototype Limitations](#6-known-prototype-limitations)
7. [Demo Script (Hackathon Presentation)](#7-demo-script-hackathon-presentation)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Prerequisites Checklist

```
Software:
[✓] Node.js v20+ (node --version)
[✓] Python 3.11+ (python --version)
[✓] Docker 24+ + Docker Compose (docker --version)
[✓] AWS CLI v2 (aws --version)
[✓] Git

AWS:
[✓] AWS account with Bedrock access enabled in us-east-1
    (Console → Bedrock → Model access → Enable Claude 3.5, Mistral Large, Titan Embed)
[✓] AWS credentials configured (aws configure)

API Keys (at least ONE news API and Google Custom Search):
[✓] NewsAPI key — https://newsapi.org (free tier: 100 req/day)
[✓] Google Custom Search API key + Search Engine ID
    https://developers.google.com/custom-search/v1/overview
[~] Twitter Bearer token — optional, social media agent
[~] Reddit client ID + secret — optional
[~] PubMed API key — optional (scientific agent works without it, just slower)
```

---

## 2. Option A: Run Entirely Local

**Best for:** Quick demo without AWS costs. Uses mocked Bedrock responses unless you have AWS credentials.

```bash
# 1. Clone repo
git clone https://github.com/zerotrust-team/zerotrust-aws.git
cd zerotrust-aws

# 2. Create .env.local with your API keys (see IMPL-02 §1.4)
cp .env.local.example .env.local
# Edit .env.local and fill in your keys

# 3. (Optional) Download ML models for media analysis
#    If you skip this, media analysis returns "unavailable" — text/URL still works fine
mkdir -p models
# Place xception_deepfake_v2.h5 and efficientnet_b4_deepfake_v1.h5 here

# 4. Install dependencies for local tools
cd apps/api-gateway && npm install && cd ../..
cd apps/verification-engine && pip install -r requirements.txt && cd ../..

# 5. Run DB migrations locally (Prisma)
cd apps/api-gateway
DATABASE_URL="postgresql://zerotrust:devpassword@localhost:5432/zerotrust_dev" \
  npx prisma migrate deploy
cd ../..

# 6. Start everything
docker-compose up -d

# 7. Check health
curl http://localhost:3000/health   # → {"status":"healthy"}
curl http://localhost:8000/health   # → {"status":"healthy","service":"verification-engine"}

# 8. Open web portal
open http://localhost:5173
```

### 2.1 API Test (local)

```bash
# Test verification (text)
curl -s -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"COVID vaccines cause infertility","type":"text","source":"api"}' \
  | python -m json.tool

# Expected response shape:
# {
#   "id": "uuid",
#   "credibility_score": 12,
#   "category": "Verified False",
#   "confidence": "High",
#   "claim_type": "factual",
#   "sources_consulted": 34,
#   "agent_consensus": "Strong consensus (87%)",
#   "evidence_summary": {"supporting":2,"contradicting":28,"neutral":4},
#   "cached": false,
#   "processing_time": 4.2
# }
```

---

## 3. Option B: Local + AWS Bedrock

**Best for:** Real LLM quality with local data stores. ~$0.01–0.05 per verification.

```bash
# Add to .env.local:
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
BEDROCK_REGION=us-east-1

# If you have AWS CLI configured with a profile:
AWS_PROFILE=your_profile  # instead of key/secret

# Start services (Bedrock calls will now use real Claude 3.5)
docker-compose up -d

# Verify Bedrock is connected:
curl -s http://localhost:8000/health
# → {"status":"healthy","bedrock_connected":true}
```

**Estimated Bedrock costs per verification:**
| Scenario | Input tokens | Output tokens | Cost (Claude 3.5 Sonnet) |
|----------|-------------|---------------|--------------------------|
| Cache hit | 0 | 0 | $0.00 |
| Full verify (text) | ~8,000 | ~2,000 | ~$0.04 |
| Full verify (6 agents) | ~15,000 | ~4,000 | ~$0.08 |

---

## 4. Option C: Full AWS Prototype Deploy

**Best for:** Hackathon demo with public URL. Follow IMPL-02 from start.

### 4.1 Quick Sequence

```bash
# 1. Run infrastructure setup (IMPL-02 §3.1)
bash scripts/setup-vpc.sh        # Creates VPC, subnets, security groups

# 2. Provision managed services
bash scripts/setup-managed.sh   # Creates RDS, Redis, DynamoDB, S3 buckets, SQS

# 3. Store secrets in SSM
bash scripts/setup-ssm.sh       # Prompts for all API keys → stores in SSM

# 4. Run DB migrations
bash scripts/run-migrations.sh

# 5. Build & push Docker images to ECR
bash scripts/build-push.sh

# 6. Deploy ECS services
bash scripts/deploy-ecs.sh

# 7. Set up ALB + CloudFront
bash scripts/setup-edge.sh

# 8. Deploy web portal to S3
cd apps/web-portal && bash ../../scripts/deploy-web.sh

echo "✅ Prototype live at https://your-cloudfront-domain.cloudfront.net"
```

### 4.2 scripts/setup-ssm.sh

```bash
#!/bin/bash
set -e
REGION="us-east-1"

read -p "Database URL: " DB_URL
read -p "Redis URL: " REDIS_URL
read -p "NewsAPI Key: " NEWS_KEY
read -p "Google Search Key: " GOOGLE_KEY
read -p "Google CSE ID: " GOOGLE_CSE

aws ssm put-parameter --name /zerotrust/db-url --value "$DB_URL" \
  --type SecureString --region $REGION --overwrite
aws ssm put-parameter --name /zerotrust/redis-url --value "$REDIS_URL" \
  --type SecureString --region $REGION --overwrite
aws ssm put-parameter --name /zerotrust/jwt-secret --value "$(openssl rand -base64 48)" \
  --type SecureString --region $REGION --overwrite
aws ssm put-parameter --name /zerotrust/news-api-key --value "$NEWS_KEY" \
  --type SecureString --region $REGION --overwrite
aws ssm put-parameter --name /zerotrust/google-search-key --value "$GOOGLE_KEY" \
  --type SecureString --region $REGION --overwrite
aws ssm put-parameter --name /zerotrust/google-cse-id --value "$GOOGLE_CSE" \
  --type SecureString --region $REGION --overwrite

echo "✅ All secrets stored in SSM Parameter Store"
```

---

## 5. Testing the Prototype

### 5.1 Smoke Test: All Claim Types

```bash
BASE="http://localhost:3000"  # or your CloudFront URL

# Text verification
curl -s -X POST $BASE/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"The Earth is flat","type":"text","source":"api"}' | python -m json.tool

# URL verification
curl -s -X POST $BASE/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"https://www.naturalnews.com/some-fake-article","type":"url","source":"api"}' \
  | python -m json.tool

# Health check all services
curl http://localhost:3000/health
curl http://localhost:8000/health
curl http://localhost:8001/health

# Verify cache works (second request should return cached:true)
curl -s -X POST $BASE/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"The Earth is flat","type":"text","source":"api"}' \
  | python -m json.tool
# → cached: true, cache_tier: "redis"
```

### 5.2 Integration Test: 6 Agents

```python
# tests/test_agents.py — run locally
import asyncio
import httpx

CLAIMS = [
    # Health — triggers scientific agent
    {"content": "Vitamin C cures cancer", "type": "text"},
    # Politics — triggers news + sentiment agent
    {"content": "Joe Biden canceled student loans for everyone", "type": "text"},
    # Science
    {"content": "Climate change is a hoax invented by China", "type": "text"},
    # Statistical
    {"content": "India's GDP grew by 8.2% in 2024-25", "type": "text"},
    # Quote
    {"content": 'WHO said "vaccines are not necessary for healthy adults"', "type": "text"},
]

async def test_all():
    async with httpx.AsyncClient(timeout=40.0) as client:
        for claim in CLAIMS:
            r = await client.post("http://localhost:3000/api/v1/verify",
                                  json={**claim, "source": "api"})
            data = r.json()
            print(f"✅ Score: {data['credibility_score']:3d} | {data['category']:<20s} | {claim['content'][:60]}")

asyncio.run(test_all())
```

### 5.3 Cache Tier Validation

```bash
# Should hit Redis (Tier 1) on second call
for i in 1 2 3; do
  curl -s -X POST http://localhost:3000/api/v1/verify \
    -H "Content-Type: application/json" \
    -d '{"content":"vaccines cause autism","type":"text","source":"api"}' \
    | python -c "import sys,json; d=json.load(sys.stdin); print(f'cached={d[\"cached\"]} tier={d.get(\"cache_tier\",\"none\")}')"
done
# Output:
# cached=False tier=none
# cached=True  tier=redis
# cached=True  tier=redis
```

### 5.4 Load Test (k6 — validate prototype handles 50 concurrent users)

```bash
# Install k6: https://k6.io/docs/get-started/installation/

cat > /tmp/load-test.js <<'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';
export const options = {
  vus: 50, duration: '60s',
  thresholds: { http_req_duration: ['p(95)<5000'], http_req_failed: ['rate<0.05'] }
};
const claims = [
  'vaccines cause autism',
  'climate change is a hoax',
  'Modi declared emergency in India 2024',
  'WHO warns about new pandemic in 2025'
];
export default function () {
  const claim = claims[Math.floor(Math.random() * claims.length)];
  const res = http.post('http://localhost:3000/api/v1/verify',
    JSON.stringify({ content: claim, type: 'text', source: 'load-test' }),
    { headers: { 'Content-Type': 'application/json' } });
  check(res, { 'status 200': r => r.status === 200 });
  sleep(1);
}
EOF

k6 run /tmp/load-test.js
```

---

## 6. Known Prototype Limitations

| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| Single-AZ RDS | No HA during AZ failure | Acceptable for prototype demo |
| No GPU for media analysis | Deepfake detection is slower (~10s) | Use CPU TF model, reduce image size |
| NewsAPI free tier: 100 req/day | News agent hits rate limit | Cache aggressively, use GNews as fallback |
| Bedrock in us-east-1 only | N/A for prototype | Cross-region call from any ECS region |
| No custom domain | CloudFront *.cloudfront.net URL | Acceptable for prototype |
| No email verification | Users can register with fake email | Fine for hackathon |
| Browser extension: no HTTPS in dev | Extension CSP blocks localhost | Use `http://localhost:3000` host_permission |
| Neptune not seeded | Graph queries return empty | Seed with `scripts/seed-sources.py` |

---

## 7. Demo Script (Hackathon Presentation)

### 7.1 Opening Statement (30 seconds)

> "False information spreads 6× faster than truth. Traditional fact-checking takes 6–48 hours. ZeroTRUST does it in under 5 seconds, using 6 AI agents running in parallel against 30–60 real-world sources."

### 7.2 Live Demo Sequence (3 minutes)

**Demo 1 — High-confidence false claim (should score ~10):**
```
Content: "COVID-19 vaccines contain microchips for tracking"
Expected: Credibility Score ~8 | Category: Verified False
Show: 6 agent panel, Wikipedia/Reuters/CDC contradiction
```

**Demo 2 — True claim (should score ~85):**
```
Content: "India launched Chandrayaan-3 moon mission in 2023"
Expected: Credibility Score ~91 | Category: Verified True
Show: AP, NDTV, ISRO sources all confirming
```

**Demo 3 — Mixed/controversial (should score ~50):**
```
Content: "5G towers cause health problems"
Expected: Credibility Score ~35 | Category: Likely False
Show: Sentiment agent detecting manipulation, scientific consensus
```

**Demo 4 — Cache speed (pre-warm Demo 1 claim):**
```
Re-submit "COVID-19 vaccines contain microchips"
Expected: cached: true, cache_tier: "redis", processing_time: 0.08s
Show: "Previously verified, returned from cache in 80ms"
```

**Demo 5 — Browser extension:**
```
Navigate to a news article, select suspicious headline, right-click
→ "Verify with ZeroTRUST"
→ Overlay appears with score in 3 seconds
```

### 7.3 Closing Statement (30 seconds)

> "ZeroTRUST is built on 3 key innovations: 1) Multi-agent parallelism — 6 agents simultaneously, 3–5s for any claim. 2) 3-tier intelligent caching — 90% of requests served in under 500ms with zero AI cost. 3) Cross-format support — text, URLs, images, and videos, all in one unified pipeline."

---

## 8. Troubleshooting

### 8.1 Verification Engine fails to start (boto3 / Bedrock error)

```bash
# Check AWS credentials are accessible inside the container
docker-compose exec verification-engine \
  python -c "import boto3; c=boto3.client('bedrock-runtime','us-east-1'); print('OK')"

# If it fails, ensure .env.local has AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
# Or mount ~/.aws inside the container:
# volumes:
#   - ~/.aws:/home/zerotrust/.aws:ro
```

### 8.2 Redis connection refused

```bash
# Check Redis is running
docker-compose ps redis
docker-compose exec redis redis-cli ping   # → PONG

# If PONG but still error, check REDIS_URL format
# Should be: redis://redis:6379 (Docker service name, not localhost)
```

### 8.3 PostgreSQL migrations fail

```bash
# Run migrations manually
docker-compose exec api-gateway \
  npx prisma migrate deploy

# If schema changes were made, generate new client
docker-compose exec api-gateway \
  npx prisma generate
```

### 8.4 News Agent returns insufficient data (rate limited)

```bash
# Check NewsAPI quota
curl "https://newsapi.org/v2/everything?q=test&apiKey=$NEWS_API_KEY" | python -m json.tool
# Look for: "message": "rateLimited"

# Solution: add GNews as fallback
GNEWS_API_KEY=your_gnews_key  # in .env.local
# GNews free tier: 100 req/day — separate from NewsAPI
```

### 8.5 Browser Extension doesn't show overlay

```bash
# Check host_permissions in manifest.json includes your API URL
# For local dev, it should be: "http://localhost:3000/*"
# For deployed, it should be: "https://api.zerotrust.ai/*"

# Check content script is injected:
# Chrome → F12 → Console → check for ZeroTRUST errors
# Check background service worker:
# chrome://extensions → ZeroTRUST → "Service Worker" → Inspect
```

### 8.6 Celery / Background tasks not processing

```bash
# For prototype, Celery is optional — bulk processing not needed
# Start a Celery worker if needed:
docker-compose exec verification-engine \
  celery -A src.worker worker --loglevel=info
```

### 8.7 View logs for any service

```bash
docker-compose logs -f api-gateway         # API Gateway logs
docker-compose logs -f verification-engine # Verification Engine logs
docker-compose logs -f media-analysis      # Media Analysis logs

# On AWS ECS:
aws logs tail /ecs/zerotrust-api-gateway --follow --region us-east-1
aws logs tail /ecs/zerotrust-verification --follow --region us-east-1
```

---

## 9. Repository Layout Quick Reference

```
zerotrust-aws/
├── apps/
│   ├── api-gateway/            Node.js 20 + Express + Prisma
│   ├── verification-engine/    Python 3.11 + FastAPI + LangGraph
│   ├── media-analysis/         Python 3.11 + TF + PyTorch
│   ├── web-portal/             React 18 + Vite 5 + Tailwind
│   ├── browser-extension/      Chrome MV3 + React
│   └── mobile-app/             React Native 0.73 + Expo
├── infrastructure/
│   └── terraform/              IaC (optional, AWS CLI scripts in IMPL-02)
├── scripts/
│   ├── setup-vpc.sh
│   ├── setup-managed.sh
│   ├── setup-ssm.sh
│   ├── run-migrations.sh
│   ├── build-push.sh
│   ├── deploy-ecs.sh
│   └── deploy-web.sh
├── docs/                       THIS documentation series (IMPL-01 to IMPL-05)
├── .env.local.example
├── docker-compose.yml
└── README.md
```
