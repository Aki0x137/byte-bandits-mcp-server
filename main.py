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

# Optional Emotion Therapy tools registration
try:
    from emotion_therapy.tools import register_tools as register_therapy_tools
    THERAPY_TOOLS_AVAILABLE = True
except Exception:
    THERAPY_TOOLS_AVAILABLE = False

# Load environment variables
load_dotenv()

# Required environment variables
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER")
# Redis-related (optional)
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
THERAPY_SESSION_TTL = os.environ.get("THERAPY_SESSION_TTL", "259200")

# Validate required environment variables
if not AUTH_TOKEN:
    raise ValueError("AUTH_TOKEN environment variable is required. Please set it in your .env file.")
if not MY_NUMBER:
    raise ValueError("MY_NUMBER environment variable is required. Please set it in your .env file.")

# Validate phone number format
if not MY_NUMBER.isdigit() or len(MY_NUMBER) < 10:
    raise ValueError("MY_NUMBER must be in format {country_code}{number} (e.g., 919876543210)")


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


@mcp.tool
async def validate() -> str:
    """
    Validate tool required by Puch AI.
    Returns the server owner's phone number for authentication.
    """
    return MY_NUMBER


# Register therapy tools if available
try:
    from emotion_therapy.tools import register_tools as register_therapy_tools
    register_therapy_tools(mcp)
    THERAPY_TOOLS_AVAILABLE = True
except Exception:
    THERAPY_TOOLS_AVAILABLE = False


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
    
    print(f"✅ Available features: {', '.join(features)}")

    # Try Redis connectivity (non-fatal)
    if REDIS_FEATURES_AVAILABLE:
        try:
            mgr = get_redis_session_manager()
            # ping may raise if Redis unavailable
            if hasattr(mgr, 'client'):
                mgr.client.ping()
            print(f"🗄️ Redis configured at {REDIS_URL} (TTL {THERAPY_SESSION_TTL}s)")
        except Exception as e:
            print(f"⚠️ Redis not reachable at {REDIS_URL}: {e}")

    # Register therapy tools if available
    if THERAPY_TOOLS_AVAILABLE:
        try:
            register_therapy_tools(mcp)
            print("🧠 Therapy tools registered")
        except Exception as e:
            print(f"⚠️ Failed to register therapy tools: {e}")
    
    print("🌐 Server running on http://0.0.0.0:8086")
    print("📋 Required: Make server publicly accessible via HTTPS for Puch AI")
    
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)


if __name__ == "__main__":
    asyncio.run(main())
