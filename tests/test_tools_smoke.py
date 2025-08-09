import os
import asyncio
import pytest

from emotion_therapy.session_store import RedisSessionManager
from emotion_therapy.tools import register_tools
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


def test_therapy_tools_smoke_flow(tmp_path):
    # Register tools into the MCP instance and obtain mapping
    tool_map = register_tools(mcp)

    user = "smoke_user"

    async def run_flow():
        # 1) Start
        out_start = await tool_map["therapy_start"](user_id=user)  # type: ignore
        assert "Session started" in out_start

        # 2) Feel
        out_feel = await tool_map["therapy_feel"](emotion="ecstatic", user_id=user)  # type: ignore
        assert "Emotion identified" in out_feel

        # 3) Why
        out_why = await tool_map["therapy_why"](user_id=user)  # type: ignore
        assert "Exploring" in out_why

        # 4) Remedy
        out_remedy = await tool_map["therapy_remedy"](user_id=user)  # type: ignore
        assert "Remedies for" in out_remedy

        # 5) Exit
        out_exit = await tool_map["therapy_exit"](user_id=user)  # type: ignore
        assert "Session ended" in out_exit

    asyncio.run(run_flow())
