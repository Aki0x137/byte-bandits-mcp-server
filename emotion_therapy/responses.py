from __future__ import annotations

from typing import Any, Iterable, List, Optional

from .models import SessionState


def start_response() -> str:
    return (
        "Session started. Let's identify what you're feeling.\n"
        "Try: /feel <emotion> (e.g., 'anger', 'joy') or /wheel for guidance."
    )


def feel_response(primary: str, variant: Optional[str], intensity: Optional[str], blend: Optional[str]) -> str:
    parts: List[str] = []
    if variant:
        parts.append(variant)
    else:
        parts.append(primary)
    if intensity:
        parts.append(f"[{intensity.lower()}]")
    label = " ".join(parts)
    if blend:
        label += f" (blend: {blend})"
    return f"Emotion identified: {label}. You can /why to explore or /remedy for coping."


def ask_response(message: str, analysis: dict[str, Any]) -> str:
    tip = analysis.get("notes") or ""
    return (
        f"User said: {message}\n"
        f"System detected: {analysis.get('emotion')} ({analysis.get('variant')})\n"
        f"Confidence: {analysis.get('confidence'):.2f}. {tip}"
    )


def wheel_response(wheel_text: str) -> str:
    return (
        "Wheel of Emotions (summary):\n\n" + wheel_text +
        "\n\nUse /feel <term> from this guide to set your emotion."
    )


def why_response(primary: str, questions: Iterable[str]) -> str:
    qtext = "\n- ".join(["\n- "] + list(questions)) if questions else "\n(no questions)"
    return f"Exploring {primary}. Consider:{qtext}"


def remedy_response(primary: str, remedies: Iterable[str]) -> str:
    rtext = "\n- ".join(["\n- "] + list(remedies)) if remedies else "\n(no remedies)"
    return f"Remedies for {primary}:{rtext}"


def breathe_response() -> str:
    return "Try box breathing: inhale 4, hold 4, exhale 4, hold 4 — repeat 4 cycles."


def sos_response() -> str:
    return (
        "Emergency protocol activated. If you're in immediate danger, contact local emergency services.\n"
        "You can /exit to end the session."
    )


def exit_response() -> str:
    return "Session ended. You're welcome back anytime."


def status_response(state: SessionState, available: list[str]) -> str:
    cmds = " ".join(f"/{c}" for c in available)
    return f"State: {state.value}. Available: {cmds}"
