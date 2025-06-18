#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/superagent-ai/superagent.git"
TARGET_DIR="superagent"

if [ ! -d "$TARGET_DIR" ]; then
  echo "Cloning Superagent repository..."
  git clone "$REPO_URL" "$TARGET_DIR"
fi

if [ ! -f .env ]; then
  echo "Creating .env from .env.development"
  cp .env.development .env
fi

docker compose build superagent
docker compose up -d
