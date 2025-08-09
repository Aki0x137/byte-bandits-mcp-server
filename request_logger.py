"""
Request Logger Middleware for FastMCP Server
Logs HTTP request headers and body to terminal for debugging and monitoring.
"""

import json
import logging
from typing import Any, Dict
from fastmcp.server.middleware import Middleware, MiddlewareContext


# Configure logger for terminal output
logger = logging.getLogger("request_logger")
logger.setLevel(logging.INFO)

# Create console handler if not already configured
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Format: timestamp - level - message
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)


class RequestLoggerMiddleware(Middleware):
    """
    Middleware that logs HTTP request headers and body to terminal.
    
    This middleware captures:
    - HTTP request headers (when available)
    - Request body/payload
    - Request method and timestamp
    - Response status and timing
    """
    
    def __init__(self, 
                 include_headers: bool = True,
                 include_body: bool = True,
                 max_body_length: int = 1000,
                 sensitive_headers: list[str] | None = None):
        """
        Initialize the request logger middleware.
        
        Args:
            include_headers: Whether to log HTTP headers
            include_body: Whether to log request body
            max_body_length: Maximum length of body to log (truncated if longer)
            sensitive_headers: List of header names to redact (case-insensitive)
        """
        self.include_headers = include_headers
        self.include_body = include_body
        self.max_body_length = max_body_length
        self.sensitive_headers = set(h.lower() for h in (sensitive_headers or []))
        
        # Common sensitive headers to redact by default
        self.sensitive_headers.update([
            'authorization', 'cookie', 'x-api-key', 'x-auth-token',
            'bearer', 'auth-token', 'api-key'
        ])
    
    async def on_message(self, context: MiddlewareContext, call_next):
        """Log all MCP messages with request details."""
        
        # Start timing
        import time
        start_time = time.perf_counter()
        
        # Log incoming request
        self._log_request(context)
        
        try:
            # Process the request
            result = await call_next(context)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log successful response
            self._log_response(context, result, duration_ms, success=True)
            
            return result
            
        except Exception as e:
            # Calculate duration for failed requests
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log error response
            self._log_response(context, str(e), duration_ms, success=False)
            
            # Re-raise the exception
            raise
    
    def _log_request(self, context: MiddlewareContext):
        """Log incoming request details."""
        
        log_parts = [
            f"🔍 INCOMING REQUEST",
            f"Method: {context.method}",
            f"Type: {context.type}",
            f"Source: {context.source}",
            f"Timestamp: {context.timestamp}"
        ]
        
        # Log HTTP headers if available and enabled
        if self.include_headers and hasattr(context, 'fastmcp_context') and context.fastmcp_context:
            headers = self._extract_headers(context)
            if headers:
                redacted_headers = self._redact_sensitive_headers(headers)
                log_parts.append(f"Headers: {json.dumps(redacted_headers, indent=2)}")
        
        # Log request body/message if enabled
        if self.include_body and hasattr(context, 'message') and context.message:
            body = self._format_message_body(context.message)
            if body:
                log_parts.append(f"Body: {body}")
        
        # Log the complete request info
        logger.info("\n" + "\n".join(log_parts) + "\n" + "─" * 80)
    
    def _log_response(self, context: MiddlewareContext, result: Any, duration_ms: float, success: bool):
        """Log response details."""
        
        status = "✅ SUCCESS" if success else "❌ ERROR"
        
        log_parts = [
            f"📤 RESPONSE {status}",
            f"Method: {context.method}",
            f"Duration: {duration_ms:.2f}ms"
        ]
        
        # Log response summary (avoid logging full response content to keep logs manageable)
        if success:
            if hasattr(result, '__len__'):
                try:
                    log_parts.append(f"Response size: {len(result)} items/chars")
                except:
                    log_parts.append("Response: Success")
            else:
                log_parts.append("Response: Success")
        else:
            log_parts.append(f"Error: {result}")
        
        logger.info("\n" + "\n".join(log_parts) + "\n" + "─" * 80)
    
    def _extract_headers(self, context: MiddlewareContext) -> Dict[str, str] | None:
        """Extract HTTP headers from the context if available."""
        try:
            # Try to access headers from FastMCP context
            if hasattr(context, 'fastmcp_context') and context.fastmcp_context:
                # FastMCP may store HTTP headers in different ways depending on transport
                fastmcp_ctx = context.fastmcp_context
                
                # Check if there's an HTTP request object
                if hasattr(fastmcp_ctx, 'request') and fastmcp_ctx.request:
                    request = fastmcp_ctx.request
                    if hasattr(request, 'headers'):
                        return dict(request.headers)
                
                # Check for headers in context state
                if hasattr(fastmcp_ctx, 'state') and fastmcp_ctx.state:
                    headers = fastmcp_ctx.state.get('headers')
                    if headers:
                        return dict(headers)
                
                # Check for HTTP-specific attributes
                for attr in ['http_headers', 'headers', 'request_headers']:
                    if hasattr(fastmcp_ctx, attr):
                        headers = getattr(fastmcp_ctx, attr)
                        if headers:
                            return dict(headers)
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not extract headers: {e}")
            return None
    
    def _redact_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Redact sensitive header values."""
        redacted = {}
        
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = value
        
        return redacted
    
    def _format_message_body(self, message: Any) -> str:
        """Format the message body for logging."""
        try:
            # Convert message to JSON string for logging
            if hasattr(message, 'model_dump'):
                # Pydantic model
                body_str = json.dumps(message.model_dump(), indent=2)
            elif hasattr(message, '__dict__'):
                # Regular object
                body_str = json.dumps(message.__dict__, indent=2, default=str)
            else:
                # Fallback to string representation
                body_str = str(message)
            
            # Truncate if too long
            if len(body_str) > self.max_body_length:
                body_str = body_str[:self.max_body_length] + "... [TRUNCATED]"
            
            return body_str
            
        except Exception as e:
            logger.debug(f"Could not format message body: {e}")
            return str(message)[:self.max_body_length]


class DetailedRequestLoggerMiddleware(RequestLoggerMiddleware):
    """
    Extended version that logs more detailed information for specific operations.
    """
    
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Log detailed tool call information."""
        logger.info(f"🔧 TOOL CALL: {context.message.name}")
        
        if self.include_body and hasattr(context.message, 'arguments'):
            args_str = json.dumps(context.message.arguments, indent=2, default=str)
            if len(args_str) > self.max_body_length:
                args_str = args_str[:self.max_body_length] + "... [TRUNCATED]"
            logger.info(f"Tool Arguments:\n{args_str}")
        
        return await call_next(context)
    
    async def on_read_resource(self, context: MiddlewareContext, call_next):
        """Log resource read operations."""
        logger.info(f"📄 RESOURCE READ: {getattr(context.message, 'uri', 'unknown')}")
        return await call_next(context)
    
    async def on_get_prompt(self, context: MiddlewareContext, call_next):
        """Log prompt operations."""
        logger.info(f"💬 PROMPT REQUEST: {getattr(context.message, 'name', 'unknown')}")
        return await call_next(context)
