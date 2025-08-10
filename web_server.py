#!/usr/bin/env python3
"""
Simple web form server for collecting name and phone number with JWT token generation.
Includes Redis storage for JWT tokens.
"""

import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import os
import jwt
import redis
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('web_server.log')
    ]
)
logger = logging.getLogger(__name__)

# Create templates directory if it doesn't exist
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL")
REDIS_TTL = int(os.getenv("REDIS_TTL", "86400"))  # 24 hours in seconds

logger.info("🔧 Initializing JWT configuration...")
logger.info(f"🔐 JWT Secret: {'Configured' if JWT_SECRET != 'your-secret-key-change-this-in-production' else 'Using default'}")
logger.info(f"⏰ JWT Expiry: {JWT_EXPIRY_HOURS} hours")

# Initialize Redis client
logger.info("🔧 Initializing Redis connection...")
logger.info(f"🗄️ Redis URL: {REDIS_URL}")

try:
    redis_client = redis.from_url(REDIS_URL)
    logger.info("📡 Testing Redis connection...")
    redis_client.ping()  # Test connection
    REDIS_AVAILABLE = True
    logger.info(f"✅ Redis connected successfully at {REDIS_URL}")
    
    # Test basic operations
    test_key = "test_connection"
    redis_client.setex(test_key, 60, "test_value")
    test_value = redis_client.get(test_key)
    if test_value and test_value.decode('utf-8') == "test_value":
        logger.info("✅ Redis read/write test successful")
    else:
        logger.warning("⚠️ Redis read/write test failed")
    
except Exception as e:
    REDIS_AVAILABLE = False
    logger.error(f"❌ Redis connection failed: {e}")
    logger.error(f"   URL: {REDIS_URL}")
    logger.error(f"   Error type: {type(e).__name__}")

