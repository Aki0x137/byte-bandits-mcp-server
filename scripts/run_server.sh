#!/usr/bin/env bash
set -euo pipefail

# Run the Byte Bandits MCP Server locally
# Usage:
#   AUTH_TOKEN=your_token MY_NUMBER=919876543210 scripts/run_server.sh
# Optional:
#   REDIS_URL=redis://localhost:6379 THERAPY_SESSION_TTL=259200
#   SKIP_REDIS=1   # set to skip bringing up local Redis via Docker

if [[ -z "${AUTH_TOKEN:-}" ]]; then
  echo "ERROR: AUTH_TOKEN is required" >&2
  exit 1
fi
if [[ -z "${MY_NUMBER:-}" ]]; then
  echo "ERROR: MY_NUMBER is required (e.g., 919876543210)" >&2
  exit 1
fi

# Defaults
: "${REDIS_URL:=redis://localhost:6379}"
: "${THERAPY_SESSION_TTL:=259200}"

# Helper: ensure local Redis (via docker compose) is running when targeting localhost
ensure_redis() {
  if [[ "${SKIP_REDIS:-0}" == "1" ]]; then
    return 0
  fi

  # Parse host:port from REDIS_URL
  read -r REDIS_HOST REDIS_PORT < <(python3 - <<'PY'
import os, urllib.parse
u = os.environ.get('REDIS_URL', 'redis://localhost:6379')
if '://' not in u:
    u = f'redis://{u}'
p = urllib.parse.urlparse(u)
h = p.hostname or 'localhost'
pt = p.port or 6379
print(h, pt)
PY
)

  # Only auto-start if host is localhost/127.0.0.1
  if [[ "$REDIS_HOST" != "localhost" && "$REDIS_HOST" != "127.0.0.1" ]]; then
    return 0
  fi

  # Check TCP connectivity
  if timeout 1 bash -c ">/dev/tcp/$REDIS_HOST/$REDIS_PORT" 2>/dev/null; then
    return 0
  fi

  echo "🗄️  Redis not reachable at $REDIS_HOST:$REDIS_PORT — starting via Docker Compose..."
  if command -v docker >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
      docker compose -f docker/compose.redis.yml up -d
    elif command -v docker-compose >/dev/null 2>&1; then
      docker-compose -f docker/compose.redis.yml up -d
    else
      echo "⚠️  Docker Compose not found. Please start Redis manually or install Docker Compose." >&2
      return 0
    fi

    # Wait for port to open (max ~15s)
    for i in {1..30}; do
      if timeout 1 bash -c ">/dev/tcp/$REDIS_HOST/$REDIS_PORT" 2>/dev/null; then
        echo "✅ Redis is up on $REDIS_HOST:$REDIS_PORT"
        break
      fi
      sleep 0.5
    done
  else
    echo "⚠️  Docker not installed; cannot auto-start Redis. Continuing without ensuring Redis."
  fi
}

echo "🚀 Starting Byte Bandits MCP Server..."
echo "📱 Phone: ${MY_NUMBER}"
echo "🗄️  Redis: ${REDIS_URL}"

ensure_redis

# Prefer uv if available
if command -v uv >/dev/null 2>&1; then
  exec uv run python main.py
else
  exec python3 main.py
fi
