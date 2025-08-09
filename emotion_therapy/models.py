from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SessionState(str, Enum):
    NO_SESSION = "NO_SESSION"
    SESSION_STARTED = "SESSION_STARTED"
    EMOTION_IDENTIFIED = "EMOTION_IDENTIFIED"
    DIAGNOSTIC_COMPLETE = "DIAGNOSTIC_COMPLETE"
    REMEDY_PROVIDED = "REMEDY_PROVIDED"
    EMERGENCY = "EMERGENCY"


class CommandType(str, Enum):
    SESSION_MANAGEMENT = "SESSION_MANAGEMENT"
    EMOTION_IDENTIFICATION = "EMOTION_IDENTIFICATION"
    DIAGNOSTIC = "DIAGNOSTIC"
    REMEDY = "REMEDY"
    SELF_HELP = "SELF_HELP"
    TRACKING = "TRACKING"
    EMERGENCY = "EMERGENCY"
    UNKNOWN = "UNKNOWN"


class TherapySession(BaseModel):
    user_id: str
    state: SessionState = SessionState.NO_SESSION
    current_emotion: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ValidationResult(BaseModel):
    is_valid: bool
    command_type: CommandType
    current_state: SessionState
    next_state: Optional[SessionState] = None
    error_message: Optional[str] = None
    suggested_commands: list[str] = Field(default_factory=list)
    llm_context: dict[str, Any] = Field(default_factory=dict)
