"""
Byte Bandits MCP Server
A Model Context Protocol server boilerplate for Puch AI integration.
"""

import asyncio
import os
from typing import Annotated

from dotenv import load_dotenv
from fastmcp import FastMCP
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, ImageContent, TextContent
from pydantic import AnyUrl, BaseModel, Field

# Optional imports for enhanced functionality
try:
    import httpx
    import markdownify
    import readabilipy
    from bs4 import BeautifulSoup
    WEB_FEATURES_AVAILABLE = True
except ImportError:
    WEB_FEATURES_AVAILABLE = False

# AI integration for therapy assistant
try:
    import openai
    from typing import Literal
    OPENAI_FEATURES_AVAILABLE = True
except ImportError:
    OPENAI_FEATURES_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_FEATURES_AVAILABLE = True
except ImportError:
    GEMINI_FEATURES_AVAILABLE = False

try:
    from PIL import Image
    import base64
    import io
    IMAGE_FEATURES_AVAILABLE = True
except ImportError:
    IMAGE_FEATURES_AVAILABLE = False

# Optional Redis session store for Emotion Therapy
try:
    from emotion_therapy.session_store import get_redis_session_manager
    REDIS_FEATURES_AVAILABLE = True
except Exception:
    REDIS_FEATURES_AVAILABLE = False

# Optional Emotion Therapy tools registration (import only; register later in main())
try:
    from emotion_therapy.tools import register_tools as register_therapy_tools
    THERAPY_TOOLS_AVAILABLE = True
except Exception:
    THERAPY_TOOLS_AVAILABLE = False

# Request Logger Middleware
try:
    from request_logger import RequestLoggerMiddleware, DetailedRequestLoggerMiddleware
    REQUEST_LOGGER_AVAILABLE = True
except Exception:
    REQUEST_LOGGER_AVAILABLE = False

# Load environment variables
load_dotenv()

# Compatibility: support OPEN_API_KEY -> OPENAI_API_KEY
if not os.environ.get("OPENAI_API_KEY") and os.environ.get("OPEN_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.environ["OPEN_API_KEY"]

# Required environment variables
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER")
# Redis-related (optional)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
THERAPY_SESSION_TTL = os.environ.get("THERAPY_SESSION_TTL", "259200")
# Server config
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8086"))

# Validate required environment variables
if not AUTH_TOKEN:
    raise ValueError("AUTH_TOKEN environment variable is required. Please set it in your .env file.")
if not MY_NUMBER:
    raise ValueError("MY_NUMBER environment variable is required. Please set it in your .env file.")

# Validate phone number format
if not MY_NUMBER.isdigit() or len(MY_NUMBER) < 10:
    raise ValueError("MY_NUMBER must be in format {country_code}{number} (e.g., 919876543210)")

# Configure AI services if available
if OPENAI_FEATURES_AVAILABLE:
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        openai.api_key = openai_key

if GEMINI_FEATURES_AVAILABLE:
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        genai.configure(api_key=gemini_key)


# Import the new LLM handler for therapeutic responses
try:
    from emotion_therapy.llm_stub import generate_therapeutic_response
    ENHANCED_THERAPY_AVAILABLE = True
except ImportError:
    ENHANCED_THERAPY_AVAILABLE = False


class SimpleTokenAuthProvider:
    """Minimal bearer token auth provider compatible with FastMCP.

    Avoids deprecated BearerAuthProvider by only implementing load_access_token.
    """

    def __init__(self, token: str):
        self.token = token
        # Optional list of required scopes
        self.required_scopes: list[str] = ["*"]

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="puch-client",
                scopes=["*"],
                expires_at=None,
            )
        return None

    # FastMCP HTTP expects a TokenVerifier-compatible object
    async def verify_token(self, token: str) -> AccessToken | None:
        return await self.load_access_token(token)

    def get_routes(self):
        """Return optional auth-related HTTP routes required by FastMCP.

        For simple static token auth we don't need any routes, so return empty list.
        """
        return []

    def get_resource_metadata_url(self):
        """No protected resource metadata for simple token auth."""
        return None


