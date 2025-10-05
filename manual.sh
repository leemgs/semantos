#!/usr/bin/env bash
set -euo pipefail

# Pick Compose CLI: prefer `docker compose`, fallback to `docker-compose`
if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=("docker" "compose")
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=("docker-compose")
else
  echo "❌ Docker Compose not found. Install docker-compose v2 or enable 'docker compose' plugin."
  exit 1
fi

COMPOSE_FILE="docker-compose.yml"

echo "🚀 [1/3] Building all SemantOS Docker images..."
"${COMPOSE_CMD[@]}" -f "${COMPOSE_FILE}" build --no-cache

echo "✅ Build complete."

echo "🔧 [2/3] Starting all SemantOS services (KB, Reasoner, Safety, Telemetry, UI)..."
"${COMPOSE_CMD[@]}" -f "${COMPOSE_FILE}" up -d

echo "✅ All services started."

echo "📜 [3/3] Tailing logs (Ctrl-C to stop)..."
"${COMPOSE_CMD[@]}" -f "${COMPOSE_FILE}" logs -f