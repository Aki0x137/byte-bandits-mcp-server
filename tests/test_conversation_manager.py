from __future__ import annotations

import asyncio
from typing import Any, Dict

import pytest

from emotion_therapy.conversation import create_conversation_manager
from emotion_therapy.models import TherapySession, SessionState


class InMemorySessionManager:
    def __init__(self) -> None:
        self._store: Dict[str, TherapySession] = {}

    def get_session(self, user_id: str) -> TherapySession:
        return self._store.setdefault(user_id, TherapySession(user_id=user_id))

    def save_session(self, session: TherapySession) -> None:
        self._store[session.user_id] = session


@pytest.mark.asyncio
async def test_conversation_flow_stub_provider():
    mgr = InMemorySessionManager()
    user = "alice"
    sess = mgr.get_session(user)
    sess.state = SessionState.SESSION_STARTED
    mgr.save_session(sess)

    conv = create_conversation_manager(mgr, use_langchain=False)

    # Start conversation window
    msg = await conv.start_conversation(user)
    assert "Conversation started" in msg

    # Ask path
    reply, analysis = await conv.process_with_llm(user, "ask", "I am worried about work", "I am worried about work")
    assert isinstance(reply, str) and len(reply) > 0
    assert isinstance(analysis, dict)

    # Add a turn and confirm it's in context
    await conv.add_turn(user, "I am worried about work", "ask", "I am worried about work", reply, analysis)
    ctx = await conv.get_conversation_context(user)
    assert len(ctx.recent_turns) == 1

    # Why path (requires an emotion set on session)
    sess = mgr.get_session(user)
    sess.current_emotion = "FEAR"
    mgr.save_session(sess)
    reply2, payload2 = await conv.process_with_llm(user, "why", sess.current_emotion, "")
    assert "understand" in reply2.lower()
    assert "questions" in payload2

    # Remedy path
    reply3, payload3 = await conv.process_with_llm(user, "remedy", sess.current_emotion, "")
    assert "strategies" in reply3.lower()
    assert "remedies" in payload3


@pytest.mark.asyncio
async def test_langchain_flag_falls_back_when_unavailable():
    mgr = InMemorySessionManager()
    user = "bob"
    sess = mgr.get_session(user)
    sess.state = SessionState.SESSION_STARTED
    mgr.save_session(sess)

    # Even if requested, should not raise if LangChain not installed; falls back to stub
    conv = create_conversation_manager(mgr, use_langchain=True)
    reply, analysis = await conv.process_with_llm(user, "ask", "hello", "hello")
    assert isinstance(reply, str)
    assert isinstance(analysis, dict)
