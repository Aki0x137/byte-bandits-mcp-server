import os
import time

import pytest

from emotion_therapy.session_store import RedisSessionManager
from emotion_therapy.models import TherapySession, SessionState


@pytest.fixture(scope="module")
def redis_url() -> str:
    return os.environ.get("REDIS_URL", "redis://localhost:6379")


@pytest.fixture()
def mgr(redis_url: str) -> RedisSessionManager:
    return RedisSessionManager(redis_url=redis_url, ttl_seconds=2)  # short TTL for test


def test_crud_session_roundtrip(mgr: RedisSessionManager):
    user = "test_user_crud"
    # ensure clean
    mgr.delete_session(user)

    s = mgr.get_session(user)
    assert s.user_id == user and s.state == SessionState.NO_SESSION

    s.state = SessionState.SESSION_STARTED
    s.context = {"token": "secret", "note": "keep"}
    mgr.save_session(s)

    s2 = mgr.get_session(user)
    assert s2.state == SessionState.SESSION_STARTED
    # sensitive keys scrubbed
    assert "token" not in s2.context and s2.context.get("note") == "keep"

    mgr.delete_session(user)
    s3 = mgr.get_session(user)
    assert s3.state == SessionState.NO_SESSION


def test_ttl_expiry(mgr: RedisSessionManager):
    user = "test_user_ttl"
    mgr.delete_session(user)

    s = mgr.get_session(user)
    s.state = SessionState.SESSION_STARTED
    mgr.save_session(s)

    # Should exist now
    assert mgr.get_session(user).state == SessionState.SESSION_STARTED

    # Wait for TTL to expire
    time.sleep(2.2)

    # After TTL, should be gone / default session
    s2 = mgr.get_session(user)
    assert s2.state == SessionState.NO_SESSION


def test_mood_history(mgr: RedisSessionManager):
    user = "test_user_history"
    # reset list
    mgr.client.delete(mgr._moodlog_key(user))

    mgr.add_to_history(user, "/feel", "sad", {"ok": True})
    mgr.add_to_history(user, "/why", None, "some text")

    hist = mgr.get_mood_history(user, limit=5)
    assert len(hist) == 2
    assert hist[0]["command"] == "/feel"
    assert hist[1]["command"] == "/why"
    assert isinstance(hist[0]["result"], dict)
    assert hist[1]["result"]["text"] == "some text"
