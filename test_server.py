#!/usr/bin/env python3
"""
Test script for the Byte Bandits MCP Server

Usage:
  uv run python test_server.py

Requires the MCP server to be running locally on :8086.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, List

import httpx

BASE_URL = os.environ.get("MCP_BASE_URL", "http://localhost:8086/mcp/")
TOKEN = os.environ.get("AUTH_TOKEN", "demo_token_12345")
COMMON_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "Authorization": f"Bearer {TOKEN}",
}


async def main() -> None:
    print("🧪 Testing Byte Bandits MCP Server...")
    print("=" * 50)

    async with httpx.AsyncClient(headers=COMMON_HEADERS) as client:
        # 1) Initialize
        print("\n1) Initializing MCP session...")
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }
        r = await client.post(BASE_URL, json=init_req)
        print(f"Status: {r.status_code}")
        r.raise_for_status()
        data = r.json()
        sid = r.headers.get("mcp-session-id")
        if sid:
            client.headers["mcp-session-id"] = sid
            print(f"✅ Session established: {sid}")
        else:
            print("⚠️  No session id header returned")

        # Send initialized notification (required by FastMCP)
        await client.post(BASE_URL, json={"jsonrpc": "2.0", "method": "notifications/initialized"})

        # 2) List tools
        print("\n2) Listing tools...")
        list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        r = await client.post(BASE_URL, json=list_req)
        r.raise_for_status()
        tools_res = r.json().get("result", {})
        tools: List[Dict[str, Any]] = tools_res.get("tools", [])
        names = {t.get("name") for t in tools}
        print(f"✅ Found {len(names)} tools: {sorted(names)}")

        async def call_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
            req = {"jsonrpc": "2.0", "id": 40, "method": "tools/call", "params": {"name": name, "arguments": args}}
            resp = await client.post(BASE_URL, json=req)
            resp.raise_for_status()
            return resp.json()

        # 3) Start + Ask (valid in SESSION_STARTED)
        print("\n3) Therapy start + ask...")
        user = os.environ.get("MCP_TEST_USER", "test_user")
        out = await call_tool("therapy_start", {"user_id": user})
        print("   • start:", json.dumps(out)[0:120], "…")

        out = await call_tool("therapy_ask", {"message": "I am worried about work", "user_id": user})
        ask_text = (out.get("result", {}).get("content", [{}]) or [{}])[0].get("text", "")
        print("   • ask:", ask_text)
        if not ("I sense" in ask_text or "I hear you" in ask_text):
            print("   ⚠️  Unexpected ask response; LLM provider may not be active")

        # 4) Feel (sets emotion)
        print("\n4) Therapy feel + why + remedy + exit...")
        out = await call_tool("therapy_feel", {"emotion": "ecstatic", "user_id": user})
        print("   • feel:", json.dumps(out)[0:120], "…")

        out = await call_tool("therapy_why", {"user_id": user})
        print("   • why:", json.dumps(out)[0:120], "…")

        out = await call_tool("therapy_remedy", {"user_id": user})
        print("   • remedy:", json.dumps(out)[0:120], "…")

        out = await call_tool("therapy_exit", {"user_id": user})
        print("   • exit:", json.dumps(out)[0:120], "…")

        print("✅ Therapy flow completed")

    print("\n" + "=" * 50)
    print("🎉 Test completed!")


if __name__ == "__main__":
    asyncio.run(main())
