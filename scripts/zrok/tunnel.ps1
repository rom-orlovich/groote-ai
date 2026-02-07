$ErrorActionPreference = "Stop"

$ZrokShareName = if ($env:ZROK_SHARE_NAME) { $env:ZROK_SHARE_NAME } else { "my-share-name" }
$LocalPort = if ($env:LOCAL_PORT) { $env:LOCAL_PORT } else { "3005" }
$PublicUrl = "https://${ZrokShareName}.tunnel-domain.example"

$ZrokBin = Get-Command zrok -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $ZrokBin) {
    $UserBin = "$env:USERPROFILE\.local\bin\zrok.exe"
    if (Test-Path $UserBin) {
        $ZrokBin = $UserBin
    } else {
        Write-Host "Error: zrok not installed."
        Write-Host ""
        Write-Host "Run setup first: .\make.ps1 tunnel-setup"
        exit 1
    }
}

$StatusResult = & $ZrokBin status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: zrok not enabled. Run: $ZrokBin enable <YOUR_TOKEN>"
    Write-Host ""
    Write-Host "  1. Create account at https://myzrok.io"
    Write-Host "  2. Check email for token"
    Write-Host "  3. Run: $ZrokBin enable <TOKEN>"
    exit 1
}

Write-Host "Starting zrok tunnel: ${PublicUrl} -> http://localhost:${LocalPort}"
Write-Host ""
Write-Host "Routes (via nginx on port ${LocalPort}):"
Write-Host "  /           -> external-dashboard (React SPA)"
Write-Host "  /api/*      -> dashboard-api:5000"
Write-Host "  /oauth/*    -> oauth-service:8010"
Write-Host "  /webhooks/* -> api-gateway:8000"
Write-Host "  /ws         -> dashboard-api:5000 (WebSocket)"
Write-Host ""
Write-Host "Webhook URLs:"
Write-Host "  GitHub: ${PublicUrl}/webhooks/github"
Write-Host "  Jira:   ${PublicUrl}/webhooks/jira"
Write-Host "  Slack:  ${PublicUrl}/webhooks/slack"
Write-Host ""
Write-Host "OAuth callback: ${PublicUrl}/oauth/callback"
Write-Host ""

& $ZrokBin share reserved $ZrokShareName --headless
