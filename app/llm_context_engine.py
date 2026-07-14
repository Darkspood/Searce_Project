"""
LLM Context Engine — the one place in this app that calls an external LLM.

Sends the full real-time context (time of day, weather, simulated
biometrics, mood-quiz answers, free-text craving) to the Claude API in a
single call and gets back the 14-dimension target flavor vector plus a
one-sentence rationale per dimension. Everything downstream of this module
(matching_engine.py) stays plain deterministic code — the LLM's job is
scoped strictly to producing the target vector + rationale, not to ranking
or matching.

If the API call fails for any reason (network error, timeout, rate limit,
refusal, or a malformed/unparseable response), get_target_vector() falls
back to a small deterministic computation (baseline + TIME_DELTAS + a
handful of fallback-only quiz/keyword deltas) instead of crashing — see
_fallback_vector_and_rationale. The caller always gets a ContextResult back,
never an exception.
"""

import json

import anthropic
from pydantic import BaseModel, Field, field_validator

from context_engine import TIME_DELTAS, add_delta, clamp_vector
from dishes import DIMENSIONS

MODEL_NAME = "claude-sonnet-5"
REQUEST_TIMEOUT_SECONDS = 25.0
MAX_TOKENS = 4096

# 0/10 anchor calibration for each dimension, folded into the system prompt
# so the model's numbers are consistently calibrated run-to-run even without
# temperature control (Sonnet 5 rejects non-default sampling parameters).
DIMENSION_ANCHORS = {
    "spice": "0 = no capsaicin/pepper at all, 10 = ghost-pepper-level heat",
    "acidity": "0 = no tang, 10 = vinegar-forward/pickled sourness",
    "richness": "0 = watery/thin, 10 = heavy cream/butter-laden",
    "warmth": "0 = served cold, 10 = piping hot and warming spices",
    "crunch": "0 = fully soft/mushy, 10 = maximally crispy",
    "umami": "0 = no savory depth, 10 = intensely savory (aged cheese, soy, mushroom)",
    "sweetness": "0 = no sugar, 10 = dessert-level sweet",
    "bitterness": "0 = none, 10 = strongly bitter (dark chocolate, bitter greens)",
    "saltiness": "0 = unsalted, 10 = very salty",
    "freshness": "0 = heavy/cooked-down, 10 = raw/crisp/vibrant",
    "moisture": "0 = bone dry, 10 = saucy/soupy/juicy",
    "aroma": "0 = neutral smell, 10 = intensely fragrant/perfumed",
    "chewiness": "0 = no chew (soft/liquid), 10 = very chewy/dense",
    "temp_contrast": "0 = uniform temperature, 10 = strong hot+cold contrast in one dish",
}

_ANCHOR_LINES = "\n".join(f"- {dim}: {desc}" for dim, desc in DIMENSION_ANCHORS.items())

SYSTEM_PROMPT = f"""You are the Context Engine for a food-recommendation prototype. Given a \
person's current real-time context (time of day, weather, simulated smartwatch biometrics, \
answers to a short mood quiz, and a free-text craving), output a target flavor vector across \
these 14 dimensions, each scored 0-10:

{_ANCHOR_LINES}

Every `value` must be a number between 0 and 10 inclusive.

For each dimension, also give a one-sentence `rationale` explaining why that value fits this \
specific context. Reference the concrete signal that drove it (a weather reading, a biometric \
reading, a quiz answer, or a phrase from the craving text) rather than generic filler.

Some context fields may be null or missing (e.g. weather or biometric data was not provided). \
Work only with what's given — do not invent or assume missing signals."""


class DimensionScore(BaseModel):
    value: float = Field(description="0-10 score for this flavor dimension.")
    rationale: str = Field(description="One sentence on why this value fits this context.")

    @field_validator("value")
    @classmethod
    def _clamp_to_range(cls, v):
        # The API's JSON schema strips numeric range constraints before it
        # reaches the model, so the 0-10 range is only ever enforced here,
        # client-side. Clamp rather than reject: a stray 10.4 shouldn't
        # discard 13 other well-reasoned dimensions along with it.
        return max(0.0, min(10.0, v))


class FlavorVectorResponse(BaseModel):
    spice: DimensionScore
    acidity: DimensionScore
    richness: DimensionScore
    warmth: DimensionScore
    crunch: DimensionScore
    umami: DimensionScore
    sweetness: DimensionScore
    bitterness: DimensionScore
    saltiness: DimensionScore
    freshness: DimensionScore
    moisture: DimensionScore
    aroma: DimensionScore
    chewiness: DimensionScore
    temp_contrast: DimensionScore


class ContextResult:
    """The uniform result get_target_vector() returns, regardless of path taken."""

    def __init__(self, vector, rationale, source, error=None):
        self.vector = vector
        self.rationale = rationale
        self.source = source  # "llm" or "fallback"
        self.error = error


