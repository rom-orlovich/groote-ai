param(
    [Parameter(Position = 0)]
    [string]$Command = "help",

    [string]$Provider = "claude",
    [int]$Scale = 1,
    [string]$Service = "",
    [string]$Msg = ""
)

$ErrorActionPreference = "Stop"
$DC = "docker-compose"

function Write-Status($icon, $message) {
    Write-Host "$icon $message"
}

function Invoke-Help {
    Write-Host @"
Groote AI Commands (Windows PowerShell)
========================================

Usage: .\make.ps1 <command> [options]

CLI:
  .\make.ps1 cli -Provider claude -Scale 1    Start Claude CLI
  .\make.ps1 cli -Provider cursor -Scale 1    Start Cursor CLI
  .\make.ps1 cli-claude                       Start Claude CLI (shortcut)
  .\make.ps1 cli-cursor                       Start Cursor CLI (shortcut)
  .\make.ps1 cli-down -Provider claude        Stop CLI
  .\make.ps1 cli-logs -Provider claude        View CLI logs

Services:
  .\make.ps1 up                               Start all services
  .\make.ps1 down                             Stop all services
  .\make.ps1 health                           Check service health
  .\make.ps1 logs -Service api-gateway        View service logs
  .\make.ps1 build                            Build Docker images

Testing:
  .\make.ps1 test                             Run all tests
  .\make.ps1 test-api-gateway                 Run API Gateway tests
  .\make.ps1 test-agent-engine                Run Agent Engine tests
  .\make.ps1 test-dashboard                   Run Dashboard API tests
  .\make.ps1 test-logger                      Run Task Logger tests
  .\make.ps1 test-services                    Run API Services tests
  .\make.ps1 test-cov                         Run tests with coverage

Database:
  .\make.ps1 db-migrate -Msg "..."            Create migration
  .\make.ps1 db-upgrade                       Apply migrations

Code Quality:
  .\make.ps1 lint                             Run ruff linter
  .\make.ps1 format                           Auto-format with ruff
  .\make.ps1 clean                            Clean cache directories

Knowledge Services:
  .\make.ps1 knowledge-up                     Start knowledge services
  .\make.ps1 knowledge-down                   Stop knowledge services
  .\make.ps1 knowledge-logs                   View knowledge service logs
  .\make.ps1 knowledge-build                  Build knowledge services

Networking:
  .\make.ps1 tunnel                           Start ngrok tunnel (uses NGROK_DOMAIN from .env)

Environment:
  .\make.ps1 init                             Initialize project
  .\make.ps1 up-full                          Start all services including knowledge

Ports:
  8000  - API Gateway
  8080  - Agent Engine
  5000  - Dashboard API
  3005  - External Dashboard
  8010  - OAuth Service
  8001  - ChromaDB
  6379  - Redis
  5432  - PostgreSQL
"@
}

function Invoke-Init {
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
    }
    Write-Status "Done." "Initialized. Edit .env with your credentials, then run: .\make.ps1 up"
}

function Invoke-Build {
    & $DC build
}

function Invoke-Up {
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
    }
    & $DC build
    & $DC up -d
    Start-Sleep -Seconds 5
    Write-Host "Checking services..."
    Invoke-Health
    Write-Host ""
    Write-Status "Done." "Groote AI ready"
    Write-Host "   API Gateway: http://localhost:8000"
    Write-Host "   Dashboard:   http://localhost:3005"
    Write-Host "   Dashboard API: http://localhost:5000"
}

function Invoke-Down {
    Write-Host "Stopping Groote AI services..."
    & $DC down
    Write-Status "Done." "Services stopped"
}