class ToolDescription(BaseModel):
    """Rich description model for MCP tools."""
    description: str
    use_when: str
    side_effects: str | None = None


# Initialize MCP server
mcp = FastMCP(
    "Byte Bandits MCP Server",
    auth=SimpleTokenAuthProvider(AUTH_TOKEN),
    # Respond with JSON for Streamable HTTP so simple HTTP clients/tests work
    json_response=True,
)

# Add request logging middleware
if REQUEST_LOGGER_AVAILABLE:
    # Add detailed request logger that logs headers and body
    mcp.add_middleware(DetailedRequestLoggerMiddleware(
        include_headers=True,
        include_body=True,
        max_body_length=2000,  # Increased limit for debugging
        sensitive_headers=["authorization", "bearer", "x-api-key", "auth-token"]
    ))


@mcp.tool
async def validate() -> str:
    """
    Validate tool required by Puch AI.
    Returns the server owner's phone number for authentication.
    """
    return MY_NUMBER


if WEB_FEATURES_AVAILABLE:
    class WebContentFetcher:
        """Utility class for web content fetching and processing."""
        
        USER_AGENT = "ByteBandits-MCP/1.0"
        
        @classmethod
        async def fetch_url(
            cls,
            url: str,
            force_raw: bool = False,
            timeout: int = 30,
        ) -> tuple[str, str]:
            """
            Fetch content from a URL and optionally convert to markdown.
            
            Returns:
                Tuple of (content, content_type_info)
            """
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        url,
                        follow_redirects=True,
                        headers={"User-Agent": cls.USER_AGENT},
                        timeout=timeout,
                    )
                    
                    if response.status_code >= 400:
                        raise McpError(
                            ErrorData(
                                code=INTERNAL_ERROR,
                                message=f"HTTP {response.status_code}: Failed to fetch {url}"
                            )
                        )
                    
                    content_type = response.headers.get("content-type", "")
                    is_html = "text/html" in content_type
                    
                    if is_html and not force_raw:
                        # Convert HTML to readable markdown
                        return cls._html_to_markdown(response.text), "text/markdown"
                    
                    return response.text, content_type
                    
            except httpx.HTTPError as e:
                raise McpError(
                    ErrorData(
                        code=INTERNAL_ERROR,
                        message=f"Network error fetching {url}: {str(e)}"
                    )
                )
        
        @staticmethod
        def _html_to_markdown(html: str) -> str:
            """Convert HTML content to markdown format."""
            try:
                # Extract main content using readabilipy
                result = readabilipy.simple_json.simple_json_from_html_string(
                    html, use_readability=True
                )
                
                if not result or not result.get("content"):
                    return "<error>Failed to extract readable content from HTML</error>"
                
                # Convert to markdown
                markdown_content = markdownify.markdownify(
                    result["content"], 
                    heading_style=markdownify.ATX
                )
                
                return markdown_content.strip()
                
            except Exception as e:
                return f"<error>HTML processing failed: {str(e)}</error>"
    
    
    # Web content fetching tool
    fetch_description = ToolDescription(
        description="Fetch and process web content from URLs, converting HTML to readable markdown",
        use_when="Use when user provides a URL and wants to extract readable content",
        side_effects="Makes HTTP request to the specified URL"
    )
    
    @mcp.tool(description=fetch_description.model_dump_json())
    async def fetch_web_content(
        url: Annotated[AnyUrl, Field(description="The URL to fetch content from")],
        raw: Annotated[bool, Field(description="Return raw content without markdown conversion")] = False,
    ) -> str:
        """Fetch content from a web URL and optionally convert to markdown."""
        try:
            content, content_type = await WebContentFetcher.fetch_url(str(url), force_raw=raw)
            
            return f"**Content from:** {url}\n**Type:** {content_type}\n\n---\n\n{content}"
            
        except McpError:
            raise
        except Exception as e:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"Unexpected error: {str(e)}"
                )
            )