# --- Fallback-only delta tables -------------------------------------------
# Deliberately small (a handful of entries) compared to the old MOODS/
# ACTIVITIES/KEYWORD_DELTAS tables — these exist only so the deterministic
# fallback still varies by quiz answer / craving text instead of being
# flatly identical for every user at the same hour, not to resurrect the
# old rule-based system as a parallel primary path.
FALLBACK_QUIZ_DELTAS = {
    "energy_level": {
        "Low": {"sweetness": 2, "warmth": 2, "moisture": 2},
        "High": {"spice": 2, "crunch": 2, "freshness": 2, "richness": -2},
        "Wired but tired": {"warmth": 2, "richness": 2, "spice": -1},
    },
    "day_descriptor": {
        "Stressful and packed": {"warmth": 3, "richness": 3, "sweetness": 2, "spice": -2, "freshness": -1},
        "Something to celebrate": {"richness": 3, "sweetness": 2, "aroma": 2, "umami": 2},
        "A slow, nostalgic kind of day": {"warmth": 2, "umami": 2, "aroma": 2, "sweetness": 1},
    },
    "notable_activity": {
        "Just worked out": {"freshness": 2, "moisture": 2, "richness": -2, "umami": 2},
        "Long day at work": {"warmth": 2, "richness": 2, "sweetness": 1, "crunch": -1},
        "Traveling": {"saltiness": 2, "crunch": 2, "moisture": -1},
        "Feeling under the weather": {"warmth": 3, "moisture": 3, "spice": -3, "crunch": -2},
        "Hosting guests": {"aroma": 2, "umami": 2, "richness": 1},
    },
    "temperature_preference": {
        "Something warm and comforting": {"warmth": 3, "richness": 2},
        "Something light and fresh": {"freshness": 3, "richness": -2, "moisture": 1},
        "Something bold and intense": {"spice": 3, "umami": 2, "aroma": 2},
    },
}

FALLBACK_KEYWORD_DELTAS = {
    "spicy": {"spice": 3},
    "tangy": {"acidity": 3},
    "rich": {"richness": 3},
    "comfort": {"warmth": 2, "richness": 2},
    "crunchy": {"crunch": 3},
    "sweet": {"sweetness": 3},
    "fresh": {"freshness": 3, "richness": -1},
    "light": {"freshness": 2, "richness": -2},
    "salty": {"saltiness": 3},
    "savory": {"umami": 2},
}


def build_context_payload(time_bucket, weather, biometrics, quiz_answers, craving_text):
    """Assembles the structured dict sent to the LLM as the user-turn content."""
    return {
        "time_of_day": time_bucket,
        "weather": weather,  # dict or None
        "biometrics": biometrics,  # dict or None
        "quiz_answers": quiz_answers or {},  # values may be None for unanswered questions
        "craving_text": craving_text or "",
    }


def _get_client():
    """Constructed lazily (not at module import time) so importing this module
    never fails just because ANTHROPIC_API_KEY is unset — e.g. during pytest
    collection or Streamlit's AppTest harness. Tests monkeypatch this function."""
    return anthropic.Anthropic()


def _to_vector_and_rationale(parsed):
    vector = {}
    rationale = {}
    for dim in DIMENSIONS:
        score = getattr(parsed, dim)
        vector[dim] = score.value
        rationale[dim] = score.rationale
    return vector, rationale


def _fallback_vector_and_rationale(time_bucket, quiz_answers, craving_text):
    vector = {dim: 5 for dim in DIMENSIONS}
    rationale = {dim: "Fallback: neutral baseline (AI unavailable)." for dim in DIMENSIONS}

    def apply(delta, reason):
        add_delta(vector, delta)
        for dim in delta:
            rationale[dim] = f"Fallback: {reason}"

    apply(TIME_DELTAS[time_bucket], f"{time_bucket} baseline adjustment.")

    for key, answer in (quiz_answers or {}).items():
        option_deltas = FALLBACK_QUIZ_DELTAS.get(key, {})
        if answer in option_deltas:
            apply(option_deltas[answer], f"quiz answer '{answer}'.")

    lower_craving = (craving_text or "").lower()
    for keyword, delta in FALLBACK_KEYWORD_DELTAS.items():
        if keyword in lower_craving:
            apply(delta, f"matched craving keyword '{keyword}'.")

    clamp_vector(vector)
    return vector, rationale


def get_target_vector(context_payload):
    """
    Turns a context payload (see build_context_payload) into a target flavor
    vector + per-dimension rationale, via a single Claude API call. Falls back
    to a deterministic computation on any failure — never raises.
    """
    time_bucket = context_payload["time_of_day"]
    quiz_answers = context_payload.get("quiz_answers") or {}
    craving_text = context_payload.get("craving_text") or ""

    try:
        client = _get_client()
        response = client.with_options(timeout=REQUEST_TIMEOUT_SECONDS).messages.parse(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(context_payload)}],
            output_format=FlavorVectorResponse,
        )
        if response.stop_reason == "refusal":
            raise RuntimeError("Claude declined the request (refusal).")
        vector, rationale = _to_vector_and_rationale(response.parsed_output)
        return ContextResult(vector, rationale, source="llm", error=None)
    except Exception as exc:  # noqa: BLE001 - deliberate safety net, see module docstring
        vector, rationale = _fallback_vector_and_rationale(time_bucket, quiz_answers, craving_text)
        return ContextResult(vector, rationale, source="fallback", error=str(exc))
