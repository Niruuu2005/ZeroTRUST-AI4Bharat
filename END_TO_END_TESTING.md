# End-to-End Testing Guide - AWS Migration

**Test the complete AWS-native stack after migration**

---

## 🎯 Complete Architecture

```
Browser/Extension
    ↓
API Gateway (REST)
    ↓
Lambda Functions
    ↓ ↓ ↓
[Verify] → ECS (Verification Engine) → ElastiCache → DynamoDB → RDS
[Auth] → RDS + Secrets Manager
[History] → RDS
```

---

## ✅ Pre-Test Checklist

Before running tests:

```bash
# 1. Verify all services are running
aws ecs list-services --cluster zerotrust-cluster --region us-east-1
aws elasticache describe-cache-clusters --cache-cluster-id zerotrust-redis
aws rds describe-db-instances --db-instance-identifier zerotrust-db
aws dynamodb list-tables --region us-east-1

# 2. Get API Gateway URL
export API_URL="https://<your-api-id>.execute-api.us-east-1.amazonaws.com/prod"
echo "API URL: $API_URL"

# 3. Check Lambda functions
aws lambda list-functions --region us-east-1 | grep zerotrust
```

---

## 🧪 Test Suite

### Test 1: Health Check

```bash
# Test API Gateway is responding
curl -i $API_URL/verify

# Expected: 200 OK or 400 (missing body)
```

### Test 2: User Registration

```bash
# Register new test user
curl -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-user@zerotrust.com",
    "password": "SecurePass123!",
    "tier": "free"
  }'

# Expected response:
# {
#   "success": true,
#   "data": {
#     "user": {
#       "id": "uuid-here",
#       "email": "test-user@zerotrust.com",
#       "tier": "free"
#     },
#     "access_token": "eyJhbGc...",
#     "refresh_token": "eyJhbGc..."
#   }
# }
```

### Test 3: User Login

```bash
# Login with test user
export LOGIN_RESPONSE=$(curl -s -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test-user@zerotrust.com",
    "password": "SecurePass123!"
  }')

echo $LOGIN_RESPONSE | jq .

# Extract access token
export ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.data.access_token')
echo "Access Token: $ACCESS_TOKEN"
```

### Test 4: Text Verification (No Cache)

```bash
# Verify a factual claim - first time (no cache)
time curl -X POST $API_URL/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "content": "The Earth revolves around the Sun",
    "type": "text",
    "source": "api-test",
    "user_id": "test-user"
  }' | jq .

# Expected response (~5-10 seconds first time):
# {
#   "request_id": "uuid",
#   "status": "completed",
#   "result": {
#     "verdict": "true",
#     "confidence": 0.95,
#     "credibility_score": 95.5,
#     "multi_agent_consensus": {
#       "agreement_level": 1.0,
#       "agents_agree": 7,
#       "agents_total": 7
#     },
#     "evidence": [...],
#     "cached": false
#   }
# }

# Check CloudWatch logs
aws logs tail /zerotrust/api-gateway --follow --region us-east-1
```

### Test 5: Cache Hit (ElastiCache)

```bash
# Verify same claim again - should hit ElastiCache
time curl -X POST $API_URL/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "content": "The Earth revolves around the Sun",
    "type": "text",
    "source": "api-test",
    "user_id": "test-user"
  }' | jq .

# Expected: ~100-300ms (from ElastiCache)
# Response should have "cached": true
```

### Test 6: DynamoDB Cache (After 5 minutes)

```bash
# Wait 5 minutes or manually delete from ElastiCache
aws elasticache describe-cache-clusters \
  --cache-cluster-id zerotrust-redis \
  --show-cache-node-info

# Connect to Redis and flush specific key
redis-cli -h <elasticache-endpoint> -p 6379
> DEL verify:hash:<content-hash>
> EXIT

# Verify again - should hit DynamoDB (Tier-2 cache)
time curl -X POST $API_URL/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "content": "The Earth revolves around the Sun",
    "type": "text",
    "source": "api-test"
  }' | jq .

# Expected: ~500ms-1s (from DynamoDB)
# Response: "cached": true, "cache_tier": "dynamodb"
```

### Test 7: Image Verification

```bash
# Upload image to S3 first
export IMAGE_URL="https://zerotrust-media-dev.s3.amazonaws.com/test-image.jpg"

# Verify image
curl -X POST $API_URL/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "content": "'$IMAGE_URL'",
    "type": "image",
    "source": "api-test"
  }' | jq .

# Expected: Media Analysis service result
# {
#   "verdict": "authentic",
#   "confidence": 0.85,
#   "ela_result": "No significant tampering detected",
#   "metadata_analysis": {...}
# }
```

### Test 8: Verification History

```bash
# Get user's verification history
curl -X GET $API_URL/history \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

# Expected response:
# {
#   "success": true,
#   "data": {
#     "verifications": [
#       {
#         "id": "uuid",
#         "content": "The Earth revolves around the Sun",
#         "verdict": "true",
#         "confidence": 0.95,
#         "created_at": "2026-03-02T10:30:00Z"
#       },
#       ...
#     ],
#     "total": 2,
#     "page": 1
#   }
# }
```

### Test 9: Rate Limiting

```bash
# Send 150 requests rapidly (exceeds 100/sec limit)
for i in {1..150}; do
  curl -X POST $API_URL/verify \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{"content":"Test '$i'","type":"text","source":"load-test"}' &
done
wait

# Expected: Some requests get 429 Too Many Requests
```

### Test 10: Browser Extension

```bash
# Update extension manifest.json with new API URL
cat > apps/browser-extension/config.js <<EOF
const API_URL = '$API_URL';
EOF

# Load extension in Chrome and test:
# 1. Highlight text on webpage
# 2. Right-click → "Verify with ZeroTRUST"
# 3. Check popup shows verification result
```