function Invoke-Health {
    Write-Host "Service Health:"

    $services = @(
        @{ Name = "API Gateway (8000)"; Url = "http://localhost:8000/health" },
        @{ Name = "Agent Engine (8080)"; Url = "http://localhost:8080/health" },
        @{ Name = "Dashboard API (5000)"; Url = "http://localhost:5000/api/health" },
        @{ Name = "OAuth Service (8010)"; Url = "http://localhost:8010/health" },
        @{ Name = "ChromaDB (8001)"; Url = "http://localhost:8001/api/v1/heartbeat" }
    )

    foreach ($svc in $services) {
        try {
            $null = Invoke-WebRequest -Uri $svc.Url -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            Write-Host "  OK $($svc.Name)"
        }
        catch {
            Write-Host "  FAIL $($svc.Name)"
        }
    }

    try {
        & $DC exec -T redis redis-cli ping 2>$null | Out-Null
        Write-Host "  OK Redis (6379)"
    }
    catch {
        Write-Host "  FAIL Redis (6379)"
    }

    try {
        & $DC exec -T postgres pg_isready -U agent 2>$null | Out-Null
        Write-Host "  OK PostgreSQL (5432)"
    }
    catch {
        Write-Host "  FAIL PostgreSQL (5432)"
    }
}

function Invoke-Logs {
    if ($Service) {
        & $DC logs -f $Service
    }
    else {
        & $DC logs -f
    }
}

function Invoke-CliStart {
    param([string]$P, [int]$S)

    Write-Host "Starting $P CLI..."

    & $DC up -d redis postgres 2>$null
    docker network create agent-network 2>$null

    $env:CLI_PROVIDER = $P
    & $DC -f docker-compose.cli.yml -p "$P-cli" --env-file .env build cli

    $existing = (docker ps --filter "name=$P-cli-cli" -q | Measure-Object -Line).Lines
    $target = if ($S -ge 1) { $S } else { $existing + 1 }
    if ($target -lt 1) { $target = 1 }

    Write-Host "Scaling to $target instance(s)..."
    & $DC -f docker-compose.cli.yml -p "$P-cli" --env-file .env up -d --scale cli=$target cli

    Write-Status "Done." "$P CLI started"
    & $DC -f docker-compose.cli.yml -p "$P-cli" ps cli
}

function Invoke-CliDown {
    param([string]$P)
    Write-Host "Stopping $P CLI..."
    & $DC -f docker-compose.cli.yml -p "$P-cli" down 2>$null
    Write-Status "Done." "$P CLI stopped"
}

function Invoke-CliLogs {
    param([string]$P)
    & $DC -f docker-compose.cli.yml -p "$P-cli" logs -f cli
}

function Invoke-TestAll {
    Write-Host "Running all tests..."
    Write-Host ""

    Write-Host "=== API Gateway Tests ==="
    $env:PYTHONPATH = "api-gateway;$($env:PYTHONPATH)"
    uv run pytest api-gateway/tests/ -v --tb=short

    Write-Host ""
    Write-Host "=== Dashboard API Tests ==="
    $env:PYTHONPATH = "dashboard-api;$($env:PYTHONPATH)"
    uv run pytest dashboard-api/tests/ -v --tb=short

    Write-Host ""
    Write-Host "=== Agent Engine Tests ==="
    $env:PYTHONPATH = "agent-engine;$($env:PYTHONPATH)"
    uv run pytest agent-engine/tests/ -v --tb=short

    Write-Host ""
    Write-Host "=== Task Logger Tests ==="
    $env:PYTHONPATH = "task-logger;$($env:PYTHONPATH)"
    uv run pytest task-logger/tests/ -v --tb=short

    Write-Host ""
    Write-Host "=== API Services Tests ==="
    uv run pytest api-services/github-api/tests/ -v --tb=short
    uv run pytest api-services/jira-api/tests/ -v --tb=short
    uv run pytest api-services/slack-api/tests/ -v --tb=short
    uv run pytest api-services/sentry-api/tests/ -v --tb=short

    Write-Host ""
    Write-Status "Done." "All tests passed!"
}

