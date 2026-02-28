# ZeroTRUST Claim Verification Test Runner
# This script automates the execution of browser tests for claim verification

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ZeroTRUST Claim Verification Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if services are running
Write-Host "🔍 Checking service health..." -ForegroundColor Yellow

$apiHealth = $null
$verificationHealth = $null
$webPortalHealth = $null

try {
    $apiHealth = Invoke-WebRequest -Uri "http://localhost:3000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ API Gateway is running" -ForegroundColor Green
} catch {
    Write-Host "❌ API Gateway is not running on port 3000" -ForegroundColor Red
    Write-Host "   Please start it with: cd apps/api-gateway && npm run dev" -ForegroundColor Yellow
}

try {
    $verificationHealth = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Verification Engine is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Verification Engine is not running on port 8000" -ForegroundColor Red
    Write-Host "   Please start it with: cd apps/verification-engine && uvicorn src.main:app --reload" -ForegroundColor Yellow
}

try {
    $webPortalHealth = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Web Portal is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Web Portal is not running on port 5173" -ForegroundColor Red
    Write-Host "   Please start it with: cd apps/web-portal && npm run dev" -ForegroundColor Yellow
}

Write-Host ""

if (-not $apiHealth -or -not $verificationHealth -or -not $webPortalHealth) {
    Write-Host "⚠️  Some services are not running. Tests may fail." -ForegroundColor Yellow
    Write-Host "   Do you want to continue anyway? (Y/N)" -ForegroundColor Yellow
    $continue = Read-Host
    if ($continue -ne "Y" -and $continue -ne "y") {
        Write-Host "Exiting..." -ForegroundColor Red
        exit 1
    }
}

# Install Playwright if needed
Write-Host "📦 Checking Playwright installation..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules/@playwright")) {
    Write-Host "Installing Playwright..." -ForegroundColor Yellow
    npm install
    npx playwright install --with-deps
} else {
    Write-Host "✅ Playwright is installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Claim Verification Tests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Run tests
$testMode = $args[0]

switch ($testMode) {
    "headed" {
        Write-Host "Running tests in headed mode (visible browser)..." -ForegroundColor Yellow
        npx playwright test --headed
    }
    "debug" {
        Write-Host "Running tests in debug mode..." -ForegroundColor Yellow
        npx playwright test --debug
    }
    "ui" {
        Write-Host "Opening Playwright UI..." -ForegroundColor Yellow
        npx playwright test --ui
    }
    "chromium" {
        Write-Host "Running tests in Chromium only..." -ForegroundColor Yellow
        npx playwright test --project=chromium
    }
    "firefox" {
        Write-Host "Running tests in Firefox only..." -ForegroundColor Yellow
        npx playwright test --project=firefox
    }
    "webkit" {
        Write-Host "Running tests in WebKit only..." -ForegroundColor Yellow
        npx playwright test --project=webkit
    }
    default {
        Write-Host "Running tests in headless mode (all browsers)..." -ForegroundColor Yellow
        npx playwright test
    }
}

$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Execution Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($exitCode -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 View detailed report:" -ForegroundColor Yellow
    Write-Host "   npm run test:report" -ForegroundColor Cyan
} else {
    Write-Host "❌ Some tests failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "📊 View detailed report:" -ForegroundColor Yellow
    Write-Host "   npm run test:report" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🔍 Debug failed tests:" -ForegroundColor Yellow
    Write-Host "   npm run test:e2e:debug" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "📁 Test artifacts saved to: test-results/" -ForegroundColor Yellow
Write-Host "   - HTML report: test-results/html/index.html" -ForegroundColor Cyan
Write-Host "   - JSON results: test-results/results.json" -ForegroundColor Cyan
Write-Host "   - JUnit XML: test-results/junit.xml" -ForegroundColor Cyan
Write-Host "   - Screenshots: test-results/ (on failure)" -ForegroundColor Cyan
Write-Host "   - Videos: test-results/ (on failure)" -ForegroundColor Cyan
Write-Host ""

exit $exitCode
