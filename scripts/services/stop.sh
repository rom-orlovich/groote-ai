#!/bin/bash
set -e

DC="docker-compose"

echo "Stopping Groote AI services..."

test -f .env && {
  set -a
  source .env
  set +a
}

$DC down
echo "✅ Services stopped"
