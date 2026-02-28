# ZeroTRUST — Test Steps & AWS Requirements Checklist

**Purpose:** What you need to run and test the app locally, and what you need for AWS (Bedrock, optional DynamoDB, and full deploy).  
**Last updated:** February 28, 2026

---

## 1. Quick Test (Local, No AWS)

You can **run and test** the stack with **no AWS account** for a limited demo:

- **Postgres** and **Redis** run in Docker (no AWS).
- **Verification engine** will use **mock LLM responses** if Bedrock is not configured (see `integrations/bedrock.py` — returns placeholder when client is `None`).
- **Agents** that call external APIs (News, Google Search, etc.) will return empty or “no results” if API keys are missing; the pipeline still runs.

### 1.1 Prerequisites (local only)

| Requirement | Check |
|-------------|--------|
| **Docker Desktop** | `docker --version` (24+) |
| **Docker Compose** | `docker compose version` |
| **Node.js 20** | Optional if you only use Docker; needed for local `npm run dev` in apps |
| **Python 3.11** | Optional if you only use Docker |

### 1.2 Run the stack

```powershell
cd d:\Dream\ZeroTRUST_AWS

# Copy env template (optional; empty keys are fine for mock mode)
copy .env.local.example .env.local

# Validate compose
docker compose config

# Build and start all services
docker compose up -d --build

# Wait ~60–90 seconds for api-gateway and verification-engine to be ready
```

### 1.3 Health checks

```powershell
# API Gateway
curl http://localhost:3000/health

# Verification Engine
curl http://localhost:8000/health

# Media Analysis (placeholder)
curl http://localhost:8001/health

# Web portal in browser
start http://localhost:5173
```

### 1.4 Test a verification (text)

```powershell
curl -X POST http://localhost:3000/api/v1/verify `
  -H "Content-Type: application/json" `
  -d '{\"content\":\"COVID vaccines cause infertility.\",\"type\":\"text\",\"source\":\"api\"}'
```

- **Without AWS Bedrock:** You get a response with mock/placeholder content (pipeline runs, agents may return “insufficient” if no API keys).
- **With Bedrock + API keys:** You get real credibility score, agents, and sources.

### 1.5 Test the web portal

1. Open **http://localhost:5173**
2. Enter a text claim (e.g. “Vaccines cause autism”) and click **Verify**.
3. You should see loading then either a result (score, recommendation, agents, sources) or an error message.

### 1.6 Run database migrations (first time)

If the API returns DB errors, run Prisma migrations from the host:

```powershell
cd apps\api-gateway
$env:DATABASE_URL="postgresql://zerotrust:devpassword@localhost:5432/zerotrust_dev"
npx prisma migrate deploy
npx prisma generate
cd ..\..
```

Then restart API Gateway: `docker compose restart api-gateway`.

---

## 2. What You Need for “Real” Verification (AWS + APIs)

For **real** LLM and multi-source verification you need **at least**:

1. **AWS account** with **Bedrock** enabled in **us-east-1**.
2. **At least one** of: **NewsAPI** or **Google Custom Search** (so News and/or Research agents return results).

Everything else is optional but improves quality.

---

## 3. AWS Requirements Checklist (MD List)

Use this as a single checklist for “what do I need for the AWS thing.”

### 3.1 AWS Account & Access

- [ ] **AWS account** (root or IAM user)
- [ ] **AWS CLI** installed and configured: `aws configure`  
  - Region: **us-east-1** (required for Bedrock)
  - Access Key + Secret (or SSO/profile)
- [ ] **Bedrock model access** enabled in Console:  
  **AWS Console → Bedrock → Model access → Enable:**
  - [ ] Anthropic **Claude 3.5 Sonnet** v2
  - [ ] Anthropic **Claude 3.5 Haiku**
  - [ ] Mistral **Mistral Large 2407**
  - (Optional) Amazon **Titan Text Embeddings G1** if you add vector features later

### 3.2 Environment Variables for Local + AWS Bedrock

Create **`.env.local`** from **`.env.local.example`** and set at least:

| Variable | Required for | Where to get |
|----------|--------------|--------------|
| `AWS_ACCESS_KEY_ID` | Bedrock (real LLM) | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | Bedrock | IAM user secret |
| `AWS_DEFAULT_REGION` | Bedrock | `us-east-1` |
| `BEDROCK_REGION` | Verification engine | `us-east-1` (set in docker-compose already; override in .env.local if needed) |

### 3.3 Optional: Tier-2 Cache (DynamoDB)

For **Tier-2 cache** (DynamoDB) when running API Gateway with AWS:

- [ ] **DynamoDB table** in **us-east-1**  
  - **Table name:** `zerotrust-claim-verifications`  
  - **Partition key:** `claim_hash` (String)  
  - **TTL:** enabled, attribute name `ttl`  
  - **Billing:** PAY_PER_REQUEST (on-demand)  
- [ ] **IAM:** credentials used by the API Gateway (e.g. same as Bedrock) must have `dynamodb:GetItem`, `dynamodb:PutItem` on `arn:aws:dynamodb:us-east-1:*:table/zerotrust-claim-verifications`.
- [ ] **Env:** `AWS_REGION=us-east-1` (already in docker-compose). Same AWS credentials as above.

