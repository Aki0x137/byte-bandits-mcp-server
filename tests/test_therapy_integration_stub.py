from emotion_therapy.models import SessionState
from emotion_therapy.validator import validate_command
from emotion_therapy.llm_stub import analyze_text, probe_questions, suggest_remedies


def test_integration_stub_with_validator_flow():
    # Start session
    res = validate_command("/start", None, SessionState.NO_SESSION)
    assert res.is_valid and res.next_state == SessionState.SESSION_STARTED

    # Feel via wheel normalization
    res2 = validate_command("/feel", "I'm ecstatic!", SessionState.SESSION_STARTED)
    assert res2.is_valid and res2.next_state == SessionState.EMOTION_IDENTIFIED
    details = res2.llm_context.get("emotion_details")
    assert details and details["primary"] == "JOY"

    # LLM stub analysis aligns with wheel
    analysis = analyze_text("I'm ecstatic!")
    assert analysis["emotion"] == "JOY"

    # Diagnostic questions for JOY
    qs = probe_questions("JOY")
    assert len(qs) >= 2

    # Remedies for JOY
    rem = suggest_remedies("JOY", {"topic": "work milestone"})
    assert isinstance(rem, list) and len(rem) >= 1
