from __future__ import annotations

"""
Conversation management layer for Emotion Therapy.

- Enforces session-aware LLM interactions
- Maintains structured conversation history on the session model
- Allows pluggable LLM providers (stub or LangChain-backed)
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
import time

try:
    # Optional: use existing stub helpers when available
    from .llm_stub import analyze_text as _stub_analyze, probe_questions as _stub_probe, suggest_remedies as _stub_remedies
except Exception:  # pragma: no cover
    _stub_analyze = None
    _stub_probe = None
    _stub_remedies = None

try:
    # Optional: LangChain backend (modern imports)
    from langchain_openai import ChatOpenAI  # type: ignore
    from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore
    LANGCHAIN_AVAILABLE = True
except Exception:  # pragma: no cover
    LANGCHAIN_AVAILABLE = False

from .models import SessionState


@dataclass
class ConversationTurn:
    timestamp: float
    user_input: str
    command: str
    parameter: Optional[str]
    system_response: str
    session_state: SessionState
    emotion_context: Optional[Dict[str, Any]] = None


@dataclass
class ConversationContext:
    user_id: str
    session_state: SessionState
    current_emotion: Optional[str]
    emotion_details: Optional[Dict[str, Any]]
    recent_turns: List[ConversationTurn]
    session_goal: Optional[str] = None


@runtime_checkable
class LLMProvider(Protocol):
    async def analyze_emotion(self, text: str, context: ConversationContext) -> Dict[str, Any]:
        ...

    async def generate_questions(self, emotion: str, context: ConversationContext) -> List[str]:
        ...

    async def suggest_remedies(self, emotion: str, context: ConversationContext) -> List[str]:
        ...

    async def continue_conversation(self, user_input: str, context: ConversationContext) -> str:
        ...


class StubLLMProvider:
    """Wraps the repository's llm_stub with context-aware defaults.

    Safe to use even if llm_stub is incomplete; falls back to deterministic strings.
    """

    async def analyze_emotion(self, text: str, context: ConversationContext) -> Dict[str, Any]:
        if _stub_analyze:
            return _stub_analyze(text)
        return {"emotion": context.current_emotion or "UNKNOWN", "confidence": 0.0, "notes": "stub"}

    async def generate_questions(self, emotion: str, context: ConversationContext) -> List[str]:
        if _stub_probe:
            return _stub_probe(emotion)
        return [f"What makes the user feel {emotion.lower()}?", "When did this start?"]

    async def suggest_remedies(self, emotion: str, context: ConversationContext) -> List[str]:
        topics = []
        for t in context.recent_turns[-3:]:
            if "work" in t.user_input.lower():
                topics.append("work")
            if "family" in t.user_input.lower():
                topics.append("family")
        ctx = {"topic": " ".join(topics)} if topics else None
        if _stub_remedies:
            return _stub_remedies(emotion, ctx)
        return [f"Try a short walk and mindful breathing to ease {emotion.lower()}."]

    async def continue_conversation(self, user_input: str, context: ConversationContext) -> str:
        # Keep deterministic and dependency-light with clear attribution
        analysis = await self.analyze_emotion(user_input, context)
        emo = analysis.get("emotion") or context.current_emotion or "something"
        return f"System detected: user is experiencing {str(emo).lower()}."


class LangChainLLMProvider(StubLLMProvider):  # type: ignore[misc]
    """LangChain-based provider (optional).

    Falls back to StubLLMProvider behavior if LangChain isn't available.
    """

    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.7):
        if not LANGCHAIN_AVAILABLE:  # pragma: no cover
            raise ImportError("LangChain is not installed. Install extras 'langchain'.")
        # ChatOpenAI uses OPENAI_API_KEY from environment.
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)

    async def continue_conversation(self, user_input: str, context: ConversationContext) -> str:
        system = self._build_system_prompt(context)
        messages = [SystemMessage(content=system)]
        for turn in context.recent_turns[-5:]:
            if turn.user_input:
                messages.append(HumanMessage(content=f"User said: {turn.user_input}"))
            if turn.system_response:
                messages.append(SystemMessage(content=f"System responded: {turn.system_response}"))
        messages.append(HumanMessage(content=f"User said: {user_input}"))
        # Modern LangChain async API
        try:
            result = await self.llm.ainvoke(messages)  # returns AIMessage
            content = getattr(result, "content", str(result))
            return f"LLM response: {content}"
        except Exception:
            # Fallback to stub behavior if invocation fails
            return await super().continue_conversation(user_input, context)

    def _build_system_prompt(self, context: ConversationContext) -> str:
        return (
            "You are a compassionate emotion therapy assistant. "
            f"State: {context.session_state.value}. "
            f"Emotion: {context.current_emotion or 'unknown'}. "
            f"Goal: {context.session_goal or 'support'}. "
            "Respond with clear attribution (User said / System responded / LLM response)."
        )


class ConversationManager:
    def __init__(self, session_manager: Any, llm_provider: Optional[LLMProvider] = None, max_turns_in_context: int = 10):
        self.session_manager = session_manager
        self.llm_provider: LLMProvider = llm_provider or StubLLMProvider()
        self.max_turns = max_turns_in_context

    async def start_conversation(self, user_id: str) -> str:
        session = self.session_manager.get_session(user_id)
        if session.state != SessionState.SESSION_STARTED:
            return "No active session. Please start a session first."
        # Reset history for a new conversation window
        session.history = []
        self.session_manager.save_session(session)
        return "Conversation started. How are you feeling today?"

    async def add_turn(
        self,
        user_id: str,
        user_input: str,
        command: str,
        parameter: Optional[str],
        system_response: str,
        emotion_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        session = self.session_manager.get_session(user_id)
        turn = ConversationTurn(
            timestamp=time.time(),
            user_input=user_input,
            command=command,
            parameter=parameter,
            system_response=system_response,
            session_state=session.state,
            emotion_context=emotion_context,
        )
        # append and trim
        session.history.append({
            "timestamp": turn.timestamp,
            "user_input": turn.user_input,
            "command": turn.command,
            "parameter": turn.parameter,
            "system_response": turn.system_response,
            "session_state": turn.session_state.value,
            "emotion_context": turn.emotion_context,
        })
        if len(session.history) > self.max_turns:
            session.history = session.history[-self.max_turns :]
        self.session_manager.save_session(session)

    async def end_conversation(self, user_id: str) -> None:
        session = self.session_manager.get_session(user_id)
        session.history = []
        self.session_manager.save_session(session)

    async def get_conversation_context(self, user_id: str) -> ConversationContext:
        session = self.session_manager.get_session(user_id)
        turns: List[ConversationTurn] = []
        for d in session.history or []:
            try:
                turns.append(
                    ConversationTurn(
                        timestamp=float(d.get("timestamp", time.time())),
                        user_input=str(d.get("user_input", "")),
                        command=str(d.get("command", "")),
                        parameter=d.get("parameter"),
                        system_response=str(d.get("system_response", "")),
                        session_state=SessionState(str(d.get("session_state", SessionState.NO_SESSION.value))),
                        emotion_context=d.get("emotion_context"),
                    )
                )
            except Exception:  # pragma: no cover
                continue
        return ConversationContext(
            user_id=user_id,
            session_state=session.state,
            current_emotion=getattr(session, "current_emotion", None),
            emotion_details=(session.context or {}).get("emotion_details") if getattr(session, "context", None) else None,
            recent_turns=turns,
            session_goal=self._infer_session_goal(session.state, turns),
        )

    def _infer_session_goal(self, state: SessionState, turns: List[ConversationTurn]) -> Optional[str]:
        if state == SessionState.SESSION_STARTED:
            return "emotion_identification"
        if state == SessionState.EMOTION_IDENTIFIED:
            return "understanding_emotions"
        if state == SessionState.DIAGNOSTIC_COMPLETE:
            return "coping_strategies"
        if state == SessionState.REMEDY_PROVIDED:
            return "implementation_support"
        return None

    async def process_with_llm(self, user_id: str, command: str, parameter: Optional[str], user_input: str) -> tuple[str, Dict[str, Any]]:
        context = await self.get_conversation_context(user_id)
        llm_result: Dict[str, Any] = {}
        if command == "ask":
            response = await self.llm_provider.continue_conversation(user_input, context)
            try:
                llm_result = await self.llm_provider.analyze_emotion(user_input, context)
            except Exception:
                llm_result = {}
        elif command == "feel":
            try:
                llm_result = await self.llm_provider.analyze_emotion(parameter or "", context)
            except Exception:
                llm_result = {"emotion": parameter or "UNKNOWN"}
            response = f"I understand you're feeling {(llm_result.get('emotion') or 'something').lower()}."
        elif command == "why":
            emo = context.current_emotion or "neutral"
            qs = await self.llm_provider.generate_questions(emo, context)
            llm_result = {"questions": qs}
            bullets = "\n".join(f"• {q}" for q in qs)
            response = f"Let me ask you some questions to understand better:\n{bullets}"
        elif command == "remedy":
            emo = context.current_emotion or "neutral"
            rems = await self.llm_provider.suggest_remedies(emo, context)
            llm_result = {"remedies": rems}
            bullets = "\n".join(f"• {r}" for r in rems)
            response = f"Here are some strategies that might help:\n{bullets}"
        else:
            response = "I'm here to help. How are you feeling?"
        return response, llm_result


def create_conversation_manager(session_manager: Any, use_langchain: bool = False, model_name: str = "gpt-3.5-turbo") -> ConversationManager:
    if use_langchain and LANGCHAIN_AVAILABLE:  # pragma: no cover - exercised only when LC installed
        # Try to instantiate LC provider; fall back safely if env (e.g., OPENAI_API_KEY) is missing
        try:
            provider = LangChainLLMProvider(model_name=model_name)
        except Exception:
            provider = StubLLMProvider()
    else:
        provider = StubLLMProvider()
    return ConversationManager(session_manager, provider)