> **Note:** Current code uses only **partition key** `claim_hash` for Get/Put. If you follow IMPL-02 and create a table with **sort key** `created_at`, the code would need to be changed to use Query instead of GetItem.

### 3.4 Optional: External API Keys (for agents)

These go in **`.env.local`** and are passed into the containers via `env_file: [.env.local]`:

| Variable | Agent(s) | Purpose |
|----------|----------|---------|
| `NEWS_API_KEY` | News | NewsAPI.org (free tier: 100 req/day) |
| `GNEWS_API_KEY` | News | GNews.io |
| `GOOGLE_SEARCH_KEY` | Research | Google Custom Search API key |
| `GOOGLE_SEARCH_ENGINE_ID` | Research | Custom Search Engine ID |
| `TWITTER_BEARER_TOKEN` | Social Media | Twitter/X API v2 Bearer token |
| `REDDIT_CLIENT_ID` | Social Media | Reddit API (optional; public search works without) |
| `REDDIT_CLIENT_SECRET` | Social Media | Reddit API |
| `PUBMED_API_KEY` | Scientific | PubMed E-utilities (optional; higher rate limit) |
| `SERPER_API_KEY` | (future) | Serper.dev search (optional) |
| `AFP_API_KEY` | (future) | AFP fact-check (optional) |

**Minimum for “real” results:** At least **one** of `NEWS_API_KEY` or (`GOOGLE_SEARCH_KEY` + `GOOGLE_SEARCH_ENGINE_ID`).

### 3.5 Full AWS Deploy (ECS, RDS, Redis, etc.)

If you deploy to **AWS** (not just local + Bedrock), you need the following. Details are in **`Docs/IMPL-02-Infrastructure-AWS.md`**.

- [ ] **VPC** (e.g. 10.0.0.0/16) in **us-east-1**
- [ ] **Subnets:** public, private, data (single-AZ for prototype)
- [ ] **Internet Gateway** + **NAT Gateway** (for private subnet egress)
- [ ] **Security groups** for ALB, ECS, RDS, Redis
- [ ] **Application Load Balancer (ALB)** in public subnet(s)
- [ ] **RDS PostgreSQL 15** (e.g. db.t3.medium, single-AZ)
- [ ] **ElastiCache Redis** (e.g. cache.t3.micro, single node) or skip and use Redis in ECS sidecar for prototype
- [ ] **DynamoDB** table: `zerotrust-claim-verifications` (see §3.3)
- [ ] **S3 buckets** (optional for prototype):  
  - [ ] `zerotrust-media-uploads-<account>`  
  - [ ] `zerotrust-static-<account>`  
  - [ ] `zerotrust-models-<account>`
- [ ] **SQS** queue: `zerotrust-media-queue` (optional; for media pipeline later)
- [ ] **ECR** repositories: `zerotrust-api-gateway`, `zerotrust-verification`, `zerotrust-media`
- [ ] **ECS cluster** + Fargate task definitions for API Gateway, Verification Engine, Media Analysis
- [ ] **IAM roles** for ECS task execution + task role (Bedrock, DynamoDB, RDS, Redis, S3, etc.)
- [ ] **SSM Parameter Store** (or Secrets Manager) for `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, API keys
- [ ] **CloudFront** (optional): in front of ALB + static web
- [ ] **Route 53** (optional): DNS for your domain

### 3.6 IAM Permissions Summary (for ECS or local AWS usage)

**Minimum for Bedrock (local or ECS):**

- `bedrock:InvokeModel` (and optionally `InvokeModelWithResponseStream`) on:
  - `anthropic.claude-3-5-sonnet-20241022-v2:0`
  - `anthropic.claude-3-5-haiku-20241022-v1:0`
  - `mistral.mistral-large-2407-v1:0`

**If using DynamoDB:**

- `dynamodb:GetItem`, `dynamodb:PutItem` on table `zerotrust-claim-verifications`

**If using S3 (media uploads / static site):**

- `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on the relevant buckets

**If using RDS/ElastiCache from ECS:**

- Network security groups and no IAM for DB auth (password in SSM).

---

## 4. One-Page “Do I have everything?” List

**Local run + test (no AWS):**

- Docker + Docker Compose  
- `.env.local` (can be empty)  
- `docker compose up -d --build`  
- Migrate DB if needed  
- Hit `/health` and `POST /api/v1/verify`

**Real verification (LLM + sources):**

- AWS account + CLI  
- Bedrock enabled (Claude 3.5 Sonnet/Haiku, Mistral Large) in us-east-1  
- `.env.local`: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION=us-east-1`  
- At least one of: NewsAPI key **or** Google Custom Search (key + engine ID)

**Tier-2 cache:**

- DynamoDB table `zerotrust-claim-verifications` (PK: `claim_hash`, TTL: `ttl`)  
- IAM permissions for GetItem/PutItem  
- `AWS_REGION=us-east-1` and same credentials

**Full AWS deploy:**

- Everything in section **3.5** (VPC, ALB, RDS, Redis, ECS, ECR, IAM, SSM, optional S3/SQS/CloudFront).

---

## 5. Reference

- **Local run & env:** `Docs/IMPL-05-DevOps-CICD.md` (Option A / B)  
- **Full AWS setup:** `Docs/IMPL-02-Infrastructure-AWS.md`  
- **Env template:** `.env.local.example`