def generate_jwt_token(phone_number: str, name: str) -> str:
    """Generate a JWT token for the user."""
    payload = {
        "phone": phone_number,
        "name": name,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
        "iss": "byte-bandits-mcp-server"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def format_phone_number(phone_number: str, country_code: str = "+91") -> str:
    """Format phone number to include country code if not present."""
    # Remove any non-digit characters from phone number
    cleaned = ''.join(filter(str.isdigit, phone_number))
    
    # Extract country code digits (remove + and spaces)
    country_digits = country_code.replace('+', '').replace(' ', '')
    
    # If it already starts with the country code, keep as is
    if cleaned.startswith(country_digits) and len(cleaned) >= len(country_digits) + 10:
        return cleaned
    
    # If it's 10 digits, add the country code
    if len(cleaned) == 10:
        return f"{country_digits}{cleaned}"
    
    # If it's already long enough, assume it has country code
    if len(cleaned) >= len(country_digits) + 10:
        return cleaned
    
    # Default: add the country code
    return f"{country_digits}{cleaned}"

def store_in_redis(jwt_token: str, phone_number: str) -> bool:
    """Store phone number in Redis with JWT token as key."""
    if not REDIS_AVAILABLE:
        logger.warning(f"⚠️ Cannot store phone number for JWT - Redis not available")
        return False
    
    try:
        logger.info(f"💾 Storing phone number in Redis with JWT as key")
        logger.info(f"   Phone: {phone_number}")
        redis_client.setex(jwt_token, REDIS_TTL, phone_number)
        logger.info(f"✅ Phone number stored successfully with JWT key")
        return True
    except Exception as e:
        logger.error(f"❌ Error storing phone number in Redis: {e}")
        return False

def get_from_redis(jwt_token: str) -> str | None:
    """Retrieve phone number from Redis using JWT token as key."""
    if not REDIS_AVAILABLE:
        logger.warning(f"⚠️ Cannot retrieve phone number - Redis not available")
        return None
    
    try:
        logger.info(f"🔍 Retrieving phone number from Redis using JWT key")
        phone_number = redis_client.get(jwt_token)
        if phone_number:
            logger.info(f"✅ Phone number retrieved successfully: {phone_number.decode('utf-8')}")
        else:
            logger.warning(f"⚠️ No phone number found for JWT token")
        return phone_number
    except Exception as e:
        logger.error(f"❌ Error retrieving phone number from Redis: {e}")
        return None

# Create a simple HTML template
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact Form</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .form-container {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2em;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        input[type="text"], input[type="tel"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
            box-sizing: border-box;
        }
        input[type="text"]:focus, input[type="tel"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .phone-input-container {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .country-code-select {
            width: 140px;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 14px;
            background: white;
            transition: border-color 0.3s ease;
        }
        
        .country-code-select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .phone-input-container input[type="tel"] {
            flex: 1;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
        }
        .error {
            background: #fee;
            border-left-color: #dc3545;
            color: #721c24;
        }
        .success {
            background: #d4edda;
            border-left-color: #28a745;
            color: #155724;
        }
        .jwt-section {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
        }
        .jwt-token {
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            word-break: break-all;
            margin: 10px 0;
            position: relative;
        }
        .copy-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 10px;
        }
        .copy-btn:hover {
            background: #218838;
        }
        .copy-btn:active {
            transform: scale(0.98);
        }
        .mcp-info {
            margin-top: 30px;
            padding: 15px;
            background: rgba(255,255,255,0.9);
            border-radius: 8px;
            text-align: center;
        }
        
        .mcp-setup-section {
            margin-top: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            color: white;
        }
        
        .mcp-setup-section h3 {
            margin-top: 0;
            text-align: center;
            font-size: 1.5em;
        }
        
        .setup-steps {
            line-height: 1.6;
        }
        
        .setup-steps p {
            margin: 12px 0;
        }
        
        .setup-steps a {
            color: #ffd700;
            text-decoration: none;
            font-weight: 600;
        }
        
        .setup-steps a:hover {
            text-decoration: underline;
        }
        
        .whatsapp-link {
            text-align: center;
            margin: 20px 0;
        }
        
        .whatsapp-btn {
            display: inline-block;
            background: #25d366;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: transform 0.2s ease;
        }
        
        .whatsapp-btn:hover {
            transform: translateY(-2px);
            text-decoration: none;
        }
        
        .example-command {
            background: rgba(255,255,255,0.1);
            padding: 12px;
            border-radius: 8px;
            margin: 15px 0;
            text-align: center;
        }
        
        .example-command code {
            font-family: 'Courier New', monospace;
            font-size: 14px;
            color: #ffd700;
        }
        .mcp-info a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        .redis-status {
            margin-top: 10px;
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
            text-align: center;
        }
        .redis-available {
            background: #d4edda;
            color: #155724;
        }
        .redis-unavailable {
            background: #f8d7da;
            color: #721c24;
        }

    </style>
</head>
<body>
    <div class="form-container">
        <h1>Contact Form</h1>
        
        <form method="POST" action="/submit">
            <div class="form-group">
                <label for="name">Name:</label>
                <input type="text" id="name" name="name" required placeholder="Enter your full name">
            </div>
            
            <div class="form-group">
                <label for="phone">Phone Number:</label>
                <div class="phone-input-container">
                    <select id="country-code" name="country_code" class="country-code-select">
                        <option value="+91" data-country="IN">🇮🇳 +91 (India)</option>
                        <option value="+1" data-country="US">🇺🇸 +1 (US/Canada)</option>
                        <option value="+44" data-country="GB">🇬🇧 +44 (UK)</option>
                        <option value="+61" data-country="AU">🇦🇺 +61 (Australia)</option>
                        <option value="+49" data-country="DE">🇩🇪 +49 (Germany)</option>
                        <option value="+33" data-country="FR">🇫🇷 +33 (France)</option>
                        <option value="+81" data-country="JP">🇯🇵 +81 (Japan)</option>
                        <option value="+86" data-country="CN">🇨🇳 +86 (China)</option>
                        <option value="+971" data-country="AE">🇦🇪 +971 (UAE)</option>
                        <option value="+65" data-country="SG">🇸🇬 +65 (Singapore)</option>
                    </select>
                    <input type="tel" id="phone" name="phone" placeholder="Enter phone number" required>
                </div>
            </div>
            
            <button type="submit">Submit</button>
        </form>
        
        {% if result %}
        <div class="result {% if error %}error{% else %}success{% endif %}">
            {{ result }}
        </div>
        {% endif %}
        
        {% if jwt_token %}
        <div class="jwt-section">
            <h3>🔐 Your JWT Token</h3>
            <p>This token is valid for 24 hours and has been stored in Redis.</p>
            <div class="jwt-token" id="jwt-token">{{ jwt_token }}</div>
            <button class="copy-btn" onclick="copyJWT()">📋 Copy JWT Token</button>
        </div>
        
        <div class="mcp-setup-section">
            <h3>🚀 Get Started with MCP on Puch.ai 🚀</h3>
            <div class="setup-steps">
                <p><strong>1️⃣</strong> Head over to <a href="https://puch.ai" target="_blank">puch.ai</a>, punch in your phone number, and grab your jwt_mcp_token 🔑</p>
                <p><strong>2️⃣</strong> Open Puch.ai chat on WhatsApp (<a href="https://puch.ai/hack" target="_blank">👉 puch.ai/hack</a> if you're new here)</p>
                <p><strong>3️⃣</strong> Click here:</p>
                <div class="whatsapp-link">
                    <a href="https://wa.me/919998881729?text=%2Fmcp%20connect%20https%3A%2F%2Fbyte-bandits-mcp-server-2.onrender.com%2Fmcp%20{{ jwt_token }}" target="_blank" class="whatsapp-btn">
                        📱 Connect to MCP via WhatsApp
                    </a>
                </div>
                <p><strong>4️⃣</strong> Wait for the magic connection ✨</p>
                <p><strong>5️⃣</strong> Dive right in — try:</p>
                <div class="example-command">
                    <code>I want to start a therapy session using mcp 💬</code>
                </div>
                <p><strong>⚡ Boom!</strong> You're talking to your MCP server.</p>
            </div>
        </div>
        {% endif %}
        
        <div class="mcp-info">
            <p>📡 MCP Server running on <a href="http://localhost:8086/mcp/">http://localhost:8086/mcp/</a></p>
            <div class="redis-status {% if redis_available %}redis-available{% else %}redis-unavailable{% endif %}">
                {% if redis_available %}
                ✅ Redis Connected - JWT tokens will be stored
                {% else %}
                ⚠️ Redis Unavailable - JWT tokens won't be stored
                {% endif %}
            </div>
        </div>
        

    </div>
    
    <script>
        function copyJWT() {
            const jwtToken = document.getElementById('jwt-token').textContent;
            navigator.clipboard.writeText(jwtToken).then(function() {
                const btn = document.querySelector('.copy-btn');
                const originalText = btn.textContent;
                btn.textContent = '✅ Copied!';
                btn.style.background = '#28a745';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            }).catch(function(err) {
                console.error('Could not copy text: ', err);
                alert('Failed to copy JWT token. Please copy it manually.');
            });
        }
        
        // Auto-detect country code based on timezone
        function detectCountryCode() {
            try {
                const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                const countryCodeMap = {
                    'Asia/Kolkata': '+91',
                    'America/New_York': '+1',
                    'America/Los_Angeles': '+1',
                    'America/Chicago': '+1',
                    'America/Denver': '+1',
                    'Europe/London': '+44',
                    'Europe/Paris': '+33',
                    'Europe/Berlin': '+49',
                    'Australia/Sydney': '+61',
                    'Australia/Melbourne': '+61',
                    'Asia/Tokyo': '+81',
                    'Asia/Shanghai': '+86',
                    'Asia/Dubai': '+971',
                    'Asia/Singapore': '+65'
                };
                
                const detectedCode = countryCodeMap[timezone];
                if (detectedCode) {
                    const select = document.getElementById('country-code');
                    select.value = detectedCode;
                    console.log(`🌍 Detected timezone: ${timezone}, setting country code: ${detectedCode}`);
                }
            } catch (error) {
                console.log('Could not detect timezone, using default');
            }
        }
        
        // Run country detection when page loads
        document.addEventListener('DOMContentLoaded', detectCountryCode);
        

    </script>
</body>
</html>
"""

# Write the template to a file
with open(templates_dir / "form.html", "w") as f:
    f.write(html_template)

# Create FastAPI app
app = FastAPI(title="Contact Form", description="Simple contact form for collecting name and phone number with JWT token generation")

@app.get("/", response_class=HTMLResponse)
async def show_form(request: Request):
    """Display the contact form."""
    logger.info("📄 Form page requested")
    
    response_html = html_template.replace(
        "{% if redis_available %}", 
        f"<!-- redis_available: {REDIS_AVAILABLE} -->"
    ).replace(
        "{{ redis_available }}", 
        str(REDIS_AVAILABLE).lower()
    ).replace(
        "{% endif %}", 
        ""
    )
    return HTMLResponse(content=response_html)

@app.post("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    country_code: str = Form(default="+91")
):
    """Handle form submission."""
    logger.info(f"📝 Form submission received - Name: {name}, Phone: {phone}")
    try:
        # Basic validation
        if not name.strip():
            result = "Error: Name is required"
            error = True
            jwt_token = None
        elif not phone.strip():
            result = "Error: Phone number is required"
            error = True
            jwt_token = None
        elif not phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "").isdigit():
            result = "Error: Please enter a valid phone number"
            error = True
            jwt_token = None
        else:
            # Generate JWT token
            logger.info(f"🔐 Generating JWT token for {name} ({phone})")
            jwt_token = generate_jwt_token(phone.strip(), name.strip())
            logger.info(f"✅ JWT token generated successfully")
            
            # Format phone number with country code
            formatted_phone = format_phone_number(phone.strip(), country_code)
            logger.info(f"📱 Phone formatting: {phone} + {country_code} → {formatted_phone}")
            
            # Store in Redis
            logger.info(f"🗄️ Attempting to store phone number in Redis...")
            redis_success = store_in_redis(jwt_token, formatted_phone)
            
            if redis_success:
                result = f"Success! Thank you {name} for submitting your phone number: {country_code} {phone}. JWT token generated and phone number stored in Redis."
                logger.info(f"🎉 Form submission completed successfully with Redis storage")
            else:
                result = f"Success! Thank you {name} for submitting your phone number: {country_code} {phone}. JWT token generated but could not be stored in Redis."
                logger.warning(f"⚠️ Form submission completed but Redis storage failed")
            
            error = False
        
        # Create response with result
        response_html = html_template.replace(
            "{% if result %}", 
            f"<!-- result: {result} -->"
        ).replace(
            "{% if error %}", 
            f"<!-- error: {error} -->"
        ).replace(
            "{{ result }}", 
            result
        ).replace(
            "{% if error %}error{% else %}success{% endif %}", 
            "error" if error else "success"
        ).replace(
            "{% if jwt_token %}", 
            f"<!-- jwt_token: {jwt_token is not None} -->"
        ).replace(
            "{{ jwt_token }}", 
            jwt_token or ""
        ).replace(
            "{% if redis_available %}", 
            f"<!-- redis_available: {REDIS_AVAILABLE} -->"
        ).replace(
            "{{ redis_available }}", 
            str(REDIS_AVAILABLE).lower()
        ).replace(
            "{% endif %}", 
            ""
        )
        
        return HTMLResponse(content=response_html)
        
    except Exception as e:
        logger.error(f"❌ Error processing form: {e}")
        result = f"Error processing form: {str(e)}"
        error = True
        jwt_token = None
        
        response_html = html_template.replace(
            "{% if result %}", 
            f"<!-- result: {result} -->"
        ).replace(
            "{% if error %}", 
            f"<!-- error: {error} -->"
        ).replace(
            "{{ result }}", 
            result
        ).replace(
            "{% if error %}error{% else %}success{% endif %}", 
            "error"
        ).replace(
            "{% if jwt_token %}", 
            f"<!-- jwt_token: {jwt_token is not None} -->"
        ).replace(
            "{{ jwt_token }}", 
            jwt_token or ""
        ).replace(
            "{% if redis_available %}", 
            f"<!-- redis_available: {REDIS_AVAILABLE} -->"
        ).replace(
            "{{ redis_available }}", 
            str(REDIS_AVAILABLE).lower()
        ).replace(
            "{% endif %}", 
            ""
        )
        
        return HTMLResponse(content=response_html)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("🏥 Health check requested")
    return {
        "status": "healthy", 
        "service": "contact-form",
        "redis_available": REDIS_AVAILABLE,
        "jwt_secret_configured": bool(JWT_SECRET and JWT_SECRET != "your-secret-key-change-this-in-production")
    }

@app.get("/phone/{jwt_token}")
async def get_phone(jwt_token: str):
    """Retrieve phone number for a JWT token (for testing)."""
    logger.info(f"🔍 Phone retrieval request for JWT token")
    
    if not REDIS_AVAILABLE:
        logger.warning(f"⚠️ Phone retrieval failed - Redis not available")
        return {"error": "Redis not available"}
    
    phone_number = get_from_redis(jwt_token)
    if phone_number:
        logger.info(f"✅ Phone number retrieved successfully")
        return {"jwt_token": jwt_token, "phone_number": phone_number.decode('utf-8')}
    else:
        logger.warning(f"⚠️ No phone number found for JWT token")
        return {"error": "Phone number not found for this JWT token"}

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("WEB_PORT", "8087"))
    host = os.getenv("WEB_HOST", "0.0.0.0")
    
    logger.info("🚀 Starting Byte Bandits Web Form Server...")
    logger.info(f"🌐 Server will run on http://{host}:{port}")
    logger.info(f"📝 Form will be available at: http://localhost:{port}/")
    logger.info(f"📡 MCP Server should be running on: http://localhost:8086/mcp/")
    logger.info(f"🔐 JWT Secret: {'Configured' if JWT_SECRET != 'your-secret-key-change-this-in-production' else 'Using default (change in production)'}")
    logger.info(f"📊 JWT Expiry: {JWT_EXPIRY_HOURS} hours")
    logger.info(f"🗄️ Redis Status: {'Connected' if REDIS_AVAILABLE else 'Not available'}")
    logger.info(f"⏰ Redis TTL: {REDIS_TTL} seconds")
    
    if REDIS_AVAILABLE:
        logger.info("✅ Server ready with Redis storage")
    else:
        logger.warning("⚠️ Server ready but Redis storage unavailable")
    
    logger.info("🎯 Starting uvicorn server...")
    
    uvicorn.run(app, host=host, port=port) 