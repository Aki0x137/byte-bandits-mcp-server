from __future__ import annotations

from typing import Any, Dict, List, Optional

from .wheel import normalize_text, PrimaryEmotion
from .llm_handler import create_handler_from_env, LLMHandler


LOW_CONFIDENCE_THRESHOLD = 0.2

# Global LLM handler instance
_llm_handler: Optional[LLMHandler] = None


def get_llm_handler() -> Optional[LLMHandler]:
    """Get or create the global LLM handler instance"""
    global _llm_handler
    if _llm_handler is None:
        _llm_handler = create_handler_from_env()
    return _llm_handler


def set_llm_handler(handler: LLMHandler) -> None:
    """Set a custom LLM handler"""
    global _llm_handler
    _llm_handler = handler


def analyze_text(text: str, wheel_helper=normalize_text, use_llm: bool = True) -> Dict[str, Any]:
    """Analyze text emotion using Wheel normalizer with optional LLM enhancement.

    Args:
        text: Text to analyze
        wheel_helper: Wheel normalization function (default: normalize_text)
        use_llm: Whether to use LLM for enhanced analysis (default: True)

    Returns a dict with keys: emotion (primary name), confidence (0..1), notes (str).
    If confidence is low, notes will suggest using /wheel for guidance.
    """
    # Always start with deterministic wheel analysis
    norm = wheel_helper(text or "")
    primary = norm.primary.value
    conf = float(norm.confidence or 0.0)

    # Base tips for each emotion
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
    
    # Enhance with LLM if available and confidence is low
    if use_llm and conf < LOW_CONFIDENCE_THRESHOLD:
        llm_handler = get_llm_handler()
        if llm_handler:
            try:
                llm_analysis = llm_handler.analyze_emotion_with_cot(text)
                # If LLM has higher confidence, use its analysis
                if llm_analysis.get("confidence", 0) > conf:
                    primary = llm_analysis.get("emotion", primary)
                    conf = llm_analysis.get("confidence", conf)
                    note = llm_analysis.get("reasoning", note)
                    # Update norm-like structure for compatibility
                    norm.primary = PrimaryEmotion(primary.upper()) if primary.upper() in [e.value for e in PrimaryEmotion] else norm.primary
            except Exception:
                # Fall back to wheel analysis if LLM fails
                pass
    
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


def probe_questions(emotion: str, use_llm: bool = False, context: str = "") -> List[str]:
    """Generate probing questions for an emotion, optionally enhanced with LLM.
    
    Args:
        emotion: Primary emotion to probe
        use_llm: Whether to use LLM for enhanced questions
        context: Additional context for LLM-generated questions
    """
    e = (emotion or "").strip().upper()
    
    # Base questions for each emotion
    base_questions = {
        PrimaryEmotion.FEAR.value: [
            "What feels unsafe or uncertain right now?",
            "What supports could reduce the risk?",
            "What would help you feel 10% safer?",
        ],
        PrimaryEmotion.ANGER.value: [
            "Which boundary or value feels crossed?",
            "What would fairness look like here?",
            "What response aligns with your values?",
        ],
        PrimaryEmotion.SADNESS.value: [
            "What loss or change are you holding?",
            "What do you miss most?",
            "What gentle support would help today?",
        ],
        PrimaryEmotion.JOY.value: [
            "What moment brought this joy?",
            "How can you savor it longer?",
            "Who might you share gratitude with?",
        ],
        PrimaryEmotion.TRUST.value: [
            "Who or what feels dependable now?",
            "How can you lean into support?",
        ],
        PrimaryEmotion.SURPRISE.value: [
            "What changed unexpectedly?",
            "What is within your control today?",
        ],
        PrimaryEmotion.DISGUST.value: [
            "What feels aversive or misaligned?",
            "How can you create distance or safety?",
        ],
        PrimaryEmotion.ANTICIPATION.value: [
            "What are you looking forward to?",
            "What's one small step to prepare?",
        ]
    }
    
    questions = base_questions.get(e, ["Tell me more about what you're feeling."])
    
    # Enhance with LLM if requested and available
    if use_llm and context:
        llm_handler = get_llm_handler()
        if llm_handler:
            try:
                # Create a simple prompt for generating contextual questions
                enhanced_response = llm_handler.generate_therapeutic_response_with_cot(
                    emotion=emotion,
                    context=context,
                    user_message="I need some thoughtful questions to explore this emotion further",
                    tone="default"
                )
                # Extract questions from response (this is a simple approach)
                if "?" in enhanced_response:
                    enhanced_questions = [q.strip() for q in enhanced_response.split("?") if q.strip()]
                    enhanced_questions = [q + "?" for q in enhanced_questions if len(q) > 10]
                    if enhanced_questions:
                        return enhanced_questions[:3]  # Return top 3 LLM questions
            except Exception:
                pass  # Fall back to base questions
    
    return questions


def suggest_remedies(emotion: str, context: Dict[str, Any] | None = None, use_llm: bool = True) -> List[str]:
    """Suggest remedies for an emotion, optionally enhanced with LLM chain of thoughts.
    
    Args:
        emotion: Primary emotion to address
        context: Additional context (e.g., topic, intensity)
        use_llm: Whether to use LLM for enhanced, contextual remedies
    """
    e = (emotion or "").strip().upper()
    ctx = context or {}
    
    # Base remedies for each emotion
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
    
    remedies = list(base.get(e, ["Hydrate and short break"]))
    
    # Simple context-based tweak: if user mentions "work" add a planning tip
    if isinstance(ctx.get("topic"), str) and "work" in ctx["topic"].lower():
        remedies.append("Write a 3-item work checklist")
    
    # Enhance with LLM if requested and available
    if use_llm:
        llm_handler = get_llm_handler()
        if llm_handler:
            try:
                context_str = ctx.get("topic", "") or ctx.get("context", "") or "general situation"
                intensity = ctx.get("intensity", "medium")
                
                llm_remedies = llm_handler.suggest_remedies_with_cot(
                    emotion=emotion,
                    context=context_str,
                    intensity=intensity
                )
                
                if llm_remedies:
                    # Combine base remedies with LLM suggestions, prioritizing LLM
                    combined = llm_remedies + [r for r in remedies if r not in llm_remedies]
                    return combined[:5]  # Return top 5 combined suggestions
            except Exception:
                pass  # Fall back to base remedies
    
    return remedies


def generate_therapeutic_response(
    emotion: str,
    context: str,
    user_message: str,
    tone: str = "default"
) -> str:
    """Generate a therapeutic response using LLM chain of thoughts.
    
    This function provides the main interface for generating therapeutic responses
    and can be called from the MCP tools.
    """
    llm_handler = get_llm_handler()
    if not llm_handler:
        return f"I understand you're experiencing {emotion}. Your feelings are valid. Consider taking a moment to breathe and reach out to someone you trust if you need support."
    
    try:
        return llm_handler.generate_therapeutic_response_with_cot(
            emotion=emotion,
            context=context,
            user_message=user_message,
            tone=tone
        )
    except Exception:
        return f"I hear that you're feeling {emotion}. That's completely understandable given your situation. Sometimes just acknowledging our emotions is the first step toward feeling better."
