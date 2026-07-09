# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-page Streamlit prototype ("Neural Taste Profile") built for **RFP 2 (Zomato)** of a Searce internal intern assignment on AI & Digital Transformation. It's the technical proof-of-concept for one claim: food can be represented as a multi-dimensional **flavor vector** instead of a cuisine label, real-time context (time/mood/activity/craving) can be converted into a target flavor vector, and cosine similarity over those vectors produces better, explainable recommendations than category browsing. The full spec/brief lives in `prompt.md`.

**Hard constraint (do not violate): no LLM/AI API calls anywhere in this app.** All context parsing (including the free-text craving box) is rule-based keyword matching against hardcoded delta tables. This is intentional — deterministic, offline, zero-latency, fully auditable. Don't introduce an OpenAI/Anthropic call or any external inference to "improve" matching or text parsing.

## Commands

```bash
cd app
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py   # http://localhost:8501
```

Tests (`app/tests/`):
```bash
cd app
.venv/bin/pip install -r requirements-dev.txt   # adds pytest on top of requirements.txt
.venv/bin/pytest                 # runs the whole suite; testpaths is set in pytest.ini
.venv/bin/pytest tests/test_matching_engine.py -v   # a single file
.venv/bin/pytest -k explain_match                   # by name
```

A `Makefile` in `app/` wraps the above: `make install-dev` (venv + all deps), `make run`, `make test` / `make test-verbose`, `make clean`.

There is no linter or backend — this is a static, client-only prototype (no auth, no persistence, no server).

## Architecture (`app/`)

