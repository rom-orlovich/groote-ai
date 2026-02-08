#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    . "$PROJECT_DIR/.env"
    set +a
fi

ZROK_BIN="${ZROK_BIN:-zrok}"
ZROK_SHARE_NAME="${ZROK_SHARE_NAME:-}"
LOCAL_PORT="${LOCAL_PORT:-3005}"
PUBLIC_URL="${PUBLIC_URL:-}"

if [ -z "$PUBLIC_URL" ] || [ -z "$ZROK_SHARE_NAME" ]; then
    echo "Error: PUBLIC_URL and ZROK_SHARE_NAME must be set in .env"
    echo "  Run 'make tunnel-setup' first"
    exit 1
fi

command -v "$ZROK_BIN" &> /dev/null || {
    if [ -x "$HOME/.local/bin/zrok" ]; then
        ZROK_BIN="$HOME/.local/bin/zrok"
    else
        echo "Error: zrok not installed."
        echo ""
        echo "Run setup first: make tunnel-setup"
        exit 1
    fi
}

"$ZROK_BIN" status &> /dev/null || {
    echo "Error: zrok not enabled. Run: zrok enable <YOUR_TOKEN>"
    echo "  1. Create account at https://myzrok.io"
    echo "  2. Check email for token"
    echo "  3. Run: $ZROK_BIN enable <TOKEN>"
    exit 1
}

echo "Starting zrok tunnel: ${PUBLIC_URL} -> http://localhost:${LOCAL_PORT}"
echo ""
echo "Routes (via nginx on port ${LOCAL_PORT}):"
echo "  /           -> external-dashboard (React SPA)"
echo "  /api/*      -> dashboard-api:5000"
echo "  /oauth/*    -> oauth-service:8010"
echo "  /webhooks/* -> api-gateway:8000"
echo "  /ws         -> dashboard-api:5000 (WebSocket)"
echo ""
echo "Webhook URLs:"
echo "  GitHub: ${PUBLIC_URL}/webhooks/github"
echo "  Jira:   ${PUBLIC_URL}/webhooks/jira"
echo "  Slack:  ${PUBLIC_URL}/webhooks/slack"
echo ""
echo "OAuth callback: ${PUBLIC_URL}/oauth/callback"
echo ""

"$ZROK_BIN" share reserved "$ZROK_SHARE_NAME" --headless