function Invoke-TestService {
    param([string]$SvcName)

    if (-not $SvcName) {
        Write-Host "Usage: .\make.ps1 test-<service>"
        Write-Host "Available: api-gateway, agent-engine, dashboard-api, task-logger, github-api, jira-api, slack-api, sentry-api"
        exit 1
    }

    switch ($SvcName) {
        "api-gateway" {
            Write-Host "Running API Gateway tests..."
            $env:PYTHONPATH = "api-gateway;$($env:PYTHONPATH)"
            uv run pytest api-gateway/tests/ -v --tb=short
        }
        "agent-engine" {
            Write-Host "Running Agent Engine tests..."
            $env:PYTHONPATH = "agent-engine;$($env:PYTHONPATH)"
            uv run pytest agent-engine/tests/ -v --tb=short
        }
        { $_ -in "dashboard", "dashboard-api" } {
            Write-Host "Running Dashboard API tests..."
            $env:PYTHONPATH = "dashboard-api;$($env:PYTHONPATH)"
            uv run pytest dashboard-api/tests/ -v --tb=short
        }
        { $_ -in "task-logger", "logger" } {
            Write-Host "Running Task Logger tests..."
            $env:PYTHONPATH = "task-logger;$($env:PYTHONPATH)"
            uv run pytest task-logger/tests/ -v --tb=short
        }
        { $_ -in "github-api", "github" } {
            Write-Host "Running GitHub API tests..."
            uv run pytest api-services/github-api/tests/ -v --tb=short
        }
        { $_ -in "jira-api", "jira" } {
            Write-Host "Running Jira API tests..."
            uv run pytest api-services/jira-api/tests/ -v --tb=short
        }
        { $_ -in "slack-api", "slack" } {
            Write-Host "Running Slack API tests..."
            uv run pytest api-services/slack-api/tests/ -v --tb=short
        }
        { $_ -in "sentry-api", "sentry" } {
            Write-Host "Running Sentry API tests..."
            uv run pytest api-services/sentry-api/tests/ -v --tb=short
        }
        "services" {
            Write-Host "Running API Services tests..."
            uv run pytest api-services/github-api/tests/ api-services/jira-api/tests/ api-services/slack-api/tests/ api-services/sentry-api/tests/ -v --tb=short
        }
        default {
            Write-Host "Unknown service: $SvcName"
            Write-Host "Available: api-gateway, agent-engine, dashboard-api, task-logger, github-api, jira-api, slack-api, sentry-api, services"
            exit 1
        }
    }

    Write-Host ""
    Write-Status "Done." "Tests passed!"
}

