# Step 8 — Environment Variables Configuration

> This is your master reference for every environment variable used across all services. Collect all values from previous steps and fill them in here.

---

## 8.1 — Master .env.local File

Location: `C:\Users\PRIHTVIRAJ\Desktop\ZeroTRUST-AI4Bharat\.env.local`

This file is loaded by Docker Compose for all services and by `dotenv` in the test scripts. It is gitignored — never commit it.

```env
# ═══════════════════════════════════════════════════════════════════
# AWS Core Credentials (from IAM step 1.4)
# ═══════════════════════════════════════════════════════════════════
# REPLACE WITH YOUR OWN CREDENTIALS - See SETUP_SECRETS_GUIDE.md
AWS_ACCESS_KEY_ID=AKIA________________
AWS_SECRET_ACCESS_KEY=________________________________________
AWS_DEFAULT_REGION=us-east-1
AWS_REGION=us-east-1

# ═══════════════════════════════════════════════════════════════════
# S3 — Media bucket (from step 3.1)
# ═══════════════════════════════════════════════════════════════════
S3_MEDIA_BUCKET=zerotrust-media-dev

# ═══════════════════════════════════════════════════════════════════
# CloudWatch Logs (from step 5.1) — optional
# ═══════════════════════════════════════════════════════════════════
CW_LOG_GROUP=/zerotrust/api-gateway
CW_LOG_STREAM_PREFIX=api-gateway

# ═══════════════════════════════════════════════════════════════════
# Lambda / Media Analysis (from step 6.3)
# ═══════════════════════════════════════════════════════════════════
MEDIA_ANALYSIS_URL=http://media-analysis:8001

# ═══════════════════════════════════════════════════════════════════
# Optional External News/Search APIs
# ═══════════════════════════════════════════════════════════════════
NEWS_API_KEY=
GNEWS_API_KEY=
GOOGLE_SEARCH_KEY=
GOOGLE_SEARCH_ENGINE_ID=
TWITTER_BEARER_TOKEN=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
```

---

## 8.2 — Per-Service Variable Reference

### API Gateway (`apps/api-gateway`)

| Variable | Required | Source | Description |
|----------|----------|--------|-------------|
| `AWS_ACCESS_KEY_ID` | ✅ | IAM step 1.4 | Programmatic access key |
| `AWS_SECRET_ACCESS_KEY` | ✅ | IAM step 1.4 | Secret for above key |
| `AWS_REGION` | ✅ | Fixed: `us-east-1` | Region for DynamoDB + S3 |
| `S3_MEDIA_BUCKET` | ⚠️ Media only | S3 step 3.1 | Bucket name for presigned URLs |
| `CW_LOG_GROUP` | ❌ Optional | CloudWatch step 5.1 | Enables CloudWatch transport |
| `CW_LOG_STREAM_PREFIX` | ❌ Optional | Fixed: `api-gateway` | Log stream name prefix |
| `DATABASE_URL` | ✅ | Docker Compose | PostgreSQL connection string |
| `REDIS_URL` | ✅ | Docker Compose | Redis connection string |
| `JWT_SECRET` | ✅ | Generate: `openssl rand -hex 32` | JWT signing secret |
| `VERIFICATION_ENGINE_URL` | ✅ | Fixed: `http://localhost:8000` | Verification engine endpoint |
| `MEDIA_ENGINE_URL` | ✅ | Fixed: `http://localhost:8001` | Media analysis endpoint |

### Verification Engine (`apps/verification-engine`)

