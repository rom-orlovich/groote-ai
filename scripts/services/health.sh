#!/bin/bash

DC="docker-compose"

AGENT_PORT=$(docker port groote-ai-cli-1 9100 2>/dev/null | head -1 | cut -d: -f2)
AGENT_PORT=${AGENT_PORT:-9100}

echo "Service Health:"

curl -sf http://localhost:8000/health >/dev/null 2>&1 && echo "  ✅ API Gateway (8000)" || echo "  ❌ API Gateway (8000)"
curl -sf http://localhost:${AGENT_PORT}/health >/dev/null 2>&1 && echo "  ✅ Agent Engine (${AGENT_PORT})" || echo "  ❌ Agent Engine (${AGENT_PORT})"
curl -sf http://localhost:5001/api/health >/dev/null 2>&1 && echo "  ✅ Dashboard API (5001)" || echo "  ❌ Dashboard API (5001)"
curl -sf http://localhost:8010/health >/dev/null 2>&1 && echo "  ✅ OAuth Service (8010)" || echo "  ❌ OAuth Service (8010)"
curl -sf http://localhost:8015/health >/dev/null 2>&1 && echo "  ✅ Admin Setup (8015)" || echo "  ❌ Admin Setup (8015)"
curl -sf http://localhost:8001/api/v1/heartbeat >/dev/null 2>&1 && echo "  ✅ ChromaDB (8001)" || echo "  ❌ ChromaDB (8001)"

$DC exec -T redis redis-cli ping >/dev/null 2>&1 && echo "  ✅ Redis (6379)" || echo "  ❌ Redis (6379)"
$DC exec -T postgres pg_isready -U agent >/dev/null 2>&1 && echo "  ✅ PostgreSQL (5432)" || echo "  ❌ PostgreSQL (5432)"

echo ""
echo "CLI Auth:"
AUTH_JSON=$(curl -sf http://localhost:${AGENT_PORT}/health/auth 2>/dev/null)
if [ -n "$AUTH_JSON" ]; then
  AUTH_OK=$(echo "$AUTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('authenticated',False))" 2>/dev/null)
  AUTH_MSG=$(echo "$AUTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('message',''))" 2>/dev/null)
  PROVIDER=$(echo "$AUTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('provider','unknown'))" 2>/dev/null)
  if [ "$AUTH_OK" = "True" ]; then
    echo "  ✅ $PROVIDER: $AUTH_MSG"
  else
    echo "  ❌ $PROVIDER: $AUTH_MSG"
  fi
else
  echo "  ⚠️  Agent Engine not reachable (auth check skipped)"
fi

echo ""
echo "CLI Prompt Test:"
CLI_TEST=$(docker logs groote-ai-cli-1 2>&1 | grep "CLI check:" | tail -1)
if [ -n "$CLI_TEST" ]; then
  if echo "$CLI_TEST" | grep -q "status=healthy"; then
    echo "  ✅ $CLI_TEST"
  else
    echo "  ❌ $CLI_TEST"
  fi
else
  echo "  ⏳ Prompt test not completed yet (check: docker logs groote-ai-cli-1)"
fi
