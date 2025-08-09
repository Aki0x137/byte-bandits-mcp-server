import os
import asyncio
import json
import time

import pytest
import httpx

BASE_URL = os.environ.get("MCP_BASE_URL", "http://localhost:8086/mcp/")
TOKEN = os.environ.get("AUTH_TOKEN", "demo_token_12345")

# Include required Accept header for FastMCP streamable-http
COMMON_HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json, text/event-stream",
}

pytestmark = pytest.mark.asyncio


async def try_initialize(client: httpx.AsyncClient) -> bool:
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "e2e-test", "version": "0.0.1"},
        },
    }
    try:
        r = await client.post(BASE_URL, json=req)
        if r.status_code != 200:
            return False
        data = r.json()
        # Persist session id for follow-up requests
        sid = r.headers.get("mcp-session-id")
        if sid:
            client.headers["mcp-session-id"] = sid
        ok = data.get("result") is not None
        if not ok:
            return False
        # Send initialized notification to complete handshake
        notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        nr = await client.post(BASE_URL, json=notif)
        if nr.status_code not in (200, 202):  # 202 is valid for notifications
            return False
        return True
    except Exception:
        return False


async def wait_for_server(timeout: float = 5.0):
    start = time.time()
    async with httpx.AsyncClient(headers=COMMON_HEADERS) as client:
        while time.time() - start < timeout:
            if await try_initialize(client):
                return True
            await asyncio.sleep(0.2)
    return False


async def rpc(client: httpx.AsyncClient, method: str, params: dict | None = None, id_: int = 10):
    req = {"jsonrpc": "2.0", "id": id_, "method": method}
    if params is not None:
        req["params"] = params
    r = await client.post(BASE_URL, json=req)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise AssertionError(f"RPC error: {data['error']}")
    return data.get("result")


async def call_tool(client: httpx.AsyncClient, name: str, arguments: dict | None = None):
    return await rpc(
        client,
        "tools/call",
        params={"name": name, "arguments": arguments or {}},
        id_=20,
    )


async def list_tools(client: httpx.AsyncClient):
    # tools/list takes no params per MCP spec; omit params entirely
    return await rpc(client, "tools/list", params=None, id_=30)


async def test_end_to_end_tools_flow():
    # Skip cleanly if server isn't running
    if not await wait_for_server():
        pytest.skip(f"MCP server is not running on {BASE_URL}")

    headers = COMMON_HEADERS
    async with httpx.AsyncClient(headers=headers) as client:
        # Ensure initialize and session header present
        ok = await try_initialize(client)
        if not ok:
            pytest.skip("Failed to initialize MCP session")
        # list tools
        tools_res = await list_tools(client)
        tool_names = {t.get("name") for t in tools_res.get("tools", [])}
        assert "echo" in tool_names
        assert "validate" in tool_names

        # echo
        echo_res = await call_tool(client, "echo", {"message": "hello"})
        content = echo_res.get("content", [])
        assert any("Echo: hello" in (c.get("text") or "") for c in content)

        # validate
        validate_res = await call_tool(client, "validate")
        content = validate_res.get("content", [])
        phone = content[0].get("text") if content else ""
        assert phone and phone.isdigit() and len(phone) >= 10

        # Therapy tools (best-effort; skip if not registered or Redis missing)
        maybe_tools = {"therapy_start", "therapy_feel", "therapy_why", "therapy_remedy", "therapy_exit"}
        if maybe_tools.issubset(tool_names):
            user = "e2e_user"
            out = await call_tool(client, "therapy_start", {"user_id": user})
            assert json.dumps(out).find("Session started") != -1

            out = await call_tool(client, "therapy_feel", {"emotion": "ecstatic", "user_id": user})
            assert json.dumps(out).find("Emotion identified") != -1

            out = await call_tool(client, "therapy_why", {"user_id": user})
            assert json.dumps(out).find("Exploring") != -1

            out = await call_tool(client, "therapy_remedy", {"user_id": user})
            assert json.dumps(out).find("Remedies for") != -1

            out = await call_tool(client, "therapy_exit", {"user_id": user})
            assert json.dumps(out).find("Session ended") != -1
        else:
            pytest.skip("Therapy tools not registered; skipping therapy flow")
