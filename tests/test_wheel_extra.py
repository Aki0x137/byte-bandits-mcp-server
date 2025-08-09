import pytest

from emotion_therapy.wheel import (
    PrimaryEmotion,
    EmotionIntensity,
    closest_primary,
    detect_blend,
    normalize_text,
    get_wheel_text,
)


def test_normalize_direct_primary_defaults_base():
    norm = normalize_text("anger rising")
    assert norm.primary == PrimaryEmotion.ANGER
    assert norm.variant_label == "anger"
    assert norm.intensity == EmotionIntensity.BASE


def test_normalize_ecstatic_intense():
    norm = normalize_text("I'm ecstatic!")
    assert norm.primary == PrimaryEmotion.JOY
    assert norm.variant_label == "ecstasy"
    assert norm.intensity == EmotionIntensity.INTENSE


def test_closest_primary_matches_synonym():
    p, conf, matched = closest_primary("so annoyed today")
    assert p == PrimaryEmotion.ANGER
    assert conf > 0
    assert "annoyed" in matched


def test_detect_blend_from_synonyms():
    name_pair = detect_blend(set("furious yet vigilant".split()))
    assert name_pair is not None
    name, pair = name_pair
    assert name == "aggressiveness"
    assert set(pair) == {PrimaryEmotion.ANGER, PrimaryEmotion.ANTICIPATION}


def test_get_wheel_text_contains_specific_blend_line():
    txt = get_wheel_text(["blends"])  # only blends section
    assert "ANGER + ANTICIPATION" in txt and "aggressiveness" in txt and "\u2192" in txt


def test_normalize_confidence_zero_on_unknown():
    norm = normalize_text("blorple snarf")
    assert norm.confidence == 0.0
    assert isinstance(norm.primary, PrimaryEmotion)


def test_tokenization_case_and_punct():
    norm = normalize_text("I feel, SAD...")
    assert norm.primary == PrimaryEmotion.SADNESS
    assert norm.variant_label == "sadness"
    assert norm.intensity == EmotionIntensity.BASE


def test_normalize_sets_blend_metadata():
    norm = normalize_text("joyful trusting")
    assert norm.is_blend is True
    assert norm.blend_name == "love"
