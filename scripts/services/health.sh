#!/bin/bash

DC="docker-compose"

echo "Service Health:"

curl -sf http://localhost:8000/health >/dev/null 2>&1 && echo "  ✅ API Gateway (8000)" || echo "  ❌ API Gateway (8000)"
curl -sf http://localhost:8080/health >/dev/null 2>&1 && echo "  ✅ Agent Engine (8080)" || echo "  ❌ Agent Engine (8080)"
curl -sf http://localhost:5000/api/health >/dev/null 2>&1 && echo "  ✅ Dashboard API (5000)" || echo "  ❌ Dashboard API (5000)"
curl -sf http://localhost:8010/health >/dev/null 2>&1 && echo "  ✅ OAuth Service (8010)" || echo "  ❌ OAuth Service (8010)"
curl -sf http://localhost:8001/api/v1/heartbeat >/dev/null 2>&1 && echo "  ✅ ChromaDB (8001)" || echo "  ❌ ChromaDB (8001)"

$DC exec -T redis redis-cli ping >/dev/null 2>&1 && echo "  ✅ Redis (6379)" || echo "  ❌ Redis (6379)"
$DC exec -T postgres pg_isready -U agent >/dev/null 2>&1 && echo "  ✅ PostgreSQL (5432)" || echo "  ❌ PostgreSQL (5432)"

echo ""
echo "CLI Auth:"
AUTH_JSON=$(curl -sf http://localhost:8080/health/auth 2>/dev/null)
if [ -n "$AUTH_JSON" ]; then
  AUTH_OK=$(echo "$AUTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('authenticated',False))" 2>/dev/null)
  AUTH_MSG=$(echo "$AUTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('message',''))" 2>/dev/null)
  if [ "$AUTH_OK" = "True" ]; then
    echo "  ✅ $AUTH_MSG"
  else
    echo "  ❌ $AUTH_MSG"
  fi
else
  echo "  ⚠️  Agent Engine not reachable (auth check skipped)"
fi
