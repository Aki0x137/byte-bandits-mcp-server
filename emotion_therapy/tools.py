from __future__ import annotations

from typing import Annotated, Optional

from fastmcp import FastMCP
from pydantic import Field

from .models import SessionState
from .session_store import get_redis_session_manager
from .validator import validate_command, get_available_commands
from .wheel import get_wheel_text
from .llm_stub import analyze_text, probe_questions, suggest_remedies
from .responses import (
    start_response,
    feel_response,
    ask_response,
    wheel_response,
    why_response,
    remedy_response,
    breathe_response,
    sos_response,
    exit_response,
    status_response,
)


def register_tools(mcp: FastMCP) -> dict[str, object]:
    mgr = get_redis_session_manager()

    # Implementation functions (returned for tests)
    async def _therapy_start(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/start", None, sess.state)
        if not res.is_valid:
            return f"Cannot start now. Try: {' '.join(res.suggested_commands)}"
        sess.state = res.next_state or sess.state
        mgr.save_session(sess)
        mgr.add_to_history(user_id, "/start", None, {"ok": True})
        return start_response()

    async def _therapy_feel(emotion: str, user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/feel", emotion, sess.state)
        if not res.is_valid:
            return f"{res.error_message}"
        details = res.llm_context.get("emotion_details", {})
        sess.state = res.next_state or sess.state
        sess.current_emotion = details.get("variant_label") or details.get("primary")
        sess.context["emotion_details"] = details
        mgr.save_session(sess)
        mgr.add_to_history(user_id, "/feel", emotion, details)
        return feel_response(
            details.get("primary", ""),
            details.get("variant_label"),
            details.get("intensity"),
            details.get("blend_name"),
        )

    async def _therapy_ask(message: str, user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/ask", message, sess.state)
        if not res.is_valid:
            return f"{res.error_message}"
        analysis = analyze_text(message)
        mgr.add_to_history(user_id, "/ask", message, analysis)
        return ask_response(message, analysis)

    async def _therapy_wheel(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        _ = validate_command("/wheel", None, sess.state)  # allowed check
        text = get_wheel_text()
        mgr.add_to_history(user_id, "/wheel", None, None)
        return wheel_response(text)

    async def _therapy_why(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/why", None, sess.state)
        if not res.is_valid:
            return f"{res.error_message}"
        sess.state = res.next_state or sess.state
        details = sess.context.get("emotion_details") or {}
        primary = details.get("primary") or (sess.current_emotion or "").upper() or "JOY"
        qs = probe_questions(primary)
        mgr.save_session(sess)
        mgr.add_to_history(user_id, "/why", None, qs)
        return why_response(primary, qs)

    async def _therapy_remedy(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/remedy", None, sess.state)
        if not res.is_valid:
            return f"{res.error_message}"
        details = sess.context.get("emotion_details") or {}
        primary = details.get("primary") or (sess.current_emotion or "").upper() or "JOY"
        rem = suggest_remedies(primary, {"topic": sess.context.get("topic", "")})
        sess.state = res.next_state or sess.state
        mgr.save_session(sess)
        mgr.add_to_history(user_id, "/remedy", None, rem)
        return remedy_response(primary, rem)

    async def _therapy_breathe(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/breathe", None, sess.state)
        if not res.is_valid:
            return f"{res.error_message}"
        mgr.add_to_history(user_id, "/breathe", None, None)
        return breathe_response()

    async def _therapy_sos(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/sos", None, sess.state)
        if not res.is_valid:
            return f"{res.error_message}"
        sess.state = res.next_state or sess.state
        mgr.save_session(sess)
        mgr.add_to_history(user_id, "/sos", None, None)
        return sos_response()

    async def _therapy_exit(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/exit", None, sess.state)
        if not res.is_valid:
            return f"{res.error_message}"
        mgr.delete_session(user_id)
        mgr.add_to_history(user_id, "/exit", None, None)
        return exit_response()

    async def _therapy_status(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        available = get_available_commands(sess.state)
        return status_response(sess.state, available)

    # Register MCP tools as thin wrappers
    @mcp.tool(description="Start a therapy session for the given user_id")
    async def therapy_start(user_id: Annotated[str, Field(description="User identifier")]) -> str:
        return await _therapy_start(user_id)

    @mcp.tool(description="Set current emotion using the wheel taxonomy")
    async def therapy_feel(
        emotion: Annotated[str, Field(description="Emotion term (primary/variant/blend)")],
        user_id: Annotated[str, Field(description="User identifier")],
    ) -> str:
        return await _therapy_feel(emotion, user_id)

    @mcp.tool(description="Free-form ask; analyze text and suggest next steps")
    async def therapy_ask(
        message: Annotated[str, Field(description="User message")],
        user_id: Annotated[str, Field(description="User identifier")],
    ) -> str:
        return await _therapy_ask(message, user_id)

    @mcp.tool(description="Show the Wheel of Emotions guide")
    async def therapy_wheel(user_id: Annotated[str, Field(description="User identifier")]) -> str:
        return await _therapy_wheel(user_id)

    @mcp.tool(description="Ask diagnostic questions based on current emotion")
    async def therapy_why(user_id: Annotated[str, Field(description="User identifier")]) -> str:
        return await _therapy_why(user_id)

    @mcp.tool(description="Suggest remedies for the current emotion")
    async def therapy_remedy(user_id: Annotated[str, Field(description="User identifier")]) -> str:
        return await _therapy_remedy(user_id)

    @mcp.tool(description="Guided breathing exercise")
    async def therapy_breathe(user_id: Annotated[str, Field(description="User identifier")]) -> str:
        return await _therapy_breathe(user_id)

    @mcp.tool(description="Emergency protocol")
    async def therapy_sos(user_id: Annotated[str, Field(description="User identifier")]) -> str:
        return await _therapy_sos(user_id)

    @mcp.tool(description="End session and clear data")
    async def therapy_exit(user_id: Annotated[str, Field(description="User identifier")]) -> str:
        return await _therapy_exit(user_id)

    @mcp.tool(description="Show current state and available commands")
    async def therapy_status(user_id: Annotated[str, Field(description="User identifier")]) -> str:
        return await _therapy_status(user_id)

    tools_map = {
        "therapy_start": _therapy_start,
        "therapy_feel": _therapy_feel,
        "therapy_ask": _therapy_ask,
        "therapy_wheel": _therapy_wheel,
        "therapy_why": _therapy_why,
        "therapy_remedy": _therapy_remedy,
        "therapy_breathe": _therapy_breathe,
        "therapy_sos": _therapy_sos,
        "therapy_exit": _therapy_exit,
        "therapy_status": _therapy_status,
    }

    # Attach for tests/introspection and return
    setattr(mcp, "_therapy_tools", tools_map)
    return tools_map
