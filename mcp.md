# Byte Bandits MCP Server - Complete Usage Guide

A comprehensive Model Context Protocol (MCP) server with emotion therapy tools, web content fetching, image processing, and core utilities for Puch AI integration.

## 🚀 Quick Start

### 1. Connect to the Server

In Puch AI, use the connect command:
```
/mcp connect https://your-domain.ngrok.app/mcp your_auth_token
```

### 2. Test Connection

Start with the echo tool to verify connectivity:
```
echo Hello MCP Server!
```

### 3. Start Therapy Session

For emotion therapy features:
```
therapy_start your_user_id
```

Then try:
```
therapy_feel ecstatic user_id=your_user_id
therapy_why user_id=your_user_id
therapy_remedy user_id=your_user_id
therapy_exit user_id=your_user_id
```

## ▶️ Run the server locally

Prerequisites: Python 3.11+, uv (recommended), Redis optional (for therapy session persistence).

- Configure environment variables (required):
  - AUTH_TOKEN: bearer token for auth
  - MY_NUMBER: your phone number digits (e.g., 14155551234)
- Optional:
  - REDIS_URL, THERAPY_SESSION_TTL
  - THERAPY_AUTO_WHY=0|1
  - THERAPY_USE_LANGCHAIN=0|1 (requires OPENAI_API_KEY and `uv pip install -e .[langchain]`)

Quick start with uv:
```bash
uv sync --dev
uv run python main.py
```

Using helper script:
```bash
AUTH_TOKEN=demo_token_12345 MY_NUMBER=14155551234 scripts/run_server.sh
```

Optional Redis (for therapy):
```bash
export REDIS_URL=redis://localhost:6379
export THERAPY_SESSION_TTL=259200
```

Optional: auto-run diagnostic questions after /feel
```bash
export THERAPY_AUTO_WHY=1   # or true/yes
```

Server URL (default):
```
http://localhost:8086/mcp/
```

Validate locally:
```bash
uv run python scripts/validate_mcp_app.py --base-url http://localhost:8086/mcp/ --wait
```

## 📋 Core Tools

### `validate`
**Purpose:** Required by Puch AI for authentication  
**Usage:** `validate`  
**Parameters:** None  
**Returns:** Server owner's phone number  
**Example:** 
```
validate
```

### `echo`
**Purpose:** Test server connectivity  
**Usage:** `echo <message>`  
**Parameters:**
- `message` (string): Text to echo back  
**Returns:** Echoed message with prefix  
**Example:**
```
echo Hello World!
# Returns: "Echo: Hello World!"
```

## 🌐 Web Content Tools

### `fetch_web_content`
**Purpose:** Fetch and convert web content to readable markdown  
**Usage:** `fetch_web_content <url> [raw]`  
**Parameters:**
- `url` (string): URL to fetch content from
- `raw` (boolean, optional): Return raw content without markdown conversion (default: false)

**Returns:** Processed web content with metadata  
**Examples:**
```
# Fetch and convert to markdown
fetch_web_content https://example.com

# Fetch raw content
fetch_web_content https://example.com true
```

**Features:**
- Converts HTML to readable markdown
- Extracts main content using readability algorithms
- Handles redirects and error responses
- Returns content type information

## 🖼️ Image Processing Tools

### `convert_to_bw`
**Purpose:** Convert images to black and white  
**Usage:** `convert_to_bw <image_data>`  
**Parameters:**
- `image_data` (string): Base64-encoded image data

**Returns:** List of ImageContent with converted black & white image  
**Example:**
```
convert_to_bw iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==
```

## 🧠 Emotion Therapy Tools

The emotion therapy system follows a state-based flow using Plutchik's Wheel of Emotions. Each user has a session that tracks their emotional state and provides appropriate interventions.

