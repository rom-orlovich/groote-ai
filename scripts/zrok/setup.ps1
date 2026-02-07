$ErrorActionPreference = "Stop"

$ZrokShareName = if ($env:ZROK_SHARE_NAME) { $env:ZROK_SHARE_NAME } else { "my-share-name" }
$LocalPort = if ($env:LOCAL_PORT) { $env:LOCAL_PORT } else { "3005" }
$InstallDir = "$env:USERPROFILE\.local\bin"

Write-Host "=== zrok Setup for Groote AI ==="
Write-Host ""

if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

$ZrokBin = Get-Command zrok -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $ZrokBin -and (Test-Path "$InstallDir\zrok.exe")) {
    $ZrokBin = "$InstallDir\zrok.exe"
}

if (-not $ZrokBin) {
    Write-Host "[1/4] Installing zrok..."

    $Arch = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "386" }
    $LatestRelease = Invoke-RestMethod -Uri "https://api.github.com/repos/openziti/zrok/releases/latest"
    $Version = $LatestRelease.tag_name -replace '^v', ''
    $DownloadUrl = "https://github.com/openziti/zrok/releases/download/v${Version}/zrok_${Version}_windows_${Arch}.tar.gz"

    Write-Host "  Downloading zrok v${Version} for windows/${Arch}..."
    $TempFile = "$env:TEMP\zrok.tar.gz"
    $TempTar = "$env:TEMP\zrok.tar"
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempFile

    if (Get-Command tar -ErrorAction SilentlyContinue) {
        tar -xzf $TempFile -C $InstallDir
    } else {
        Write-Host "  Error: 'tar' command not found. Please install zrok manually:"
        Write-Host "  https://docs.zrok.io/docs/guides/install/windows/"
        exit 1
    }

    Remove-Item $TempFile -Force -ErrorAction SilentlyContinue
    $ZrokBin = "$InstallDir\zrok.exe"

    $CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($CurrentPath -notlike "*$InstallDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$CurrentPath;$InstallDir", "User")
        $env:Path = "$env:Path;$InstallDir"
        Write-Host "  Added $InstallDir to PATH"
    }

    Write-Host "  Installed to $ZrokBin"
} else {
    $VersionOutput = & $ZrokBin version 2>&1 | Select-Object -First 1
    Write-Host "[1/4] zrok already installed ($VersionOutput)"
}

Write-Host ""
Write-Host "[2/4] Account setup"

$StatusResult = & $ZrokBin status 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  zrok environment already enabled"
} else {
    Write-Host ""
    Write-Host "  You need a free zrok account:"
    Write-Host "    1. Go to https://myzrok.io and sign up"
    Write-Host "    2. Check your email for the enable token"
    Write-Host "    3. Run: $ZrokBin enable <TOKEN_FROM_EMAIL>"
    Write-Host ""
    Write-Host "  Then re-run this script: .\make.ps1 tunnel-setup"
    exit 1
}

Write-Host ""
Write-Host "[3/4] Reserving permanent share name '${ZrokShareName}'..."

$ReserveOutput = & $ZrokBin reserve public "http://localhost:${LocalPort}" --unique-name $ZrokShareName 2>&1
$ReserveStr = $ReserveOutput | Out-String

if ($ReserveStr -match "reserved frontend endpoint") {
    Write-Host "  Reserved: https://${ZrokShareName}.tunnel-domain.example"
} elseif ($ReserveStr -match "already reserved") {
    Write-Host "  Already reserved: https://${ZrokShareName}.tunnel-domain.example"
} else {
    Write-Host "  $ReserveStr"
    Write-Host "  If the name is taken, set ZROK_SHARE_NAME in .env to a different name"
}

Write-Host ""
Write-Host "[4/4] Configuration"
Write-Host ""
Write-Host "  Add to your .env file:"
Write-Host "    PUBLIC_URL=https://${ZrokShareName}.tunnel-domain.example"
Write-Host "    ZROK_SHARE_NAME=${ZrokShareName}"
Write-Host ""
Write-Host "=== Setup complete! ==="
Write-Host ""
Write-Host "  Start tunnel:  .\make.ps1 tunnel-zrok"
Write-Host "  Your URL:      https://${ZrokShareName}.tunnel-domain.example"