if IMAGE_FEATURES_AVAILABLE:
    # Image processing tool
    image_description = ToolDescription(
        description="Convert images to black and white",
        use_when="Use when user provides image data and wants black & white conversion",
        side_effects="Processes and converts the provided image data"
    )
    
    @mcp.tool(description=image_description.model_dump_json())
    async def convert_to_bw(
        image_data: Annotated[str, Field(description="Base64-encoded image data to convert")],
    ) -> list[ImageContent]:
        """Convert an image to black and white."""
        try:
            # Decode base64 image data
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to grayscale
            bw_image = image.convert("L")
            
            # Save to bytes
            output_buffer = io.BytesIO()
            bw_image.save(output_buffer, format="PNG")
            bw_bytes = output_buffer.getvalue()
            
            # Encode back to base64
            bw_base64 = base64.b64encode(bw_bytes).decode("utf-8")
            
            return [ImageContent(type="image", mimeType="image/png", data=bw_base64)]
            
        except Exception as e:
            raise McpError(
                ErrorData(
                    code=INTERNAL_ERROR,
                    message=f"Image processing failed: {str(e)}"
                )
            )


# Echo tool for testing
echo_description = ToolDescription(
    description="Echo back the provided text - useful for testing server connection",
    use_when="Use for testing server connectivity and basic functionality",
    side_effects="None - simply returns the input text"
)

@mcp.tool(description=echo_description.model_dump_json())
async def echo(
    message: Annotated[str, Field(description="Message to echo back")],
) -> str:
    """Simple echo tool for testing server connectivity."""
    return f"Echo: {message}"


if ENHANCED_THERAPY_AVAILABLE:
    # Enhanced Therapy assistant tool with Chain of Thoughts
    therapy_description = ToolDescription(
        description="Generate therapeutic responses for emotional support using Plutchik's Wheel of Emotions with Chain of Thoughts reasoning",
        use_when="Use when user needs emotional support, wants to process feelings, or seeks therapeutic guidance",
        side_effects="Provides empathetic responses and therapeutic suggestions using advanced LLM reasoning (not medical advice)"
    )
    
    @mcp.tool(description=therapy_description.model_dump_json())
    async def therapeutic_response(
        emotion: Annotated[str, Field(description="The user's most likely emotion (e.g., anger, sadness, joy, fear)")],
        context: Annotated[str, Field(description="Inferred context (e.g., work, relationships, self-image)")],
        user_message: Annotated[str, Field(description="The user's most recent message or question")],
        tone: Annotated[str, Field(description="Response tone: default, soothing, or motivational")] = "default",
    ) -> str:
        """Generate a therapeutic response for emotional support using enhanced LLM with Chain of Thoughts."""
        try:
            return generate_therapeutic_response(emotion, context, user_message, tone)
        except Exception as e:
            # Fallback response
            return f"I understand you're experiencing {emotion}. Your feelings are valid and important. Consider taking a moment to breathe deeply and reach out to someone you trust for support."


import datetime
from pathlib import Path

# FastAPI app for HTML form endpoints
try:
    from fastapi import FastAPI, Request, Form, HTTPException
    from fastapi.responses import HTMLResponse
    from fastapi.templating import Jinja2Templates
    FASTAPI_AVAILABLE = True
except Exception:
    FASTAPI_AVAILABLE = False

# JWT
try:
    import jwt  # PyJWT
    JWT_AVAILABLE = True
except Exception:
    JWT_AVAILABLE = False

# JWT config (2 weeks default)
JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-dev-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = int(os.environ.get("JWT_EXPIRATION_DAYS", "14"))

# Token app mount path / separate port
TOKEN_APP_PATH = os.environ.get("TOKEN_APP_PATH", "/")
TOKEN_APP_PORT = int(os.environ.get("TOKEN_APP_PORT", "0"))  # 0 => try mount into main app

