#!/usr/bin/env python3
"""
Simple test script for the web form functionality.
"""

import asyncio
import httpx
import json

async def test_web_form():
    """Test the web form functionality."""
    base_url = "http://localhost:8087"
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed")
            print(f"   JWT secret configured: {health_data.get('jwt_secret_configured')}")
        else:
            print("❌ Health check failed!")
            return
        
        # Test form display
        print("\nTesting form display...")
        response = await client.get(f"{base_url}/")
        if response.status_code == 200 and "Contact Form" in response.text:
            print("✅ Form display works!")
        else:
            print("❌ Form display failed!")
            return
        
        # Test form submission with JWT generation
        print("\nTesting form submission with JWT generation...")
        form_data = {
            "name": "John Doe",
            "phone": "1234567890"
        }
        
        response = await client.post(f"{base_url}/submit", data=form_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Form submission works!")
            if "JWT token generated" in response.text:
                print("✅ JWT token generation works!")
            else:
                print("⚠️ JWT token generation not found in response")
            
            if "🔐 Your JWT Token" in response.text:
                print("✅ JWT token display works!")
            else:
                print("⚠️ JWT token display not found in response")
        else:
            print("❌ Form submission failed!")
            return
        
        # Test validation (empty name)
        print("\nTesting validation (empty name)...")
        form_data = {
            "name": "",
            "phone": "1234567890"
        }
        
        response = await client.post(f"{base_url}/submit", data=form_data)
        if response.status_code == 200 and "Error: Name is required" in response.text:
            print("✅ Validation works (empty name)!")
        else:
            print("❌ Validation failed (empty name)!")
        
        # Test validation (invalid phone)
        print("\nTesting validation (invalid phone)...")
        form_data = {
            "name": "John Doe",
            "phone": "abc123"
        }
        
        response = await client.post(f"{base_url}/submit", data=form_data)
        if response.status_code == 200 and "Error: Please enter a valid phone number" in response.text:
            print("✅ Validation works (invalid phone)!")
        else:
            print("❌ Validation failed (invalid phone)!")

if __name__ == "__main__":
    print("🧪 Testing web form functionality...")
    asyncio.run(test_web_form())
    print("\n🎉 Test completed!") 