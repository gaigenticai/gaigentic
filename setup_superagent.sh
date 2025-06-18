#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ]; then
  echo "Creating .env from .env.development"
  cp .env.development .env
fi

# Clone Superagent locally if not present
if [ ! -d external/superagent ]; then
  echo "Cloning Superagent..."
  mkdir -p external
  git clone https://github.com/superagent-ai/superagent.git external/superagent
fi

docker compose build superagent
docker compose up -d
