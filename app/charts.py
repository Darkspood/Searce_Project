"""Chart building — Plotly radar (Scatterpolar) figures for flavor vectors."""

import plotly.graph_objects as go

from dishes import DIMENSIONS, DIM_LABELS


def make_radar_chart(vector, title=""):
    """Builds a Plotly radar (Scatterpolar) chart figure for one 14-dim flavor vector."""
    categories = [DIM_LABELS[d] for d in DIMENSIONS]
    values = [vector[d] for d in DIMENSIONS]
    # Close the polygon by repeating the first point at the end.
    categories = categories + [categories[0]]
    values = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name=title,
            line_color="#7c5cff",
            fillcolor="rgba(124, 92, 255, 0.45)",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10], tickfont=dict(size=8))),
        showlegend=False,
        margin=dict(l=30, r=30, t=20, b=20),
        height=280,
    )
    return fig
