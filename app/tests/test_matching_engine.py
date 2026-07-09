"""Tests for matching_engine.py — cosine similarity, ranking, and explanations."""

import pytest

from dishes import DIMENSIONS, DISHES
from matching_engine import cosine_similarity, explain_match, rank_dishes


def test_cosine_similarity_of_a_vector_with_itself_is_one():
    vector = DISHES[0]["vector"]
    assert cosine_similarity(vector, vector) == pytest.approx(1.0)


def test_cosine_similarity_is_symmetric():
    a, b = DISHES[0]["vector"], DISHES[1]["vector"]
    assert cosine_similarity(a, b) == pytest.approx(cosine_similarity(b, a))


def test_cosine_similarity_zero_vector_does_not_divide_by_zero():
    zero_vector = {dim: 0 for dim in DIMENSIONS}
    assert cosine_similarity(zero_vector, DISHES[0]["vector"]) == 0.0


def test_cosine_similarity_is_bounded_between_0_and_1_for_nonnegative_vectors():
    for dish in DISHES:
        score = cosine_similarity(DISHES[0]["vector"], dish["vector"])
        assert 0.0 <= score <= 1.0 + 1e-9


def test_rank_dishes_returns_every_dish():
    target = {dim: 5 for dim in DIMENSIONS}
    ranked = rank_dishes(target, DISHES)
    assert len(ranked) == len(DISHES)


def test_rank_dishes_is_sorted_best_first():
    target = {dim: 5 for dim in DIMENSIONS}
    ranked = rank_dishes(target, DISHES)
    scores = [entry["score"] for entry in ranked]
    assert scores == sorted(scores, reverse=True)


def test_explain_match_falls_back_to_broad_match_when_nothing_lines_up():
    zero_vector = {dim: 0 for dim in DIMENSIONS}
    dish = {"vector": zero_vector}
    explanation = explain_match(zero_vector, dish, contributions=[])
    assert explanation == "Broad match across your current context."


def test_explain_match_names_the_dimensions_and_the_driving_source():
    target = {dim: 0 for dim in DIMENSIONS}
    target["spice"] = 8
    dish = {"vector": {dim: 0 for dim in DIMENSIONS}}
    dish["vector"]["spice"] = 9
    contributions = [{"source": "Bored", "delta": {"spice": 2}}]

    explanation = explain_match(target, dish, contributions)

    assert "Spice" in explanation
    assert "Bored" in explanation
    assert explanation.startswith("High ")
    assert "driven by" in explanation


def test_explain_match_picks_the_largest_contributor_when_several_fired():
    target = {dim: 0 for dim in DIMENSIONS}
    target["warmth"] = 8
    dish = {"vector": {dim: 0 for dim in DIMENSIONS}}
    dish["vector"]["warmth"] = 8
    contributions = [
        {"source": "Evening", "delta": {"warmth": 1}},
        {"source": "Stressed", "delta": {"warmth": 3}},
    ]

    explanation = explain_match(target, dish, contributions)

    assert "Stressed" in explanation
    assert "Evening" not in explanation


def test_explain_match_never_crashes_for_any_dish_in_a_realistic_scenario():
    target = {dim: 5 for dim in DIMENSIONS}
    contributions = [{"source": "Late Night", "delta": {"warmth": 3, "richness": 3}}]
    for dish in DISHES:
        explanation = explain_match(target, dish, contributions)
        assert isinstance(explanation, str)
        assert len(explanation) > 0
