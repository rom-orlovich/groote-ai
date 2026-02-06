#!/bin/bash
set -e

PUBLIC_URL=$(grep "^PUBLIC_URL=" .env | cut -d '=' -f 2 | tr -d '"')

if [ -z "$PUBLIC_URL" ]; then
    echo "❌ PUBLIC_URL not configured in .env"
    exit 1
fi

echo "🌐 Starting ngrok tunnel to $PUBLIC_URL"
echo "   Forwarding to: http://localhost:5000"

command -v ngrok &> /dev/null || {
    echo "❌ ngrok not installed. Install it with: brew install ngrok"
    exit 1
}

ngrok http --domain "$PUBLIC_URL" 5000
