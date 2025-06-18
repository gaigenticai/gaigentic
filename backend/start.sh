#!/bin/bash
set -e

echo "⏳ Waiting for PostgreSQL to start..."
while ! nc -z db 5432; do
  sleep 0.5
done
echo "✅ PostgreSQL is up"

# ✅ Add PYTHONPATH fix
export PYTHONPATH=/app

# Run Alembic migrations
alembic -c gaigentic_backend/alembic.ini upgrade head

# Start FastAPI app
exec uvicorn gaigentic_backend.main:app --host 0.0.0.0 --port 8001
