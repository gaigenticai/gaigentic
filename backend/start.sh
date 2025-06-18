#!/usr/bin/env bash
set -e
alembic -c gaigentic_backend/alembic.ini upgrade head
exec uvicorn gaigentic_backend.main:app --host 0.0.0.0 --port 8001
