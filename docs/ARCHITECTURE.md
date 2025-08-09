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
                              │
                              ▼
                       ┌────────────────────────┐
                       │ Emotion Therapy Module │
                       │  - Validator (DAG)     │
                       │  - Session Store       │
                       │  - Conversation Mgr    │
                       │  - LLM Provider (plug) │
                       └────────────────────────┘
```

## Core Components

### 1. Server Entry Point (`main.py`)
- **FastMCP Server**: High-level MCP server implementation
- **Authentication**: Minimal token validation compatible with FastMCP
- **Environment Configuration**: Secure environment variable management
- **Tool Registration**: Dynamic tool discovery and registration

### 2. Authentication Layer
```python
SimpleTokenAuthProvider
├── Access Token Validation (static token)
└── Client Authentication
```

**Features:**
- Simple, deterministic token auth suitable for MCP
- Puch AI client compatibility

### 3. Tool Framework
```python
Tool Categories
├── Core Tools (validate, echo)
├── Web Tools (fetch_web_content)
├── Image Tools (convert_to_bw)
└── Therapy Tools (session-aware)
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
│   ├── Content Extraction (readabilipy)
│   └── Markdown Conversion (markdownify)
└── ImageProcessor
    ├── PIL Image Processing
    └── Base64 Encoding/Decoding
```

### 5. Emotion Therapy Module

- `validator.py`: Parses and validates commands through a DAG of permissible transitions.
- `session_store.py`: Redis-backed `TherapySession` persistence with TTL and history.
- `conversation.py`: Conversation Manager that maintains a sliding window of structured turns and gates LLM usage by session state.
- `tools.py`: MCP tools that orchestrate validator, session manager, and conversation manager.
- `llm_stub.py`: Deterministic, testable LLM stub for local/dev.
- Optional LangChain backend via `LangChainLLMProvider` when `THERAPY_USE_LANGCHAIN=1`.

## Data Flow

### Therapy Tool Flow
```
/mcp tools/call → tools.py → validator → session_store → conversation manager → LLM provider → response
                                  ↑                 ↓
                             history kept      structured context
```

### Web Content Processing Flow
```
URL Request → HTTP Fetch → Extraction → Markdown → Response
```

### Image Processing Flow
```
Base64 Image → Decode → PIL Processing → Encode → Response
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
AUTH_TOKEN            # Required: Bearer token for authentication
MY_NUMBER             # Required: Phone number for validation
REDIS_URL             # Optional: Redis connection string
THERAPY_SESSION_TTL   # Optional: TTL in seconds for session keys
THERAPY_AUTO_WHY      # Optional: Auto-run diagnostic after /feel
THERAPY_USE_LANGCHAIN # Optional: Enable LangChain LLM provider
OPENAI_API_KEY        # Optional: for LangChain OpenAI (or use OPEN_API_KEY)
```

The server maps `OPEN_API_KEY` → `OPENAI_API_KEY` automatically for compatibility.

## Extensibility

### LLM Providers
- Implement the `LLMProvider` protocol with methods for analysis, questions, remedies, and conversation.
- Plug into the Conversation Manager via `create_conversation_manager(session_manager, use_langchain=...)`.

### Adding New Tools
- Follow the pattern in `emotion_therapy/tools.py` to integrate with validator + session + conversation.

## Testing Strategy

- Unit tests for validator, wheel integration, and stub LLM.
- Smoke tests for MCP server and therapy tool happy-path.
- Conversation Manager tests validate structured history and provider fallback behavior.

## Deployment Notes

- For LangChain provider, install extras: `pip install -e .[langchain]` and set `OPENAI_API_KEY`.
- Redis can be started locally via `docker/compose.redis.yml`.
