from emotion_therapy.llm_stub import analyze_text, probe_questions, suggest_remedies, LOW_CONFIDENCE_THRESHOLD
from emotion_therapy.wheel import PrimaryEmotion


def test_analyze_text_uses_wheel_and_returns_structure():
    res = analyze_text("I'm ecstatic and so joyful")
    assert res["emotion"] == PrimaryEmotion.JOY.value
    assert res["confidence"] >= 0.0
    assert isinstance(res["matched_terms"], list)
    assert res["variant"] in {"ecstasy", "joy", "serenity"}


def test_analyze_text_low_confidence_suggests_wheel():
    res = analyze_text("blorple snarf")
    assert res["confidence"] < LOW_CONFIDENCE_THRESHOLD
    assert "/wheel" in res["notes"]


def test_probe_questions_are_deterministic_by_emotion():
    fear_qs = probe_questions(PrimaryEmotion.FEAR.value)
    anger_qs = probe_questions(PrimaryEmotion.ANGER.value)
    assert any("unsafe" in q.lower() for q in fear_qs)
    assert any("boundary" in q.lower() for q in anger_qs)


def test_suggest_remedies_basic_and_contextual():
    base = suggest_remedies(PrimaryEmotion.FEAR.value)
    assert any("breathing" in r.lower() or "box" in r.lower() for r in base)

    ctx = {"topic": "work stress"}
    with_ctx = suggest_remedies(PrimaryEmotion.SADNESS.value, ctx)
    assert any("work" in r.lower() for r in with_ctx)