| Variable | Required | Source | Description |
|----------|----------|--------|-------------|
| `AWS_ACCESS_KEY_ID` | ✅ | IAM step 1.4 | Used by boto3 for Bedrock |
| `AWS_SECRET_ACCESS_KEY` | ✅ | IAM step 1.4 | Used by boto3 for Bedrock |
| `BEDROCK_REGION` | ✅ | Fixed: `us-east-1` | Bedrock client region |
| `DATABASE_URL` | ✅ | Docker Compose | PostgreSQL for result storage |
| `REDIS_URL` | ✅ | Docker Compose | Redis cache |
| `MAX_AGENT_TIMEOUT` | ❌ Optional | Default: `10` | Seconds before agent timeout |
| `MAX_SOURCES_PER_AGENT` | ❌ Optional | Default: `20` | Max sources each agent queries |
| `NEWS_API_KEY` | ❌ Optional | newsapi.org | News agent data source |
| `GNEWS_API_KEY` | ❌ Optional | gnews.io | Alternative news source |
| `GOOGLE_SEARCH_KEY` | ❌ Optional | Google Cloud Console | Research agent web search |
| `GOOGLE_SEARCH_ENGINE_ID` | ❌ Optional | Google Custom Search | Paired with above |
| `TWITTER_BEARER_TOKEN` | ❌ Optional | Twitter Developer Portal | Social media agent |
| `REDDIT_CLIENT_ID` | ❌ Optional | Reddit Apps | Reddit source for agents |
| `REDDIT_CLIENT_SECRET` | ❌ Optional | Reddit Apps | Paired with above |

### Media Analysis (`apps/media-analysis`)

| Variable | Required | Source | Description |
|----------|----------|--------|-------------|
| `AWS_ACCESS_KEY_ID` | ✅ | IAM step 1.4 | Used by boto3 for Textract/Rekognition/Transcribe |
| `AWS_SECRET_ACCESS_KEY` | ✅ | IAM step 1.4 | Used by boto3 |
| `AWS_REGION` | ✅ | Fixed: `us-east-1` | Region for all media clients |
| `REDIS_URL` | ✅ | Docker Compose | Cache for analysis results |

### Lambda (`apps/lambda/media-trigger`)

| Variable | Required | Source | Description |
|----------|----------|--------|-------------|
| `MEDIA_ANALYSIS_URL` | ✅ | Your deployment | URL Lambda calls to trigger analysis |
| `AWS_REGION` | ✅ | Fixed: `us-east-1` | Region for SDK calls |

> Lambda gets its own AWS credentials automatically from the execution role (`zerotrust-lambda-role`) — you do NOT put access keys in Lambda env vars.

---

## 8.3 — Generate JWT Secret

```powershell
# Using OpenSSL (if installed)
openssl rand -hex 32

# Or using PowerShell
-join ((1..64) | ForEach-Object { "{0:x2}" -f (Get-Random -Max 256) })
```

Add the output to `.env.local`:
```env
JWT_SECRET=<generated-64-char-hex>
```

---

## 8.4 — Validate All Variables Are Set

Run this PowerShell script to check which required variables are missing:

```powershell
$required = @(
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'AWS_DEFAULT_REGION',
    'AWS_REGION',
    'S3_MEDIA_BUCKET',
    'JWT_SECRET'
)

$env_content = Get-Content "C:\Users\PRIHTVIRAJ\Desktop\ZeroTRUST-AI4Bharat\.env.local" | 
  Where-Object { $_ -notmatch '^#' -and $_.Trim() -ne '' }

foreach ($var in $required) {
    $line = $env_content | Where-Object { $_ -match "^$var=" }
    $value = if ($line) { ($line -split '=', 2)[1].Trim() } else { $null }
    
    if ($value -and $value -ne 'your_access_key_here' -and $value -ne 'your_secret_key_here') {
        Write-Host "✅ $var" -ForegroundColor Green
    } else {
        Write-Host "❌ $var — NOT SET" -ForegroundColor Red
    }
}
```

---

## 8.5 — Full Bedrock Config Test

With all variables set, run the project's own test script:

```powershell
cd "C:\Users\PRIHTVIRAJ\Desktop\ZeroTRUST-AI4Bharat\apps\verification-engine"
.venv\Scripts\Activate.ps1
cd "C:\Users\PRIHTVIRAJ\Desktop\ZeroTRUST-AI4Bharat"
python scripts\test-aws-bedrock-config.py
```

This validates credentials, Bedrock model invocations, and optional API keys.

---

## Next Step

→ [09-improvements.md](09-improvements.md)
