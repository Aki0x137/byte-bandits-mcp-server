#!/usr/bin/env bash
set -euo pipefail

# Run the Byte Bandits MCP Server locally
# Usage:
#   AUTH_TOKEN=your_token MY_NUMBER=919876543210 scripts/run_server.sh
# Optional:
#   REDIS_URL=redis://localhost:6379 THERAPY_SESSION_TTL=259200

if [[ -z "${AUTH_TOKEN:-}" ]]; then
  echo "ERROR: AUTH_TOKEN is required" >&2
  exit 1
fi
if [[ -z "${MY_NUMBER:-}" ]]; then
  echo "ERROR: MY_NUMBER is required (e.g., 919876543210)" >&2
  exit 1
fi

# Hint about Redis
if [[ -z "${REDIS_URL:-}" ]]; then
  export REDIS_URL="redis://localhost:6379"
fi

echo "🚀 Starting Byte Bandits MCP Server..."
echo "📱 Phone: ${MY_NUMBER}"
echo "🗄️  Redis: ${REDIS_URL}"

# Prefer uv if available
if command -v uv >/dev/null 2>&1; then
  exec uv run python main.py
else
  exec python main.py
fi
