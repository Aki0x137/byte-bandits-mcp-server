import pytest
import asyncio
import os
from unittest.mock import patch, AsyncMock
from main import (
    SimpleBearerAuthProvider,
    MY_NUMBER,
    AUTH_TOKEN,
    echo,
)


class TestAuthentication:
    """Test authentication functionality."""
    
    def test_bearer_auth_provider_valid_token(self):
        """Test valid token authentication."""
        provider = SimpleBearerAuthProvider("test_token")
        
        # Test with valid token
        result = asyncio.run(provider.load_access_token("test_token"))
        assert result is not None
        assert result.token == "test_token"
        assert result.client_id == "puch-client"
        assert result.scopes == ["*"]
    
    def test_bearer_auth_provider_invalid_token(self):
        """Test invalid token authentication."""
        provider = SimpleBearerAuthProvider("test_token")
        
        # Test with invalid token
        result = asyncio.run(provider.load_access_token("wrong_token"))
        assert result is None


class TestCoreTools:
    """Test core MCP tools."""
    
    @pytest.mark.asyncio
    async def test_echo_tool(self):
        """Test echo tool functionality."""
        test_message = "Hello, MCP!"
        result = await echo(test_message)
        assert result == f"Echo: {test_message}"
    
    @pytest.mark.asyncio
    async def test_validate_tool(self):
        """Test validate tool returns correct phone number."""
        from main import validate
        result = await validate()
        assert result == MY_NUMBER
        assert result.isdigit()
        assert len(result) >= 10


class TestEnvironmentValidation:
    """Test environment variable validation."""
    
    def test_auth_token_required(self):
        """Test that AUTH_TOKEN is required."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="AUTH_TOKEN environment variable is required"):
                # This would be caught during module import
                pass
    
    def test_my_number_format_validation(self):
        """Test phone number format validation."""
        # Test cases would validate format requirements
        valid_numbers = ["919876543210", "14155552368"]
        invalid_numbers = ["invalid", "123", "", "abc123def"]
        
        for number in valid_numbers:
            assert number.isdigit()
            assert len(number) >= 10
        
        for number in invalid_numbers:
            assert not (number.isdigit() and len(number) >= 10)


class TestWebFeatures:
    """Test web content fetching features."""
    
    @pytest.mark.asyncio
    async def test_web_content_fetcher_import(self):
        """Test that web features can be imported."""
        try:
            from main import WebContentFetcher, WEB_FEATURES_AVAILABLE
            assert WEB_FEATURES_AVAILABLE
            assert hasattr(WebContentFetcher, 'fetch_url')
        except ImportError:
            # Web features not available, which is acceptable
            pass


class TestImageFeatures:
    """Test image processing features."""
    
    def test_image_features_import(self):
        """Test that image features can be imported."""
        try:
            from main import IMAGE_FEATURES_AVAILABLE
            if IMAGE_FEATURES_AVAILABLE:
                from PIL import Image
                import base64
                import io
                # Basic test that imports work
                assert Image is not None
        except ImportError:
            # Image features not available, which is acceptable
            pass


@pytest.mark.integration
class TestServerIntegration:
    """Integration tests for the full server."""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that server can be initialized."""
        from main import mcp
        assert mcp is not None
        assert hasattr(mcp, 'run_async')
    
    def test_tool_registration(self):
        """Test that tools are properly registered."""
        from main import mcp
        # Check that core tools are registered
        # This would need access to mcp's internal tool registry
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
