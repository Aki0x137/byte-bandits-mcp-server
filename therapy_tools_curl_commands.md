# CURL Commands for Emotion Therapy Tools

This document provides CURL commands for all therapy tools available in the MCP server.

## Server Configuration
- **Base URL**: `http://localhost:8086`
- **Authentication**: Bearer token required (set AUTH_TOKEN env var)
- **Content-Type**: `application/json`

## Environment Setup
```bash
# Set your auth token
export AUTH_TOKEN="your_auth_token_here"
export BASE_URL="http://localhost:8086"
```

## 1. therapy_start - Start a new therapy session

```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_start",
      "arguments": {
        "user_id": "user123"
      }
    }
  }'
```

## 2. therapy_feel - Set emotional state

```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_feel",
      "arguments": {
        "emotion": "anxious",
        "user_id": "user123"
      }
    }
  }'
```

### Alternative emotions to try:
```bash
# Fear/anxiety
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_feel",
      "arguments": {
        "emotion": "fear",
        "user_id": "user123"
      }
    }
  }'

# Anger
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_feel",
      "arguments": {
        "emotion": "angry about work deadlines",
        "user_id": "user123"
      }
    }
  }'

# Sadness
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_feel",
      "arguments": {
        "emotion": "sad and lonely",
        "user_id": "user123"
      }
    }
  }'

# Joy
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_feel",
      "arguments": {
        "emotion": "excited about promotion",
        "user_id": "user123"
      }
    }
  }'
```

## 3. therapy_ask - Free-form conversation

```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_ask",
      "arguments": {
        "message": "I have been feeling overwhelmed at work lately",
        "user_id": "user123"
      }
    }
  }'
```

### Example conversation starters:
```bash
# Work stress
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_ask",
      "arguments": {
        "message": "My boss keeps giving me impossible deadlines and I feel like I am failing",
        "user_id": "user123"
      }
    }
  }'

# Relationship issues
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_ask",
      "arguments": {
        "message": "I had a fight with my partner and I do not know how to resolve it",
        "user_id": "user123"
      }
    }
  }'

# Self-doubt
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_ask",
      "arguments": {
        "message": "I keep doubting myself and wondering if I am good enough",
        "user_id": "user123"
      }
    }
  }'
```

## 4. therapy_wheel - Show emotion wheel guide

```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_wheel",
      "arguments": {
        "user_id": "user123"
      }
    }
  }'
```

## 5. therapy_why - Get diagnostic questions

```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_why",
      "arguments": {
        "user_id": "user123"
      }
    }
  }'
```

## 6. therapy_remedy - Get coping strategies

```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_remedy",
      "arguments": {
        "user_id": "user123"
      }
    }
  }'
```

## 7. therapy_breathe - Breathing exercise

```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_breathe",
      "arguments": {
        "user_id": "user123"
      }
    }
  }'
```

## 8. therapy_sos - Emergency support

```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_sos",
      "arguments": {
        "user_id": "user123"
      }
    }
  }'
```

## 9. therapy_exit - End session

```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_exit",
      "arguments": {
        "user_id": "user123"
      }
    }
  }'
```

## 10. therapy_status - Check session status

```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_status",
      "arguments": {
        "user_id": "user123"
      }
    }
  }'
```

## Complete Therapy Session Flow Example

Here's a complete session flow from start to finish:

```bash
# 1. Start session
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_start",
      "arguments": {
        "user_id": "demo_user"
      }
    }
  }'

# 2. Check what's available
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_status",
      "arguments": {
        "user_id": "demo_user"
      }
    }
  }'

# 3. Express emotion
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_feel",
      "arguments": {
        "emotion": "stressed about deadlines",
        "user_id": "demo_user"
      }
    }
  }'

# 4. Get diagnostic questions
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_why",
      "arguments": {
        "user_id": "demo_user"
      }
    }
  }'

# 5. Get coping strategies
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_remedy",
      "arguments": {
        "user_id": "demo_user"
      }
    }
  }'

# 6. Try breathing exercise
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_breathe",
      "arguments": {
        "user_id": "demo_user"
      }
    }
  }'

# 7. End session
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapy_exit",
      "arguments": {
        "user_id": "demo_user"
      }
    }
  }'
```

## Additional MCP Tools in main.py

The server also includes these non-therapy tools:

### validate - Required by Puch AI
```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "validate",
      "arguments": {}
    }
  }'
```

### echo - Test connectivity
```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {
        "message": "Hello MCP Server!"
      }
    }
  }'
```

### therapeutic_response - Enhanced therapy with Chain of Thoughts
```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "therapeutic_response",
      "arguments": {
        "emotion": "anxiety",
        "context": "work pressure and deadlines",
        "user_message": "I feel overwhelmed by everything I need to do",
        "tone": "soothing"
      }
    }
  }'
```

### fetch_web_content - Fetch web content (if enabled)
```bash
curl -X POST "$BASE_URL/mcp/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "fetch_web_content",
      "arguments": {
        "url": "https://example.com",
        "raw": false
      }
    }
  }'
```

## Error Handling

Common response formats:

### Success Response
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Session started. How are you feeling today?"
      }
    ]
  },
  "id": "call_id"
}
```

### Error Response
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": "Additional error details"
  },
  "id": "call_id"
}
```

## Notes

1. **Authentication**: All requests require a valid bearer token in the Authorization header
2. **User ID**: Use consistent user_id across calls to maintain session state
3. **State Management**: Follow the therapy flow: start → feel → why → remedy → exit
4. **Emergency**: `therapy_sos` can be called at any time
5. **Enhanced Manager**: The unified LLM manager provides additional safety checks and enhanced responses when enabled
6. **Environment Variables**: Make sure Redis is running and properly configured for session persistence