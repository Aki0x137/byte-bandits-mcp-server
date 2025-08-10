from __future__ import annotations

import os
import json
import base64
import textwrap
from typing import Annotated, Optional, List, Union

from fastmcp import FastMCP
from pydantic import Field
from mcp.types import TextContent, ImageContent

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

def _make_json_content(payload: dict) -> TextContent:
    return TextContent(type="text", mimeType="application/json", text=json.dumps(payload, indent=2))


def _load_wheel_image() -> Optional[str]:
    """Load the emotion wheel image as base64 string if available."""
    candidates = [
        os.path.join("docs", "assets", "wheel_of_emotion.jpg"),
        "wheel_of_emotion.jpg",
        os.path.join(os.path.dirname(__file__), "wheel_of_emotion.jpg"),
    ]
    for path in candidates:
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            continue
    return None


def _wheel_guide_text() -> str:
    """Improved user-facing Wheel of Emotion guide text used by the wheel tool.

    Note: This does not modify the canonical wheel.get_wheel_text(), which is still
    used by unit tests. Only the tool's JSON payload uses this richer text.
    """
    return textwrap.dedent(
        """
        1. Structure

            Petals: Each petal represents a primary emotion (Plutchik identified 8 core ones):

                Joy

                Trust

                Fear

                Surprise

                Sadness

                Disgust

                Anger

                Anticipation

            Color gradient: Moving inward increases intensity; moving outward decreases intensity.

                Inner = strongest form (e.g., Rage for anger)

                Middle = normal form (e.g., Anger)

                Outer = mild form (e.g., Annoyance)

            Between petals: Shows secondary emotions formed by mixing two adjacent primary emotions (e.g., Joy + Trust = Love).

        2. Traversing Layers

        You can move through the wheel in three main ways for emotional understanding:
        A. Radial Movement (Intensity changes)

        Move inward or outward along a petal to track how intense the feeling is:

            Example:
            Annoyance → Anger → Rage (increasing intensity)
            Rage → Anger → Annoyance (decreasing intensity)

        B. Circular Movement (Emotion relationships)

        Move around the wheel to see how one primary emotion relates to another:

            Clockwise or counterclockwise, you transition into different core emotions.

            Example:
            Anger → Anticipation → Joy → Trust...

        C. Diagonal Movement (Blending emotions)

        Combine neighboring emotions to understand mixed feelings:

            Example:
            Joy + Trust = Love
            Fear + Surprise = Awe
            Disgust + Anger = Contempt

        3. Practical Use

            Self-reflection: Start at your current feeling, then check inward (is it more intense?) or outward (is it less intense?).

            Conflict resolution: Identify underlying emotions by checking blends (e.g., “Why do I feel contempt? Is it anger + disgust?”).

            Empathy building: Helps you map what others might feel and at what intensity.

        If you want, I can give you a step-by-step “emotional traversal method” that lets you start from a vague feeling and pinpoint its precise position on this wheel. That’s especially useful for journaling or therapy work.
        """
    ).strip()


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
    async def _therapy_start(user_id: str) -> TextContent:
        res = validate_command("/start", None, SessionState.NO_SESSION)
        if not res.is_valid:
            data = {"type": "error", "message": res.error_message or "Unable to start session."}
            return TextContent(type="text", mimeType="application/json", text=json.dumps(data))
        sess = mgr.get_session(user_id)
        sess.state = res.next_state or SessionState.SESSION_STARTED
        sess.current_emotion = None
        sess.context = {}
        sess.history = []
        mgr.save_session(sess)
        # Initialize conversation window
        await conv_mgr.start_conversation(user_id)
        data = start_response()
        return TextContent(type="text", mimeType="application/json", text=json.dumps(data))

    async def _therapy_feel(emotion: str, user_id: str) -> TextContent:
        sess = mgr.get_session(user_id)
        
        # Use enhanced manager if available for full validation and safety checks
        if unified_mgr:
            response, validation_result, llm_context = await unified_mgr.process_user_input_with_validation(
                user_id, f"/feel {emotion}", sess.state
            )
            details = llm_context.get("emotion_details") or {}
            primary = details.get("primary")
            variant = details.get("variant_label")  
            intensity = details.get("intensity")
            blend = details.get("blend_name")
            data = feel_response(primary, variant, intensity, blend)
        else:
            # Fallback to basic validation and processing
            res = validate_command("/feel", emotion, sess.state)
            if not res.is_valid:
                data = {"type": "error", "message": res.error_message or "Invalid input"}
                return TextContent(type="text", mimeType="application/json", text=json.dumps(data))
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

            data = feel_response(primary, variant, intensity, blend)
            await conv_mgr.add_turn(user_id, emotion, "feel", emotion, data.get("message", ""), details)

        if AUTO_WHY:
            # Append diagnostic questions to the JSON payload
            ctx = await conv_mgr.get_conversation_context(user_id)
            emo = (ctx.current_emotion or primary or "neutral")
            qs_data = await _therapy_why(user_id)
            try:
                qs_json = json.loads(qs_data.text)
                data["auto_why"] = qs_json
            except Exception:
                pass
        return TextContent(type="text", mimeType="application/json", text=json.dumps(data))

    async def _therapy_ask(message: str, user_id: str) -> TextContent:
        sess = mgr.get_session(user_id)
        
        if unified_mgr:
            response, validation_result, llm_context = await unified_mgr.process_user_input_with_validation(
                user_id, message, sess.state
            )
            data = ask_response(message, llm_context or {}) if llm_context else {"type": "message", "message": response}
        else:
            res = validate_command("/ask", message, sess.state)
            if not res.is_valid:
                data = {"type": "error", "message": res.error_message or "Please start a session with /start"}
                return TextContent(type="text", mimeType="application/json", text=json.dumps(data))
            reply, analysis = await conv_mgr.process_with_llm(user_id, "ask", message, message)
            await conv_mgr.add_turn(user_id, message, "ask", message, reply, analysis)
            data = ask_response(message, analysis) if analysis else {"type": "message", "message": reply}
        return TextContent(type="text", mimeType="application/json", text=json.dumps(data))

    async def _therapy_wheel(user_id: str, include_image: bool = True) -> Union[TextContent, List[Union[TextContent, ImageContent]]]:
        # Use the improved, user-friendly guide text for the wheel tool's JSON payload
        txt = _wheel_guide_text()
        data = wheel_response(txt, include_image=include_image)
        json_part = TextContent(type="text", mimeType="application/json", text=json.dumps(data))
        if include_image:
            b64 = _load_wheel_image()
            if b64:
                img = ImageContent(type="image", mimeType="image/jpeg", data=b64)
                return [json_part, img]
        return json_part

    async def _therapy_why(user_id: str) -> TextContent:
        sess = mgr.get_session(user_id)
        res = validate_command("/why", None, sess.state)
        if not res.is_valid:
            data = {"type": "error", "message": res.error_message or "Diagnostic not available now"}
            return TextContent(type="text", mimeType="application/json", text=json.dumps(data))
        ctx = await conv_mgr.get_conversation_context(user_id)
        emo = ctx.current_emotion or "neutral"
        reply, payload = await conv_mgr.process_with_llm(user_id, "why", emo, emo)
        await conv_mgr.add_turn(user_id, "", "why", emo, reply, payload)
        data = why_response(emo, payload.get("questions", []))
        return TextContent(type="text", mimeType="application/json", text=json.dumps(data))

    async def _therapy_remedy(user_id: str) -> TextContent:
        sess = mgr.get_session(user_id)
        res = validate_command("/remedy", None, sess.state)
        if not res.is_valid:
            data = {"type": "error", "message": res.error_message or "Remedy not available now"}
            return TextContent(type="text", mimeType="application/json", text=json.dumps(data))
        ctx = await conv_mgr.get_conversation_context(user_id)
        emo = ctx.current_emotion or "neutral"
        reply, payload = await conv_mgr.process_with_llm(user_id, "remedy", emo, emo)
        await conv_mgr.add_turn(user_id, "", "remedy", emo, reply, payload)
        data = remedy_response(emo, payload.get("remedies", []))
        return TextContent(type="text", mimeType="application/json", text=json.dumps(data))

    async def _therapy_breathe(user_id: str) -> TextContent:
        data = breathe_response()
        return TextContent(type="text", mimeType="application/json", text=json.dumps(data))

    async def _therapy_sos(user_id: str) -> TextContent:
        data = sos_response()
        return TextContent(type="text", mimeType="application/json", text=json.dumps(data))

    async def _therapy_exit(user_id: str) -> TextContent:
        sess = mgr.get_session(user_id)
        res = validate_command("/exit", None, sess.state)
        if not res.is_valid:
            data = {"type": "error", "message": res.error_message or "Unable to exit"}
            return TextContent(type="text", mimeType="application/json", text=json.dumps(data))
        await conv_mgr.end_conversation(user_id)
        sess.state = SessionState.NO_SESSION
        sess.current_emotion = None
        sess.context = {}
        sess.history = []
        mgr.save_session(sess)
        data = exit_response()
        return TextContent(type="text", mimeType="application/json", text=json.dumps(data))

    async def _therapy_status(user_id: str) -> TextContent:
        sess = mgr.get_session(user_id)
        available = get_available_commands(sess.state)
        data = status_response(sess.state, available)
        return TextContent(type="text", mimeType="application/json", text=json.dumps(data))

    # MCP tool registration wrappers
    @mcp.tool(name="therapy_start")
    async def therapy_start(user_id: Annotated[str, Field(description="User ID")]) -> TextContent:  # type: ignore
        return await _therapy_start(user_id)

    @mcp.tool(name="therapy_feel")
    async def therapy_feel(emotion: Annotated[str, Field(description="Emotion or free text")], user_id: Annotated[str, Field(description="User ID")]) -> TextContent:  # type: ignore
        return await _therapy_feel(emotion, user_id)

    @mcp.tool(name="therapy_ask")
    async def therapy_ask(message: Annotated[str, Field(description="User message")], user_id: Annotated[str, Field(description="User ID")]) -> TextContent:  # type: ignore
        return await _therapy_ask(message, user_id)

    @mcp.tool(name="therapy_wheel")
    async def therapy_wheel(user_id: Annotated[str, Field(description="User ID")], include_image: Annotated[bool, Field(description="Include wheel image")] = True) -> Union[TextContent, List[Union[TextContent, ImageContent]]]:  # type: ignore
        return await _therapy_wheel(user_id, include_image)

    @mcp.tool(name="therapy_why")
    async def therapy_why(user_id: Annotated[str, Field(description="User ID")]) -> TextContent:  # type: ignore
        return await _therapy_why(user_id)

    @mcp.tool(name="therapy_remedy")
    async def therapy_remedy(user_id: Annotated[str, Field(description="User ID")]) -> TextContent:  # type: ignore
        return await _therapy_remedy(user_id)

    @mcp.tool(name="therapy_breathe")
    async def therapy_breathe(user_id: Annotated[str, Field(description="User ID")]) -> TextContent:  # type: ignore
        return await _therapy_breathe(user_id)

    @mcp.tool(name="therapy_sos")
    async def therapy_sos(user_id: Annotated[str, Field(description="User ID")]) -> TextContent:  # type: ignore
        return await _therapy_sos(user_id)

    @mcp.tool(name="therapy_exit")
    async def therapy_exit(user_id: Annotated[str, Field(description="User ID")]) -> TextContent:  # type: ignore
        return await _therapy_exit(user_id)

    @mcp.tool(name="therapy_status")
    async def therapy_status(user_id: Annotated[str, Field(description="User ID")]) -> TextContent:  # type: ignore
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
