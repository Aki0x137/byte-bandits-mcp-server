from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .models import SessionState


def start_response() -> Dict[str, Any]:
    return {
        "type": "session_start",
        "message": "System: Session started. LLM ready to process user emotions.",
        "instructions": "Try: /feel <emotion> (e.g., 'anger', 'joy') or /wheel for guidance.",
        "available_commands": ["/feel", "/wheel", "/ask", "/why", "/remedy", "/status", "/exit"],
        "status": "ready",
    }


def feel_response(primary: Optional[str], variant: Optional[str], intensity: Optional[str], blend: Optional[str]) -> Dict[str, Any]:
    parts: List[str] = []
    if variant:
        parts.append(str(variant))
    elif primary:
        parts.append(str(primary))
    if intensity:
        parts.append(f"[{str(intensity).lower()}]")
    label = " ".join(parts) if parts else "unknown"
    if blend:
        label += f" (blend: {blend})"

    return {
        "type": "emotion_identification",
        "emotion": {
            "primary": primary,
            "variant": variant,
            "intensity": intensity,
            "blend": blend,
        },
        "display_label": label,
        "message": f"Emotion identified: {label}",
        "next_steps": ["/why to explore", "/remedy for coping"],
        "available_commands": ["/why", "/remedy", "/status"],
    }


def ask_response(message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    emotion = analysis.get("emotion")
    variant = analysis.get("variant")
    confidence = float(analysis.get("confidence", 0.0))
    notes = analysis.get("notes", "")
    return {
        "type": "conversation",
        "user_input": message,
        "analysis": {
            "emotion": emotion,
            "variant": variant,
            "confidence": confidence,
            "notes": notes,
        },
        "attribution": {
            "user_said": message,
            "system_detected": f"{emotion} ({variant})" if emotion else None,
            "confidence": confidence,
        },
        "message": f"User said: {message}",
        "interpretation": f"System detected: {emotion} ({variant})" if emotion else "System detected: unknown",
    }


def wheel_response(wheel_text: str, include_image: bool = False) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "type": "emotion_wheel",
        "title": "Plutchik's Wheel of Emotions",
        "content": wheel_text,
        "message": "LLM response: Emotion wheel reference provided",
        "usage_instruction": "System: Use /feel <term> from this guide to set your emotion",
        "available_commands": ["/feel"],
    }
    if include_image:
        data["image_included"] = True
        data["image_description"] = "Visual representation of Plutchik's Wheel of Emotions"
    return data


def why_response(primary: str, questions: Iterable[str]) -> Dict[str, Any]:
    question_list = list(questions)
    return {
        "type": "diagnostic_questions",
        "emotion": primary,
        "questions": question_list,
        "message": f"Exploring {primary}",
        "instruction": "LLM generated questions for analysis:",
        "available_commands": ["/remedy", "/ask"],
    }


def remedy_response(primary: str, remedies: Iterable[str]) -> Dict[str, Any]:
    remedy_list = list(remedies)
    return {
        "type": "coping_strategies",
        "emotion": primary,
        "remedies": remedy_list,
        "message": f"Remedies for {primary}",
        "instruction": "System recommends these approaches:",
        "available_commands": ["/ask", "/checkin"],
    }


def breathe_response() -> Dict[str, Any]:
    return {
        "type": "breathing_exercise",
        "technique": "box_breathing",
        "instructions": {
            "pattern": "4-4-4-4",
            "steps": ["inhale 4", "hold 4", "exhale 4", "hold 4"],
            "cycles": 4,
        },
        "message": "System guidance: Box breathing exercise",
    }


def sos_response() -> Dict[str, Any]:
    return {
        "type": "emergency",
        "priority": "high",
        "message": "System alert: Emergency protocol activated",
        "warning": "If in immediate danger, contact local emergency services",
        "resources": {"us_crisis_line": "988", "text_option": "Text 988"},
        "available_commands": ["/exit"],
    }


def exit_response() -> Dict[str, Any]:
    return {
        "type": "session_end",
        "message": "System: Session ended. LLM available for future sessions.",
        "status": "completed",
    }


def status_response(state: SessionState, available: List[str]) -> Dict[str, Any]:
    return {
        "type": "status",
        "session_state": state.value,
        "available_commands": available,
        "formatted_commands": [f"/{c}" for c in available],
        "message": f"System status: {state.value}",
    }
