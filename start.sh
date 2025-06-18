#!/bin/bash
set -e

echo "🚀 Starting Gaigentic AI platform..."

# Step 1: Ensure .env exists
if [ ! -f .env ]; then
  echo "📄 .env not found. Copying from .env.development..."
  cp .env.development .env
fi

# Step 2: Ensure Superagent is available
if [ ! -d external/superagent ]; then
  echo "📦 Cloning Superagent source..."
  mkdir -p external
  git clone https://github.com/superagent-ai/superagent.git external/superagent
else
  echo "✅ Superagent directory found"
fi

# Step 3: Pull latest submodules if present
if [ -f .gitmodules ]; then
  echo "🔄 Updating git submodules..."
  git submodule update --init --recursive
fi

# Step 4: Rebuild all containers
echo "🔨 Rebuilding Docker containers..."
docker compose down
docker compose build --no-cache

# Step 5: Launch services
echo "🚀 Launching Gaigentic..."
docker compose up
