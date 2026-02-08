#!/bin/bash
set -e

DC="docker-compose"
PROVIDER="${CLI_PROVIDER:-claude}"

echo "Starting Groote AI services..."

test -f .env || cp .env.example .env

set -a
source .env
set +a

PROVIDER="${CLI_PROVIDER:-claude}"

echo ""
echo "CLI Provider: $PROVIDER"
echo "Checking credentials..."

if [ "$PROVIDER" = "claude" ]; then
  CREDS_FILE="$HOME/.claude/.credentials.json"
  if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "  ✅ ANTHROPIC_API_KEY is set"
  elif [ -f "$CREDS_FILE" ]; then
    EXPIRED=$(python3 -c "
import json, time
try:
    d = json.load(open('$CREDS_FILE'))
    oauth = d.get('claudeAiOauth', d)
    exp = oauth.get('expiresAt') or oauth.get('expires_at', 0)
    print('yes' if time.time() * 1000 >= exp else 'no')
except:
    print('unknown')
" 2>/dev/null)
    if [ "$EXPIRED" = "yes" ]; then
      echo "  ⚠️  OAuth token expired, refreshing..."
      ./agent-engine/scripts/extract_oauth_creds.sh "$CREDS_FILE" || true
    else
      echo "  ✅ OAuth credentials found"
    fi
  else
    echo "  ⚠️  No credentials found, extracting from Keychain..."
    ./agent-engine/scripts/extract_oauth_creds.sh "$CREDS_FILE" || {
      echo "  ❌ Failed to extract credentials"
      echo "     Set ANTHROPIC_API_KEY in .env or run: claude login"
      exit 1
    }
  fi
elif [ "$PROVIDER" = "cursor" ]; then
  if [ -n "$CURSOR_API_KEY" ]; then
    echo "  ✅ CURSOR_API_KEY is set"
  else
    echo "  ❌ CURSOR_API_KEY not set in .env"
    exit 1
  fi
fi

echo ""
$DC build

$DC up -d --scale cli=0
echo "  ✅ Core services started"

CREDS_FILE="$HOME/.claude/.credentials.json"
CLAUDE_JSON="$HOME/.claude/.claude.json"

if [ "$PROVIDER" = "claude" ]; then
  if [ ! -f "$CREDS_FILE" ]; then
    echo "  ⚠️  Credentials file missing, extracting..."
    ./agent-engine/scripts/extract_oauth_creds.sh "$CREDS_FILE" || true
  fi

  if [ ! -f "$CREDS_FILE" ]; then
    echo "  ⚠️  Creating placeholder credentials file for Docker mount"
    mkdir -p "$(dirname "$CREDS_FILE")"
    echo '{}' > "$CREDS_FILE"
  fi

  if [ ! -f "$CLAUDE_JSON" ]; then
    echo "  ⚠️  Creating placeholder .claude.json for Docker mount"
    echo '{}' > "$CLAUDE_JSON"
  fi
fi

echo "  Starting agent engine (CLI)..."
$DC up -d cli

echo ""
echo "Waiting for agent engine..."

MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
  AGENT_PORT=$(docker port groote-ai-cli-1 9100 2>/dev/null | head -1 | cut -d: -f2)
  if [ -n "$AGENT_PORT" ]; then
    if curl -sf "http://localhost:${AGENT_PORT}/health" >/dev/null 2>&1; then
      break
    fi
  fi
  sleep 2
  WAITED=$((WAITED + 2))
  printf "."
done
echo ""

if [ $WAITED -ge $MAX_WAIT ]; then
  echo "⚠️  Agent Engine did not become healthy in ${MAX_WAIT}s"
  echo "   Continuing with health check..."
fi

echo "Checking services..."
./scripts/services/health.sh

echo ""
echo "✅ Groote AI ready"
echo "   API Gateway: http://localhost:8000"
echo "   Dashboard:   http://localhost:3005"
echo "   Dashboard API: http://localhost:5001"
