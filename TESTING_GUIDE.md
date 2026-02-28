# ZeroTRUST Testing Guide
**Complete Testing Procedures**

## Prerequisites

1. Docker containers running
2. Database migrations applied
3. API keys configured in `.env.local`

---

## Phase 1: Health Checks

### Test All Services

```bash
# API Gateway
curl http://localhost:3000/health
# Expected: {"status":"healthy","service":"api-gateway","time":"..."}

# Verification Engine
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"verification-engine","environment":"development"}

# Media Analysis
curl http://localhost:8001/health
# Expected: {"status":"healthy","service":"media-analysis","note":"..."}

# Web Portal
curl http://localhost:5173
# Expected: HTML response
```

---

## Phase 2: Database Setup

### Run Migrations

```bash
cd apps/api-gateway
npx prisma migrate dev --name init
npx prisma generate
```

### Verify Database

```bash
# Connect to PostgreSQL
docker exec -it zt-postgres psql -U zerotrust -d zerotrust_dev

# Check tables
\dt

# Expected tables:
# - users
# - verifications
# - sources
# - api_keys

# Exit
\q
```

---

## Phase 3: Authentication Flow

### 1. Register User

```bash
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@zerotrust.ai",
    "password": "SecurePass123!"
  }'
```

**Expected Response:**
```json
{
  "message": "Registration successful",
  "user": {
    "id": "uuid",
    "email": "test@zerotrust.ai",
    "tier": "free"
  }
}
```

### 2. Login

```bash
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@zerotrust.ai",
    "password": "SecurePass123!"
  }'
```

**Expected Response:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid",
    "email": "test@zerotrust.ai",
    "tier": "free"
  }
}
```

**Save the accessToken for next tests!**

### 3. Test Protected Route

```bash
# Replace YOUR_TOKEN with the accessToken from login
curl http://localhost:3000/api/v1/history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "limit": 20,
  "pages": 0
}
```

---

## Phase 4: Verification Flow

### Test 1: Simple False Claim

```bash
curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "content": "COVID-19 vaccines contain microchips for tracking",
    "type": "text",
    "source": "api"
  }'
```

**Expected Response Structure:**
```json
{
  "id": "uuid",
  "credibility_score": 5-15,
  "category": "Verified False",
  "confidence": "High",
  "claim_type": "factual",
  "sources_consulted": 20-40,
  "agent_consensus": "Strong consensus (80-90%)",
  "evidence_summary": {
    "supporting": 0-2,
    "contradicting": 25-35,
    "neutral": 3-5
  },
  "sources": [...],
  "agent_verdicts": {
    "news": {...},
    "scientific": {...},
    "research": {...},
    "social_media": {...},
    "sentiment": {...}
  },
  "limitations": [...],
  "recommendation": "...",
  "processing_time": 3-6,
  "created_at": "..."
}
```

### Test 2: True Claim

```bash
curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "content": "India launched Chandrayaan-3 moon mission in 2023",
    "type": "text",
    "source": "api"
  }'
```

**Expected:**
- `credibility_score`: 85-95
- `category`: "Verified True" or "Likely True"
- `confidence`: "High"

### Test 3: Mixed Evidence

```bash
curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "content": "5G towers cause health problems",
    "type": "text",
    "source": "api"
  }'
```

**Expected:**
- `credibility_score`: 30-50
- `category`: "Likely False" or "Mixed Evidence"
- `confidence`: "Medium"

---

## Phase 5: Cache Testing

### Test Cache Tiers

```bash
# First request (cache miss)
time curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The Earth is flat",
    "type": "text",
    "source": "api"
  }'
```

**Expected:**
- `cached`: false
- Processing time: 3-6 seconds

```bash
# Second request (Redis hit)
time curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The Earth is flat",
    "type": "text",
    "source": "api"
  }'
```

**Expected:**
- `cached`: true
- `cache_tier`: "redis"
- Processing time: <200ms

### Verify Redis Cache

```bash
# Connect to Redis
docker exec -it zt-redis redis-cli

# Check keys
KEYS verify:*

# Get a cached result
GET verify:HASH_HERE

# Exit
exit
```

---

## Phase 6: Rate Limiting

### Test Public Rate Limit

```bash
# Run 25 requests rapidly (limit is 20/minute)
for i in {1..25}; do
  curl -X POST http://localhost:3000/api/v1/verify \
    -H "Content-Type: application/json" \
    -d '{"content":"test claim '$i'","type":"text","source":"api"}' \
    -w "\nStatus: %{http_code}\n"
  sleep 0.1
done
```

**Expected:**
- First 20 requests: Status 200
- Requests 21-25: Status 429 (Rate limit exceeded)

---

## Phase 7: Agent Testing

### Test Individual Agents

Create a test script to verify each agent works:

```python
# test_agents.py
import asyncio
import sys
sys.path.append('apps/verification-engine/src')

from agents import (
    ResearchAgent, NewsAgent, ScientificAgent,
    SocialMediaAgent, SentimentAgent, ScraperAgent
)

