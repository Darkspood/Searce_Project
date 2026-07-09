# Prompt for Claude Code: Zomato "Neural Taste Profile" Prototype

## Context

This is a prototype for **RFP 2 (Zomato)** of a Searce internal intern assignment ("AI & Digital Transformation RFPs"). The RFP asks us to solve "Discovery Fatigue" — the fact that food recommendation apps treat every user the same regardless of their real-time context (mood, time of day, recent activity), and categorize food by broad cuisine labels instead of actual flavor properties.

The full RFP response needs a To-Be Process, GCP architecture, BOM, ROI, and timeline — **this prototype is only the technical proof-of-concept** for the core claim: food can be represented as a "Flavor Vector" (not a cuisine label), context can be turned into a target flavor vector, and cosine similarity matching produces better, explainable recommendations than category browsing.

**Hard constraint: this prototype must be fully deterministic. Do NOT call any LLM/AI API anywhere in the logic.** No OpenAI, no Anthropic API, no external inference calls of any kind. Free-text parsing must use rule-based keyword matching, not a model. This is intentional — it keeps the demo reliable (no network dependency, no latency, no hallucination risk) and mirrors an explicit requirement from a sibling RFP in this same assignment (deterministic-only extraction for regulated logic). Everything else in this app must run instantly, client-side, in-memory.

## What to build

A single-page web app (React, single file) that demonstrates:
1. Dishes represented as multi-dimensional **Flavor Vectors** instead of cuisine tags.
2. A **Context Engine** that deterministically converts time of day, mood, activity, and free-text cravings into a target flavor vector.
3. A **Matching Engine** that ranks dishes by cosine similarity against that target vector.
4. A **"Why" explanation** per result, so the match is never a black box.

## 1. Data Layer — Dish Dataset

- Build **35–40 dishes** spanning a wide cuisine spread: North Indian, South Indian, Chinese, Italian, Continental, Fast Food, Desserts, Beverages (roughly 4-6 dishes per cuisine bucket).
- Each dish is scored **0–10** on **14 flavor dimensions**:
  1. spice
  2. acidity
  3. richness (heaviness)
  4. warmth (serving temperature — hot vs cold, not spice)
  5. crunch (texture)
  6. umami
  7. sweetness
  8. bitterness
  9. saltiness
  10. freshness
  11. moisture / juiciness
  12. aroma-intensity
  13. chewiness
  14. temperature-contrast (hot/cold elements combined in one dish)
- Each dish also has metadata: `name`, `cuisine`, `prepTimeMinutes`, `mealType` (breakfast/lunch/dinner/snack/dessert/beverage — can be multiple).
- Store this as a structured JS array/JSON at the top of the file — hand-authored is fine, values should be *plausible* for each dish (e.g., a fiery Chicken 65 should score high spice/crunch/umami, low sweetness).

## 2. Context Engine (fully rule-based — no ML)

### Inputs
- **Time of day**: auto-read from the browser clock (`new Date()`), bucketed into e.g. Morning / Afternoon / Evening / Late Night.
- **Mood chips** (single-select, pick one of 8): Stressed, Relaxed, Tired, Energized, Anxious, Celebratory, Nostalgic, Bored.
- **Activity toggles** (multi-select, pick any of 6): Just worked out, Long day at work, Lazy Sunday, Traveling, Sick / unwell, Hosting guests.
- **Free-text craving box**: e.g. "something crunchy and tangy." Parsed via **keyword matching only** — maintain a keyword → flavor-dimension delta lookup table (e.g. "crunchy"/"crispy" → +crunch, "tangy"/"acidic"/"sour" → +acidity, "spicy"/"hot" → +spice, "comfort"/"cozy" → +warmth +richness, "juicy" → +moisture, "fragrant"/"aromatic" → +aroma-intensity, "burnt"/"bitter" → +bitterness, "sweet" → +sweetness, "light"/"fresh" → +freshness -richness, "salty" → +saltiness, "chewy" → +chewiness). Build at least ~2 keyword mappings per flavor dimension (~25-30 keyword entries total).

### Logic
- Each input source (time bucket, mood, each selected activity, matched free-text keywords) contributes a **fixed, hardcoded delta vector** across the 14 dimensions.
  - Example: Late Night + Stressed → strong +warmth, +richness, +sweetness, -spice, -freshness (comfort-food bias).
  - Example: Just worked out → +freshness, +moisture, -richness, +umami (protein/light bias).
- Sum all contributing deltas into one **Target Flavor Vector**, applying a simple clamp (e.g., 0–10) so it never runs out of range.
- Keep every delta table as an explicit, readable JS object — no hidden logic. This transparency is a deliberate design goal (it's the "auditability" story for the RFP).

## 3. Matching Engine

- Compute **cosine similarity** between the Target Flavor Vector and every dish's Flavor Vector (standard 14-dim cosine similarity, plain JS — no libraries needed).
- Return **top 5 ranked dishes**.
- For each result, identify the **2-3 flavor dimensions that contributed most** to the match (e.g., largest products between target and dish vector components) and generate a plain-language explanation string referencing the *input signals* that drove those dimensions (e.g., "High warmth + richness match — because it's Late Night and you're Stressed").

## 4. UI / UX

- Single-page layout, top to bottom:
  1. Auto-detected context bar (current time bucket, shown read-only).
  2. Mood chip selector (single-select, visually distinct when active).
  3. Activity toggle group (multi-select).
  4. Free-text craving input box.
  5. "Find My Meal" button.
  6. Ranked results: 5 dish cards, each showing:
     - Dish name, cuisine, prep time.
     - A small **radar/spider chart** of its 14-dimension flavor vector (use `recharts`, which is available in this environment — a radar chart suits 14 dimensions much better than bars).
     - The plain-language "why this matched" explanation.
- Clean, modern styling. No login, no persistence, no backend — everything is in-memory React state.
- This is a **prototype/demo artifact**, not a production app — prioritize clarity of the underlying logic being demonstrated over polish, but it should still look credible in front of a jury.

## 5. Explicitly Out of Scope (do not build)

- No LLM/AI API calls anywhere.
- No wearable/health data integration (real version would be a GCP architecture diagram box only — Fit API → Pub/Sub — not code here).
- No real vector database (in-memory cosine similarity over ~40 dishes is fine and instant).
- No backend, no auth, no data persistence across sessions.

## 6. Suggested build order (if doing this incrementally)

1. Dish dataset (35-40 dishes × 14 dimensions + metadata) as a static array.
2. Context delta tables (time buckets, 8 moods, 6 activities, ~25-30 keyword rules) as static objects.
3. Pure functions: `getContextBucket(date)`, `computeTargetVector(selections)`, `cosineSimilarity(vecA, vecB)`, `rankDishes(target, dishes)`, `explainMatch(target, dish)`.
4. Wire up React state for chip/toggle/text selections → call the pure functions → render ranked results.
5. Add radar chart visualization per result card.
6. Polish styling last.

## 7. Success criteria for this prototype

- Selecting different moods/times/activities visibly changes the ranked results (proves the vectors aren't collapsing to the same answer).
- The "why" explanation is legible and traceable to actual selected inputs — not generic filler text.
- Runs entirely client-side with zero network calls and no perceptible latency.
