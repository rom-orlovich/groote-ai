#!/bin/bash
set -e

echo "Database schema is managed via SQLAlchemy create_all + inline migrations."
echo "No alembic migration framework is configured."
echo ""
echo "To add new tables or columns:"
echo "  1. Add SQLAlchemy models in the relevant service"
echo "  2. Add migration logic in dashboard-api/core/database/__init__.py"
echo "  3. Restart the service to apply changes"
