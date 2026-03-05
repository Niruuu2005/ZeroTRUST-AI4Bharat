# Step 9 — Service Improvement Suggestions

> This document reviews the current AWS service choices and recommends improvements or replacements where a better option exists.  
> Changes are **suggestions only** — the codebase analysis is the basis, implementation impact is rated per change.

---

## Summary

| # | Current Choice | Issue | Suggested Improvement | Impact |
|---|---------------|-------|----------------------|--------|
| 1 | psycopg2-binary (pinned 2.9.9) | No Python 3.14 wheel | Use `psycopg[binary]` v3 | Low |
| 2 | DynamoDB for Tier-2 cache | Overkill for TTL cache | Replace with **ElastiCache Redis cluster** (longer TTL tier) | Medium |
| 3 | Transcribe polling (120s sync) | Blocks the thread | Switch to **async callback** via SNS/SQS + webhook | Medium |
| 4 | IAM long-term access keys | Security risk (static credentials) | Use **IAM Roles + instance profiles** (IRSA for EKS / task roles for ECS) | High |
| 5 | Lambda calling internal service via HTTP | Tightly coupled, brittle URL | Use **SQS queue** between Lambda and Media Analysis | Medium |
| 6 | Single AWS region (us-east-1) | Single point of failure | Multi-region with **Route 53 failover** for production | High |
| 7 | No Bedrock guardrails | Risk of harmful AI outputs | Add **Bedrock Guardrails** for content filtering | Medium |
| 8 | CloudWatch only for logs | Limited observability | Add **AWS X-Ray** for distributed tracing | Low |

---

## Details

---

### 1. psycopg2-binary → psycopg v3

**Current:** `psycopg2-binary==2.9.9` in `requirements.txt` (both verification-engine and media-analysis)  
**Problem:** No pre-built wheel for Python 3.14 — forces source compilation or version override.  
**Fix:** Migrate to `psycopg[binary]>=3.1` which ships native Python 3.14 wheels.

```python
# requirements.txt (change)
# psycopg2-binary==2.9.9    ← remove
psycopg[binary]>=3.1        # ← add
```

Connection string format stays identical: `postgresql://user:pass@host/db`  
**Impact:** Low — drop-in replacement for SQLAlchemy usage.

---

### 2. DynamoDB Tier-2 Cache → Redis with Longer TTL

**Current:** DynamoDB used as Tier-2 (24h TTL) between Redis (1h) and PostgreSQL (30d).  
**Problem:** 
- DynamoDB read latency (~5ms) vs Redis (<1ms) makes it only marginally better than PostgreSQL for a cache
- DynamoDB's on-demand write cost ($1.25/million writes) adds up at volume
- Extra SDK dependency in CacheService.ts

**Better approach:** Use **a single Redis cluster with two TTL buckets**:
- Hot tier: `verify:hot:<hash>` TTL = 1 hour
- Warm tier: `verify:warm:<hash>` TTL = 24 hours

AWS **ElastiCache for Redis** (cluster mode) gives you both in one service.  
For production, use **ElastiCache Serverless** (no instance sizing needed).

**Impact:** Medium — requires updating `CacheService.ts`.

---

### 3. Transcribe Synchronous Poll → Async SNS Callback

**Current:** `analyze_audio_transcribe()` starts a Transcribe job then polls every 3 seconds for up to 120 seconds — blocking the HTTP request thread.  
**Problem:**
- Ties up a worker thread for up to 2 minutes
- Client sees no response until done (or times out)
- Doesn't scale to concurrent audio uploads

**Better approach:**
1. Start Transcribe job and return immediately with a job ID
2. Configure Transcribe to send completion notification to an **SNS topic**
3. SNS triggers a **Lambda** (or sends to **SQS**) to store the result
4. Client polls `/results/<job_id>` for status

**Impact:** Medium — requires new API route + SNS topic + Lambda handler.

---

### 4. Long-term IAM Access Keys → IAM Roles

**Current:** Static `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` stored in `.env.local`.  
**Problem:** Long-term credentials are a security risk:
- If `.env.local` is accidentally committed, credentials are exposed
- Keys don't rotate automatically
- AWS Security Hub flags long-term key usage

**Better approach for production:**
- **ECS Fargate**: Assign an IAM Task Role to each service — no credentials needed in env vars, AWS SDK picks up short-lived tokens automatically
- **EC2**: Use Instance Profiles
- **Local dev**: Use `aws sso login` or `aws-vault` for credential management

