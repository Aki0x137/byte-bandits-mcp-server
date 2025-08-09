from __future__ import annotations

from typing import Any, Dict, List

from .wheel import normalize_text, PrimaryEmotion


LOW_CONFIDENCE_THRESHOLD = 0.2


def analyze_text(text: str, wheel_helper=normalize_text) -> Dict[str, Any]:
    """Deterministic stub that classifies text using the Wheel normalizer.

    Returns a dict with keys: emotion (primary name), confidence (0..1), notes (str).
    If confidence is low, notes will suggest using /wheel for guidance.
    """
    norm = wheel_helper(text or "")
    primary = norm.primary.value
    conf = float(norm.confidence or 0.0)

    tips = {
        PrimaryEmotion.FEAR.value: "Consider grounding; acknowledge uncertainty.",
        PrimaryEmotion.ANGER.value: "Notice boundaries and fairness concerns.",
        PrimaryEmotion.SADNESS.value: "Reflect on loss or change.",
        PrimaryEmotion.JOY.value: "Savor positive moments and share gratitude.",
        PrimaryEmotion.TRUST.value: "Lean into supportive relationships.",
        PrimaryEmotion.SURPRISE.value: "Orient to what's new or unexpected.",
        PrimaryEmotion.DISGUST.value: "Identify aversive triggers and distance.",
        PrimaryEmotion.ANTICIPATION.value: "Plan small next steps; channel energy.",
    }

    note = tips.get(primary, "")
    if conf < LOW_CONFIDENCE_THRESHOLD:
        if note:
            note = f"{note} Confidence low—consider /wheel for guidance."
        else:
            note = "Confidence low—consider /wheel for guidance."

    return {
        "emotion": primary,
        "variant": norm.variant_label,
        "intensity": norm.intensity.value if norm.intensity else None,
        "is_blend": norm.is_blend,
        "blend_name": norm.blend_name,
        "confidence": conf,
        "notes": note,
        "matched_terms": norm.matched_terms,
    }


def probe_questions(emotion: str) -> List[str]:
    e = (emotion or "").strip().upper()
    if e == PrimaryEmotion.FEAR.value:
        return [
            "What feels unsafe or uncertain right now?",
            "What supports could reduce the risk?",
            "What would help you feel 10% safer?",
        ]
    if e == PrimaryEmotion.ANGER.value:
        return [
            "Which boundary or value feels crossed?",
            "What would fairness look like here?",
            "What response aligns with your values?",
        ]
    if e == PrimaryEmotion.SADNESS.value:
        return [
            "What loss or change are you holding?",
            "What do you miss most?",
            "What gentle support would help today?",
        ]
    if e == PrimaryEmotion.JOY.value:
        return [
            "What moment brought this joy?",
            "How can you savor it longer?",
            "Who might you share gratitude with?",
        ]
    if e == PrimaryEmotion.TRUST.value:
        return [
            "Who or what feels dependable now?",
            "How can you lean into support?",
        ]
    if e == PrimaryEmotion.SURPRISE.value:
        return [
            "What changed unexpectedly?",
            "What is within your control today?",
        ]
    if e == PrimaryEmotion.DISGUST.value:
        return [
            "What feels aversive or misaligned?",
            "How can you create distance or safety?",
        ]
    if e == PrimaryEmotion.ANTICIPATION.value:
        return [
            "What are you looking forward to?",
            "What's one small step to prepare?",
        ]
    return ["Tell me more about what you're feeling."]


def suggest_remedies(emotion: str, context: Dict[str, Any] | None = None) -> List[str]:
    e = (emotion or "").strip().upper()
    ctx = context or {}
    base = {
        PrimaryEmotion.FEAR.value: ["Box breathing 4-4-4-4", "List top 3 supports"],
        PrimaryEmotion.ANGER.value: ["Pause and name the boundary", "Write an unsent letter"],
        PrimaryEmotion.SADNESS.value: ["Reach out to a friend", "Gentle walk or music"],
        PrimaryEmotion.JOY.value: ["Gratitude note", "Share a positive moment"],
        PrimaryEmotion.TRUST.value: ["Ask for a small favor", "Affirm a reliable routine"],
        PrimaryEmotion.SURPRISE.value: ["Orient: 5 things you see", "Note what remains stable"],
        PrimaryEmotion.DISGUST.value: ["Create distance from trigger", "Rinse/reset ritual"],
        PrimaryEmotion.ANTICIPATION.value: ["Plan next step", "Time-box prep (10 mins)"]
    }
    # Simple context-based tweak: if user mentions "work" add a planning tip
    remedies = list(base.get(e, ["Hydrate and short break"]))
    if isinstance(ctx.get("topic"), str) and "work" in ctx["topic"].lower():
        remedies.append("Write a 3-item work checklist")
    return remedies