async def test_agents():
    claim = "COVID vaccines cause autism"
    analysis = {
        "main_assertion": claim,
        "entities": ["COVID", "vaccines", "autism"],
        "type": "factual",
        "domain": "health"
    }
    
    agents = {
        'research': ResearchAgent(),
        'news': NewsAgent(),
        'scientific': ScientificAgent(),
        'social_media': SocialMediaAgent(),
        'sentiment': SentimentAgent(),
        'scraper': ScraperAgent(),
    }
    
    for name, agent in agents.items():
        print(f"\n{'='*50}")
        print(f"Testing {name.upper()} Agent")
        print('='*50)
        try:
            result = await agent.investigate(claim, analysis)
            print(f"✅ Verdict: {result.get('verdict')}")
            print(f"✅ Confidence: {result.get('confidence')}")
            print(f"✅ Sources: {len(result.get('sources', []))}")
            print(f"✅ Summary: {result.get('summary', '')[:100]}...")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    asyncio.run(test_agents())
```

Run:
```bash
cd apps/verification-engine
python test_agents.py
```

---

## Phase 8: Load Testing

### Install k6

```bash
# Windows (Chocolatey)
choco install k6

# Or download from https://k6.io/docs/get-started/installation/
```

### Create Load Test Script

```javascript
// load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 50 },   // Stay at 50 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<5000'],  // 95% of requests < 5s
    http_req_failed: ['rate<0.05'],     // <5% failure rate
  },
};

const claims = [
  'vaccines cause autism',
  'climate change is a hoax',
  'Modi declared emergency in India 2024',
  'WHO warns about new pandemic in 2025',
  'The Earth is flat',
];

export default function () {
  const claim = claims[Math.floor(Math.random() * claims.length)];
  
  const payload = JSON.stringify({
    content: claim,
    type: 'text',
    source: 'load-test',
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const res = http.post('http://localhost:3000/api/v1/verify', payload, params);
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'has credibility_score': (r) => JSON.parse(r.body).credibility_score !== undefined,
  });
  
  sleep(1);
}
```

### Run Load Test

```bash
k6 run load-test.js
```

**Expected Results:**
- ✅ 95% of requests complete in <5 seconds
- ✅ <5% failure rate
- ✅ Cache hit rate increases over time
- ✅ Response times decrease as cache warms up

---

## Phase 9: Error Scenarios

### Test Invalid Inputs

```bash
# Empty content
curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"","type":"text","source":"api"}'
# Expected: 400 Bad Request

# Content too short
curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"test","type":"text","source":"api"}'
# Expected: 400 Bad Request

# Invalid type
curl -X POST http://localhost:3000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"content":"test claim here","type":"invalid","source":"api"}'
# Expected: 400 Bad Request
```

### Test Authentication Errors

```bash
# Invalid token
curl http://localhost:3000/api/v1/history \
  -H "Authorization: Bearer invalid_token"
# Expected: 401 Unauthorized

# Missing token
curl http://localhost:3000/api/v1/history
# Expected: 401 Unauthorized
```

---

## Phase 10: Performance Metrics

### Measure Response Times

```bash
# Create performance test script
cat > perf-test.sh <<'EOF'
#!/bin/bash

echo "Testing verification performance..."
echo "=================================="

for i in {1..10}; do
  echo -n "Request $i: "
  time curl -s -X POST http://localhost:3000/api/v1/verify \
    -H "Content-Type: application/json" \
    -d '{"content":"test claim '$i'","type":"text","source":"api"}' \
    -o /dev/null
done
EOF

chmod +x perf-test.sh
./perf-test.sh
```

**Expected:**
- First request: 3-6 seconds (cache miss)
- Subsequent requests: <200ms (cache hit)

---

## Success Criteria

### ✅ All Tests Pass If:

1. **Health Checks**
   - All services return 200 OK
   - Health endpoints return correct JSON

2. **Authentication**
   - User registration works
   - Login returns valid JWT tokens
   - Protected routes require authentication
   - Token refresh works
   - Logout revokes tokens

3. **Verification**
   - Claims are verified successfully
   - Credibility scores are reasonable (0-100)
   - All 6 agents execute
   - Sources are returned
   - Processing time < 10 seconds

4. **Caching**
   - First request is cache miss
   - Second identical request is cache hit
   - Cache hit response time < 200ms
   - Cache tier promotion works (L2→L1)

5. **Rate Limiting**
   - Public rate limit enforced (20/min)
   - User rate limits enforced (tier-based)
   - 429 responses returned correctly

6. **Error Handling**
   - Invalid inputs return 400
   - Missing auth returns 401
   - Server errors return 500
   - Error messages are clear

7. **Performance**
   - 95% of requests < 5 seconds
   - Cache hit rate > 80% after warmup
   - System handles 50 concurrent users
   - No memory leaks or crashes

---

## Troubleshooting

### Issue: Verification Engine Returns "Bedrock unavailable"

**Solution:** Add AWS credentials to `.env.local`:
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
```

### Issue: Agents Return "No API keys configured"

**Solution:** Add API keys to `.env.local`:
```bash
NEWS_API_KEY=your_newsapi_key
GOOGLE_SEARCH_KEY=your_google_key
GOOGLE_SEARCH_ENGINE_ID=your_cse_id
```

### Issue: Database Connection Failed

**Solution:** Check PostgreSQL is running:
```bash
docker-compose ps postgres
docker-compose logs postgres
```

### Issue: Redis Connection Failed

**Solution:** Check Redis is running:
```bash
docker-compose ps redis
docker-compose logs redis
```

---

## Next Steps After Testing

1. ✅ All tests pass → Deploy to AWS
2. ❌ Some tests fail → Debug and fix issues
3. 📊 Performance issues → Optimize bottlenecks
4. 🐛 Bugs found → Create issues and fix
5. 📝 Missing features → Implement remaining components

---

**Testing Guide Version:** 1.0  
**Last Updated:** February 28, 2026  
**Status:** Ready for execution
