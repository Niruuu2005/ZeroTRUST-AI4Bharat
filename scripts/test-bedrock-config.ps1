#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test AWS Bedrock and External API configuration
.DESCRIPTION
    Validates AWS Bedrock models are accessible and external API keys are configured.
    This script wraps the Python test script for easier execution.
.EXAMPLE
    .\scripts\test-bedrock-config.ps1
#>

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  AWS Bedrock Configuration Test                           ║" -ForegroundColor Cyan
Write-Host "║  Task 1: Configure AWS Bedrock and External APIs         ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Check if .env.local exists
if (-not (Test-Path ".env.local")) {
    Write-Host "✗ .env.local not found. Please create it from .env.local.example" -ForegroundColor Red
    exit 1
}

Write-Host "✓ .env.local found" -ForegroundColor Green
Write-Host ""

# Install required packages if needed
Write-Host "Checking Python dependencies..." -ForegroundColor Cyan
$packages = @("boto3", "python-dotenv")
foreach ($package in $packages) {
    $installed = pip show $package 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing $package..." -ForegroundColor Yellow
        pip install $package --quiet
    }
}

Write-Host ""
Write-Host "Running configuration test..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Run the Python test script
python scripts/test-aws-bedrock-config.py

$exitCode = $LASTEXITCODE

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✓ Task 1 Configuration Test PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Review TASK_1_CONFIGURATION_GUIDE.md for details" -ForegroundColor White
    Write-Host "  2. Proceed to Task 2: Implement Normalization Layer" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "✗ Task 1 Configuration Test FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Action required:" -ForegroundColor Yellow
    Write-Host "  1. Review TASK_1_CONFIGURATION_GUIDE.md for detailed instructions" -ForegroundColor White
    Write-Host "  2. Enable Bedrock models in AWS Console (CRITICAL)" -ForegroundColor White
    Write-Host "  3. Optionally configure external API keys" -ForegroundColor White
    Write-Host "  4. Run this script again to verify" -ForegroundColor White
    Write-Host ""
}

exit $exitCode
