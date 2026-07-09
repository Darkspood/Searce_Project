"""
Integration tests for app.py, driven through Streamlit's official AppTest
harness (streamlit.testing.v1) — runs the real UI script headlessly, without
a browser, and lets us click/type/select exactly like a user would.
"""

from datetime import datetime
from pathlib import Path

from streamlit.testing.v1 import AppTest

from context_engine import compute_target_vector, get_time_bucket
from dishes import DISHES
from matching_engine import rank_dishes

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_runs_without_raising():
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception


def test_default_state_shows_empty_state_prompt():
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert any("Find My Meal" in m.value for m in at.markdown)
    # No mood is pre-selected.
    assert at.radio[0].value is None


def test_find_my_meal_with_no_selections_still_returns_five_results():
    at = AppTest.from_file(APP_PATH)
    at.run()
    at.button[0].click().run()
    assert not at.exception
    assert sum(1 for m in at.markdown if m.value.startswith("### ")) == 5


def test_full_scenario_matches_independently_computed_expected_top_result():
    at = AppTest.from_file(APP_PATH)
    at.run()

    at.radio[0].set_value("Stressed")
    at.multiselect[0].set_value(["Long day at work"])
    at.text_input[0].set_value("something crunchy and tangy")
    at.button[0].click().run()

    assert not at.exception
    markdown_values = [m.value for m in at.markdown]

    signals_line = next(v for v in markdown_values if v.startswith("**Signals used:**"))
    assert "Stressed" in signals_line
    assert "Long day at work" in signals_line
    assert "'tangy'" in signals_line
    assert "'crunchy'" in signals_line

    # The app derives its time bucket from datetime.now(), so the expected
    # top result and score are computed here the same way rather than
    # hardcoded — a fixed expectation would be flaky depending on what time
    # of day the suite runs (time-of-day deltas shift every dish's score).
    time_bucket = get_time_bucket(datetime.now())
    target_vector, _, _ = compute_target_vector(
        time_bucket, "Stressed", ["Long day at work"], "something crunchy and tangy"
    )
    ranked = rank_dishes(target_vector, DISHES)
    top_entry = ranked[0]
    top_dish, top_score = top_entry["dish"], top_entry["score"]

    assert any(top_dish["name"] in v for v in markdown_values)
    assert any(f"{top_score * 100:.1f}% similarity" in v for v in markdown_values)


def test_results_persist_across_an_unrelated_rerun():
    """Changing the craving text after clicking Find My Meal should not
    wipe the previously computed results (they live in st.session_state)."""
    at = AppTest.from_file(APP_PATH)
    at.run()

    at.radio[0].set_value("Energized")
    at.button[0].click().run()
    assert any("### " in m.value for m in at.markdown)

    # Simulate the user typing in the craving box without clicking the
    # button again — a plain rerun, not a new search.
    at.text_input[0].set_value("just browsing").run()

    assert not at.exception
    assert any("Signals used" in m.value for m in at.markdown)
    assert sum(1 for m in at.markdown if m.value.startswith("### ")) == 5


def test_different_moods_produce_different_top_results():
    def top_result_names(mood, activities):
        at = AppTest.from_file(APP_PATH)
        at.run()
        at.radio[0].set_value(mood)
        at.multiselect[0].set_value(activities)
        at.button[0].click().run()
        assert not at.exception
        return [m.value for m in at.markdown if m.value.startswith("### ")]

    stressed_results = top_result_names("Stressed", [])
    energized_results = top_result_names("Energized", ["Just worked out"])

    assert stressed_results != energized_results
