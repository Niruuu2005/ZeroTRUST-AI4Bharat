# ZeroTRUST Backend Pipeline Test
# Run from repo root. Requires: API Gateway on :3000, optionally VE on :8000, media-analysis on :8001.
# Usage: .\scripts\test-backend.ps1

$ErrorActionPreference = "Stop"
$API = "http://localhost:3000"
$VE   = "http://localhost:8000"
$MEDIA = "http://localhost:8001"

$passed = 0
$failed = 0
$results = @()

function Test-Step {
    param([string]$Name, [scriptblock]$Run)
    try {
        & $Run
        $script:passed++
        $script:results += [pscustomobject]@{ Element = $Name; Status = "PASS" }
        return $true
    } catch {
        $script:failed++
        $script:results += [pscustomobject]@{ Element = $Name; Status = "FAIL"; Detail = $_.Exception.Message }
        return $false
    }
}

Write-Host "`n=== ZeroTRUST Backend Pipeline Tests ===`n" -ForegroundColor Cyan

# 1. API Gateway health (Diagram 1 - API layer)
Test-Step "API Gateway health" {
    $r = Invoke-RestMethod -Uri "$API/health" -Method Get
    if ($r.status -ne "healthy" -or $r.service -ne "api-gateway") { throw "Unexpected response: $($r | ConvertTo-Json)" }
} | Out-Null

# 2. Verification Engine health (Diagram 1 - Compute) — optional
$veUp = $false
try {
    $r = Invoke-RestMethod -Uri "$VE/health" -Method Get -TimeoutSec 2
    if ($r.status -eq "healthy" -and $r.service -eq "verification-engine") { $veUp = $true; $passed++; $results += [pscustomobject]@{ Element = "Verification Engine health"; Status = "PASS" } }
} catch { $results += [pscustomobject]@{ Element = "Verification Engine health"; Status = "SKIP"; Detail = "Not running" } }

# 3. Media Analysis health (Diagram 4 - Media pipeline) — optional
$mediaUp = $false
try {
    $r = Invoke-RestMethod -Uri "$MEDIA/health" -Method Get -TimeoutSec 2
    if ($r.status -eq "healthy" -and $r.service -eq "media-analysis") { $mediaUp = $true; $passed++; $results += [pscustomobject]@{ Element = "Media Analysis health"; Status = "PASS" } }
} catch { $results += [pscustomobject]@{ Element = "Media Analysis health"; Status = "SKIP"; Detail = "Not running" } }

# 4. Auth: register (Diagram 1 - API)
$testEmail = "test-backend-" + [guid]::NewGuid().ToString("N").Substring(0,8) + "@example.com"
$testPassword = "TestPass123!"
Test-Step "Auth register" {
    $body = @{ email = $testEmail; password = $testPassword } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "$API/api/v1/auth/register" -Method Post -Body $body -ContentType "application/json"
    if (-not $r.message -or $r.message -notmatch "success") { throw $r }
} | Out-Null

# 5. Auth: login and get token
$token = $null
Test-Step "Auth login" {
    $body = @{ email = $testEmail; password = $testPassword } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "$API/api/v1/auth/login" -Method Post -Body $body -ContentType "application/json"
    if (-not $r.accessToken) { throw "No accessToken" }
    $script:token = $r.accessToken
} | Out-Null

# 6. Verify (text) - full pipeline Diagram 3: cache miss -> VE -> store (requires VE)
if ($veUp) {
    Test-Step "Verify (text) - full pipeline" {
        $body = @{ content = "The Earth orbits the Sun once every 365 days. This is a test claim for pipeline verification."; type = "text"; source = "api" } | ConvertTo-Json
        $r = Invoke-RestMethod -Uri "$API/api/v1/verify" -Method Post -Body $body -ContentType "application/json"
        if ($r.error -and -not $r.credibility_score) { throw $r.message }
        if ($null -ne $r.credibility_score -and ($r.credibility_score -lt 0 -or $r.credibility_score -gt 100)) { throw "Invalid score: $($r.credibility_score)" }
    } | Out-Null
} else {
    $results += [pscustomobject]@{ Element = "Verify (text) - full pipeline"; Status = "SKIP"; Detail = "Verification Engine not running" }
}

