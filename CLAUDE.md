# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single-page Streamlit prototype ("Neural Taste Profile") built for **RFP 2 (Zomato)** of a Searce internal intern assignment on AI & Digital Transformation. It's the technical proof-of-concept for one claim: food can be represented as a multi-dimensional **flavor vector** instead of a cuisine label, real-time context (weather, simulated biometrics, mood, craving) can be fused into a target flavor vector, and cosine similarity over those vectors produces better, explainable recommendations than category browsing.

**The context-fusion step is LLM-driven, not rule-based.** Earlier versions of this prototype used hardcoded delta tables for every input signal (time/mood/activity/keyword). That approach has been replaced: `llm_context_engine.py` sends the full real-time context (time of day, weather, simulated smartwatch biometrics, mood-quiz answers, free-text craving) to the Claude API in a single call and gets back the 14-dimension target flavor vector **plus a per-dimension rationale**, so the "why this matched" explanation stays legible instead of becoming a black box. This is the one place in the app that calls an external LLM — everything downstream (`matching_engine.py`) remains plain deterministic code, and a deterministic fallback exists for when the API call fails (see below). Don't reintroduce a parallel rule-based context-fusion path outside this scope; extend `llm_context_engine.py`'s prompt/schema instead.

## Commands

```bash
cd app
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
.venv/bin/streamlit run app.py   # http://localhost:8501
```

Without `ANTHROPIC_API_KEY` set, the app still runs — it just always shows the fallback banner and uses the deterministic baseline vector instead of the LLM-authored one. `app.py` calls `load_dotenv()` at startup, which reads `app/.env` (gitignored; `app/.env.example` is the committed template).

Tests (`app/tests/`):
```bash
cd app
.venv/bin/pip install -r requirements-dev.txt   # adds pytest on top of requirements.txt
.venv/bin/pytest                 # runs the whole suite; testpaths is set in pytest.ini
.venv/bin/pytest tests/test_matching_engine.py -v   # a single file
.venv/bin/pytest -k explain_match                   # by name
```

The test suite makes **zero** real network or API calls — every Claude API call and every Open-Meteo call is monkeypatched (see "Tests" below). It runs the same with or without `ANTHROPIC_API_KEY` set.

A `Makefile` in `app/` wraps the above: `make install-dev` (venv + all deps), `make run`, `make test` / `make test-verbose`, `make clean`.

There is no linter or backend — this is a static prototype with one external network dependency (the Claude API call) and one optional one (Open-Meteo weather), no auth, no persistence, no server of its own.

## Architecture (`app/`)

