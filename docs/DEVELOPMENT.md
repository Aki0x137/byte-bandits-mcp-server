# Development Commands for Byte Bandits MCP Server

## Setup
```bash
# Initial setup
./scripts/setup.sh

# Manual setup
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Running the Server
```bash
# Development mode
python main.py

# Production mode (with gunicorn)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:mcp --bind 0.0.0.0:8086
```

## Development Tools
```bash
# Code formatting
black main.py tests/
isort main.py tests/

# Type checking
mypy main.py

# Linting
flake8 main.py tests/

# Testing
pytest
pytest --cov=main
pytest -v tests/test_mcp_server.py
```

## Environment Management
```bash
# Create .env from template
cp .env.example .env

# Check environment variables
python -c "from main import AUTH_TOKEN, MY_NUMBER; print(f'Token: {AUTH_TOKEN[:8]}..., Number: {MY_NUMBER}')"
```

## Deployment

### Using ngrok (Development)
```bash
# Install and setup ngrok
# Download from https://ngrok.com/download
ngrok config add-authtoken YOUR_AUTHTOKEN
ngrok http 8086
```

### Using Docker (Production)
```bash
# Build image
docker build -t byte-bandits-mcp .

# Run container
docker run -p 8086:8086 --env-file .env byte-bandits-mcp
```

### Cloud Deployment
```bash
# Railway
railway login
railway init
railway up

# Render
# Push to GitHub and connect via Render dashboard

# Heroku
heroku create your-app-name
heroku config:set AUTH_TOKEN=your_token MY_NUMBER=your_number
git push heroku main
```

## Testing with Puch AI
```bash
# Connect to server
# In Puch AI chat: /mcp connect https://your-domain/mcp your_token

# Debug mode
# In Puch AI chat: /mcp diagnostics-level debug

# Test tools
# In Puch AI chat: Use natural language to test your tools
```

## Monitoring
```bash
# Check server logs
tail -f server.log

# Monitor server status
curl -X POST https://your-domain/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "ping"}'
```

## Troubleshooting
```bash
# Check dependencies
pip list

# Verify Python version
python --version

# Test imports
python -c "import fastmcp, mcp; print('MCP imports OK')"

# Test server locally
curl http://localhost:8086/health
```
