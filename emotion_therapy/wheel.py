from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class PrimaryEmotion(str, Enum):
    JOY = "JOY"
    TRUST = "TRUST"
    FEAR = "FEAR"
    SURPRISE = "SURPRISE"
    SADNESS = "SADNESS"
    DISGUST = "DISGUST"
    ANGER = "ANGER"
    ANTICIPATION = "ANTICIPATION"


class EmotionIntensity(str, Enum):
    MILD = "MILD"
    BASE = "BASE"
    INTENSE = "INTENSE"


@dataclass(frozen=True)
class EmotionVariant:
    primary: PrimaryEmotion
    intensity: EmotionIntensity
    label: str


@dataclass(frozen=True)
class SecondaryBlend:
    name: str
    left: PrimaryEmotion
    right: PrimaryEmotion


@dataclass
class NormalizedEmotion:
    primary: PrimaryEmotion
    variant_label: Optional[str]
    intensity: Optional[EmotionIntensity]
    is_blend: bool = False
    blend_name: Optional[str] = None
    confidence: float = 0.0
    matched_terms: List[str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.matched_terms is None:
            self.matched_terms = []


# Variants mapping (INTENSE, BASE, MILD)
PRIMARY_TO_VARIANTS: Dict[PrimaryEmotion, Tuple[str, str, str]] = {
    PrimaryEmotion.JOY: ("ecstasy", "joy", "serenity"),
    PrimaryEmotion.TRUST: ("admiration", "trust", "acceptance"),
    PrimaryEmotion.FEAR: ("terror", "fear", "apprehension"),
    PrimaryEmotion.SURPRISE: ("amazement", "surprise", "distraction"),
    PrimaryEmotion.SADNESS: ("grief", "sadness", "pensiveness"),
    PrimaryEmotion.DISGUST: ("loathing", "disgust", "boredom"),
    PrimaryEmotion.ANGER: ("rage", "anger", "annoyance"),
    PrimaryEmotion.ANTICIPATION: ("vigilance", "anticipation", "interest"),
}

# Blends (order-agnostic)
SECONDARY_BLENDS: Dict[Tuple[PrimaryEmotion, PrimaryEmotion], str] = {
    tuple(sorted((PrimaryEmotion.JOY, PrimaryEmotion.TRUST), key=lambda x: x.value)): "love",
    tuple(sorted((PrimaryEmotion.TRUST, PrimaryEmotion.FEAR), key=lambda x: x.value)): "submission",
    tuple(sorted((PrimaryEmotion.FEAR, PrimaryEmotion.SURPRISE), key=lambda x: x.value)): "awe",
    tuple(sorted((PrimaryEmotion.SURPRISE, PrimaryEmotion.SADNESS), key=lambda x: x.value)): "disapproval",
    tuple(sorted((PrimaryEmotion.SADNESS, PrimaryEmotion.DISGUST), key=lambda x: x.value)): "remorse",
    tuple(sorted((PrimaryEmotion.DISGUST, PrimaryEmotion.ANGER), key=lambda x: x.value)): "contempt",
    tuple(sorted((PrimaryEmotion.ANGER, PrimaryEmotion.ANTICIPATION), key=lambda x: x.value)): "aggressiveness",
    tuple(sorted((PrimaryEmotion.ANTICIPATION, PrimaryEmotion.JOY), key=lambda x: x.value)): "optimism",
}

# Synonyms from free text to canonical variant labels
# Note: Keep minimal but useful coverage for tests; extend as needed.
SYNONYMS: Dict[str, List[str]] = {
    # FEAR
    "anxious": ["apprehension"],
    "worry": ["apprehension"],
    "scared": ["fear"],
    "terrified": ["terror"],
    # ANGER
    "annoyed": ["annoyance"],
    "furious": ["rage"],
    "mad": ["anger"],
    # JOY
    "happy": ["joy", "serenity"],
    "ecstatic": ["ecstasy"],
    "joyful": ["joy", "serenity"],
    # TRUST
    "admire": ["admiration"],
    "trusting": ["trust", "acceptance"],
    # SADNESS
    "sad": ["sadness"],
    "grieving": ["grief"],
    # DISGUST
    "gross": ["disgust"],
    # ANTICIPATION
    "interested": ["interest"],
    "vigilant": ["vigilance"],
    # SURPRISE
    "amazed": ["amazement"],
}

# Build reverse lookup: variant label -> (primary, intensity)
VARIANT_LOOKUP: Dict[str, Tuple[PrimaryEmotion, EmotionIntensity]] = {}
for primary, (intense, base, mild) in PRIMARY_TO_VARIANTS.items():
    VARIANT_LOOKUP[intense] = (primary, EmotionIntensity.INTENSE)
    VARIANT_LOOKUP[base] = (primary, EmotionIntensity.BASE)
    VARIANT_LOOKUP[mild] = (primary, EmotionIntensity.MILD)


def _tokenize(text: str) -> List[str]:
    return [t for t in ''.join(ch.lower() if ch.isalnum() else ' ' for ch in text).split() if t]


def _tokens_to_primaries(tokens: Set[str]) -> Set[PrimaryEmotion]:
    primaries: Set[PrimaryEmotion] = set()
    for tok in tokens:
        # direct match to primary name
        for p in PrimaryEmotion:
            if tok == p.value.lower():
                primaries.add(p)
        # variant match
        if tok in VARIANT_LOOKUP:
            primaries.add(VARIANT_LOOKUP[tok][0])
        # synonym -> variants -> primary
        if tok in SYNONYMS:
            for var in SYNONYMS[tok]:
                if var in VARIANT_LOOKUP:
                    primaries.add(VARIANT_LOOKUP[var][0])
    return primaries


def closest_primary(text: str) -> Tuple[PrimaryEmotion, float, List[str]]:
    tokens = set(_tokenize(text))
    scores: Dict[PrimaryEmotion, int] = {p: 0 for p in PrimaryEmotion}
    matched: Dict[PrimaryEmotion, List[str]] = {p: [] for p in PrimaryEmotion}

    for tok in tokens:
        # direct primary token
        for p in PrimaryEmotion:
            if tok == p.value.lower():
                scores[p] += 2
                matched[p].append(tok)
        # variant labels
        if tok in VARIANT_LOOKUP:
            p, _ = VARIANT_LOOKUP[tok]
            scores[p] += 3
            matched[p].append(tok)
        # synonyms
        if tok in SYNONYMS:
            for var in SYNONYMS[tok]:
                if var in VARIANT_LOOKUP:
                    p, _ = VARIANT_LOOKUP[var]
                    scores[p] += 2
                    matched[p].append(tok)

    # fallback: if no tokens matched, default to SADNESS with very low confidence
    best_primary = max(scores, key=lambda p: scores[p])
    best_score = scores[best_primary]
    total = sum(scores.values())
    confidence = (best_score / (total or 1)) if best_score > 0 else 0.0
    return best_primary, confidence, matched[best_primary]


def detect_blend(tokens: Set[str]) -> Optional[Tuple[str, Tuple[PrimaryEmotion, PrimaryEmotion]]]:
    primaries = _tokens_to_primaries(tokens)
    if len(primaries) < 2:
        return None
    # Try all unordered pairs
    plist = sorted(list(primaries), key=lambda p: p.value)
    for i in range(len(plist)):
        for j in range(i + 1, len(plist)):
            pair = (plist[i], plist[j])
            if pair in SECONDARY_BLENDS:
                return SECONDARY_BLENDS[pair], pair
    return None


def normalize_text(text: str) -> NormalizedEmotion:
    tokens = set(_tokenize(text))
    primary, conf, matched = closest_primary(text)

    # determine variant among this primary by checking tokens against its variants and synonyms
    variants = PRIMARY_TO_VARIANTS[primary]
    label: Optional[str] = None
    intensity: Optional[EmotionIntensity] = None

    # Priority: direct variant token -> synonym -> base label if primary token mentioned -> None
    for idx, var in enumerate(variants):
        if var in tokens:
            label = var
            intensity = [EmotionIntensity.INTENSE, EmotionIntensity.BASE, EmotionIntensity.MILD][idx]
            break
    if label is None:
        for tok in tokens:
            if tok in SYNONYMS:
                for var in SYNONYMS[tok]:
                    if var in variants:
                        label = var
                        intensity = EmotionIntensity.INTENSE if var == variants[0] else (
                            EmotionIntensity.BASE if var == variants[1] else EmotionIntensity.MILD
                        )
                        break
            if label is not None:
                break
    if label is None:
        # if primary token exists, prefer BASE label
        if primary.value.lower() in tokens:
            label = variants[1]
            intensity = EmotionIntensity.BASE

    # blend detection
    blend = detect_blend(tokens)
    is_blend = blend is not None
    blend_name = blend[0] if blend else None

    return NormalizedEmotion(
        primary=primary,
        variant_label=label,
        intensity=intensity,
        is_blend=is_blend,
        blend_name=blend_name,
        confidence=conf,
        matched_terms=matched,
    )


def get_wheel_text(levels: List[str] | None = None) -> str:
    levels = levels or ["primary", "variants", "blends"]
    lines: List[str] = []
    if "primary" in levels:
        lines.append("# Primary Emotions")
        for p in PrimaryEmotion:
            lines.append(f"- {p.value}")
        lines.append("")
    if "variants" in levels:
        lines.append("# Variants by Intensity (INTENSE, BASE, MILD)")
        for p, (inten, base, mild) in PRIMARY_TO_VARIANTS.items():
            lines.append(f"- {p.value}: {inten}, {base}, {mild}")
        lines.append("")
    if "blends" in levels:
        lines.append("# Secondary Blends")
        for (l, r), name in SECONDARY_BLENDS.items():
            lines.append(f"- {l.value} + {r.value} → {name}")
        lines.append("")
    return "\n".join(lines).strip()