### Session States
- **NO_SESSION**: Initial state, no active session
- **SESSION_STARTED**: Session active, ready for emotion input
- **EMOTION_IDENTIFIED**: User's emotion has been identified
- **DIAGNOSTIC_COMPLETE**: Diagnostic questions completed
- **REMEDY_PROVIDED**: Coping strategies provided
- **EMERGENCY**: Emergency protocol activated

### Session Management

#### `therapy_start`
**Purpose:** Start a new therapy session  
**Usage:** `therapy_start <user_id>`  
**Parameters:**
- `user_id` (string): Unique identifier for the user

**Returns:** Session start confirmation  
**Example:**
```
therapy_start alice123
# Returns: "Session started! Ready to explore your emotions..."
```

#### `therapy_exit`
**Purpose:** End session and clear data  
**Usage:** `therapy_exit <user_id>`  
**Parameters:**
- `user_id` (string): User identifier

**Returns:** Session end confirmation  
**Example:**
```
therapy_exit alice123
# Returns: "Session ended. You're welcome back anytime."
```

#### `therapy_status`
**Purpose:** Show current state and available commands  
**Usage:** `therapy_status <user_id>`  
**Parameters:**
- `user_id` (string): User identifier

**Returns:** Current session state and available commands  
**Example:**
```
therapy_status alice123
# Returns: "State: SESSION_STARTED. Available: /ask /wheel /feel /breathe /exit /sos"
```

### Emotion Identification

#### `therapy_feel`
**Purpose:** Set current emotion using the wheel taxonomy  
**Usage:** `therapy_feel <emotion> <user_id>`  
**Parameters:**
- `emotion` (string): Emotion term (primary/variant/blend)
- `user_id` (string): User identifier

**Supported Emotions:**

**Primary Emotions:** joy, trust, fear, surprise, sadness, disgust, anger, anticipation

**Intensity Variants:**
- **JOY**: ecstasy (intense), joy (base), serenity (mild)
- **TRUST**: admiration (intense), trust (base), acceptance (mild)
- **FEAR**: terror (intense), fear (base), apprehension (mild)
- **SURPRISE**: amazement (intense), surprise (base), distraction (mild)
- **SADNESS**: grief (intense), sadness (base), pensiveness (mild)
- **DISGUST**: loathing (intense), disgust (base), boredom (mild)
- **ANGER**: rage (intense), anger (base), annoyance (mild)
- **ANTICIPATION**: vigilance (intense), anticipation (base), interest (mild)

**Emotion Blends:**
- **love** (joy + trust)
- **submission** (trust + fear)
- **awe** (fear + surprise)
- **disapproval** (surprise + sadness)
- **remorse** (sadness + disgust)
- **contempt** (disgust + anger)
- **aggressiveness** (anger + anticipation)
- **optimism** (anticipation + joy)

**Examples:**
```
therapy_feel joy alice123
therapy_feel ecstatic alice123
therapy_feel love alice123
therapy_feel anxious alice123  # Maps to fear/apprehension
```

#### `therapy_ask`
**Purpose:** Free-form message analysis and emotion suggestion  
**Usage:** `therapy_ask <message> <user_id>`  
**Parameters:**
- `message` (string): User's free-form message
- `user_id` (string): User identifier

**Returns:** Emotion analysis with confidence and suggestions  
**Example:**
```
therapy_ask "I'm feeling overwhelmed by work deadlines" alice123
# Returns analysis with detected emotion and confidence level
```

#### `therapy_wheel`
**Purpose:** Show the Wheel of Emotions guide  
**Usage:** `therapy_wheel <user_id>`  
**Parameters:**
- `user_id` (string): User identifier

**Returns:** Complete wheel taxonomy and usage instructions  
**Example:**
```
therapy_wheel alice123
# Returns: Comprehensive emotion wheel with all categories and examples
```

### Diagnostic Tools

#### `therapy_why`
**Purpose:** Ask diagnostic questions based on current emotion  
**Usage:** `therapy_why <user_id>`  
**Parameters:**
- `user_id` (string): User identifier

