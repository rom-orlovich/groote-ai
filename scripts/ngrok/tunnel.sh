#!/bin/bash
set -e

NGROK_DOMAIN=$(grep "^NGROK_DOMAIN=" .env | cut -d '=' -f 2 | tr -d '"')

if [ -z "$NGROK_DOMAIN" ]; then
    echo "❌ NGROK_DOMAIN not configured in .env"
    exit 1
fi

echo "🌐 Starting ngrok tunnel to $NGROK_DOMAIN"
echo "   Forwarding to: http://localhost:5000"

command -v ngrok &> /dev/null || {
    echo "❌ ngrok not installed. Install it with: brew install ngrok"
    exit 1
}

ngrok http --domain "$NGROK_DOMAIN" 5000