Dataset, engines, charts, and UI are split across flat modules (no packages/`__init__.py` — Streamlit adds the script's own directory to `sys.path`, so plain top-level imports like `from dishes import DISHES` resolve). Each module is a self-contained stage of the pipeline; `app.py` only wires them to widgets and holds no data or matching logic itself.

1. **`dishes.py`** — the single source of truth for vector shape. `DIMENSIONS` (the canonical list of 14 flavor dimensions: spice, acidity, richness, warmth, crunch, umami, sweetness, bitterness, saltiness, freshness, moisture, aroma, chewiness, temp_contrast — order matters since `vec(...)` builds dish vectors positionally from it), `DIM_LABELS` (display names), and `DISHES` (40 hand-authored dishes across 8 cuisine buckets, each with a 14-dim `vector` plus `cuisine`/`prep_time_minutes`/`meal_type` metadata). Every other module imports `DIMENSIONS`/`DIM_LABELS` from here.
2. **`context_engine.py`** — now a small module: `get_time_bucket(now)` buckets a datetime's hour into Morning/Afternoon/Evening/Late Night; `TIME_DELTAS` is a fixed delta table (kept from the old rule-based design) that does double duty as a labeled input sent to the LLM and as the backbone of the deterministic fallback vector; `QUIZ_QUESTIONS` is the mood-quiz question bank (a handful of optional multiple-choice questions, replacing the old single mood chip + activity multiselect); `add_delta`/`clamp_vector` are small vector utilities shared with `llm_context_engine.py`'s fallback path.
3. **`weather_client.py`** — calls Open-Meteo's free current-weather endpoint for a lat/lon. `PRESET_CITIES` is the dropdown of major Indian cities (plus a "Custom location" option). `get_current_weather(lat, lon)` returns a dict on success or `None` on **any** failure (network error, timeout, unexpected response shape) — it never raises. A weather-fetch failure is a small, separate failure surface from the LLM fallback below: `app.py` just omits weather from the context payload and shows a small warning.
4. **`llm_context_engine.py`** — the Context Engine, and the only module that calls an external LLM. `build_context_payload(...)` assembles the structured dict (time bucket, weather-or-`None`, biometrics-or-`None`, quiz answers, craving text) sent as the user-turn content. `FlavorVectorResponse` (a Pydantic model, one `DimensionScore(value, rationale)` field per dimension in `DIMENSIONS`) is passed as `output_format` to `client.messages.parse(...)` (model: `claude-sonnet-5`) — Sonnet 5 runs adaptive thinking on by default, which is why no extra `thinking` config is needed for "decent reasoning depth." `DimensionScore`'s `value` field clamps to `[0, 10]` via a `field_validator` rather than rejecting the whole response over one out-of-range number (the API's JSON schema strips numeric range constraints before it reaches the model, so the 0-10 instruction lives in the system prompt as text, backed by this client-side clamp). `get_target_vector(context_payload)` wraps the whole call in a broad `try/except` — any failure (network, rate limit, refusal, malformed response, timeout) routes to `_fallback_vector_and_rationale(...)`, a small deterministic computation (`{dim: 5} + TIME_DELTAS[bucket]` plus a handful of fallback-only quiz-answer and craving-keyword deltas, `FALLBACK_QUIZ_DELTAS`/`FALLBACK_KEYWORD_DELTAS` — deliberately much smaller than the old rule-based tables, kept only so the fallback isn't flatly identical for every user at the same hour). Always returns a `ContextResult(vector, rationale, source, error)` — never raises. `_get_client()` is a small seam (constructs `anthropic.Anthropic()` lazily, not at import time) that tests monkeypatch directly.
5. **`matching_engine.py`** — the Matching Engine: `cosine_similarity(vec_a, vec_b)` (numpy) and `rank_dishes(target_vector, dishes)` do the actual matching — both unchanged by the LLM pivot, fully deterministic; `explain_match(target_vector, dish, rationale)` finds the top 2-3 dimensions by `target*dish` product (still deterministic and instant, no LLM call at explain-time) and pulls the "why this matched" text from `rationale[dim]` — the per-dimension strings authored by the LLM, or by the deterministic fallback when the LLM call failed.
6. **`charts.py`** — `make_radar_chart(vector, title)` builds a Plotly `Scatterpolar` figure from a 14-dim vector dict. Unaffected by the LLM pivot.
7. **`app.py`** — Streamlit UI only. Order: auto-detected time bucket → location + "Check Weather" (its own step/button, fetched *before* "Find My Meal" so the two network calls don't stack into one wait) → "Connect smartwatch" (simulated, sliders for HRV/calories burned/sleep score) → mood quiz (`QUIZ_QUESTIONS`, each optional) → free-text craving → "Find My Meal" (wrapped in `st.spinner`, this is the one click that calls `llm_context_engine.get_target_vector(...)`). Calls `load_dotenv()` at startup. Results (including whether the fallback path fired, and the raw error for a debug expander) are stored in `st.session_state.results` on click, so they persist across unrelated reruns (e.g. typing in the craving box) instead of disappearing. `app.py` calls `llm_context_engine.get_target_vector(...)` and `weather_client.get_current_weather(...)` via qualified module access (`import llm_context_engine`, not `from llm_context_engine import get_target_vector`) — this is the seam that lets tests monkeypatch each function directly.

`dishes.py`, `context_engine.py`, `weather_client.py`, `llm_context_engine.py`, and `matching_engine.py` are all plain, side-effect-free-at-import functions/data with no Streamlit calls — that's deliberate, so this logic can be imported and tested independently of the running app (and, for `weather_client`/`llm_context_engine`, without ever making a real network/API call in tests).

### Adding a dish
Append to `DISHES` in `dishes.py` using `vec(...)` with 14 positional values in the exact `DIMENSIONS` order. Scores should stay plausible relative to existing dishes in the same cuisine bucket.

### Adding a quiz question
Add an entry to `QUIZ_QUESTIONS` in `context_engine.py` (`key`, `question`, `options`). Flavor deltas are no longer hand-authored for the primary path — the LLM interprets quiz answers directly as part of the context payload. If you want the new question's answers to meaningfully affect the *fallback* path too, add corresponding entries to `FALLBACK_QUIZ_DELTAS` in `llm_context_engine.py` (keep it small and explicit, matching the existing entries' style).

### Verifying logic changes
Prefer running the test suite (`pytest`) over ad-hoc scripts. `tests/` imports `dishes`/`context_engine`/`weather_client`/`llm_context_engine`/`matching_engine` directly (no `streamlit` stub needed — none of those five modules import `streamlit`) and covers dataset shape, `TIME_DELTAS`/quiz-question shape, weather-client success/failure (mocked `requests.get`), the LLM context engine's happy path/fallback triggers/clamping (mocked Anthropic client via `_get_client`), and matching/explanation correctness. Add a test alongside the existing ones in the relevant test file rather than writing a throwaway script.

Run `.venv/bin/pip install -r requirements.txt` after editing `requirements.txt`; it now includes `streamlit`, `numpy`, `plotly`, `anthropic`, `requests`, `pydantic`, `python-dotenv`. `requirements-dev.txt` layers `pytest` on top for the test suite — don't add test-only deps to `requirements.txt`.

## Tests (`app/tests/`)

`conftest.py` puts `app/` on `sys.path` so test files import the app modules as plain top-level modules (`from dishes import DISHES`) regardless of the directory `pytest` is invoked from.

- **`test_dishes.py`** — dataset shape: dish count, unique ids/names, all 14 dims present and in 0-10, required metadata, `vec()` positional mapping.
- **`test_context_engine.py`** — `TIME_DELTAS` bucket coverage and dimension validity, `get_time_bucket` boundary conditions (parametrized across all 4 bucket edges), and `QUIZ_QUESTIONS` shape (unique keys, non-empty questions, ≥2 options each).
- **`test_weather_client.py`** — `get_current_weather` mocked against `requests.get`: success (parses the Open-Meteo payload correctly), and returns `None` (never raises) on a connection error, a bad HTTP status, or a malformed payload. No real network calls.
- **`test_llm_context_engine.py`** — `DimensionScore`'s clamping validator (above/below range), `get_target_vector`'s happy path, refusal, and exception paths (all via monkeypatching `_get_client()` to return a fake client — no real Anthropic call), and the deterministic fallback formula (baseline + `TIME_DELTAS` + fallback-only quiz/keyword deltas, and that it stays within 0-10 and actually varies with input).
- **`test_matching_engine.py`** — `cosine_similarity` properties (self=1, symmetric, no div-by-zero on a zero vector), `rank_dishes` ordering, and `explain_match` correctness against hand-built `rationale` dicts (top-dimension selection, the 2-reason cap for readability, graceful handling of a dimension with no rationale entry).
- **`test_charts.py`** — `make_radar_chart` returns a `plotly.graph_objects.Figure`, closes the polygon (first point repeated at the end), and handles every dish in the dataset.
- **`test_app.py`** — integration tests that run the *actual* `app.py` headlessly via Streamlit's official `streamlit.testing.v1.AppTest` harness (no browser, key-based widget lookups like `at.button(key="find_meal_btn")` rather than positional indices, since the widget list has grown). None of these tests make a real Claude API or weather call: `llm_context_engine.get_target_vector` is monkeypatched (module-attribute style — `app.py` calls it via `import llm_context_engine` specifically so this works) to either a fake result (for the mocked-happy-path and "different inputs" tests) or, for the one test that needs an exact numeric expectation, `_get_client` is monkeypatched to raise so the *real* fallback code path runs and can be asserted against an independently-computed expectation — mirroring how `test_llm_context_engine.py` verifies the same formula directly. Also covers: the fallback warning banner (and its debug expander) appearing when forced, and session-state persistence across an unrelated rerun.

When adding a dish or a quiz question (see above), add or extend a test in the relevant test file rather than only manually re-running the app.
