#!/bin/bash
set -e

DC="docker-compose"

echo "Stopping Groote AI services..."
$DC down
echo "✅ Services stopped"
