#!/usr/bin/env bash
set -euo pipefail

echo "[council-api] Running database migrations..."
alembic upgrade head

echo "[council-api] Seeding demo data (idempotent)..."
python -m app.scripts.seed || echo "[council-api] Seed skipped/failed (non-fatal)."

echo "[council-api] Starting API on ${COUNCIL_API_HOST:-0.0.0.0}:${COUNCIL_API_PORT:-8000}"
exec uvicorn app.main:app \
  --host "${COUNCIL_API_HOST:-0.0.0.0}" \
  --port "${COUNCIL_API_PORT:-8000}" \
  --proxy-headers
