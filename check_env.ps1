$required = @(
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'AWS_DEFAULT_REGION',
    'AWS_REGION',
    'S3_MEDIA_BUCKET',
    'JWT_SECRET',
    'MEDIA_ANALYSIS_URL'
)

$env_path = "C:\Users\PRIHTVIRAJ\Desktop\ZeroTRUST-AI4Bharat\.env.local"
Write-Host "Checking .env.local at: $env_path"

if (Test-Path $env_path) {
    $env_content = Get-Content $env_path | Where-Object { $_ -notmatch '^#' -and $_.Trim() -ne '' }
    
    foreach ($var in $required) {
        $line = $env_content | Where-Object { $_ -match "^$var=" }
        $value = if ($line) { ($line -split '=', 2)[1].Trim() } else { $null }
        
        if ($value -and $value -ne 'AKIAIOSFODNN7EXAMPLE') {
            Write-Host "  ✅ $var is set"
        } else {
            Write-Host "  ❌ $var is MISSING"
        }
    }
} else {
    Write-Host "  ERROR: .env.local not found."
}