# Country codes for dropdown
COUNTRY_CODES: list[tuple[str, str]] = [
    ("1", "🇺🇸 United States (+1)"),
    ("91", "🇮🇳 India (+91)"),
    ("44", "🇬🇧 United Kingdom (+44)"),
    ("49", "🇩🇪 Germany (+49)"),
    ("33", "🇫🇷 France (+33)"),
    ("81", "🇯🇵 Japan (+81)"),
    ("86", "🇨🇳 China (+86)"),
    ("7", "🇷🇺 Russia (+7)"),
    ("55", "🇧🇷 Brazil (+55)"),
    ("61", "🇦🇺 Australia (+61)"),
    ("34", "🇪🇸 Spain (+34)"),
    ("39", "🇮🇹 Italy (+39)"),
    ("31", "🇳🇱 Netherlands (+31)"),
    ("46", "🇸🇪 Sweden (+46)"),
    ("47", "🇳🇴 Norway (+47)"),
    ("45", "🇩🇰 Denmark (+45)"),
    ("41", "🇨🇭 Switzerland (+41)"),
    ("43", "🇦🇹 Austria (+43)"),
    ("32", "🇧🇪 Belgium (+32)"),
    ("351", "🇵🇹 Portugal (+351)"),
]

# Redis client for token storage
from utils.redis import get_redis_client  # ...existing import ok


def _generate_jwt_token(full_phone: str) -> str:
    if not JWT_AVAILABLE:
        raise RuntimeError("PyJWT not installed. Please install PyJWT.")
    now = datetime.datetime.utcnow()
    exp = now + datetime.timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {"sub": full_phone, "phone_number": full_phone, "iat": now, "exp": exp}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _create_token_app() -> "FastAPI":
    if not FASTAPI_AVAILABLE:
        raise RuntimeError("FastAPI not installed; cannot create token app")
    app = FastAPI(title="Token Generator", docs_url=None, redoc_url=None, openapi_url=None)
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

    @app.get("/token-generator", response_class=HTMLResponse)
    async def token_generator_form(request: Request):
        options = "\n".join([f'<option value="{code}">{name}</option>' for code, name in COUNTRY_CODES])
        return templates.TemplateResponse(
            "token_form.html",
            {"request": request, "country_options": options},
        )

    @app.post("/generate-token", response_class=HTMLResponse)
    async def generate_token(request: Request, country_code: str = Form(...), phone_number: str = Form(...)):
        try:
            if not country_code or not phone_number:
                raise HTTPException(status_code=400, detail="Both country code and phone number are required")
            if not phone_number.isdigit():
                raise HTTPException(status_code=400, detail="Phone number must contain only digits")
            if len(phone_number) < 7 or len(phone_number) > 15:
                raise HTTPException(status_code=400, detail="Phone number must be between 7 and 15 digits")

            full_phone = f"{country_code}{phone_number}"
            r = get_redis_client()
            existing = r.get(full_phone)
            if existing:
                return templates.TemplateResponse(
                    "token_success.html",
                    {
                        "request": request,
                        "status": "(Existing)",
                        "is_existing": True,
                        "phone_number": full_phone,
                        "token": existing,
                        "expiry_text": f"{JWT_EXPIRATION_DAYS} days from original generation",
                    },
                )

            token = _generate_jwt_token(full_phone)
            # store with TTL aligned to JWT expiry
            r.set(full_phone, token)
            r.expire(full_phone, JWT_EXPIRATION_DAYS * 24 * 3600)

            return templates.TemplateResponse(
                "token_success.html",
                {
                    "request": request,
                    "status": "Generated",
                    "is_existing": False,
                    "phone_number": full_phone,
                    "token": token,
                    "expiry_text": f"{JWT_EXPIRATION_DAYS} days from now",
                },
            )
        except HTTPException:
            raise
        except Exception as e:
            return templates.TemplateResponse(
                "token_error.html",
                {"request": request, "error_message": str(e)},
                status_code=500,
            )

    return app


