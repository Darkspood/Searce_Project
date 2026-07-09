"""Tests for dishes.py — dataset shape and integrity."""

from dishes import DIMENSIONS, DIM_LABELS, DISHES, vec


def test_dish_count_is_35_to_40():
    assert 35 <= len(DISHES) <= 40


def test_dish_ids_are_unique():
    ids = [d["id"] for d in DISHES]
    assert len(ids) == len(set(ids))


def test_dish_names_are_unique():
    names = [d["name"] for d in DISHES]
    assert len(names) == len(set(names))


def test_every_dish_has_all_14_dimensions():
    for dish in DISHES:
        assert set(dish["vector"].keys()) == set(DIMENSIONS), dish["id"]


def test_every_dish_score_is_in_0_to_10_range():
    for dish in DISHES:
        for dim, value in dish["vector"].items():
            assert 0 <= value <= 10, f"{dish['id']}.{dim} = {value}"


def test_every_dish_has_required_metadata():
    for dish in DISHES:
        assert dish.get("cuisine"), dish["id"]
        assert dish.get("prep_time_minutes"), dish["id"]
        assert dish.get("meal_type"), dish["id"]


def test_dim_labels_cover_every_dimension():
    assert set(DIM_LABELS.keys()) == set(DIMENSIONS)


def test_cuisines_span_expected_buckets():
    cuisines = {dish["cuisine"] for dish in DISHES}
    expected = {
        "North Indian", "South Indian", "Chinese", "Italian",
        "Continental", "Fast Food", "Desserts", "Beverages",
    }
    assert expected <= cuisines


def test_vec_maps_positional_values_onto_dimensions_in_order():
    values = list(range(len(DIMENSIONS)))
    result = vec(*values)
    assert result == dict(zip(DIMENSIONS, values))
