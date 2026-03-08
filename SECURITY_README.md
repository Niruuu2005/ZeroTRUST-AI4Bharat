# 🔐 Security & Credentials - Quick Reference

## ⚠️ BEFORE COMMITTING TO GITHUB

**CRITICAL**: This repository contains example/placeholder credentials only. Real credentials must be configured locally.

### 🚨 Quick Pre-Commit Check

```powershell
# Run this before git push
git diff --staged | Select-String -Pattern "AKIA[0-9A-Z]{16}|secret_access_key.{20,}"
# Should return NOTHING
```

---

## 📁 Important Files

| File | Purpose | Status |
|------|---------|--------|
| [SETUP_SECRETS_GUIDE.md](SETUP_SECRETS_GUIDE.md) | **START HERE** - Complete guide to obtain & configure credentials | ✅ Read First |
| [DELETE_BEFORE_COMMIT.md](DELETE_BEFORE_COMMIT.md) | Checklist of sensitive files to delete | ⚠️ Action Required |
| [SECRETS.local](SECRETS.local) | Your personal credential backup | 🔒 Keep Private |
| `test-admin_accessKeys.csv` | AWS keys CSV (if exists) | ❌ DELETE THIS |

---

## 🎯 Quick Setup (3 Steps)

### 1. Get Your Credentials

Follow [SETUP_SECRETS_GUIDE.md](SETUP_SECRETS_GUIDE.md) to obtain:
- AWS access keys (from IAM console)
- Database connection string (from Supabase/RDS)
- JWT secret (generate new one)

### 2. Configure Environment Files

```powershell
# API Gateway
cd apps/api-gateway
cp .env.example .env
# Edit .env with your real credentials

# Web Portal
cd ../web-portal
cp .env.example .env
# Edit if needed (default: http://localhost:8000)
```

### 3. Verify Everything is Secure

```powershell
# Check .gitignore is working
git status --ignored | Select-String -Pattern "\.env"

# Should see:
# .env (ignored)
# SECRETS.local (ignored)
# test-admin_accessKeys.csv (ignored)
```

---

## 🔍 Files Containing Placeholders Only

These files are safe to commit - they contain NO real credentials:

- ✅ `apps/api-gateway/.env` - Now contains placeholders
- ✅ `apps/api-gateway/.env.example` - Template for users
- ✅ `apps/web-portal/.env.example` - Template for users
- ✅ `aws-setup/08-env-config.md` - Now contains placeholders
- ✅ `.env.local.example` - Template at root

---

## 🔐 Files to NEVER Commit

These files are in `.gitignore` but verify they're not tracked:

- ❌ `SECRETS.local` - Your credential backup
- ❌ `test-admin_accessKeys.csv` - AWS keys (DELETE THIS)
- ❌ `.env.local` - Root environment
- ❌ `apps/**/.env` - Service environments
- ❌ Any file matching `*credentials*.json`
- ❌ Any file matching `*secret*.json`

---

## 🚀 For New Contributors

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/ZeroTRUST-AI4Bharat.git
   cd ZeroTRUST-AI4Bharat
   ```

2. **Read the setup guide**
   - Open [SETUP_SECRETS_GUIDE.md](SETUP_SECRETS_GUIDE.md)
   - Follow instructions to get your own credentials

3. **Configure your environment**
   ```powershell
   # Copy example files
   cp apps/api-gateway/.env.example apps/api-gateway/.env
   cp apps/web-portal/.env.example apps/web-portal/.env
   
   # Edit with your credentials
   notepad apps/api-gateway/.env
   ```

4. **Test the setup**
   ```powershell
   # Check AWS credentials work
   python scripts/test-aws-bedrock-config.py
   ```

---

## 📖 Documentation

- **Complete Setup Guide**: [SETUP_SECRETS_GUIDE.md](SETUP_SECRETS_GUIDE.md)
- **Pre-Commit Checklist**: [DELETE_BEFORE_COMMIT.md](DELETE_BEFORE_COMMIT.md)
- **AWS Migration**: [AWS_MIGRATION_GUIDE.md](AWS_MIGRATION_GUIDE.md)
- **Quick Start**: [QUICKSTART_FREE_TIER.md](QUICKSTART_FREE_TIER.md)

---

## 🆘 Emergency: I Committed Secrets!

If you accidentally committed real credentials:

### Immediate Actions

1. **Revoke the credentials**
   - AWS: IAM Console → Users → Security Credentials → Delete access key
   - Database: Change password immediately

2. **Remove from Git history**
   ```powershell
   # This is destructive - backup first!
   git filter-branch --force --index-filter `
     "git rm --cached --ignore-unmatch path/to/secret-file" `
     --prune-empty --tag-name-filter cat -- --all
   
   git push origin --force --all
   ```

3. **Generate new credentials**
   - Create new AWS access keys
   - Generate new JWT secret
   - Update all local `.env` files

4. **Notify your team**
   - All developers need to pull the cleaned history
   - All need to update their credentials

---

## ✅ Verification Commands

```powershell
# 1. Check no secrets are staged
git diff --staged | Select-String -Pattern "AKIA|secret.*=.*[a-zA-Z0-9]{20,}"

# 2. Verify .env files are ignored
git check-ignore apps/api-gateway/.env apps/web-portal/.env SECRETS.local
# Should return the file paths (means they're ignored)

# 3. Check what will be committed
git status

# 4. Scan all tracked files for AWS keys (should find none)
git grep -i "AKIA3C4G5RHS" $(git ls-files)
# Should return: nothing

# 5. Check for database passwords
git grep -i "postgresql://.*:.*@" $(git ls-files)
# Should only show examples/placeholders
```

---

## 📞 Support

- File structure: Everything is now safe with placeholders
- Secrets backed up in: `SECRETS.local` (gitignored)
- Setup instructions: [SETUP_SECRETS_GUIDE.md](SETUP_SECRETS_GUIDE.md)

---

**Last Updated**: March 3, 2026  
**Security Review**: ✅ All sensitive data removed from repository
