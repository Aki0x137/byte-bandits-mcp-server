#!/usr/bin/env python3
"""
Test script for the Byte Bandits MCP Server
"""

import asyncio
import json
import httpx


async def test_mcp_server():
    """Test the MCP server functionality."""
    base_url = "http://localhost:8086/mcp/"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer demo_token_12345"
    }
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Byte Bandits MCP Server...")
        print("=" * 50)
        
        # Test 1: Initialize connection
        print("\n1. Testing initialization...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        try:
            response = await client.post(base_url, json=init_request, headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Initialize successful")
                print(f"Server capabilities: {json.dumps(result.get('result', {}).get('capabilities', {}), indent=2)}")
            else:
                print(f"❌ Initialize failed: {response.text}")
        except Exception as e:
            print(f"❌ Initialize error: {e}")
        
        # Test 2: List tools
        print("\n2. Testing tools/list...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        try:
            response = await client.post(base_url, json=tools_request, headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                tools = result.get('result', {}).get('tools', [])
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
            else:
                print(f"❌ Tools list failed: {response.text}")
        except Exception as e:
            print(f"❌ Tools list error: {e}")
        
        # Test 3: Test echo tool
        print("\n3. Testing echo tool...")
        echo_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "echo",
                "arguments": {
                    "message": "Hello from test script!"
                }
            }
        }
        
        try:
            response = await client.post(base_url, json=echo_request, headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                content = result.get('result', {}).get('content', [])
                if content:
                    print(f"✅ Echo response: {content[0].get('text', 'No text')}")
                else:
                    print(f"✅ Echo result: {result}")
            else:
                print(f"❌ Echo failed: {response.text}")
        except Exception as e:
            print(f"❌ Echo error: {e}")
        
        # Test 4: Test validate tool
        print("\n4. Testing validate tool...")
        validate_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "validate",
                "arguments": {}
            }
        }
        
        try:
            response = await client.post(base_url, json=validate_request, headers=headers)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                content = result.get('result', {}).get('content', [])
                if content:
                    phone_number = content[0].get('text', 'No text')
                    print(f"✅ Validate response: {phone_number}")
                    if phone_number.isdigit() and len(phone_number) >= 10:
                        print("✅ Phone number format is valid")
                    else:
                        print("⚠️  Phone number format may be invalid")
                else:
                    print(f"✅ Validate result: {result}")
            else:
                print(f"❌ Validate failed: {response.text}")
        except Exception as e:
            print(f"❌ Validate error: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Test completed!")
        print("\n📋 Next steps:")
        print("1. Make server public via ngrok or cloud deployment")
        print("2. Connect with Puch AI using: /mcp connect https://your-domain/mcp demo_token_12345")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
