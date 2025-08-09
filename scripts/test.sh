#!/usr/bin/env bash
set -euo pipefail

# Run test suite using uv with reasonable defaults.
# Ensures Redis is available locally (docker compose) unless SKIP_REDIS=1.
# -q by default; pass VERBOSE=1 for -v.

: "${REDIS_URL:=redis://localhost:6379}"

ensure_redis() {
  if [[ "${SKIP_REDIS:-0}" == "1" ]]; then
    return 0
  fi

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

  if [[ "$REDIS_HOST" != "localhost" && "$REDIS_HOST" != "127.0.0.1" ]]; then
    return 0
  fi

  if timeout 1 bash -c ">/dev/tcp/$REDIS_HOST/$REDIS_PORT" 2>/dev/null; then
    return 0
  fi

  echo "🗄️  Redis not reachable at $REDIS_HOST:$REDIS_PORT — starting via Docker Compose for tests..."
  if command -v docker >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
      docker compose -f docker/compose.redis.yml up -d
    elif command -v docker-compose >/dev/null 2>&1; then
      docker-compose -f docker/compose.redis.yml up -d
    else
      echo "⚠️  Docker Compose not found. Skipping Redis auto-start." >&2
      return 0
    fi

    for i in {1..30}; do
      if timeout 1 bash -c ">/dev/tcp/$REDIS_HOST/$REDIS_PORT" 2>/dev/null; then
        echo "✅ Redis is up on $REDIS_HOST:$REDIS_PORT"
        break
      fi
      sleep 0.5
    done
  else
    echo "⚠️  Docker not installed; cannot auto-start Redis for tests."
  fi
}

ensure_redis

if [[ "${VERBOSE:-0}" == "1" ]]; then
  echo "> Running: uv run --with pytest --with pytest-asyncio python -m pytest -v"
  uv run --with pytest --with pytest-asyncio python -m pytest -v
else
  echo "> Running: uv run --with pytest --with pytest-asyncio python -m pytest -q"
  uv run --with pytest --with pytest-asyncio python -m pytest -q
fi
