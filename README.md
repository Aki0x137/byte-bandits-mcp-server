# Byte Bandits MCP Server

A comprehensive Model Context Protocol (MCP) server boilerplate designed for seamless integration with Puch AI. This server provides a robust foundation for building custom MCP tools and services.

## 🚀 Features

### Core MCP Protocol Support
- ✅ **Bearer Token Authentication** - Secure token-based authentication
- ✅ **HTTPS Ready** - Production-ready HTTPS support
- ✅ **Validate Tool** - Required phone number validation for Puch AI
- ✅ **JSON-RPC 2.0** - Full MCP protocol compliance
- ✅ **Error Handling** - Comprehensive error handling with proper MCP error codes

### Built-in Tools
- 🔄 **Echo Tool** - Test server connectivity and basic functionality
- 🌐 **Web Content Fetcher** - Fetch and convert web content to readable markdown
- 🖼️ **Image Processing** - Convert images to black and white
- 🔧 **Extensible Framework** - Easy-to-extend tool registration system

### Development Features
- 📝 **Comprehensive Documentation** - Well-documented code and APIs
- 🧪 **Testing Framework** - Built-in testing support
- 🔧 **Development Tools** - Code formatting, linting, and type checking
- 📦 **Modular Design** - Clean separation of concerns

## 📋 Requirements

- Python 3.11 or higher
- Virtual environment (recommended)
- Environment variables for configuration
- HTTPS deployment for production use with Puch AI

## 🛠️ Quick Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <your-repo-url>
cd byte-bandits-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# For development (optional)
pip install -e ".[dev]"
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your configuration
nano .env
```

**Required environment variables:**
```env
# Your secret authentication token (keep this secure!)
AUTH_TOKEN=your_secret_token_here

# Your phone number in format {country_code}{number}
# Example: 919876543210 for +91-9876543210
MY_NUMBER=919876543210
```

### 3. Run the Server

```bash
python main.py
```

You should see output like:
```
🚀 Starting Byte Bandits MCP Server...
📱 Phone number: 919876543210
🔐 Authentication: Bearer token configured
✅ Available features: Core MCP Protocol, Echo Tool, Web Content Fetching, Image Processing
🌐 Server running on http://0.0.0.0:8086
📋 Required: Make server publicly accessible via HTTPS for Puch AI
```

### 4. Make Server Public (Required for Puch AI)

Puch AI requires HTTPS access to your server. Choose one of these options:

#### Option A: Using ngrok (Recommended for Development)

```bash
# Install ngrok from https://ngrok.com/download
# Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken

# Configure ngrok
ngrok config add-authtoken YOUR_AUTHTOKEN

# Start tunnel
ngrok http 8086
```

#### Option B: Deploy to Cloud Platform

Deploy to services like:
- Railway
- Render
- Heroku
- DigitalOcean App Platform
- Vercel
- Cloudflare Workers

### 5. Connect with Puch AI

1. Open [Puch AI](https://wa.me/+919998881729)
2. Start a new conversation
3. Use the connect command:
   ```
   /mcp connect https://your-domain.ngrok.app/mcp your_secret_token_here
   ```

## 🔧 Development

### Adding New Tools

1. **Create a new tool function:**
   ```python
   @mcp.tool(description=your_description.model_dump_json())
   async def your_tool_name(
       parameter: Annotated[str, Field(description="Parameter description")]
   ) -> str:
       # Your tool logic here
       return "Tool result"
   ```

2. **Add tool description:**
   ```python
   your_description = ToolDescription(
       description="What your tool does",
       use_when="When to use this tool",
       side_effects="Any side effects (optional)"
   )
   ```

### Testing

Run the test suite using uv (recommended):

- Quick run: `uv run pytest -q`
- Verbose run: `uv run --with pytest python -m pytest -v`
- One-off without syncing dev deps: `uvx pytest -q`
- Using helper script:
  - Quiet: `scripts/test.sh`
  - Verbose: `VERBOSE=1 scripts/test.sh`

Notes:
- Using `python -m pytest` ensures the workspace root is on `sys.path`.
- `--with pytest` guarantees pytest is provisioned for the run when not installed locally.

```bash
# Type checking
mypy main.py

# Code formatting
black main.py
isort main.py
```

## 📚 Architecture

### Core Components

- **Authentication**: Bearer token with RSA key pair generation
- **Tool Registry**: Pydantic-based tool descriptions and validation
- **Error Handling**: MCP-compliant error codes and messages
- **Content Processing**: HTML to Markdown conversion utilities
- **Image Processing**: PIL-based image manipulation

### Tool Categories

1. **Core Tools**: validate, echo
2. **Web Tools**: fetch_web_content
3. **Image Tools**: convert_to_bw
4. **Custom Tools**: (add your own)

## 🔒 Security Considerations

- Store sensitive tokens in environment variables
- Use HTTPS in production
- Validate all inputs
- Implement proper error handling
- Follow principle of least privilege

## 📖 API Reference

### Required Tools

#### `validate()`
- **Purpose**: Required by Puch AI for authentication
- **Returns**: Server owner's phone number
- **Format**: `{country_code}{number}` (e.g., "919876543210")

### Optional Tools

#### `echo(message: str)`
- **Purpose**: Test server connectivity
- **Parameters**: `message` - Text to echo back
- **Returns**: Echoed message with prefix

#### `fetch_web_content(url: AnyUrl, raw: bool = False)`
- **Purpose**: Fetch and process web content
- **Parameters**: 
  - `url` - URL to fetch
  - `raw` - Return raw content without markdown conversion
- **Returns**: Processed content with metadata

#### `convert_to_bw(image_data: str)`
- **Purpose**: Convert images to black and white
- **Parameters**: `image_data` - Base64-encoded image data
- **Returns**: List of ImageContent with converted image

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Authentication Failures**: Check AUTH_TOKEN and MY_NUMBER format
3. **Connection Issues**: Verify HTTPS accessibility
4. **Tool Errors**: Check tool parameter validation

### Debug Mode

Enable debug logging in Puch AI:
```
/mcp diagnostics-level debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Getting Help

- **Puch AI Discord**: https://discord.gg/VMCnMvYx
- **Puch AI MCP Documentation**: https://puch.ai/mcp
- **Puch WhatsApp**: +91 99988 81729
- **MCP Protocol Documentation**: https://modelcontextprotocol.io/

---

**Happy coding! 🚀**

Built with ❤️ by the Byte Bandits team.

Use the hashtag `#BuildWithPuch` when sharing your MCP creations!

## Redis setup (for Emotion Therapy sessions)

1. Start Redis via Docker:

```bash
docker compose -f docker/compose.redis.yml up -d
```

2. Configure your `.env`:

```
REDIS_URL=redis://localhost:6379
THERAPY_SESSION_TTL=259200  # 3 days
```

3. Install dependencies (includes redis-py):

```bash
pip install -e .
```

4. Verify connectivity (optional):

```python
from emotion_therapy.session_store import get_redis_session_manager
mgr = get_redis_session_manager()
sess = mgr.get_session("alice")
sess.state = "SESSION_STARTED"
mgr.save_session(sess)
print(mgr.get_session("alice"))
```