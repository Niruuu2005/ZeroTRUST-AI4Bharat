# 🔐 Secrets & Credentials Setup Guide

**⚠️ IMPORTANT: Never commit actual credentials to GitHub!**

This guide explains how to obtain and configure all sensitive credentials needed for the ZeroTRUST AI4Bharat project.

---

## 📋 Quick Start Checklist

Before deploying or testing the application, you need:

- ✅ AWS Account with IAM user credentials
- ✅ Database connection details
- ✅ JWT secret keys
- ✅ (Optional) Third-party API keys for enhanced features

---

## 1️⃣ AWS Credentials

### Where to Get Them

1. **Login to AWS Console**: https://console.aws.amazon.com/
2. **Navigate to IAM** → Users → [Your User] → Security Credentials
3. **Create Access Key** → Choose "Application running outside AWS"
4. **Download CSV** or copy both:
   - Access Key ID (starts with `AKIA`)
   - Secret Access Key (shown only once!)

### Where to Use Them

**File: `apps/api-gateway/.env`**
```env
AWS_ACCESS_KEY_ID=AKIA________________
AWS_SECRET_ACCESS_KEY=________________________________________
AWS_DEFAULT_REGION=us-east-1
AWS_REGION=us-east-1
```

**File: `.env.local` (root directory)**
```env
AWS_ACCESS_KEY_ID=AKIA________________
AWS_SECRET_ACCESS_KEY=________________________________________
AWS_DEFAULT_REGION=us-east-1
```

### Security Notes

- ⚠️ **NEVER** commit these keys to GitHub
- 🔄 Rotate keys every 90 days
- 🗑️ Delete any CSV files after copying credentials
- 🔒 Use IAM roles for production (not access keys)

---

## 2️⃣ Database Configuration

### PostgreSQL / Supabase Database

#### Where to Get Connection String

**For Supabase:**
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to Project Settings → Database
4. Copy the connection string (pooler mode recommended)

**Format:**
```
postgresql://postgres.[project]:password@aws-[region].pooler.supabase.com:5432/postgres
```

#### Where to Use It

**File: `apps/api-gateway/.env`**
```env
DATABASE_URL=postgresql://username:password@host:5432/database
```

**Security:**
- Never expose database password in code
- Use connection pooling for production
- Consider AWS RDS with IAM authentication

---

## 3️⃣ JWT Secret Keys

### How to Generate

**Using OpenSSL (recommended):**
```bash
# Linux/Mac/WSL
openssl rand -hex 64

# PowerShell
[Convert]::ToBase64String((1..64 | ForEach-Object { Get-Random -Min 0 -Max 255 }))
```

### Where to Use Them

**File: `apps/api-gateway/.env`**
```env
JWT_SECRET=<64-character-random-string>
```

**Security:**
- Use different secrets for development and production
- Never reuse secrets across environments
- Store in AWS Secrets Manager for production

---

## 4️⃣ AWS Services Configuration

### S3 Bucket Name

**Where to Set:**
```env
S3_MEDIA_BUCKET=zerotrust-media-<environment>
```

Create bucket: https://s3.console.aws.amazon.com/s3/

### Bedrock Model Configuration

**File: `apps/api-gateway/.env`**
```env
MANAGER_MODEL_ID=us.amazon.nova-pro-v1:0
RESEARCH_MODEL_ID=us.mistral.pixtral-large-2502-v1:0
SENTIMENT_MODEL_ID=us.amazon.nova-lite-v1:0
BEDROCK_REGION=us-east-1
```

Enable models at: https://console.aws.amazon.com/bedrock/

### CloudWatch Logs (Optional)

```env
CW_LOG_GROUP=/zerotrust/api-gateway
CW_LOG_STREAM_PREFIX=api-gateway
```

---

## 5️⃣ Optional Third-Party APIs

### News APIs (FREE Tiers Available)

#### NewsAPI.org
- **Website**: https://newsapi.org/
- **Free Tier**: 100 requests/day
- **Get Key**: Sign up → Copy API key
```env
NEWS_API_KEY=your_newsapi_key_here
```

#### GNews.io
- **Website**: https://gnews.io/
- **Free Tier**: 100 requests/day
```env
GNEWS_API_KEY=your_gnews_key_here
```

### Search APIs

#### Google Custom Search
- **Console**: https://console.cloud.google.com/
- **Enable**: Custom Search API
- **Create**: Custom Search Engine at https://cse.google.com/
```env
GOOGLE_SEARCH_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
```

#### Google Fact Check API
- **Console**: https://console.cloud.google.com/
- **Enable**: Fact Check Tools API
```env
GOOGLE_FACTCHECK_API_KEY=your_factcheck_api_key
```

### Social Media APIs

#### Reddit API
- **Website**: https://www.reddit.com/prefs/apps
- **Create App**: Select "script" type
```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
```

