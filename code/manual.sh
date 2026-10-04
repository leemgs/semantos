#!/usr/bin/env bash
set -euo pipefail

# =====================================================
# GroundKern Manual Deployment Script
# -----------------------------------------------------
# This script builds and runs all GroundKern services
# using docker-compose. It performs three steps:
#   1. Build Docker images
#   2. Start all services
#   3. Tail logs
# =====================================================

COMPOSE_FILE="docker-compose.yml"

# 1️⃣ Build all Docker images (no cache)
echo "🚀 [1/3] Building all GroundKern Docker images..."
docker-compose -f "${COMPOSE_FILE}" build --no-cache
echo "✅ Build complete."

# 2️⃣ Start all services
echo "🔧 [2/3] Starting all GroundKern services (KB, Reasoner, Safety, Telemetry, UI)..."
docker-compose -f "${COMPOSE_FILE}" up -d
echo "✅ All services started."

# 3️⃣ Tail logs (Ctrl+C to stop)
echo "📜 [3/3] Tailing logs (Ctrl+C to stop)..."
docker-compose -f "${COMPOSE_FILE}" logs -f
