#!/usr/bin/env bash
set -euo pipefail

# Byte Bandits MCP Server Setup Script (uv-based)
# This script prepares a local development environment using uv
# - Ensures Python 3.11+
# - Uses `uv sync --dev` to create/manage .venv and install deps
# - Creates a starter .env if missing
#
# Usage: scripts/setup.sh

echo "🚀 Setting up Byte Bandits MCP Server (uv) ..."

# Check uv
if ! command -v uv >/dev/null 2>&1; then
  echo "❌ 'uv' is required but not installed. Install from https://docs.astral.sh/uv/getting-started/" >&2
  echo "   Example (Linux): curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

# Python version check (3.11+)
echo "📋 Checking Python version..."
if ! uv run python - <<'PY'
import sys
assert sys.version_info >= (3, 11), f"Python 3.11+ required, found {sys.version.split()[0]}"
print("✅ Python version check passed:", sys.version.split()[0])
PY
then
  exit 1
fi

# Sync dependencies (creates .venv)
echo "📦 Installing dependencies with uv (including dev)..."
uv sync --dev

# Create .env if missing (no template required)
if [[ ! -f .env ]]; then
  cat > .env <<'ENV'
# Byte Bandits MCP Server configuration
# Fill these before running the server
AUTH_TOKEN=demo_token_12345
MY_NUMBER=14155551234
# Optional Redis for therapy session persistence
REDIS_URL=redis://localhost:6379
THERAPY_SESSION_TTL=259200
# Optional: auto-run diagnostic questions after /feel
THERAPY_AUTO_WHY=0
ENV
  echo "✅ Created .env with defaults. Edit it to match your environment."
else
  echo "✅ .env already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1) Edit .env and set AUTH_TOKEN and MY_NUMBER"
echo "2) Start the server: AUTH_TOKEN=... MY_NUMBER=... scripts/run_server.sh"
echo "   or: source .venv/bin/activate && uv run python main.py"
echo "3) (Optional) Start Redis: docker compose -f docker/compose.redis.yml up -d"
echo "4) Validate: uv run python scripts/validate_mcp_app.py --base-url http://localhost:8086/mcp/ --wait"