For the hackathon, the current approach is acceptable — but rotate the keys before sharing any screenshots or repos.

**Immediate mitigation (no code change needed):**
```powershell
# Verify .env.local is gitignored
git check-ignore -v .env.local
# Should output: .gitignore:.env.local
```

**Impact:** High for production; Low for hackathon dev.

---

### 5. Lambda → HTTP → Media Analysis: Use SQS

**Current:** Lambda calls the media-analysis service synchronously via HTTP (`POST /analyze`).  
**Problem:**
- Lambda will fail/timeout if the media-analysis service is down or slow
- No retry logic or dead-letter queue
- URL must be hardcoded or discoverable at Lambda deploy time

**Better approach:** Lambda publishes to an **SQS queue** → Media Analysis service polls the queue.

```
S3 Event → Lambda → SQS queue → Media Analysis polls → process → store result
```

Benefits:
- Decoupled: media-analysis can restart without losing jobs
- Built-in retry with DLQ
- Scales naturally
- No hardcoded URLs

**Impact:** Medium — requires SQS queue, updating Lambda handler.py and media-analysis main.py.

---

### 6. Single Region → Multi-Region (Production Only)

**Current:** All services hardcoded to `us-east-1`.  
**Problem:** For a fact-checking service with global users (AI4Bharat targets Indian language content), latency to `us-east-1` from India is ~200ms.

**Better approach:**
- Use **AWS Global Accelerator** or **CloudFront** in front of the API for edge routing
- Deploy verification-engine to `ap-south-1` (Mumbai) — Bedrock available there
- **Route 53 latency-based routing** between regions

> Bedrock model availability varies by region. Verify model IDs for `ap-south-1` before migrating.

**Impact:** High — significant infrastructure change, not recommended for hackathon.

---

### 7. Add AWS Bedrock Guardrails

**Current:** AI agent prompts and responses have no content filtering guardrails.  
**Problem:** 
- A malicious claim could prompt the LLM to generate harmful content
- No protection against prompt injection in user-submitted claims
- No PII detection in agent scraping results

**Better approach:** Create a **Bedrock Guardrail**:

1. Open AWS Console → Amazon Bedrock → Guardrails → **Create guardrail**
2. Configure:
   - Content filters: HATE, INSULTS, SEXUAL, VIOLENCE → High threshold
   - Denied topics: "Generate harmful content", "Ignore previous instructions"
   - PII redaction: Email, Phone, SSN
3. Apply the guardrail ARN in `bedrock.py`:

```python
response = client.converse(
    modelId=model_id,
    messages=messages,
    guardrailConfig={
        "guardrailIdentifier": "your-guardrail-id",
        "guardrailVersion": "DRAFT",
        "trace": "enabled"
    }
)
```

**Impact:** Medium — small code change in `bedrock.py`, significant security improvement.

---

### 8. Add AWS X-Ray Distributed Tracing

**Current:** Only request-level logging in CloudWatch — no way to trace a single claim verification through all 6 agents.  
**Problem:** Hard to debug performance issues across the verification pipeline.

**Better approach:** Add **AWS X-Ray** SDK to the verification engine and API gateway.

```python
# verification-engine (Python)
pip install aws-xray-sdk
from aws_xray_sdk.core import xray_recorder, patch_all
patch_all()  # auto-instruments boto3, httpx, etc.
```

```typescript
// api-gateway (Node.js)
npm install aws-xray-sdk-core
import * as AWSXRay from 'aws-xray-sdk-core';
AWSXRay.captureHTTPsGlobal(require('http'));
```

This creates a service map showing the full path of each request through Bedrock, cache layers, and agents.

**Impact:** Low — additive instrumentation, no breaking changes.

---

## Priority Order for Implementation

1. **Bedrock Guardrails** — security, low effort ← do this now
2. **psycopg v3** — unblocks Python 3.14 natively ← easy win
3. **IAM credential rotation warning** — check `.env.local` is gitignored ← immediate
4. **SQS for Lambda-Media decoupling** — production reliability
5. **ElastiCache instead of DynamoDB cache** — cost + perf at scale
6. **X-Ray tracing** — debugging aid
7. **Async Transcribe** — UX improvement for audio
8. **Multi-region** — only needed post-launch
