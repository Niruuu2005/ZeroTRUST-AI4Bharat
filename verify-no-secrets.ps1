# ============================================================================
# Pre-Commit Security Verification Script
# ============================================================================
# Run this script before committing to GitHub to ensure no secrets are exposed
# Usage: .\verify-no-secrets.ps1
# ============================================================================

Write-Host "🔍 ZeroTRUST Security Verification - Checking for sensitive data..." -ForegroundColor Cyan
Write-Host ""

$errors = 0

# ============================================================================
# Function: Check for AWS Keys in Staged Files
# ============================================================================
function Test-AWSKeys {
    Write-Host "1️⃣  Checking for AWS Access Keys..." -ForegroundColor Yellow
    
    $awsKeys = git diff --cached | Select-String -Pattern "AKIA[0-9A-Z]{16}" -Quiet
    
    if ($awsKeys) {
        Write-Host "   ❌ FOUND AWS ACCESS KEYS in staged files!" -ForegroundColor Red
        Write-Host "      DO NOT COMMIT! Remove these credentials first." -ForegroundColor Red
        git diff --cached | Select-String -Pattern "AKIA[0-9A-Z]{16}"
        return $false
    } else {
        Write-Host "   ✅ No AWS keys found in staged files" -ForegroundColor Green
        return $true
    }
}

# ============================================================================
# Function: Check for Secret Access Keys
# ============================================================================
function Test-SecretKeys {
    Write-Host "2️⃣  Checking for AWS Secret Keys..." -ForegroundColor Yellow
    
    $secretKeys = git diff --cached | Select-String -Pattern "aws_secret_access_key.{0,5}=.{20,}" -Quiet
    
    if ($secretKeys) {
        Write-Host "   ❌ FOUND AWS SECRET KEYS in staged files!" -ForegroundColor Red
        return $false
    } else {
        Write-Host "   ✅ No secret keys found in staged files" -ForegroundColor Green
        return $true
    }
}

# ============================================================================
# Function: Check for Database Passwords
# ============================================================================
function Test-DatabasePasswords {
    Write-Host "3️⃣  Checking for database passwords..." -ForegroundColor Yellow
    
    # Look for postgresql:// with actual passwords (not placeholders)
    $dbUrls = git diff --cached | Select-String -Pattern "postgresql://[^:]+:[^@]{8,}@" -Quiet
    
    if ($dbUrls) {
        $content = git diff --cached | Select-String -Pattern "postgresql://[^:]+:[^@]{8,}@"
        # Check if it's a placeholder
        $isPlaceholder = $content -match "password@host" -or $content -match "your_password" -or $content -match "username:password"
        
        if ($dbUrls -and -not $isPlaceholder) {
            Write-Host "   ⚠️  FOUND DATABASE CONNECTION STRING with possible real password!" -ForegroundColor Red
            Write-Host "      Please verify these are placeholders only." -ForegroundColor Yellow
            return $false
        }
    }
    
    Write-Host "   ✅ No real database passwords found" -ForegroundColor Green
    return $true
}

# ============================================================================
# Function: Check for JWT Secrets
# ============================================================================
function Test-JWTSecrets {
    Write-Host "4️⃣  Checking for JWT secrets..." -ForegroundColor Yellow
    
    # Look for long hex strings that might be JWT secrets
    $jwtSecrets = git diff --cached | Select-String -Pattern "JWT_SECRET=\w{32,}" -Quiet
    
    if ($jwtSecrets) {
        $content = git diff --cached | Select-String -Pattern "JWT_SECRET=\w{64,}"
        # Check if it's a placeholder
        $isPlaceholder = $content -match "<generate" -or $content -match "your-jwt-secret"
        
        if ($jwtSecrets -and -not $isPlaceholder) {
            Write-Host "   ⚠️  FOUND POTENTIAL JWT SECRET!" -ForegroundColor Red
            Write-Host "      Verify this is a placeholder, not a real secret." -ForegroundColor Yellow
            return $false
        }
    }
    
    Write-Host "   ✅ No JWT secrets found" -ForegroundColor Green
    return $true
}