**Requirements:** Must have identified emotion first  
**Returns:** 2-3 tailored diagnostic questions  
**Example:**
```
therapy_why alice123
# For FEAR: "What specific situation makes you feel unsafe?"
# For ANGER: "What boundaries feel like they're being crossed?"
```

### Remedy and Coping Tools

#### `therapy_remedy`
**Purpose:** Suggest coping strategies for the current emotion  
**Usage:** `therapy_remedy <user_id>`  
**Parameters:**
- `user_id` (string): User identifier

**Requirements:** Must have identified emotion  
**Returns:** Personalized coping strategies and exercises  
**Example:**
```
therapy_remedy alice123
# Returns context-appropriate remedies based on emotion and situation
```

#### `therapy_breathe`
**Purpose:** Guided breathing exercise  
**Usage:** `therapy_breathe <user_id>`  
**Parameters:**
- `user_id` (string): User identifier

**Returns:** Step-by-step breathing instructions  
**Example:**
```
therapy_breathe alice123
# Returns: "Try box breathing: inhale 4, hold 4, exhale 4, hold 4 — repeat 4 cycles."
```

### Self-Help Tools (Available Anytime)

#### `therapy_quote`
**Purpose:** Quick motivation quote  
**Usage:** `therapy_quote <user_id>`  
**Returns:** A short motivational quote.

#### `therapy_journal`
**Purpose:** Guided journaling prompts  
**Usage:** `therapy_journal <user_id>`  
**Returns:** A short list of prompts to reflect on.

#### `therapy_audio`
**Purpose:** Meditation / grounding audio suggestions  
**Usage:** `therapy_audio <user_id>`  
**Returns:** Suggested audio searches to try.

### Tracking & Continuity

#### `therapy_checkin`
**Purpose:** Daily mood check-in and lightweight snapshot  
**Usage:** `therapy_checkin <user_id>`  
**Behavior:** Adds an entry to mood history. May transition to SESSION_STARTED from NO_SESSION/REMEDY_PROVIDED.

#### `therapy_moodlog`
**Purpose:** View recent mood history  
**Usage:** `therapy_moodlog <user_id> [limit]`  
**Parameters:**
- `limit` (int, optional, default 10, max 50)

**Note:** Scheduling of future check-ins is not implemented; use an external scheduler if needed.

### Emergency Tools

#### `therapy_sos`
**Purpose:** Emergency protocol activation  
**Usage:** `therapy_sos <user_id>`  
**Parameters:**
- `user_id` (string): User identifier

**Available:** Always accessible from any state  
**Returns:** Emergency resources and contact information  
**Example:**
```
therapy_sos alice123
# Returns emergency protocol with crisis helpline information
```

## 🔄 Therapy Session Flow Examples

### Basic Emotion Processing Flow

1. **Start Session**
   ```
   therapy_start alice123
   ```

2. **Identify Emotion**
   ```
   therapy_feel "stressed and overwhelmed" alice123
   # OR use specific terms:
   therapy_feel anxiety alice123
   ```

3. **Explore with Questions**
   ```
   therapy_why alice123
   ```

4. **Get Coping Strategies**
   ```
   therapy_remedy alice123
   ```

5. **Use Self-Help Tools**
   ```
   therapy_breathe alice123
   therapy_quote alice123
   therapy_journal alice123
   therapy_audio alice123
   ```

6. **End Session**
   ```
   therapy_exit alice123
   ```

### Alternative Flow with Free-Form Input

1. **Start Session**
   ```
   therapy_start bob456
   ```

2. **Free-Form Analysis**
   ```
   therapy_ask "I had a terrible day at work and feel like giving up" bob456
   ```

3. **Get Emotion Wheel for Reference**
   ```
   therapy_wheel bob456
   ```

4. **Set Specific Emotion**
   ```
   therapy_feel sadness bob456
   ```

5. **Continue with diagnostic and remedies...**

### Emergency Situations

Emergency protocol can be activated at any time:
```
therapy_sos alice123
```

## 🎯 State Transitions

