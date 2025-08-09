from __future__ import annotations

from typing import Annotated, Optional
import os

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

# Optional: auto-run diagnostic after /feel if enabled via env var
AUTO_WHY = os.environ.get("THERAPY_AUTO_WHY", "0").lower() in ("1", "true", "yes")


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
        out = feel_response(
            details.get("primary", ""),
            details.get("variant_label"),
            details.get("intensity"),
            details.get("blend_name"),
        )
        # Optionally auto-trigger diagnostic questions
        if AUTO_WHY:
            primary = details.get("primary") or (sess.current_emotion or "").upper() or "JOY"
            qs = probe_questions(primary)
            sess.state = SessionState.DIAGNOSTIC_COMPLETE
            mgr.save_session(sess)
            mgr.add_to_history(user_id, "/why", None, qs)
            out = out + "\n\n" + why_response(primary, qs)
        return out

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

    # --- New: Self-help tools ---
    async def _therapy_quote(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/quote", None, sess.state)
        if not res.is_valid:
            return f"{res.error_message}"
        quotes = [
            "This too shall pass.",
            "Small steps every day.",
            "Feelings are real, but not final.",
        ]
        text = f"Quote: {quotes[hash(user_id) % len(quotes)]}"
        mgr.add_to_history(user_id, "/quote", None, {"text": text})
        return text

    async def _therapy_journal(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/journal", None, sess.state)
        if not res.is_valid:
            return f"{res.error_message}"
        prompts = [
            "Name one feeling right now and what triggered it.",
            "What helped a little today?",
            "If tomorrow is 10% better, what changed?",
        ]
        text = "Journal prompts:\n- " + "\n- ".join(prompts)
        mgr.add_to_history(user_id, "/journal", None, prompts)
        return text

    async def _therapy_audio(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/audio", None, sess.state)
        if not res.is_valid:
            return f"{res.error_message}"
        tracks = [
            "Search: 'box breathing 4-4-4-4'",
            "Search: '5-minute grounding audio'",
        ]
        text = "Audio suggestions:\n- " + "\n- ".join(tracks)
        mgr.add_to_history(user_id, "/audio", None, tracks)
        return text

    # --- New: Tracking & continuity ---
    async def _therapy_checkin(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/checkin", None, sess.state)
        if not res.is_valid:
            return f"{res.error_message}"
        snapshot = {
            "state": sess.state.value,
            "emotion": (sess.context.get("emotion_details") or {}).get("variant_label") or sess.current_emotion,
        }
        if res.next_state:
            sess.state = res.next_state
            mgr.save_session(sess)
        mgr.add_to_history(user_id, "/checkin", None, snapshot)
        return f"Daily check-in recorded. State={snapshot['state']}, emotion={snapshot['emotion'] or 'n/a'}"

    async def _therapy_moodlog(user_id: str, limit: int = 10) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/moodlog", None, sess.state)
        if not res.is_valid:
            return f"{res.error_message}"
        items = mgr.get_mood_history(user_id, limit=limit)
        if not items:
            return "No mood history yet."
        lines = []
        for it in items:
            cmd = it.get("command", "?")
            res_summary = it.get("result")
            if isinstance(res_summary, dict) and "text" in res_summary:
                res_summary = res_summary["text"]
            lines.append(f"- {cmd}: {str(res_summary)[:120]}")
        mgr.add_to_history(user_id, "/moodlog", None, {"count": len(items)})
        return "Recent mood history:\n" + "\n".join(lines)

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

    @mcp.tool(description="Daily mood check-in (adds entry to history)")
    async def therapy_checkin(user_id: Annotated[str, Field(description="User identifier")]) -> str:
        return await _therapy_checkin(user_id)

    @mcp.tool(description="Show recent mood history")
    async def therapy_moodlog(
        user_id: Annotated[str, Field(description="User identifier")],
        limit: Annotated[int, Field(description="Max entries to show", ge=1, le=50)] = 10,
    ) -> str:
        return await _therapy_moodlog(user_id, limit)

    @mcp.tool(description="Daily motivation quote")
    async def therapy_quote(user_id: Annotated[str, Field(description="User identifier")]) -> str:
        return await _therapy_quote(user_id)

    @mcp.tool(description="Reflection journaling prompts")
    async def therapy_journal(user_id: Annotated[str, Field(description="User identifier")]) -> str:
        return await _therapy_journal(user_id)

    @mcp.tool(description="Meditation/audio suggestions")
    async def therapy_audio(user_id: Annotated[str, Field(description="User identifier")]) -> str:
        return await _therapy_audio(user_id)

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
        "therapy_checkin": _therapy_checkin,
        "therapy_moodlog": _therapy_moodlog,
        "therapy_quote": _therapy_quote,
        "therapy_journal": _therapy_journal,
        "therapy_audio": _therapy_audio,
    }

    # Attach for tests/introspection and return
    setattr(mcp, "_therapy_tools", tools_map)
    return tools_map
