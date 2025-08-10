from __future__ import annotations

from typing import Optional

from .models import CommandType, SessionState, ValidationResult
from .wheel import normalize_text  # wheel integration

# Command groups
EMOTION_IDENTIFICATION_COMMANDS = {"ask", "wheel", "feel"}
SELF_HELP_COMMANDS = {"breathe", "quote", "journal", "audio"}
TRACKING_COMMANDS = {"checkin", "moodlog"}
SESSION_MANAGEMENT_COMMANDS = {"start", "exit"}
DIAGNOSTIC_COMMANDS = {"why"}
REMEDY_COMMANDS = {"remedy"}
EMERGENCY_COMMANDS = {"sos"}

ALL_COMMANDS = (
    EMOTION_IDENTIFICATION_COMMANDS
    | SELF_HELP_COMMANDS
    | TRACKING_COMMANDS
    | SESSION_MANAGEMENT_COMMANDS
    | DIAGNOSTIC_COMMANDS
    | REMEDY_COMMANDS
    | EMERGENCY_COMMANDS
)


def parse_command(raw: str) -> tuple[str, Optional[str]]:
    """Parse raw input into (command, parameter).

    - If input starts with '/', extract command (lowercased) and the rest as parameter (original case, trimmed).
    - If no leading '/', default to ('ask', text) if text present, else ('ask', None).
    - Handles empty/whitespace and extra spaces gracefully.
    """
    if not raw or not raw.strip():
        return ("ask", None)

    text = raw.strip()
    if not text:
        return ("ask", None)

    if text.startswith("/"):
        payload = text[1:].strip()
        if not payload:
            return ("ask", None)
        parts = payload.split(None, 1)
        cmd = parts[0].lower() if parts else "ask"
        param = parts[1].strip() if len(parts) > 1 and parts[1].strip() else None
        return (cmd, param)

    # No slash → implicit ask
    return ("ask", text)


def command_type_of(cmd: str) -> CommandType:
    if cmd in EMERGENCY_COMMANDS:
        return CommandType.EMERGENCY
    if cmd in SESSION_MANAGEMENT_COMMANDS:
        return CommandType.SESSION_MANAGEMENT
    if cmd in EMOTION_IDENTIFICATION_COMMANDS:
        return CommandType.EMOTION_IDENTIFICATION
    if cmd in DIAGNOSTIC_COMMANDS:
        return CommandType.DIAGNOSTIC
    if cmd in REMEDY_COMMANDS:
        return CommandType.REMEDY
    if cmd in SELF_HELP_COMMANDS:
        return CommandType.SELF_HELP
    if cmd in TRACKING_COMMANDS:
        return CommandType.TRACKING
    return CommandType.UNKNOWN


def _normalize_command(command: str) -> str:
    c = (command or "").strip().lower()
    return c[1:] if c.startswith("/") else c


def get_available_commands(state: SessionState) -> list[str]:
    # DAG: permissible commands by state
    if state == SessionState.NO_SESSION:
        return sorted({"start", "sos", "checkin"})
    if state == SessionState.SESSION_STARTED:
        return sorted(EMOTION_IDENTIFICATION_COMMANDS | SELF_HELP_COMMANDS | {"exit", "sos"})
    if state == SessionState.EMOTION_IDENTIFIED:
        # Allow /ask for clarification/new details per DAG guidance
        return sorted({"ask", "why", "remedy", "moodlog", "exit", "sos"} | SELF_HELP_COMMANDS)
    if state == SessionState.DIAGNOSTIC_COMPLETE:
        # Keep self-help available and permit /ask to refine/clarify
        return sorted({"ask", "remedy", "moodlog", "exit", "sos"} | SELF_HELP_COMMANDS)
    if state == SessionState.REMEDY_PROVIDED:
        return sorted({"ask", "checkin", "moodlog", "exit", "sos"} | SELF_HELP_COMMANDS)
    if state == SessionState.EMERGENCY:
        return sorted({"sos", "exit"})
    return []


def _next_state_for(command: str, current: SessionState) -> Optional[SessionState]:
    if command == "sos":
        return SessionState.EMERGENCY
    if command == "start":
        return SessionState.SESSION_STARTED
    if command == "exit":
        return SessionState.NO_SESSION
    if command == "feel":
        return SessionState.EMOTION_IDENTIFIED
    if command == "why":
        return SessionState.DIAGNOSTIC_COMPLETE
    if command == "remedy":
        return SessionState.REMEDY_PROVIDED
    if command == "ask":
        # New issue cycle after remedy; otherwise remain in current phase
        return SessionState.SESSION_STARTED if current == SessionState.REMEDY_PROVIDED else current
    if command == "checkin":
        if current in (SessionState.NO_SESSION, SessionState.REMEDY_PROVIDED):
            return SessionState.SESSION_STARTED
        return current
    return current


def validate_command(
    command: str,
    parameter: Optional[str],
    current_state: SessionState,
    context: Optional[dict] = None,
) -> ValidationResult:
    cmd = _normalize_command(command)
    ctype = command_type_of(cmd)

    # Emergency always valid
    if cmd == "sos":
        return ValidationResult(
            is_valid=True,
            command_type=ctype,
            current_state=current_state,
            next_state=SessionState.EMERGENCY,
            suggested_commands=["/exit"],
        )

    # Unknown command name
    if cmd not in ALL_COMMANDS:
        return ValidationResult(
            is_valid=False,
            command_type=CommandType.UNKNOWN,
            current_state=current_state,
            next_state=None,
            error_message=f"Unknown command: '/{cmd}'.",
            suggested_commands=[f"/{c}" for c in get_available_commands(current_state)],
        )

    allowed = set(get_available_commands(current_state))
    if cmd not in allowed:
        suggestions = [f"/{c}" for c in get_available_commands(current_state)]
        msg = f"Command '/{cmd}' not allowed in state {current_state}. Try: {', '.join(suggestions[:5])}"
        return ValidationResult(
            is_valid=False,
            command_type=ctype,
            current_state=current_state,
            next_state=None,
            error_message=msg,
            suggested_commands=suggestions,
        )

    # Optional wheel normalization for `/feel`
    llm_ctx = {}
    if cmd == "feel":
        norm = normalize_text(parameter or "")
        llm_ctx = {
            "emotion_details": {
                "primary": norm.primary.value,
                "variant_label": norm.variant_label,
                "intensity": norm.intensity.value if norm.intensity else None,
                "is_blend": norm.is_blend,
                "blend_name": norm.blend_name,
                "confidence": norm.confidence,
                "matched_terms": norm.matched_terms,
            },
            # convenience keys for session storage
            "current_emotion_primary": norm.primary.value,
            "current_emotion_variant": norm.variant_label,
            "current_emotion_blend": norm.blend_name if norm.is_blend else None,
        }

    next_state = _next_state_for(cmd, current_state)
    return ValidationResult(
        is_valid=True,
        command_type=ctype,
        current_state=current_state,
        next_state=next_state,
        suggested_commands=[f"/{c}" for c in get_available_commands(next_state or current_state)],
        llm_context=llm_ctx,
    )


def validate_command_from_raw(
    raw_input: str,
    current_state: SessionState,
    context: Optional[dict] = None,
) -> ValidationResult:
    """Convenience: parse raw input then validate."""
    cmd, param = parse_command(raw_input)
    return validate_command(cmd, param, current_state, context)
