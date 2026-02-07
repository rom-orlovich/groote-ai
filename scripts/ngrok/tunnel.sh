#!/bin/bash
set -e

PUBLIC_URL=$(grep "^PUBLIC_URL=" .env 2>/dev/null | cut -d '=' -f 2 | tr -d '"' | tr -d "'")
PUBLIC_URL=$(grep "^PUBLIC_URL=" .env 2>/dev/null | cut -d '=' -f 2 | tr -d '"' | tr -d "'")

DOMAIN="${PUBLIC_URL}"
if [ -z "$DOMAIN" ] && [ -n "$PUBLIC_URL" ]; then
    DOMAIN=$(echo "$PUBLIC_URL" | sed 's|https\?://||' | sed 's|/.*||')
fi

if [ -z "$DOMAIN" ]; then
    echo "Error: Set PUBLIC_URL or PUBLIC_URL in .env"
    echo "  PUBLIC_URL=https://your-domain.ngrok-free.app"
    exit 1
fi

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
