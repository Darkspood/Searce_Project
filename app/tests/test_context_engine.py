"""Tests for context_engine.py — delta tables and target-vector computation."""

from datetime import datetime

import pytest

from context_engine import (
    ACTIVITIES,
    ACTIVITY_DELTAS,
    KEYWORD_DELTAS,
    MOOD_DELTAS,
    MOODS,
    TIME_DELTAS,
    compute_target_vector,
    get_time_bucket,
)
from dishes import DIMENSIONS


def test_moods_list_has_8_entries():
    assert len(MOODS) == 8


def test_activities_list_has_6_entries():
    assert len(ACTIVITIES) == 6


def test_time_deltas_cover_all_four_buckets():
    assert set(TIME_DELTAS.keys()) == {"Morning", "Afternoon", "Evening", "Late Night"}


def test_mood_deltas_cover_every_mood():
    assert set(MOOD_DELTAS.keys()) == set(MOODS)


def test_activity_deltas_cover_every_activity():
    assert set(ACTIVITY_DELTAS.keys()) == set(ACTIVITIES)


def test_keyword_deltas_has_at_least_25_entries():
    assert len(KEYWORD_DELTAS) >= 25


def test_every_delta_table_only_targets_real_dimensions():
    for table in (TIME_DELTAS, MOOD_DELTAS, ACTIVITY_DELTAS, KEYWORD_DELTAS):
        for source, delta in table.items():
            assert set(delta.keys()) <= set(DIMENSIONS), source


@pytest.mark.parametrize(
    "hour, expected",
    [
        (0, "Late Night"),
        (4, "Late Night"),
        (5, "Morning"),
        (11, "Morning"),
        (12, "Afternoon"),
        (16, "Afternoon"),
        (17, "Evening"),
        (20, "Evening"),
        (21, "Late Night"),
        (23, "Late Night"),
    ],
)
def test_get_time_bucket_boundaries(hour, expected):
    assert get_time_bucket(datetime(2026, 1, 1, hour, 0)) == expected


def test_compute_target_vector_with_no_signals_is_baseline_plus_time_delta():
    vector, contributions, matched = compute_target_vector("Morning", None, [], "")
    expected = {dim: 5 for dim in DIMENSIONS}
    for dim, delta in TIME_DELTAS["Morning"].items():
        expected[dim] += delta
    assert vector == expected
    assert matched == []
    assert len(contributions) == 1  # only the time bucket contributed


def test_compute_target_vector_stays_within_0_to_10_even_when_maxed_out():
    all_keywords_text = " ".join(KEYWORD_DELTAS.keys())
    vector, _, matched = compute_target_vector("Late Night", "Stressed", ACTIVITIES, all_keywords_text)
    assert all(0 <= v <= 10 for v in vector.values())
    assert len(matched) == len(KEYWORD_DELTAS)


def test_compute_target_vector_keyword_matching_is_case_insensitive():
    _, _, matched = compute_target_vector("Morning", None, [], "SPICY AND TANGY")
    assert "spicy" in matched
    assert "tangy" in matched


def test_compute_target_vector_empty_craving_matches_no_keywords():
    _, _, matched = compute_target_vector("Morning", None, [], "")
    assert matched == []


def test_compute_target_vector_handles_no_mood_selected():
    vector, contributions, _ = compute_target_vector("Evening", None, [], "")
    assert all(0 <= v <= 10 for v in vector.values())
    # No mood was selected, so no contribution entry should reference one.
    assert all(c["source"] is not None for c in contributions)
    assert len(contributions) == 1  # only the time bucket contributed


def test_compute_target_vector_contributions_include_one_entry_per_active_signal():
    _, contributions, matched = compute_target_vector(
        "Late Night", "Stressed", ["Long day at work"], "crunchy"
    )
    sources = [c["source"] for c in contributions]
    assert "Late Night" in sources
    assert "Stressed" in sources
    assert "Long day at work" in sources
    assert '"crunchy"' in sources
    assert matched == ["crunchy"]
