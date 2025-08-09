#!/usr/bin/env python3
"""
Standalone MCP validation client.

Validates:
- initialize handshake (JSON-RPC + session header)
- tools/list
- tools/call echo
- tools/call validate
- optional therapy flow (start -> feel -> why -> remedy -> exit) if tools are present

Usage:
  uv run python scripts/validate_mcp_app.py \
    --base-url http://localhost:8086/mcp/ \
    --token demo_token_12345

Environment variables:
  MCP_BASE_URL (default: http://localhost:8086/mcp/)
  AUTH_TOKEN   (default: demo_token_12345)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, Optional

import httpx

DEFAULT_BASE_URL = os.environ.get("MCP_BASE_URL", "http://localhost:8086/mcp/")
DEFAULT_TOKEN = os.environ.get("AUTH_TOKEN", "demo_token_12345")

COMMON_HEADERS = {
    "Authorization": f"Bearer {DEFAULT_TOKEN}",
    "Accept": "application/json, text/event-stream",
}


async def try_initialize(client: httpx.AsyncClient, base_url: str) -> bool:
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "clientInfo": {"name": "validator", "version": "0.1.0"},
        },
    }
    try:
        r = await client.post(base_url, json=req)
        if r.status_code != 200:
            return False
        data = r.json()
        sid = r.headers.get("mcp-session-id")
        if sid:
            client.headers["mcp-session-id"] = sid
        ok = data.get("result") is not None
        if not ok:
            return False
        notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        nr = await client.post(base_url, json=notif)
        if nr.status_code not in (200, 202):
            return False
        return True
    except Exception:
        return False


async def wait_for_server(base_url: str, timeout: float = 5.0) -> bool:
    start = time.time()
    async with httpx.AsyncClient(headers=COMMON_HEADERS, timeout=10.0) as client:
        while time.time() - start < timeout:
            if await try_initialize(client, base_url):
                return True
            await asyncio.sleep(0.2)
    return False


async def rpc(client: httpx.AsyncClient, base_url: str, method: str, params: Optional[dict] = None, id_: int = 10) -> dict:
    req: Dict[str, Any] = {"jsonrpc": "2.0", "id": id_, "method": method}
    if params is not None:
        req["params"] = params
    r = await client.post(base_url, json=req)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"RPC error: {data['error']}")
    return data.get("result", {})


async def call_tool(client: httpx.AsyncClient, base_url: str, name: str, arguments: Optional[dict] = None) -> dict:
    return await rpc(
        client,
        base_url,
        "tools/call",
        params={"name": name, "arguments": arguments or {}},
        id_=20,
    )


async def list_tools(client: httpx.AsyncClient, base_url: str) -> dict:
    return await rpc(client, base_url, "tools/list", params=None, id_=30)


async def validate_core(client: httpx.AsyncClient, base_url: str) -> None:
    print("1) initialize ...", end=" ")
    ok = await try_initialize(client, base_url)
    if not ok:
        raise RuntimeError("initialize failed")
    print("ok")

    print("2) tools/list ...", end=" ")
    tools_res = await list_tools(client, base_url)
    tools = tools_res.get("tools", [])
    names = {t.get("name") for t in tools}
    if not tools:
        raise RuntimeError("no tools returned")
    print(f"{len(tools)} tools -> {sorted(names)}")

    print("3) echo ...", end=" ")
    msg = "Hello from validator"
    echo_res = await call_tool(client, base_url, "echo", {"message": msg})
    content = echo_res.get("content", [])
    if not any(f"Echo: {msg}" in (c.get("text") or "") for c in content):
        raise RuntimeError("echo response mismatch")
    print("ok")

    print("4) validate ...", end=" ")
    validate_res = await call_tool(client, base_url, "validate")
    content = validate_res.get("content", [])
    phone = content[0].get("text") if content else ""
    if not (phone and phone.isdigit() and len(phone) >= 10):
        raise RuntimeError("validate did not return a phone number")
    print(f"ok ({phone})")

    # Return tool names for optional flows
    return names


async def validate_therapy_flow(client: httpx.AsyncClient, base_url: str, tool_names: set[str], user_id: str) -> None:
    required = {"therapy_start", "therapy_feel", "therapy_why", "therapy_remedy", "therapy_exit"}
    if not required.issubset(tool_names):
        print("therapy tools not fully available; skipping")
        return

    print("5) therapy_start ...", end=" ")
    out = await call_tool(client, base_url, "therapy_start", {"user_id": user_id})
    if json.dumps(out).find("Session started") == -1:
        raise RuntimeError("therapy_start failed")
    print("ok")

    print("6) therapy_feel ...", end=" ")
    out = await call_tool(client, base_url, "therapy_feel", {"emotion": "ecstatic", "user_id": user_id})
    if json.dumps(out).find("Emotion identified") == -1:
        raise RuntimeError("therapy_feel failed")
    print("ok")

    print("7) therapy_why ...", end=" ")
    out = await call_tool(client, base_url, "therapy_why", {"user_id": user_id})
    if json.dumps(out).find("Exploring") == -1:
        raise RuntimeError("therapy_why failed")
    print("ok")

    print("8) therapy_remedy ...", end=" ")
    out = await call_tool(client, base_url, "therapy_remedy", {"user_id": user_id})
    if json.dumps(out).find("Remedies for") == -1:
        raise RuntimeError("therapy_remedy failed")
    print("ok")

    print("9) therapy_exit ...", end=" ")
    out = await call_tool(client, base_url, "therapy_exit", {"user_id": user_id})
    if json.dumps(out).find("Session ended") == -1:
        raise RuntimeError("therapy_exit failed")
    print("ok")


async def main_async(args: argparse.Namespace) -> int:
    headers = {
        **COMMON_HEADERS,
        "Authorization": f"Bearer {args.token}",
    }
    async with httpx.AsyncClient(headers=headers, timeout=args.timeout) as client:
        if args.wait:
            print(f"Waiting for server {args.base_url} ...")
            if not await wait_for_server(args.base_url, timeout=args.wait_timeout):
                print("Server not ready", file=sys.stderr)
                return 2
        try:
            names = await validate_core(client, args.base_url)
            if not args.skip_therapy:
                uid = args.user_id or f"validator_{int(time.time())}"
                await validate_therapy_flow(client, args.base_url, names, uid)
            print("\nAll checks passed ✅")
            return 0
        except Exception as e:
            print(f"\nValidation failed: {e}", file=sys.stderr)
            return 1


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MCP Server Validation Client")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL, help="MCP base URL (default from MCP_BASE_URL)")
    p.add_argument("--token", default=DEFAULT_TOKEN, help="Auth token (default from AUTH_TOKEN)")
    p.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout seconds")
    p.add_argument("--wait", action="store_true", help="Wait for server readiness using initialize loop")
    p.add_argument("--wait-timeout", type=float, default=8.0, help="Max seconds to wait for server readiness")
    p.add_argument("--skip-therapy", action="store_true", help="Skip therapy flow validation")
    p.add_argument("--user-id", default=None, help="User id to use for therapy flow")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    code = asyncio.run(main_async(args))
    sys.exit(code)


if __name__ == "__main__":
    main()
