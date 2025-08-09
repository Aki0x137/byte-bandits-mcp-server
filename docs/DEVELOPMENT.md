# Development Commands for Byte Bandits MCP Server

## Prerequisites
- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Git

## Setup
```bash
# Quick setup using uv
uv sync --dev
cp .env.example .env

# Enable LangChain backend (optional)
uv pip install -e ".[langchain]"

# Alternative: Manual setup with virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
cp .env.example .env

# Legacy setup script (uses pip)
./scripts/setup.sh
```

## Environment
- AUTH_TOKEN (required)
- MY_NUMBER (required)
- REDIS_URL (optional, default redis://localhost:6379)
- THERAPY_SESSION_TTL (optional, default 259200)
- THERAPY_AUTO_WHY (optional, 0/1)
- THERAPY_USE_LANGCHAIN (optional, 0/1)
- OPENAI_API_KEY (required if THERAPY_USE_LANGCHAIN=1)

## Running the Server
```bash
# Development mode (recommended)
uv run python main.py

# Alternative: Activate venv first
source .venv/bin/activate
python main.py

# Production mode (with uvicorn directly)
uv run uvicorn main:mcp --host 0.0.0.0 --port 8086

# Check server status
curl http://localhost:8086/mcp/
```

## Development Tools
```bash
# Code formatting
uv run black main.py tests/
uv run isort main.py tests/

# Type checking
uv run mypy main.py

# Testing (uv standard)
uv run pytest -q           # quiet
uv run --with pytest python -m pytest -v   # verbose, ensures pytest present

# Coverage
uv run pytest --cov=main

# Run specific test files
uv run python -m pytest -v tests/test_mcp_server.py
```

## Environment Management
```bash
# Create .env from template
cp .env.example .env

# Check environment variables
uv run python -c "from main import AUTH_TOKEN, MY_NUMBER; print(f'Token: {AUTH_TOKEN[:8]}..., Number: {MY_NUMBER}')"

# View current environment
uv run python -c "import os; print('AUTH_TOKEN:', bool(os.getenv('AUTH_TOKEN'))); print('MY_NUMBER:', os.getenv('MY_NUMBER', 'Not set'))"
```

## Available Tools
The server provides these tools:
- **validate**: Returns phone number for Puch AI authentication
- **echo**: Simple echo tool for testing connectivity
- **fetch_web_content**: Fetch and convert web content to markdown (if dependencies available)
- **convert_to_bw**: Convert images to black and white (if PIL available)

## Dependency Management
```bash
# Add new dependencies
uv add package-name

# Add development dependencies
uv add --dev package-name

# Update all dependencies
uv sync --upgrade

# View dependency tree
uv tree

# Remove dependencies
uv remove package-name
```

## Project Structure
```
byte-bandits-mcp-server/
├── main.py                 # Main MCP server implementation
├── pyproject.toml          # Project configuration and dependencies
├── uv.lock                 # Locked dependencies
├── .env.example            # Environment variables template
├── .env                    # Your local environment (create from .env.example)
├── docs/                   # Documentation
├── scripts/                # Utility scripts
│   ├── setup.sh           # Legacy setup script
│   └── extract_todos.py   # TODO extraction utility
└── tests/                  # Test suite
    ├── test_mcp_server.py # Main server tests
    └── test_smoke.py      # Smoke tests
```

## Deployment

### Local Development with ngrok
```bash
# Install ngrok (if not already installed)
# Download from https://ngrok.com/download

# Configure ngrok with your authtoken
ngrok config add-authtoken YOUR_AUTHTOKEN

# Make server publicly accessible
ngrok http 8086

# In another terminal, start the server
uv run python main.py
```

### Docker Deployment
```bash
# Build Docker image
docker build -t byte-bandits-mcp .

# Run container with environment file
docker run -p 8086:8086 --env-file .env byte-bandits-mcp

# Run with environment variables
docker run -p 8086:8086 \
  -e AUTH_TOKEN=your_token \
  -e MY_NUMBER=your_number \
  byte-bandits-mcp
```

### Cloud Deployment Options

#### Railway
```bash
railway login
railway init
railway up

# Set environment variables in Railway dashboard
railway variables set AUTH_TOKEN=your_token
railway variables set MY_NUMBER=your_number
```

#### Render
```bash
# Push to GitHub first
git push origin main

# Connect repository via Render dashboard
# Set environment variables in Render settings:
# - AUTH_TOKEN=your_token
# - MY_NUMBER=your_number
```

#### Heroku
```bash
heroku create your-app-name
heroku config:set AUTH_TOKEN=your_token MY_NUMBER=your_number
git push heroku main
```

## Testing with Puch AI
```bash
# Start the server locally
uv run python main.py

# Make it publicly accessible (choose one method):
# 1. Using ngrok
ngrok http 8086

# 2. Deploy to cloud (Railway, Render, Heroku, etc.)

# Connect to server in Puch AI chat
/mcp connect https://your-domain/mcp your_auth_token

# Test basic connectivity
/mcp tools list

# Enable debug mode
/mcp diagnostics-level debug

# Test tools with natural language
"Please echo back 'Hello World'"
"Fetch content from https://example.com"
"What's my phone number?" # Tests validate tool
```

## Monitoring & Debugging
```bash
# View server logs (if running locally)
uv run python main.py  # Logs appear in terminal

# Test server endpoints
curl -X GET http://localhost:8086/mcp/ \
  -H "Authorization: Bearer your_auth_token"

# Test with MCP client tools
uv run python test_connectivity.py
uv run python test_server.py

# Check tool registration
uv run python -c "
from main import mcp
print('Registered tools:')
for tool_name in mcp._tools:
    print(f'  - {tool_name}')
"

# Validate environment setup
uv run python -c "
from main import AUTH_TOKEN, MY_NUMBER, WEB_FEATURES_AVAILABLE, IMAGE_FEATURES_AVAILABLE
print(f'✅ Auth Token: {bool(AUTH_TOKEN)}')
print(f'✅ Phone Number: {MY_NUMBER}')
print(f'🌐 Web Features: {WEB_FEATURES_AVAILABLE}')
print(f'🖼️  Image Features: {IMAGE_FEATURES_AVAILABLE}')
"
```

## Troubleshooting
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Verify uv installation
uv --version

# Check dependencies
uv tree

# Reinstall dependencies
uv sync --reinstall

# Clean and reinstall
rm -rf .venv uv.lock
uv sync --dev

# Test imports manually
uv run python -c "
try:
    import fastmcp
    print('✅ FastMCP available')
except ImportError as e:
    print(f'❌ FastMCP error: {e}')

try:
    import httpx, bs4, readabilipy, markdownify
    print('✅ Web features available')
except ImportError as e:
    print(f'⚠️  Web features unavailable: {e}')

try:
    from PIL import Image
    print('✅ Image features available')
except ImportError as e:
    print(f'⚠️  Image features unavailable: {e}')
"

# Common issues and solutions:
# 1. Import errors: Run 'uv sync --dev' to install dependencies
# 2. Permission errors: Check file permissions and virtual environment
# 3. Port already in use: Change port in main.py or kill existing process
# 4. Authentication issues: Verify AUTH_TOKEN in .env file
# 5. HTTPS required for Puch AI: Use ngrok or deploy to cloud with HTTPS
```