async def _maybe_start_token_app(mcp_instance) -> None:
    """Mount FastAPI app into FastMCP HTTP server if possible; otherwise start separate server."""
    if not (FASTAPI_AVAILABLE and JWT_AVAILABLE):
        print("⚠️ Token generator disabled (FastAPI or PyJWT not available)")
        return

    try:
        token_app = _create_token_app()
        # Try to mount into FastMCP app if supported
        mounted = False
        for attr in ("mount", "mount_app", "add_app", "add_route"):
            if hasattr(mcp_instance, attr):
                try:
                    if attr in ("mount", "mount_app"):
                        getattr(mcp_instance, attr)(TOKEN_APP_PATH, token_app)  # type: ignore
                        mounted = True
                        break
                except Exception:
                    pass
        if mounted:
            print(f"🎫 JWT Token Generator mounted at: http://{HOST}:{PORT}/token-generator")
            return
    except Exception as e:
        # Fallback to separate server
        print(f"ℹ️ Mounting token app failed, will attempt separate server: {e}")

    # Start separate server on TOKEN_APP_PORT (default 0 -> pick PORT+1)
    try:
        import uvicorn
        port = TOKEN_APP_PORT or (PORT + 1)
        app = _create_token_app()
        config = uvicorn.Config(app, host=HOST, port=port, log_level="info")
        server = uvicorn.Server(config)
        asyncio.create_task(server.serve())
        print(f"🎫 JWT Token Generator available at: http://{HOST}:{port}/token-generator")
    except Exception as e:
        print(f"⚠️ Failed to start token generator server: {e}")


async def main():
    """Main server entry point."""
    print("🚀 Starting Byte Bandits MCP Server...")
    print(f"📱 Phone number: {MY_NUMBER}")
    print(f"🔐 Authentication: Bearer token configured")
    
    # Log available features
    features = ["Core MCP Protocol", "Echo Tool"]
    if WEB_FEATURES_AVAILABLE:
        features.append("Web Content Fetching")
    if IMAGE_FEATURES_AVAILABLE:
        features.append("Image Processing")
    if REDIS_FEATURES_AVAILABLE:
        features.append("Redis Session Store (Emotion Therapy)")
    if THERAPY_TOOLS_AVAILABLE:
        features.append("Therapy Tools")
    if REQUEST_LOGGER_AVAILABLE:
        features.append("Request Logger Middleware")
    if ENHANCED_THERAPY_AVAILABLE:
        features.append("Enhanced Emotion Therapy Assistant (Chain of Thoughts)")
    elif OPENAI_FEATURES_AVAILABLE or GEMINI_FEATURES_AVAILABLE:
        features.append("Basic Emotion Therapy Assistant")
    
    print(f"✅ Available features: {', '.join(features)}")

    # Try Redis connectivity (non-fatal)
    if REDIS_FEATURES_AVAILABLE:
        try:
            mgr = get_redis_session_manager()
            # ping may raise if Redis unavailable
            if hasattr(mgr, 'client'):
                mgr.client.ping()
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            session_ttl = os.getenv("THERAPY_SESSION_TTL", "259200")
            print(f"🗄️ Redis configured at {redis_url} (TTL {session_ttl}s)")
        except Exception as e:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            print(f"⚠️ Redis not reachable at {redis_url}: {e}")

    # Register therapy tools if available
    if THERAPY_TOOLS_AVAILABLE:
        try:
            register_therapy_tools(mcp)
            print("🧠 Therapy tools registered")
        except Exception as e:
            print(f"⚠️ Failed to register therapy tools: {e}")
    
    # Start/mount token generator app
    await _maybe_start_token_app(mcp)

    print(f"🌐 Server running on http://{HOST}:{PORT}")
    print("📋 Required: Make server publicly accessible via HTTPS for Puch AI")
    
    await mcp.run_async("streamable-http", host=HOST, port=PORT)


if __name__ == "__main__":
    asyncio.run(main())
