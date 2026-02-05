#!/bin/bash
set -e

DC="docker-compose"

echo "Starting Groote AI services..."

test -f .env || cp .env.example .env

$DC build
$DC up -d

sleep 5

echo "Checking services..."
./scripts/services/health.sh

echo ""
echo "✅ Groote AI ready"
echo "   API Gateway: http://localhost:8000"
echo "   Dashboard:   http://localhost:3005"
echo "   Dashboard API: http://localhost:5000"
