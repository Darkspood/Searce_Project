"""
Neural Taste Profile — Zomato "Discovery Fatigue" prototype (Streamlit UI).

Dishes are scored on 14 flavor dimensions instead of cuisine tags (dishes.py).
Real-time context — location/weather (weather_client.py), a simulated
smartwatch connection, a short mood quiz (context_engine.py), and a free-text
craving — is fused into a target flavor vector by a single Claude API call
(llm_context_engine.py), which also returns a per-dimension rationale so the
match is never a black box. A Matching Engine ranks dishes by cosine
similarity against that target (matching_engine.py). This file only wires
those pieces to Streamlit widgets — no data, fusion, or matching logic lives
here.

The LLM's role is scoped strictly to producing the target vector + rationale
from context. Dish data, cosine similarity, and ranking remain plain
deterministic code. If the LLM call fails for any reason, a deterministic
fallback vector is used instead and clearly signaled in the UI — see
llm_context_engine.get_target_vector().
"""

from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

import llm_context_engine
import weather_client
from charts import make_radar_chart
from context_engine import QUIZ_QUESTIONS, get_time_bucket
from dishes import DISHES
from matching_engine import explain_match, rank_dishes

load_dotenv()  # populates ANTHROPIC_API_KEY from app/.env before any API call is made

st.set_page_config(page_title="Neural Taste Profile", page_icon="🍽️", layout="wide")

st.title("Neural Taste Profile")
st.caption(
    "Real-time context — weather, simulated biometrics, a mood quiz, and a free-text craving — "
    "fused by Claude into a target flavor vector, then matched against 40 dishes by cosine similarity."
)

time_bucket = get_time_bucket(datetime.now())
st.info(f"🕒 Detected context: **{time_bucket}**")

# --- Location & weather -----------------------------------------------------
st.subheader("Where are you?")
city = st.selectbox("City", list(weather_client.PRESET_CITIES.keys()), key="city_select")

if city == "Custom location":
    default_lat, default_lon = next(iter(weather_client.PRESET_CITIES.values()))
    lat = st.number_input("Latitude", value=default_lat, key="custom_lat")
    lon = st.number_input("Longitude", value=default_lon, key="custom_lon")
else:
    lat, lon = weather_client.PRESET_CITIES[city]

if "weather_data" not in st.session_state:
    st.session_state.weather_data = None

if st.button("Check Weather", key="check_weather_btn"):
    st.session_state.weather_data = weather_client.get_current_weather(lat, lon)
    if st.session_state.weather_data is None:
        st.warning("Couldn't reach the weather service — continuing without a weather signal.")

if st.session_state.weather_data:
    w = st.session_state.weather_data
    st.caption(f"🌡️ {w['temperature_c']}°C · weather code {w['weather_code']}")

# --- Simulated smartwatch ----------------------------------------------------
st.subheader("Connect smartwatch")
smartwatch_connected = st.checkbox("Connect smartwatch (simulated)", key="smartwatch_checkbox")

biometrics = None
if smartwatch_connected:
    hrv = st.slider("Heart rate variability (ms)", 20, 120, 60, key="hrv_slider")
    calories_burned = st.slider("Calories burned today", 0, 1500, 300, key="calories_slider")
    sleep_score = st.slider("Sleep score", 0, 100, 70, key="sleep_slider")
    biometrics = {"hrv": hrv, "calories_burned": calories_burned, "sleep_score": sleep_score}

# --- Mood quiz ---------------------------------------------------------------
st.subheader("A few quick questions")
quiz_answers = {}
for q in QUIZ_QUESTIONS:
    quiz_answers[q["key"]] = st.radio(
        q["question"], q["options"], index=None, key=q["key"], horizontal=True
    )

# --- Craving -------------------------------------------------------------
st.subheader("Craving anything specific?")
craving = st.text_input(
    "Craving",
    placeholder="e.g. something crunchy and tangy",
    key="craving_input",
    label_visibility="collapsed",
)

find_meal = st.button("Find My Meal", type="primary", width="stretch", key="find_meal_btn")

if "results" not in st.session_state:
    st.session_state.results = None

if find_meal:
    with st.spinner("Reading the vibe..."):
        payload = llm_context_engine.build_context_payload(
            time_bucket, st.session_state.weather_data, biometrics, quiz_answers, craving
        )
        result = llm_context_engine.get_target_vector(payload)

    ranked = rank_dishes(result.vector, DISHES)[:5]
    ranked_with_explanations = [
        {**entry, "explanation": explain_match(result.vector, entry["dish"], result.rationale)}
        for entry in ranked
    ]
    st.session_state.results = {
        "ranked": ranked_with_explanations,
        "used_fallback": result.source == "fallback",
        "fallback_error": result.error,
        "weather_used": st.session_state.weather_data is not None,
        "quiz_answers": quiz_answers,
        "craving": craving,
    }

results = st.session_state.results

if results:
    if results["used_fallback"]:
        st.warning(
            "Using fallback — AI service unavailable. Recommendations are based on a "
            "simplified deterministic baseline, not full context fusion."
        )
        with st.expander("Why fallback?"):
            st.code(results["fallback_error"] or "Unknown error")

    signals = [time_bucket]
    if results["weather_used"]:
        signals.append("weather")
    signals.extend(a for a in results["quiz_answers"].values() if a)
    if results["craving"]:
        signals.append(f'craving: "{results["craving"]}"')
    st.markdown(f"**Signals used:** {', '.join(signals)}")

    st.divider()

    columns = st.columns(2)
    for i, entry in enumerate(results["ranked"]):
        dish = entry["dish"]
        with columns[i % 2]:
            with st.container(border=True):
                st.caption(f"#{i + 1} MATCH")
                st.markdown(f"### {dish['name']}")
                st.caption(f"{dish['cuisine']} · {dish['prep_time_minutes']} min")
                st.markdown(f":green[{entry['score'] * 100:.1f}% similarity]")
                st.plotly_chart(make_radar_chart(dish["vector"], dish["name"]), width="stretch")
                st.info(entry["explanation"])
else:
    st.markdown("_Answer a few questions and hit **Find My Meal** to see your matches._")