# ============================================================================
# Function: Check for Sensitive Files
# ============================================================================
function Test-SensitiveFiles {
    Write-Host "5️⃣  Checking for sensitive files in staging..." -ForegroundColor Yellow
    
    $sensitivePatterns = @(
        "\.env$",
        "SECRETS\.local",
        "accessKeys\.csv",
        "_accessKeys\.csv"
    )
    
    $stagedFiles = git diff --cached --name-only
    $foundSensitive = $false
    
    foreach ($pattern in $sensitivePatterns) {
        $matches = $stagedFiles | Select-String -Pattern $pattern
        if ($matches) {
            Write-Host "   ❌ FOUND SENSITIVE FILE: $matches" -ForegroundColor Red
            $foundSensitive = $true
        }
    }
    
    if (-not $foundSensitive) {
        Write-Host "   ✅ No sensitive files in staging area" -ForegroundColor Green
        return $true
    }
    return $false
}

# ============================================================================
# Function: Verify .gitignore is Working
# ============================================================================
function Test-GitignoreWorking {
    Write-Host "6️⃣  Verifying .gitignore is protecting sensitive files..." -ForegroundColor Yellow
    
    $protectedFiles = @(
        "SECRETS.local",
        "test-admin_accessKeys.csv",
        "apps/api-gateway/.env",
        "apps/web-portal/.env"
    )
    
    $allProtected = $true
    
    foreach ($file in $protectedFiles) {
        if (Test-Path $file) {
            $isIgnored = git check-ignore $file 2>$null
            if ($isIgnored) {
                # File is properly ignored
            } else {
                Write-Host "   ⚠️  WARNING: $file exists but is NOT gitignored!" -ForegroundColor Red
                $allProtected = $false
            }
        }
    }
    
    if ($allProtected) {
        Write-Host "   ✅ Sensitive files are properly gitignored" -ForegroundColor Green
        return $true
    }
    return $false
}

# ============================================================================
# Function: Check for test-admin_accessKeys.csv
# ============================================================================
function Test-CSVFileExists {
    Write-Host "7️⃣  Checking for AWS CSV files..." -ForegroundColor Yellow
    
    if (Test-Path "test-admin_accessKeys.csv") {
        Write-Host "   ⚠️  WARNING: test-admin_accessKeys.csv still exists!" -ForegroundColor Red
        Write-Host "      This file contains real AWS credentials." -ForegroundColor Yellow
        Write-Host "      Recommendation: Delete with 'Remove-Item test-admin_accessKeys.csv'" -ForegroundColor Yellow
        return $false
    } else {
        Write-Host "   ✅ No AWS CSV files found" -ForegroundColor Green
        return $true
    }
}

# ============================================================================
# Run All Checks
# ============================================================================
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                   RUNNING SECURITY CHECKS                  " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$results = @{
    "AWSKeys" = Test-AWSKeys
    "SecretKeys" = Test-SecretKeys
    "DatabasePasswords" = Test-DatabasePasswords
    "JWTSecrets" = Test-JWTSecrets
    "SensitiveFiles" = Test-SensitiveFiles
    "GitignoreWorking" = Test-GitignoreWorking
    "CSVFileExists" = Test-CSVFileExists
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                      RESULTS SUMMARY                       " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$failedChecks = $results.GetEnumerator() | Where-Object { -not $_.Value }

if ($failedChecks.Count -eq 0) {
    Write-Host "🎉 ALL CHECKS PASSED! Safe to commit." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  git commit -m 'your commit message'" -ForegroundColor White
    Write-Host "  git push origin main" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host "❌ FAILED CHECKS: $($failedChecks.Count)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Failed checks:" -ForegroundColor Yellow
    foreach ($check in $failedChecks) {
        Write-Host "  - $($check.Key)" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "⚠️  DO NOT COMMIT until all issues are resolved!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Actions required:" -ForegroundColor Yellow
    Write-Host "1. Review the failed checks above" -ForegroundColor White
    Write-Host "2. Remove any real credentials from staged files" -ForegroundColor White
    Write-Host "3. Run this script again: .\verify-no-secrets.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "For help, see: SECURITY_README.md" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}