The therapy system enforces proper flow transitions:

- **From NO_SESSION**: `/start`, `/sos`, `/checkin`
- **From SESSION_STARTED**: Emotion ID commands (`/ask`, `/wheel`, `/feel`), Self-help (`/breathe`, `/quote`, `/journal`, `/audio`), `/exit`, `/sos`
- **From EMOTION_IDENTIFIED**: `/why`, `/remedy`, `/moodlog`, Self-help, `/exit`, `/sos`
- **From DIAGNOSTIC_COMPLETE**: `/remedy`, `/moodlog`, Self-help, `/exit`, `/sos`
- **From REMEDY_PROVIDED**: `/ask`, `/checkin`, `/moodlog`, Self-help, `/exit`, `/sos`
- **From EMERGENCY**: `/sos`, `/exit`

## 🔧 Technical Details

### Authentication
All tools require Bearer token authentication:
```
Authorization: Bearer your_auth_token
```

### MCP Protocol
The server implements JSON-RPC 2.0 over HTTP with MCP extensions:

1. **Initialize Connection**
   ```json
   {
     "jsonrpc": "2.0",
     "id": 1,
     "method": "initialize",
     "params": {
       "protocolVersion": "2024-11-05",
       "capabilities": {"tools": {}},
       "clientInfo": {"name": "client", "version": "1.0.0"}
     }
   }
   ```

2. **List Available Tools**
   ```json
   {
     "jsonrpc": "2.0",
     "id": 2,
     "method": "tools/list"
   }
   ```

3. **Call Tool**
   ```json
   {
     "jsonrpc": "2.0",
     "id": 3,
     "method": "tools/call",
     "params": {
       "name": "therapy_start",
       "arguments": {"user_id": "alice123"}
     }
   }
   ```

### Data Persistence

- **Session Storage**: Redis with TTL (default 3 days)
- **History Tracking**: Command history per user
- **Privacy**: No PII stored beyond user_id

### Error Handling

The server provides detailed error messages for:
- Invalid state transitions
- Missing required parameters
- Authentication failures
- Network/connectivity issues

### Rate Limiting

Consider implementing rate limits, especially for:
- Emergency protocol (`therapy_sos`)
- Session creation
- Repeated failed authentication

## 🚨 Best Practices

### For Users
1. **Start with a session** before using therapy tools
2. **Use specific emotion terms** when possible for better accuracy
3. **Follow the suggested flow** for best therapeutic outcomes
4. **Use emergency protocol** when in crisis

### For Developers
1. **Always check state transitions** before calling tools
2. **Handle authentication properly** with Bearer tokens
3. **Implement proper error handling** for network issues
4. **Respect user privacy** - use stable user_ids without PII

### Security Considerations
1. **Use HTTPS** in production
2. **Validate all inputs** before processing
3. **Store auth tokens securely**
4. **Implement session timeouts**
5. **Monitor for abuse** of emergency protocols

## 🆘 Troubleshooting

### Common Issues

1. **Tool Not Found**
   - Verify tool name spelling
   - Check if optional features are enabled
   - Ensure proper authentication

2. **Invalid State Transition**
   - Check current session state with `therapy_status`
   - Follow the required flow sequence
   - Start new session if needed

3. **Authentication Errors**
   - Verify Bearer token format
   - Check token expiration
   - Ensure token matches server configuration

4. **Redis Connection Issues**
   - Verify Redis server is running
   - Check REDIS_URL configuration
   - Validate network connectivity

### Debug Commands

Check server status:
```
therapy_status your_user_id
```

Test basic connectivity:
```
echo test
validate
```

Verify available tools:
```
# Use MCP tools/list method
```

## 📞 Support

- **Documentation**: See README.md for setup instructions
- **Issues**: Check repository issues page
- **Community**: Join Puch AI Discord for MCP support
- **Emergency**: If experiencing mental health crisis, contact local emergency services

---

**Built with ❤️ by the Byte Bandits team for Puch AI integration**
