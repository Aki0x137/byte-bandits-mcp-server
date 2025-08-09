from emotion_therapy.models import SessionState
from emotion_therapy.validator import validate_command


def test_feel_normalizes_and_sets_context():
    res = validate_command("/feel", "I feel anxious but also joyful", SessionState.SESSION_STARTED, None)
    assert res.is_valid
    assert res.next_state == SessionState.EMOTION_IDENTIFIED

    ctx = res.llm_context
    assert ctx
    details = ctx.get("emotion_details")
    assert details and details["primary"] in {"FEAR", "JOY"}
    # When text contains multiple cues, closest_primary picks one; ensure structure is present
    assert "variant_label" in details
    assert "intensity" in details
    assert "matched_terms" in details and isinstance(details["matched_terms"], list)

    # Convenience keys for session storage
    assert ctx.get("current_emotion_primary") in {"FEAR", "JOY"}
    assert "current_emotion_variant" in ctx
    # blend fields present if detected
    # Not asserting exact blend here; just ensure key exists
    assert "current_emotion_blend" in ctx


def test_feel_requires_session_started():
    res = validate_command("/feel", "sad", SessionState.NO_SESSION, None)
    assert not res.is_valid
    assert "/start" in res.suggested_commands
