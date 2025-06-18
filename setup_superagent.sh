#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ]; then
  echo "Creating .env from .env.development"
  cp .env.development .env
fi

git submodule update --init --recursive

docker compose build superagent
docker compose up -d
