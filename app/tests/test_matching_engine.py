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
    explanation = explain_match(zero_vector, dish, rationale={})
    assert explanation == "Broad match across your current context."


def test_explain_match_names_the_dimensions_and_the_rationale():
    target = {dim: 0 for dim in DIMENSIONS}
    target["spice"] = 8
    dish = {"vector": {dim: 0 for dim in DIMENSIONS}}
    dish["vector"]["spice"] = 9
    rationale = {"spice": "You seem bored, so a spicy kick fits the mood."}

    explanation = explain_match(target, dish, rationale)

    assert "Spice" in explanation
    assert "bored" in explanation
    assert explanation.startswith("High ")


def test_explain_match_caps_to_two_reasons_for_readability():
    target = {dim: 0 for dim in DIMENSIONS}
    target["warmth"] = 8
    target["richness"] = 7
    target["umami"] = 6
    dish = {"vector": {dim: 0 for dim in DIMENSIONS}}
    dish["vector"]["warmth"] = 8
    dish["vector"]["richness"] = 7
    dish["vector"]["umami"] = 6
    rationale = {
        "warmth": "Reason one.",
        "richness": "Reason two.",
        "umami": "Reason three.",
    }

    explanation = explain_match(target, dish, rationale)

    assert "Reason one." in explanation
    assert "Reason two." in explanation
    assert "Reason three." not in explanation


def test_explain_match_handles_a_dimension_with_no_rationale_entry():
    target = {dim: 0 for dim in DIMENSIONS}
    target["spice"] = 8
    dish = {"vector": {dim: 0 for dim in DIMENSIONS}}
    dish["vector"]["spice"] = 9

    explanation = explain_match(target, dish, rationale={})

    assert explanation == "High Spice match."


def test_explain_match_never_crashes_for_any_dish_in_a_realistic_scenario():
    target = {dim: 5 for dim in DIMENSIONS}
    rationale = {dim: f"Because of {dim}." for dim in DIMENSIONS}
    for dish in DISHES:
        explanation = explain_match(target, dish, rationale)
        assert isinstance(explanation, str)
        assert len(explanation) > 0
