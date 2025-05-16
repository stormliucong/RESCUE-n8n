#!/usr/bin/env bash
set -euo pipefail

echo "Starting HAPI FHIR server restart process..."

# 1) Prefer the built-in 'docker compose' if available
if docker compose version &>/dev/null; then
  COMPOSE_CMD="docker compose"
# 2) Otherwise fall back to the old 'docker-compose' binary if it really exists
elif command -v docker-compose &>/dev/null; then
  COMPOSE_CMD="docker-compose"
else
  echo "Error: neither 'docker compose' nor 'docker-compose' is available." >&2
  exit 1
fi

echo "Using compose command: $COMPOSE_CMD"

# 3) Use it for all operations
echo "Stopping and removing FHIR containers..."
$COMPOSE_CMD down

echo "Starting FHIR containers..."
$COMPOSE_CMD up -d

echo "Waiting for FHIR server to be healthy (30 seconds)..."
sleep 30

if docker ps --format '{{.Names}}' | grep -q 'hapifhir'; then
  echo "HAPI FHIR server successfully restarted!"
else
  echo "Error: FHIR container is not running. Please check the logs."
  $COMPOSE_CMD logs web
  exit 1
fi
