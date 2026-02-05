#!/bin/bash
set -e

echo "Database tables are auto-created on service startup (dashboard-api init_db)."
echo "No manual migration step is needed."
echo ""
echo "To force table recreation, restart the dashboard-api service:"
echo "  docker-compose restart dashboard-api"
