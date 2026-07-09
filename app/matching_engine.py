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


def explain_match(target_vector, dish, contributions):
    """
    Builds the plain-language "why this matched" string for one dish.

    Finds the 2-3 dimensions with the largest target*dish product (i.e. the
    dimensions that contributed most to the cosine similarity score), then
    for each one finds whichever selected input contributed the largest
    positive delta to it. The explanation names both, so the match is never
    a black box.
    """
    products = sorted(
        ({"dim": dim, "product": target_vector[dim] * dish["vector"][dim]} for dim in DIMENSIONS),
        key=lambda entry: entry["product"],
        reverse=True,
    )
    top_dims = [entry["dim"] for entry in products if entry["product"] > 0][:3]

    if not top_dims:
        return "Broad match across your current context."

    source_set = []
    for dim in top_dims:
        best = None
        for c in contributions:
            value = (c["delta"] or {}).get(dim)
            if value and value > 0 and (best is None or value > best["value"]):
                best = {"source": c["source"], "value": value}
        if best and best["source"] not in source_set:
            source_set.append(best["source"])

    dim_phrase = " + ".join(DIM_LABELS[d] for d in top_dims)

    if len(source_set) == 1:
        source_phrase = source_set[0]
    elif len(source_set) > 1:
        source_phrase = f"{', '.join(source_set[:-1])} and {source_set[-1]}"
    else:
        source_phrase = "a broad match across your current context"

    return f"High {dim_phrase} match — driven by {source_phrase}."