function Invoke-TestCov {
    Write-Host "Running tests with coverage..."
    $env:PYTHONPATH = "api-gateway;agent-engine;dashboard-api;task-logger;$($env:PYTHONPATH)"
    uv run pytest `
        api-gateway/tests/ `
        agent-engine/tests/ `
        dashboard-api/tests/ `
        task-logger/tests/ `
        --cov=. --cov-report=html --cov-report=term-missing -v --tb=short
    Write-Host ""
    Write-Status "Done." "Coverage report generated: htmlcov/index.html"
}

function Invoke-Lint {
    uv run ruff check .
}

function Invoke-Format {
    uv run ruff format .
}

function Invoke-DbMigrate {
    Write-Host "Database schema is managed via SQLAlchemy create_all + inline migrations."
    Write-Host "No alembic migration framework is configured."
    Write-Host ""
    Write-Host "To add new tables or columns:"
    Write-Host "  1. Add SQLAlchemy models in the relevant service"
    Write-Host "  2. Add migration logic in dashboard-api/core/database/__init__.py"
    Write-Host "  3. Restart the service to apply changes"
}

function Invoke-DbUpgrade {
    Write-Host "Database tables are auto-created on service startup (dashboard-api init_db)."
    Write-Host "No manual migration step is needed."
    Write-Host ""
    Write-Host "To force table recreation, restart the dashboard-api service:"
    Write-Host "  docker-compose restart dashboard-api"
}

function Invoke-KnowledgeUp {
    Write-Host "Starting knowledge services (LlamaIndex, GKG, Indexer)..."
    & $DC --profile knowledge up -d llamaindex-service llamaindex-mcp gkg-service gkg-mcp indexer-worker
    Write-Status "Done." "Knowledge services started"
}

function Invoke-KnowledgeDown {
    Write-Host "Stopping knowledge services..."
    & $DC --profile knowledge stop llamaindex-service llamaindex-mcp gkg-service gkg-mcp indexer-worker
    Write-Status "Done." "Knowledge services stopped"
}

function Invoke-KnowledgeLogs {
    & $DC --profile knowledge logs -f llamaindex-service gkg-service indexer-worker
}

function Invoke-KnowledgeBuild {
    Write-Host "Building knowledge services..."
    & $DC --profile knowledge build llamaindex-service llamaindex-mcp gkg-service gkg-mcp indexer-worker
    Write-Status "Done." "Knowledge services built"
}

function Invoke-UpFull {
    Invoke-Up
    & $DC --profile knowledge up -d
    Write-Status "Done." "All services including knowledge started"
}

function Invoke-Clean {
    Write-Host "Cleaning up..."
    Get-ChildItem -Recurse -Directory -Include "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache" -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Include "*.pyc" -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Status "Done." "Cleaned cache directories"
}

function Invoke-Tunnel {
    $envContent = Get-Content .env -Raw
    $match = [regex]::Match($envContent, '^NGROK_DOMAIN=(.+)$', [System.Text.RegularExpressions.RegexOptions]::Multiline)

    if (-not $match.Success) {
        Write-Host "❌ NGROK_DOMAIN not configured in .env"
        exit 1
    }

    $ngrokDomain = $match.Groups[1].Value.Trim('"')

    Write-Host "🌐 Starting ngrok tunnel to $ngrokDomain"
    Write-Host "   Forwarding to: http://localhost:5000"

    try {
        $null = & ngrok --version
    }
    catch {
        Write-Host "❌ ngrok not installed. Install it with: choco install ngrok"
        exit 1
    }

    & ngrok http --domain $ngrokDomain 5000
}

switch ($Command) {
    "help"             { Invoke-Help }
    "init"             { Invoke-Init }
    "build"            { Invoke-Build }
    "up"               { Invoke-Up }
    "down"             { Invoke-Down }
    "start"            { Invoke-Up }
    "health"           { Invoke-Health }
    "logs"             { Invoke-Logs }
    "cli"              { Invoke-CliStart -P $Provider -S $Scale }
    "cli-down"         { Invoke-CliDown -P $Provider }
    "cli-logs"         { Invoke-CliLogs -P $Provider }
    "cli-claude"       { Invoke-CliStart -P "claude" -S $Scale }
    "cli-cursor"       { Invoke-CliStart -P "cursor" -S $Scale }
    "test"             { Invoke-TestAll }
    "test-all"         { Invoke-TestAll }
    "test-api-gateway" { Invoke-TestService -SvcName "api-gateway" }
    "test-agent-engine" { Invoke-TestService -SvcName "agent-engine" }
    "test-dashboard"   { Invoke-TestService -SvcName "dashboard-api" }
    "test-logger"      { Invoke-TestService -SvcName "task-logger" }
    "test-services"    { Invoke-TestService -SvcName "services" }
    "test-cov"         { Invoke-TestCov }
    "lint"             { Invoke-Lint }
    "format"           { Invoke-Format }
    "db-migrate"       { Invoke-DbMigrate }
    "db-upgrade"       { Invoke-DbUpgrade }
    "knowledge-up"     { Invoke-KnowledgeUp }
    "knowledge-down"   { Invoke-KnowledgeDown }
    "knowledge-logs"   { Invoke-KnowledgeLogs }
    "knowledge-build"  { Invoke-KnowledgeBuild }
    "up-full"          { Invoke-UpFull }
    "tunnel"           { Invoke-Tunnel }
    "clean"            { Invoke-Clean }
    default {
        Write-Host "Unknown command: $Command"
        Write-Host "Run '.\make.ps1 help' for available commands"
        exit 1
    }
}
