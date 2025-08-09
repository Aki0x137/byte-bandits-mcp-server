from __future__ import annotations

import os
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
from .conversation import create_conversation_manager
from .llm_manager import create_enhanced_manager_from_env

# Optional: auto-run diagnostic after /feel if enabled via env var
AUTO_WHY = os.environ.get("THERAPY_AUTO_WHY", "0").lower() in ("1", "true", "yes")
USE_ENHANCED_MANAGER = os.environ.get("THERAPY_USE_ENHANCED_MANAGER", "1").lower() in ("1", "true", "yes")


def register_tools(mcp: FastMCP) -> dict[str, object]:
    mgr = get_redis_session_manager()
    
    # Use enhanced manager if enabled, otherwise fall back to basic conversation manager
    if USE_ENHANCED_MANAGER:
        unified_mgr = create_enhanced_manager_from_env(mgr)
        conv_mgr = unified_mgr.conv_manager  # Access the underlying conversation manager
    else:
        use_langchain = os.environ.get("THERAPY_USE_LANGCHAIN", "0").lower() in ("1", "true", "yes")
        conv_mgr = create_conversation_manager(mgr, use_langchain=use_langchain)
        unified_mgr = None

    # Implementation functions (returned for tests)
    async def _therapy_start(user_id: str) -> str:
        res = validate_command("/start", None, SessionState.NO_SESSION)
        if not res.is_valid:
            return "Unable to start session."
        sess = mgr.get_session(user_id)
        sess.state = res.next_state or SessionState.SESSION_STARTED
        sess.current_emotion = None
        sess.context = {}
        sess.history = []
        mgr.save_session(sess)
        # Initialize conversation window
        await conv_mgr.start_conversation(user_id)
        return start_response()

    async def _therapy_feel(emotion: str, user_id: str) -> str:
        sess = mgr.get_session(user_id)
        
        # Use enhanced manager if available for full validation and safety checks
        if unified_mgr:
            response, validation_result, llm_context = await unified_mgr.process_user_input_with_validation(
                user_id, f"/feel {emotion}", sess.state
            )
            
            # Extract emotion details for response formatting
            details = llm_context.get("emotion_details") or {}
            primary = details.get("primary")
            variant = details.get("variant_label")  
            intensity = details.get("intensity")
            blend = details.get("blend_name")
            
            msg = feel_response(primary, variant, intensity, blend)
            
            if AUTO_WHY:
                why_qs = await _therapy_why(user_id)
                return f"{msg}\n\n{why_qs}"
            return msg
        else:
            # Fallback to basic validation and processing
            res = validate_command("/feel", emotion, sess.state)
            if not res.is_valid:
                return res.error_message or "Invalid input"
            # update session emotion context
            sess.state = res.next_state or sess.state
            if res.llm_context:
                sess.current_emotion = res.llm_context.get("current_emotion_primary")
                sess.context.update(res.llm_context)
            mgr.save_session(sess)

            details = (res.llm_context or {}).get("emotion_details") or {}
            primary = details.get("primary")
            variant = details.get("variant_label")
            intensity = details.get("intensity")
            blend = details.get("blend_name")

            # optional auto questions
            msg = feel_response(primary, variant, intensity, blend)
            await conv_mgr.add_turn(user_id, emotion, "feel", emotion, msg, details)

            if AUTO_WHY:
                why_qs = await _therapy_why(user_id)
                return f"{msg}\n\n{why_qs}"
            return msg

    async def _therapy_ask(message: str, user_id: str) -> str:
        sess = mgr.get_session(user_id)
        
        # Use enhanced manager if available for full validation and safety checks
        if unified_mgr:
            response, validation_result, llm_context = await unified_mgr.process_user_input_with_validation(
                user_id, message, sess.state
            )
            return ask_response(message, llm_context) if llm_context else response
        else:
            # Fallback to basic validation and conversation manager
            res = validate_command("/ask", message, sess.state)
            if not res.is_valid:
                return res.error_message or "Please start a session with /start"
            reply, analysis = await conv_mgr.process_with_llm(user_id, "ask", message, message)
            await conv_mgr.add_turn(user_id, message, "ask", message, reply, analysis)
            return ask_response(message, analysis) if analysis else reply

    async def _therapy_wheel(user_id: str) -> str:
        txt = get_wheel_text()
        return wheel_response(txt)

    async def _therapy_why(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/why", None, sess.state)
        if not res.is_valid:
            return res.error_message or "Diagnostic not available now"
        ctx = await conv_mgr.get_conversation_context(user_id)
        emo = ctx.current_emotion or "neutral"
        reply, payload = await conv_mgr.process_with_llm(user_id, "why", emo, emo)
        await conv_mgr.add_turn(user_id, "", "why", emo, reply, payload)
        return why_response(emo, payload.get("questions", []))

    async def _therapy_remedy(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/remedy", None, sess.state)
        if not res.is_valid:
            return res.error_message or "Remedy not available now"
        ctx = await conv_mgr.get_conversation_context(user_id)
        emo = ctx.current_emotion or "neutral"
        reply, payload = await conv_mgr.process_with_llm(user_id, "remedy", emo, emo)
        await conv_mgr.add_turn(user_id, "", "remedy", emo, reply, payload)
        return remedy_response(emo, payload.get("remedies", []))

    async def _therapy_breathe(user_id: str) -> str:
        return breathe_response()

    async def _therapy_sos(user_id: str) -> str:
        return sos_response()

    async def _therapy_exit(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        res = validate_command("/exit", None, sess.state)
        if not res.is_valid:
            return res.error_message or "Unable to exit"
        await conv_mgr.end_conversation(user_id)
        sess.state = SessionState.NO_SESSION
        sess.current_emotion = None
        sess.context = {}
        sess.history = []
        mgr.save_session(sess)
        return exit_response()

    async def _therapy_status(user_id: str) -> str:
        sess = mgr.get_session(user_id)
        available = get_available_commands(sess.state)
        return status_response(sess.state, available)

    # MCP tool registration wrappers
    @mcp.tool(name="therapy_start")
    async def therapy_start(user_id: Annotated[str, Field(description="User ID")]) -> str:  # type: ignore
        return await _therapy_start(user_id)

    @mcp.tool(name="therapy_feel")
    async def therapy_feel(emotion: Annotated[str, Field(description="Emotion or free text")], user_id: Annotated[str, Field(description="User ID")]) -> str:  # type: ignore
        return await _therapy_feel(emotion, user_id)

    @mcp.tool(name="therapy_ask")
    async def therapy_ask(message: Annotated[str, Field(description="User message")], user_id: Annotated[str, Field(description="User ID")]) -> str:  # type: ignore
        return await _therapy_ask(message, user_id)

    @mcp.tool(name="therapy_wheel")
    async def therapy_wheel(user_id: Annotated[str, Field(description="User ID")]) -> str:  # type: ignore
        return await _therapy_wheel(user_id)

    @mcp.tool(name="therapy_why")
    async def therapy_why(user_id: Annotated[str, Field(description="User ID")]) -> str:  # type: ignore
        return await _therapy_why(user_id)

    @mcp.tool(name="therapy_remedy")
    async def therapy_remedy(user_id: Annotated[str, Field(description="User ID")]) -> str:  # type: ignore
        return await _therapy_remedy(user_id)

    @mcp.tool(name="therapy_breathe")
    async def therapy_breathe(user_id: Annotated[str, Field(description="User ID")]) -> str:  # type: ignore
        return await _therapy_breathe(user_id)

    @mcp.tool(name="therapy_sos")
    async def therapy_sos(user_id: Annotated[str, Field(description="User ID")]) -> str:  # type: ignore
        return await _therapy_sos(user_id)

    @mcp.tool(name="therapy_exit")
    async def therapy_exit(user_id: Annotated[str, Field(description="User ID")]) -> str:  # type: ignore
        return await _therapy_exit(user_id)

    @mcp.tool(name="therapy_status")
    async def therapy_status(user_id: Annotated[str, Field(description="User ID")]) -> str:  # type: ignore
        return await _therapy_status(user_id)

    return {
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
