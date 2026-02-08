#!/bin/bash
set -e

PUBLIC_URL=$(grep "^PUBLIC_URL=" .env 2>/dev/null | cut -d '=' -f 2 | tr -d '"' | tr -d "'")

if [ -z "$PUBLIC_URL" ]; then
    echo "Error: PUBLIC_URL is not set. Configure it in .env or via the dashboard setup wizard."
    echo "  PUBLIC_URL=https://your-domain.example.com"
    exit 1
fi

DOMAIN=$(echo "$PUBLIC_URL" | sed 's|https\?://||' | sed 's|/.*||')

command -v ngrok &> /dev/null || {
    echo "Error: ngrok not installed. Install with: brew install ngrok"
    exit 1
}

echo "Starting ngrok tunnel: https://$DOMAIN -> http://localhost:3005"
echo ""
echo "Routes:"
echo "  /           -> external-dashboard (React SPA)"
echo "  /api/*      -> dashboard-api:5000"
echo "  /oauth/*    -> oauth-service:8010"
echo "  /webhooks/* -> api-gateway:8000"
echo "  /ws         -> dashboard-api:5000 (WebSocket)"

ngrok http --domain "$DOMAIN" 3005
