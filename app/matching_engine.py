"""
Matching Engine — cosine-similarity ranking of dishes against a target
flavor vector, plus the "why this matched" explanation generator.
"""

import numpy as np

from dishes import DIMENSIONS, DIM_LABELS


def cosine_similarity(vec_a, vec_b):
    """Standard 14-dim cosine similarity between two flavor-vector dicts."""
    a = np.array([vec_a[d] for d in DIMENSIONS], dtype=float)
    b = np.array([vec_b[d] for d in DIMENSIONS], dtype=float)
    mag_a = np.linalg.norm(a)
    mag_b = np.linalg.norm(b)
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return float(np.dot(a, b) / (mag_a * mag_b))


def rank_dishes(target_vector, dishes):
    """Scores every dish against the target vector and returns them sorted best-first."""
    scored = [{"dish": dish, "score": cosine_similarity(target_vector, dish["vector"])} for dish in dishes]
    return sorted(scored, key=lambda entry: entry["score"], reverse=True)


def explain_match(target_vector, dish, rationale):
    """
    Builds the plain-language "why this matched" string for one dish.

    Finds the 2-3 dimensions with the largest target*dish product (i.e. the
    dimensions that contributed most to the cosine similarity score) — this
    part stays deterministic and instant, no LLM call needed at explain-time
    — then pulls the explanation text for those dimensions from `rationale`
    (per-dimension strings authored by the LLM, or by the deterministic
    fallback when the LLM call failed). The explanation names both the
    matched dimensions and why the target vector emphasized them, so the
    match is never a black box.
    """
    products = sorted(
        ({"dim": dim, "product": target_vector[dim] * dish["vector"][dim]} for dim in DIMENSIONS),
        key=lambda entry: entry["product"],
        reverse=True,
    )
    top_dims = [entry["dim"] for entry in products if entry["product"] > 0][:3]

    if not top_dims:
        return "Broad match across your current context."

    dim_phrase = " + ".join(DIM_LABELS[d] for d in top_dims)
    reasons = [rationale[d].strip() for d in top_dims if rationale.get(d)]
    reason_phrase = " ".join(reasons[:2])  # cap to keep the card readable

    if not reason_phrase:
        return f"High {dim_phrase} match."

    return f"High {dim_phrase} match — {reason_phrase}"
