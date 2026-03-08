# ⚠️ IMPORTANT: Sensitive Files to Delete Before Committing

This file lists sensitive files that contain real credentials. These files should be deleted or moved outside the repository before committing to GitHub.

## 📋 Files to Handle

### ❌ Delete These Files:

1. **test-admin_accessKeys.csv**
   - Location: Root directory
   - Contains: Real AWS access keys
   - Action: **DELETE THIS FILE** after copying credentials to SECRETS.local
   - Command: `Remove-Item test-admin_accessKeys.csv`

### ✅ Files Already Protected:

2. **SECRETS.local**
   - Location: Root directory
   - Contains: Backup of all your real credentials
   - Status: ✅ Already in .gitignore
   - Keep this file PRIVATE and NEVER commit it

3. **apps/api-gateway/.env**
   - Status: ✅ Now contains only placeholders
   - Note: Your real values are backed up in SECRETS.local

4. **apps/web-portal/.env**
   - Status: ✅ Now contains only placeholders

5. **.env.local** (if it exists)
   - Status: ✅ Already in .gitignore

## 🔍 How to Verify Before Committing

Run these commands to check for sensitive data:

```powershell
# Check what files will be committed
git status

# Search for potential AWS keys in staged files
git diff --staged | Select-String -Pattern "AKIA[0-9A-Z]{16}"

# Verify .env files are gitignored
git ls-files | Select-String -Pattern "\.env$"
# (Should return nothing or only .env.example files)

# Check for CSV files
git ls-files | Select-String -Pattern "\.csv$"
# (Should return nothing or only sample/example files)
```

## ✅ Final Checklist Before `git push`

- [ ] Deleted `test-admin_accessKeys.csv`
- [ ] Verified `SECRETS.local` is in .gitignore
- [ ] No real credentials in `apps/api-gateway/.env`
- [ ] No real credentials in `aws-setup/08-env-config.md`
- [ ] Run: `git status --ignored` to check ignored files
- [ ] Run: `git diff --cached` to review staged changes
- [ ] No AWS keys pattern (AKIA...) in staged files
- [ ] No JWT secrets in staged files
- [ ] No database passwords in staged files

## 📝 Quick Command to Delete Sensitive File

```powershell
# Delete the AWS keys CSV file
Remove-Item -Path "test-admin_accessKeys.csv" -Force

# Confirm it's deleted
Test-Path "test-admin_accessKeys.csv"
# Should return: False
```

## 🔐 Your Credentials Are Safe In:

- **SECRETS.local** - Personal backup (gitignored)
- **AWS Console** - You can always retrieve/regenerate them
- **Password Manager** - Copy them to your password manager for safekeeping

---

**Remember**: Once you delete test-admin_accessKeys.csv, you can no longer recover the secret key from AWS. Make sure you've backed it up to SECRETS.local or your password manager first!
