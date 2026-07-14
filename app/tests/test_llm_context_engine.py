"""
Tests for llm_context_engine.py — no real network or API calls anywhere.

The Anthropic client is monkeypatched via `_get_client()`, the one seam
get_target_vector() uses to reach the SDK, so every test here is fast,
free, and deterministic.
"""

import llm_context_engine
from context_engine import TIME_DELTAS
from dishes import DIMENSIONS
from llm_context_engine import (
    DimensionScore,
    FlavorVectorResponse,
    build_context_payload,
    get_target_vector,
)


def _build_flavor_vector_response(value=5.0, rationale_prefix="stub rationale for"):
    kwargs = {dim: DimensionScore(value=value, rationale=f"{rationale_prefix} {dim}") for dim in DIMENSIONS}
    return FlavorVectorResponse(**kwargs)


class _FakeMessages:
    def __init__(self, response=None, exception=None):
        self._response = response
        self._exception = exception

    def parse(self, **kwargs):
        if self._exception is not None:
            raise self._exception
        return self._response


class _FakeClient:
    def __init__(self, response=None, exception=None):
        self.messages = _FakeMessages(response, exception)

    def with_options(self, **kwargs):
        return self


class _StubResponse:
    def __init__(self, stop_reason, parsed_output):
        self.stop_reason = stop_reason
        self.parsed_output = parsed_output


def test_build_context_payload_shape():
    payload = build_context_payload("Morning", {"temperature_c": 30}, None, {"energy_level": "Low"}, "spicy")
    assert payload == {
        "time_of_day": "Morning",
        "weather": {"temperature_c": 30},
        "biometrics": None,
        "quiz_answers": {"energy_level": "Low"},
        "craving_text": "spicy",
    }


def test_dimension_score_clamps_above_range():
    assert DimensionScore(value=15, rationale="x").value == 10.0


def test_dimension_score_clamps_below_range():
    assert DimensionScore(value=-3, rationale="x").value == 0.0


def test_get_target_vector_happy_path(monkeypatch):
    stub = _StubResponse(stop_reason="end_turn", parsed_output=_build_flavor_vector_response(value=7.0))
    monkeypatch.setattr(llm_context_engine, "_get_client", lambda: _FakeClient(response=stub))

    payload = build_context_payload("Morning", None, None, {}, "")
    result = get_target_vector(payload)

    assert result.source == "llm"
    assert result.error is None
    assert all(v == 7.0 for v in result.vector.values())
    assert result.rationale["spice"] == "stub rationale for spice"


def test_get_target_vector_falls_back_on_connection_error(monkeypatch):
    monkeypatch.setattr(
        llm_context_engine, "_get_client", lambda: _FakeClient(exception=ConnectionError("no network"))
    )

    payload = build_context_payload("Morning", None, None, {}, "")
    result = get_target_vector(payload)

    assert result.source == "fallback"
    assert "no network" in result.error


def test_get_target_vector_falls_back_on_refusal(monkeypatch):
    stub = _StubResponse(stop_reason="refusal", parsed_output=None)
    monkeypatch.setattr(llm_context_engine, "_get_client", lambda: _FakeClient(response=stub))

    payload = build_context_payload("Morning", None, None, {}, "")
    result = get_target_vector(payload)

    assert result.source == "fallback"
    assert "refusal" in result.error.lower()


def test_get_target_vector_falls_back_on_malformed_response(monkeypatch):
    monkeypatch.setattr(
        llm_context_engine, "_get_client", lambda: _FakeClient(exception=ValueError("malformed schema"))
    )

    payload = build_context_payload("Morning", None, None, {}, "")
    result = get_target_vector(payload)

    assert result.source == "fallback"
    assert "malformed schema" in result.error


def test_fallback_vector_is_baseline_plus_time_delta_with_no_other_signals():
    vector, rationale = llm_context_engine._fallback_vector_and_rationale("Morning", {}, "")
    expected = {dim: 5 for dim in DIMENSIONS}
    for dim, delta in TIME_DELTAS["Morning"].items():
        expected[dim] += delta
    assert vector == expected
    assert rationale["spice"] == "Fallback: neutral baseline (AI unavailable)."


def test_fallback_vector_changes_with_quiz_answers_and_craving_text():
    baseline, _ = llm_context_engine._fallback_vector_and_rationale("Morning", {}, "")
    varied, rationale = llm_context_engine._fallback_vector_and_rationale(
        "Morning", {"energy_level": "High"}, "something spicy"
    )
    assert varied != baseline
    assert varied["spice"] > baseline["spice"]
    assert "quiz answer" in rationale["crunch"] or "keyword" in rationale["spice"]


def test_fallback_vector_stays_within_0_to_10():
    vector, _ = llm_context_engine._fallback_vector_and_rationale(
        "Late Night", {"notable_activity": "Feeling under the weather"}, "spicy tangy rich crunchy"
    )
    assert all(0 <= v <= 10 for v in vector.values())
