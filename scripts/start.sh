#!/bin/sh
# Startup script for Railway and other container environments.
# Runs Alembic migration before starting the server so fresh Postgres
# deployments get the schema without manual intervention.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting cultivOS API server..."
exec python -m uvicorn cultivos.app:create_app --factory --host 0.0.0.0 --port "${PORT:-8000}"