### Test 11: Web Portal

```bash
# Update web portal environment
cat > apps/web-portal/.env <<EOF
VITE_API_URL=$API_URL
EOF

# Rebuild
cd apps/web-portal
npm run build

# Test in browser:
# 1. Login with test user
# 2. Submit claim for verification
# 3. Check results display correctly
# 4. Navigate to history page
```

### Test 12: Multi-Agent Verification

```bash
# Submit complex claim requiring all 7 agents
curl -X POST $API_URL/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "content": "According to a recent Nature study, a new cancer treatment shows 80% success rate in clinical trials",
    "type": "text",
    "source": "api-test",
    "require_all_agents": true
  }' | jq .

# Expected agents to respond:
# - ResearchAgent: Searches Semantic Scholar
# - NewsAgent: Checks news outlets
# - ScientificAgent: Verifies in scientific databases
# - SocialMediaAgent: Checks social media mentions
# - SentimentAgent: Analyzes sentiment
# - ScraperAgent: Scrapes relevant web pages
# - FactCheckAgent: Queries Google Fact Check API

# Response should show all agent results:
# {
#   "multi_agent_consensus": {
#     "agents_total": 7,
#     "agents_agree": 6,
#     "agreement_level": 0.857
#   },
#   "agent_results": {
#     "research": {...},
#     "news": {...},
#     "scientific": {...},
#     "social_media": {...},
#     "sentiment": {...},
#     "scraper": {...},
#     "factcheck": {...}
#   }
# }
```

### Test 13: FactCheck API Integration (60% Weight)

```bash
# Submit claim known to be fact-checked
curl -X POST $API_URL/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "content": "COVID-19 vaccines contain microchips",
    "type": "text",
    "source": "api-test"
  }' | jq .

# Expected:
# - FactCheckAgent should find official fact-checks
# - Credibility score calculation:
#   * Official fact-check rating: 60% weight
#   * Other agents: 40% weight
# - Final verdict should be "false" with high confidence
```

---

## 📊 Performance Benchmarks

### Expected Response Times

| Scenario | Expected Time | Acceptable Range |
|----------|--------------|------------------|
| Cache hit (Redis) | 100-300ms | < 500ms |
| Cache hit (DynamoDB) | 500-1000ms | < 1500ms |
| Cache miss (text) | 5-10s | < 15s |
| Cache miss (image) | 10-20s | < 30s |
| History query | 200-500ms | < 1000ms |
| Auth (login/register) | 300-700ms | < 1500ms |

### Load Test

```bash
# Install Apache Bench
# For Windows: Download from https://www.apachelounge.com/download/

# Test API Gateway throughput
ab -n 1000 -c 10 -p verify.json -T application/json \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  $API_URL/verify

# Expected:
# - Requests per second: 50-100
# - 99th percentile latency: < 2000ms
# - Error rate: < 1%
```

---

## 🔍 Debugging Failed Tests

### Lambda Function Logs

```bash
# Check logs for each function
aws logs tail /aws/lambda/zerotrust-verify-handler --follow
aws logs tail /aws/lambda/zerotrust-auth-handler --follow
aws logs tail /aws/lambda/zerotrust-history-handler --follow
```

### ECS Task Logs

```bash
# Check ECS service logs
aws logs tail /ecs/zerotrust/verification-engine --follow
aws logs tail /ecs/zerotrust/media-analysis --follow
```

### API Gateway Logs

```bash
# Check API Gateway execution logs
aws logs tail API-Gateway-Execution-Logs_$API_ID/prod --follow
```

### Database Connections

```bash
# Test RDS connection
psql -h <rds-endpoint> -U zerotrust_admin -d zerotrust_db -c "SELECT COUNT(*) FROM verifications;"

# Check ElastiCache
redis-cli -h <elasticache-endpoint> -p 6379 PING

# Query DynamoDB
aws dynamodb scan --table-name ZeroTrustCache --limit 5
```

---

## ✅ Success Criteria

All tests should pass with:
- ✅ HTTP 200/201 responses
- ✅ Correct JSON structure
- ✅ Response times within acceptable range
- ✅ Cache working (Redis → DynamoDB → RDS)
- ✅ All 7 agents responding
- ✅ FactCheck API integration working
- ✅ Authentication working
- ✅ History queries returning data
- ✅ Rate limiting enforced
- ✅ Browser extension functional
- ✅ Web portal functional

---

## 🎯 Post-Migration Tasks

Once all tests pass:

1. **Update DNS** (if using custom domain)
2. **Configure CloudWatch alarms**
3. **Set up backup schedules**
4. **Document API endpoints** for partners
5. **Train team** on new architecture
6. **Decommission old infrastructure**:
   - Stop local Docker containers
   - Cancel Supabase subscription
   - Update documentation

---

## 📈 Monitoring Dashboard

Create CloudWatch dashboard:

```bash
# Create comprehensive dashboard
aws cloudwatch put-dashboard \
  --dashboard-name ZeroTRUST-Production \
  --dashboard-body file://dashboard.json

# dashboard.json
cat > dashboard.json <<'EOF'
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ApiGateway", "Count", {"stat": "Sum"}],
          [".", "4XXError", {"stat": "Sum"}],
          [".", "5XXError", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "API Gateway Requests"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
          [".", "Errors", {"stat": "Sum"}],
          [".", "Duration", {"stat": "Average"}]
        ],
        "period": 300,
        "region": "us-east-1",
        "title": "Lambda Performance"
      }
    }
  ]
}
EOF
```

---

**🎉 Congratulations! Your ZeroTRUST platform is now fully AWS-native and production-ready!**
