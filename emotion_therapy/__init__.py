# Emotion Therapy package initialization
# Guard optional imports so submodule imports (e.g., emotion_therapy.validator)
# don't fail while other modules are WIP.
try:
    from .session_store import (
        RedisSessionManager,
        TherapySession,
        get_redis_session_manager,
    )
except Exception:  # pragma: no cover - optional during early scaffolding
    RedisSessionManager = None  # type: ignore
    TherapySession = None  # type: ignore

    def get_redis_session_manager():  # type: ignore
        raise RuntimeError("Redis session manager unavailable")

from .models import CommandType, SessionState, TherapySession as ModelTherapySession, ValidationResult
from .validator import get_available_commands, validate_command, parse_command
from .llm_stub import analyze_text, probe_questions, suggest_remedies
# Conversation layer (optional LangChain)
try:
    from .conversation import (
        ConversationManager,
        create_conversation_manager,
        LLMProvider,
    )
except Exception:  # pragma: no cover
    ConversationManager = None  # type: ignore
    create_conversation_manager = None  # type: ignore
    LLMProvider = None  # type: ignore

__all__ = [
    "RedisSessionManager",
    "TherapySession",
    "get_redis_session_manager",
    # models
    "CommandType",
    "SessionState",
    "ModelTherapySession",
    "ValidationResult",
    # validator
    "validate_command",
    "get_available_commands",
    "parse_command",
    # llm stub
    "analyze_text",
    "probe_questions",
    "suggest_remedies",
    # conversation
    "ConversationManager",
    "create_conversation_manager",
    "LLMProvider",
]
