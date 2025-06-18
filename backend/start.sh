#!/usr/bin/env bash
set -e
alembic upgrade head
exec uvicorn gaigentic_backend.main:app --host 0.0.0.0 --port 8001
