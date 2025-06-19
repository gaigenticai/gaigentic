#!/usr/bin/env bash
set -euo pipefail

if [ ! -f .env ]; then
  echo "Creating .env from .env.development"
  cp .env.development .env
fi

if [ ! -d external/superagent ]; then
  echo "Cloning Superagent repository"
  mkdir -p external
  git clone https://github.com/superagent-ai/superagent.git external/superagent
else
  echo "Updating Superagent repository"
  git -C external/superagent pull --ff-only
fi

docker compose build superagent
docker compose up -d