Dataset, engines, charts, and UI are split across five flat modules (no packages/`__init__.py` — Streamlit adds the script's own directory to `sys.path`, so plain top-level imports like `from dishes import DISHES` resolve). Each module is a self-contained stage of the pipeline; `app.py` only wires them to widgets and holds no data or matching logic itself.

1. **`dishes.py`** — the single source of truth for vector shape. `DIMENSIONS` (the canonical list of 14 flavor dimensions: spice, acidity, richness, warmth, crunch, umami, sweetness, bitterness, saltiness, freshness, moisture, aroma, chewiness, temp_contrast — order matters since `vec(...)` builds dish vectors positionally from it), `DIM_LABELS` (display names), and `DISHES` (40 hand-authored dishes across 8 cuisine buckets, each with a 14-dim `vector` plus `cuisine`/`prep_time_minutes`/`meal_type` metadata). Every other module imports `DIMENSIONS`/`DIM_LABELS` from here.
2. **`context_engine.py`** — the Context Engine: hardcoded delta dicts (`TIME_DELTAS`, `MOOD_DELTAS`, `ACTIVITY_DELTAS`, `KEYWORD_DELTAS`) that each map one input signal to a fixed delta across (a subset of) the 14 dimensions, plus `MOODS`/`ACTIVITIES` (the selectable option lists) and the functions that consume them: `get_time_bucket(now)` buckets a datetime's hour into Morning/Afternoon/Evening/Late Night; `compute_target_vector(time_bucket, mood, activities, free_text)` starts from a neutral baseline (5 on every dimension), sums in the deltas for every active input, does substring keyword matching against `KEYWORD_DELTAS`, and clamps to 0–10 — it also returns a `contributions` list (source → delta) used by `explain_match` in `matching_engine.py`. The delta dicts are intentionally explicit and flat (no computed/hidden logic) — that transparency is the "auditability" story for the RFP, so keep new rules in the same explicit style rather than deriving them dynamically. `KEYWORD_DELTAS` has 31 entries mapping free-text substrings (e.g. "crunchy", "tangy") to deltas — matching is plain case-insensitive substring search, no NLP.
3. **`matching_engine.py`** — the Matching Engine: `cosine_similarity(vec_a, vec_b)` (numpy) and `rank_dishes(target_vector, dishes)` do the actual matching; `explain_match(target_vector, dish, contributions)` finds the top 2–3 dimensions by `target*dish` product and traces each back to whichever input contributed the most delta to it, producing the "why this matched" string.
4. **`charts.py`** — `make_radar_chart(vector, title)` builds a Plotly `Scatterpolar` figure from a 14-dim vector dict. The only module with no equivalent purpose crossover with the others.
5. **`app.py`** — Streamlit UI only: mood via `st.radio` (single-select, `index=None` so nothing is pre-selected), activities via `st.multiselect`, craving via `st.text_input`, time bucket read once per run via `datetime.now()`. Since Streamlit reruns the whole script on every widget interaction, match results are stored in `st.session_state.results` on "Find My Meal" clicks so they persist across unrelated reruns (e.g. typing in the craving box) instead of disappearing.

All of `dishes.py`, `context_engine.py`, and `matching_engine.py` are plain, side-effect-free functions/data with no Streamlit calls — that's deliberate, so the matching logic can be imported and tested independently of the running app.

### Adding a dish
Append to `DISHES` in `dishes.py` using `vec(...)` with 14 positional values in the exact `DIMENSIONS` order. Scores should stay plausible relative to existing dishes in the same cuisine bucket.

### Adding a context rule
In `context_engine.py`, add a new key to `TIME_DELTAS` / `MOOD_DELTAS` / `ACTIVITY_DELTAS` (and the corresponding `MOODS`/`ACTIVITIES` list if it's a new selectable option), or a new keyword to `KEYWORD_DELTAS`. Only set the dimensions the rule actually affects — omitted dimensions default to a delta of 0 via `_add_delta`.

### Verifying logic changes
Prefer running the test suite (`pytest`) over ad-hoc scripts — `tests/` already imports `context_engine`/`matching_engine`/`dishes` directly (no `streamlit` stub needed, since those three modules never import `streamlit`) and covers dataset shape, delta-table coverage, boundary conditions, and explanation attribution. Add a test alongside the existing ones in the matching module's test file rather than writing a throwaway script.

Run `.venv/bin/pip install -r requirements.txt` after editing `requirements.txt`; keep it to `streamlit`, `numpy`, `plotly` only. `requirements-dev.txt` layers `pytest` on top for the test suite — don't add test-only deps to `requirements.txt`.

## Tests (`app/tests/`)

`conftest.py` puts `app/` on `sys.path` so test files import the app modules as plain top-level modules (`from dishes import DISHES`) regardless of the directory `pytest` is invoked from.

- **`test_dishes.py`** — dataset shape: dish count, unique ids/names, all 14 dims present and in 0–10, required metadata, `vec()` positional mapping.
- **`test_context_engine.py`** — delta-table coverage (every mood/activity has a delta entry), `get_time_bucket` boundary conditions (parametrized across all 4 bucket edges), `compute_target_vector` baseline/clamping/case-insensitive keyword matching/no-mood handling, and that `contributions` records one entry per active input signal.
- **`test_matching_engine.py`** — `cosine_similarity` properties (self=1, symmetric, no div-by-zero on a zero vector), `rank_dishes` ordering, and `explain_match` correctness with small hand-constructed vectors (so the expected dimension/source attribution is known exactly, not just "didn't crash").
- **`test_charts.py`** — `make_radar_chart` returns a `plotly.graph_objects.Figure`, closes the polygon (first point repeated at the end), and handles every dish in the dataset.
- **`test_app.py`** — integration tests that run the *actual* `app.py` headlessly via Streamlit's official `streamlit.testing.v1.AppTest` harness (no browser): sets widget values (`at.radio[0].set_value(...)`, `at.multiselect[0].set_value(...)`, `at.text_input[0].set_value(...)`), clicks `at.button[0].click().run()`, and asserts on the rendered markdown. Covers the no-mood-selected path, session-state persistence across an unrelated rerun, and that different moods produce different top-5 results. One scenario (Stressed + "Long day at work" + "something crunchy and tangy") asserts the top result against an expectation computed independently in the test via `context_engine`/`matching_engine` (rather than a hardcoded percentage) — the app's time bucket comes from `datetime.now()`, so a fixed number would be flaky depending on time of day.

When adding a dish or a context rule (see above), add or extend a test in the matching file rather than only manually re-running the app.
