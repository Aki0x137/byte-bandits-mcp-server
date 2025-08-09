import pytest

from emotion_therapy.wheel import (
    PrimaryEmotion,
    EmotionIntensity,
    closest_primary,
    detect_blend,
    normalize_text,
    get_wheel_text,
)


def test_wheel_normalize_basic():
    norm = normalize_text("I feel anxious today")
    assert norm.primary == PrimaryEmotion.FEAR
    assert norm.variant_label in {"apprehension", "fear"}
    # if mapped via synonym to apprehension, intensity may be MILD
    if norm.variant_label == "apprehension":
        assert norm.intensity in {EmotionIntensity.MILD, EmotionIntensity.BASE}


def test_wheel_blend_detection():
    blend = detect_blend(set("joyful trusting vibes".split()))
    assert blend is not None
    name, pair = blend
    assert name == "love"
    assert set(pair) == {PrimaryEmotion.JOY, PrimaryEmotion.TRUST}


def test_wheel_ascii_contains_core_labels():
    txt = get_wheel_text()
    # primary section
    for p in [
        "JOY",
        "TRUST",
        "FEAR",
        "SURPRISE",
        "SADNESS",
        "DISGUST",
        "ANGER",
        "ANTICIPATION",
    ]:
        assert p in txt
    # a couple of variants and blends
    assert "ecstasy" in txt and "annoyance" in txt
    assert "JOY + TRUST" in txt or "Joy + Trust" in txt