# 7. Verify by ID — get first verification id from history and fetch (Diagram 3 - store/retrieve)
$verifyId = $null
if ($token) {
    try {
        $hist = Invoke-RestMethod -Uri "$API/api/v1/history?page=1&limit=1" -Method Get -Headers @{ Authorization = "Bearer $token" }
        if ($hist.items.Count -gt 0) { $script:verifyId = $hist.items[0].id }
    } catch {}
}
if ($verifyId) {
    Test-Step "GET verify by ID" {
        $r = Invoke-RestMethod -Uri "$API/api/v1/verify/$verifyId" -Method Get
        if (-not $r.id -and -not $r.credibilityScore) { throw "Missing id or credibilityScore" }
    } | Out-Null
} else {
    $results += [pscustomobject]@{ Element = "GET verify by ID"; Status = "SKIP"; Detail = "No verification id" }
}

# 8. History (Diagram 1 - authenticated)
Test-Step "History (authenticated)" {
    if (-not $token) { throw "No token" }
    $r = Invoke-RestMethod -Uri "$API/api/v1/history?page=1&limit=5" -Method Get -Headers @{ Authorization = "Bearer $token" }
    if ($null -eq $r.items) { throw "No items key" }
} | Out-Null

# 9. Trending (Diagram 2 - Trending Fake News)
Test-Step "Trending" {
    $r = Invoke-RestMethod -Uri "$API/api/v1/trending?limit=5&days=7" -Method Get
    if ($null -eq $r.items) { throw "No items key" }
} | Out-Null

# 10. Media presign (Diagram 4 - S3 presign) - expect 503 when S3_MEDIA_BUCKET not set
Test-Step "Media presign (expect 503 or 200)" {
    $body = @{ contentType = "image/jpeg" } | ConvertTo-Json
    try {
        $r = Invoke-RestMethod -Uri "$API/api/v1/media/presign" -Method Post -Body $body -ContentType "application/json"
        if (-not $r.uploadUrl) { throw "No uploadUrl" }
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 503) { return } # expected when no bucket
        throw
    }
} | Out-Null

# 11. Cache: second verify same content should hit Redis (Diagram 6 - Tier 1) — only if we ran full verify
if ($veUp) {
    Test-Step "Cache Tier 1 (Redis) hit" {
        $body = @{ content = "The Earth orbits the Sun once every 365 days. This is a test claim for pipeline verification."; type = "text" } | ConvertTo-Json
        $r = Invoke-RestMethod -Uri "$API/api/v1/verify" -Method Post -Body $body -ContentType "application/json"
        if (-not $r.cached) { throw "Expected cached: true (Redis hit)" }
        if ($r.cache_tier -ne "redis") { throw "Expected cache_tier: redis, got $($r.cache_tier)" }
    } | Out-Null
} else {
    $results += [pscustomobject]@{ Element = "Cache Tier 1 (Redis) hit"; Status = "SKIP"; Detail = "Requires prior verify" }
}

# 12. Unauthenticated history returns 401
Test-Step "History without token returns 401" {
    try {
        Invoke-RestMethod -Uri "$API/api/v1/history" -Method Get
        throw "Expected 401"
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 401) { return }
        throw
    }
} | Out-Null

Write-Host "`n--- Results ---" -ForegroundColor Cyan
$results | Format-Table -AutoSize
Write-Host "Passed: $passed  Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
if ($failed -gt 0) {
    $results | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object { Write-Host "  $($_.Element): $($_.Detail)" -ForegroundColor Red }
    exit 1
}
exit 0
