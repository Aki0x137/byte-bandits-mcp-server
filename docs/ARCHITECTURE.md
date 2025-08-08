# Architecture Overview

The Byte Bandits MCP Server is designed as a modular, extensible Model Context Protocol server that integrates seamlessly with Puch AI. The architecture follows clean separation of concerns with robust error handling and security.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Puch AI       │    │   MCP Server    │    │  External APIs  │
│   Client        │◄──►│   (FastMCP)     │◄──►│  (Web, etc.)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Tool Registry │
                       │   & Execution   │
                       └─────────────────┘
```

## Core Components

### 1. Server Entry Point (`main.py`)
- **FastMCP Server**: High-level MCP server implementation
- **Authentication**: Bearer token with RSA key pair generation
- **Environment Configuration**: Secure environment variable management
- **Tool Registration**: Dynamic tool discovery and registration

### 2. Authentication Layer
```python
SimpleBearerAuthProvider
├── RSA Key Pair Generation
├── Access Token Validation
└── Client Authentication
```

**Features:**
- Secure bearer token authentication
- RSA key pair for cryptographic operations
- Puch AI client compatibility
- Configurable token validation

### 3. Tool Framework
```python
Tool Categories
├── Core Tools (validate, echo)
├── Web Tools (fetch_web_content)
├── Image Tools (convert_to_bw)
└── Custom Tools (extensible)
```

**Tool Description Model:**
```python
class ToolDescription(BaseModel):
    description: str      # What the tool does
    use_when: str        # When to use it
    side_effects: str    # Any side effects
```

### 4. Content Processing Layer
```python
Content Processors
├── WebContentFetcher
│   ├── HTTP Client (httpx)
│   ├── HTML Parser (BeautifulSoup)
│   ├── Content Extraction (readabilipy)
│   └── Markdown Conversion (markdownify)
└── ImageProcessor
    ├── PIL Image Processing
    ├── Base64 Encoding/Decoding
    └── Format Conversion
```

### 5. Error Handling System
```python
Error Management
├── MCP Error Codes
├── Structured Error Responses
├── Graceful Degradation
└── Debug Information
```

## Data Flow

### 1. Authentication Flow
```
Client Request → Bearer Token Validation → RSA Verification → Access Grant/Deny
```

### 2. Tool Execution Flow
```
Tool Call → Parameter Validation → Business Logic → Response Formatting → Client Response
```

### 3. Web Content Processing Flow
```
URL Request → HTTP Fetch → HTML Parsing → Content Extraction → Markdown Conversion → Response
```

### 4. Image Processing Flow
```
Base64 Image → Decode → PIL Processing → Format Conversion → Re-encode → Response
```

## Security Architecture

### Authentication & Authorization
- **Bearer Token**: Secure token-based authentication
- **Environment Variables**: Secure credential storage
- **HTTPS Enforcement**: Production security requirement
- **Input Validation**: Comprehensive parameter validation

### Data Protection
- **No Persistent Storage**: Stateless operation
- **Secure Transmission**: HTTPS/TLS encryption
- **Token Rotation**: Support for token refresh
- **Error Sanitization**: No sensitive data in error messages

## Configuration Management

### Environment Variables
```bash
AUTH_TOKEN    # Required: Bearer token for authentication
MY_NUMBER     # Required: Phone number for validation
PORT          # Optional: Server port (default: 8086)
HOST          # Optional: Server host (default: 0.0.0.0)
WEB_TIMEOUT   # Optional: Web request timeout (default: 30s)
```

### Feature Flags
```python
WEB_FEATURES_AVAILABLE    # Web content fetching capability
IMAGE_FEATURES_AVAILABLE  # Image processing capability
```

## Extensibility

### Adding New Tools
1. **Define Tool Function**: Async function with proper typing
2. **Create Tool Description**: Structured metadata
3. **Register with MCP**: Automatic registration via decorators
4. **Add Error Handling**: Proper MCP error responses

### Tool Categories
- **Core Tools**: Essential functionality (validate, echo)
- **Content Tools**: Data processing (web, files, images)
- **Integration Tools**: External service connectors
- **Utility Tools**: Helper functions and utilities

## Performance Considerations

### Async Architecture
- **Non-blocking I/O**: Full async/await support
- **Concurrent Requests**: Multiple simultaneous tool calls
- **Resource Management**: Proper cleanup and resource handling

### Optimization Strategies
- **Connection Pooling**: Reuse HTTP connections
- **Content Caching**: Optional response caching
- **Request Timeouts**: Prevent hanging requests
- **Graceful Degradation**: Continue operation with partial failures

## Deployment Architecture

### Development Environment
```
Local Machine → ngrok → Public HTTPS → Puch AI
```

### Production Environment
```
Cloud Platform → Load Balancer → HTTPS → MCP Server → Puch AI
```

### Supported Platforms
- **Railway**: Recommended for quick deployment
- **Render**: Free tier available
- **Heroku**: Classic PaaS option
- **DigitalOcean**: App Platform
- **Vercel**: Serverless deployment
- **Self-hosted**: Docker containers

## Monitoring & Observability

### Logging Strategy
- **Structured Logging**: JSON-formatted logs
- **Error Tracking**: Comprehensive error logging
- **Performance Metrics**: Request timing and throughput
- **Debug Information**: Configurable verbosity levels

### Health Checks
- **Server Status**: Basic health endpoint
- **Dependency Checks**: External service availability
- **Authentication Status**: Token validation checks

## Future Extensions

### Planned Components
- **Plugin System**: Dynamic tool loading
- **Configuration API**: Runtime configuration updates
- **Metrics Dashboard**: Real-time monitoring
- **Tool Marketplace**: Shareable tool packages
- **Rate Limiting**: Request throttling
- **Caching Layer**: Response caching system

### Integration Opportunities
- **Database Connectors**: SQL/NoSQL database tools
- **API Integrations**: External service connectors
- **File Processing**: Document and media processing
- **AI/ML Tools**: Model inference and data processing
- **Notification Systems**: Email, SMS, webhooks

## Technology Stack

### Core Dependencies
- **FastMCP**: MCP server framework
- **Pydantic**: Data validation and serialization
- **httpx**: Async HTTP client
- **cryptography**: Security and authentication

### Optional Dependencies
- **beautifulsoup4**: HTML parsing
- **readabilipy**: Content extraction
- **markdownify**: HTML to Markdown conversion
- **Pillow**: Image processing
- **uvicorn**: ASGI server

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
