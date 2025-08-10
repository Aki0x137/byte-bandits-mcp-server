import os
import asyncio
import json
import pytest

from emotion_therapy.session_store import RedisSessionManager
from emotion_therapy.tools import register_tools
from mcp.types import TextContent, ImageContent
from main import mcp


@pytest.fixture(scope="module", autouse=True)
def ensure_redis_running():
    # If no Redis accessible, skip the suite
    url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    try:
        mgr = RedisSessionManager(url)
        mgr.client.ping()
    except Exception:
        pytest.skip("Redis not available; skipping tools smoke tests")


def _as_json(content: TextContent) -> dict:
    assert isinstance(content, TextContent)
    assert content.mimeType == "application/json"
    return json.loads(content.text)


def test_therapy_tools_smoke_flow(tmp_path):
    # Register tools into the MCP instance and obtain mapping
    tool_map = register_tools(mcp)

    user = "smoke_user"

    async def run_flow():
        # 1) Start
        out_start = await tool_map["therapy_start"](user_id=user)  # type: ignore
        data_start = _as_json(out_start)
        assert data_start.get("type") == "session_start"
        assert "Session started" in data_start.get("message", "")

        # 2) Feel
        out_feel = await tool_map["therapy_feel"](emotion="ecstatic", user_id=user)  # type: ignore
        data_feel = _as_json(out_feel)
        assert data_feel.get("type") == "emotion_identification"
        assert data_feel.get("emotion", {}).get("primary") is None or isinstance(data_feel.get("emotion", {}).get("primary"), str)

        # 3) Why
        out_why = await tool_map["therapy_why"](user_id=user)  # type: ignore
        data_why = _as_json(out_why)
        assert data_why.get("type") == "diagnostic_questions"
        assert isinstance(data_why.get("questions", []), list)

        # 4) Remedy
        out_remedy = await tool_map["therapy_remedy"](user_id=user)  # type: ignore
        data_remedy = _as_json(out_remedy)
        assert data_remedy.get("type") == "coping_strategies"
        assert isinstance(data_remedy.get("remedies", []), list)

        # 5) Wheel (may return image)
        out_wheel = await tool_map["therapy_wheel"](user_id=user)  # type: ignore
        if isinstance(out_wheel, list):
            # Expect first to be JSON, second possibly image
            assert isinstance(out_wheel[0], TextContent)
            data_wheel = json.loads(out_wheel[0].text)
            assert data_wheel.get("type") == "emotion_wheel"
            if len(out_wheel) > 1:
                assert isinstance(out_wheel[1], ImageContent)
                assert out_wheel[1].mimeType in {"image/jpeg", "image/png"}
        else:
            data_wheel = _as_json(out_wheel)
            assert data_wheel.get("type") == "emotion_wheel"

        # 6) Exit
        out_exit = await tool_map["therapy_exit"](user_id=user)  # type: ignore
        data_exit = _as_json(out_exit)
        assert data_exit.get("type") == "session_end"

    asyncio.run(run_flow())