#### Twitter/X API (Optional)
- **Website**: https://developer.twitter.com/
```env
TWITTER_BEARER_TOKEN=your_bearer_token
```

### Scientific APIs

#### PubMed E-utilities (Optional - Higher Rate Limits)
- **Website**: https://www.ncbi.nlm.nih.gov/account/
- **Sign up** for NCBI account
- **Get API Key** from settings
```env
PUBMED_API_KEY=your_pubmed_api_key
```

**Note:** PubMed works without API key but with lower rate limits.

---

## 📂 File Structure

Your sensitive files should be organized as:

```
ZeroTRUST-AI4Bharat/
├── .env.local                    # Root environment (gitignored)
├── SECRETS.local                 # Your personal backup (gitignored)
├── apps/
│   ├── api-gateway/
│   │   └── .env                  # API gateway secrets (gitignored)
│   └── web-portal/
│       └── .env                  # Web portal config (gitignored)
└── test-admin_accessKeys.csv    # AWS keys backup (gitignored)
```

---

## 🔄 Creating Your Configuration Files

### Step 1: Create Root `.env.local`

```bash
# Copy template
cp .env.local.example .env.local

# Edit with your values (use a text editor)
nano .env.local  # or notepad .env.local on Windows
```

### Step 2: Create API Gateway `.env`

```bash
# Copy example
cp apps/api-gateway/.env.example apps/api-gateway/.env

# Edit with your values
nano apps/api-gateway/.env
```

### Step 3: Create Web Portal `.env`

```bash
# Update API URL
echo "VITE_API_URL=http://localhost:8000" > apps/web-portal/.env
```

### Step 4: Backup Your Secrets (Optional)

Create `SECRETS.local` (gitignored) for your personal backup:

```env
# SECRETS.local - Personal backup (NEVER commit!)
# Generated: 2026-03-03

[AWS]
AWS_ACCESS_KEY_ID=AKIA________________
AWS_SECRET_ACCESS_KEY=________________________________________

[DATABASE]
DATABASE_URL=postgresql://user:pass@host:5432/db
SUPABASE_PASSWORD=________________

[SECURITY]
JWT_SECRET=________________________________________________________________

[S3]
S3_MEDIA_BUCKET=zerotrust-media-dev

[THIRD_PARTY_APIS]
NEWS_API_KEY=
GNEWS_API_KEY=
GOOGLE_SEARCH_KEY=
GOOGLE_SEARCH_ENGINE_ID=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
```

---

## 🔒 Security Best Practices

### ✅ DO

- ✅ Use `.env.local` for development secrets (gitignored)
- ✅ Use AWS Secrets Manager for production
- ✅ Rotate credentials regularly (every 90 days)
- ✅ Use different secrets per environment (dev/staging/prod)
- ✅ Enable MFA on your AWS account
- ✅ Use IAM roles instead of access keys when possible
- ✅ Delete AWS key CSV files after copying
- ✅ Review .gitignore before every commit

### ❌ DON'T

- ❌ Commit `.env` files to GitHub
- ❌ Share credentials via email or chat
- ❌ Use production credentials in development
- ❌ Hardcode secrets in source code
- ❌ Reuse passwords across services
- ❌ Store credentials in plain text outside `.env` files
- ❌ Commit AWS CSV key files

---

## 🚨 Emergency: Credentials Exposed

If you accidentally commit credentials to GitHub:

### Immediate Actions

1. **Revoke Immediately**
   - AWS: Delete the access key in IAM console
   - GitHub: Delete the repository or use git filter-branch
   - Database: Change password immediately

2. **Create New Credentials**
   - Generate new AWS access keys
   - Update all `.env` files

3. **Clean Git History**
   ```bash
   # Remove file from all commits
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/file" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push (WARNING: Destructive)
   git push origin --force --all
   ```

4. **Check for Automated Scanning**
   - GitHub will scan for common secrets
   - AWS GuardDuty may alert you
   - Rotate all credentials as precaution

---

## 📞 Support

### AWS Documentation
- IAM Users: https://docs.aws.amazon.com/IAM/latest/UserGuide/
- Bedrock: https://docs.aws.amazon.com/bedrock/
- S3: https://docs.aws.amazon.com/s3/

### Project Documentation
- [AWS Migration Guide](./AWS_MIGRATION_GUIDE.md)
- [Quick Start Free Tier](./QUICKSTART_FREE_TIER.md)
- [Development Plan](./DEVELOPMENT_PLAN.md)

---

## ✅ Final Verification

Before committing to GitHub, run this checklist:

```bash
# Check for sensitive data
git diff --staged | grep -iE "AKIA|secret|password|key"

# Verify .gitignore is working
git status --ignored

# Ensure sensitive files are not tracked
git ls-files | grep -E "\.env$|accessKeys\.csv|SECRETS\.local"
# (This should return nothing)
```

---

**Last Updated**: March 3, 2026  
**Maintainer**: ZeroTRUST AI4Bharat Team
