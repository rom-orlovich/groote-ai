#!/bin/bash
set -e

TUNNEL_BIN="${TUNNEL_BIN:-zrok}"
TUNNEL_SHARE_NAME="${TUNNEL_SHARE_NAME:-my-app}"
LOCAL_PORT="${LOCAL_PORT:-3005}"

if [ -z "$PUBLIC_URL" ]; then
    echo "Error: PUBLIC_URL is not set. Configure it in .env or via the dashboard setup wizard."
    exit 1
fi

command -v "$TUNNEL_BIN" &> /dev/null || {
    if [ -x "$HOME/.local/bin/zrok" ]; then
        TUNNEL_BIN="$HOME/.local/bin/zrok"
    else
        echo "Error: zrok not installed."
        echo ""
        echo "Install zrok:"
        echo "  curl -sL https://github.com/openziti/zrok/releases/latest/download/zrok_\$(uname -s | tr '[:upper:]' '[:lower:]')_amd64.tar.gz | tar -xz -C ~/.local/bin/"
        echo ""
        echo "Then setup (one-time):"
        echo "  1. Create account at https://myzrok.io"
        echo "  2. zrok enable <TOKEN_FROM_EMAIL>"
        echo "  3. zrok reserve public http://localhost:${LOCAL_PORT} --unique-name ${TUNNEL_SHARE_NAME}"
        exit 1
    fi
}

"$TUNNEL_BIN" status &> /dev/null || {
    echo "Error: zrok not enabled. Run: zrok enable <YOUR_TOKEN>"
    echo "  1. Create account at https://myzrok.io"
    echo "  2. Check email for token"
    echo "  3. Run: $TUNNEL_BIN enable <TOKEN>"
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

"$TUNNEL_BIN" share reserved "$TUNNEL_SHARE_NAME" --headless
