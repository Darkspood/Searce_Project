"""Tests for charts.py — Plotly radar chart construction."""

import plotly.graph_objects as go

from charts import make_radar_chart
from dishes import DIMENSIONS, DISHES


def test_make_radar_chart_returns_a_plotly_figure():
    fig = make_radar_chart(DISHES[0]["vector"], DISHES[0]["name"])
    assert isinstance(fig, go.Figure)


def test_make_radar_chart_closes_the_polygon():
    fig = make_radar_chart(DISHES[0]["vector"], DISHES[0]["name"])
    trace = fig.data[0]
    # 14 dimensions + 1 repeated point to close the polygon.
    assert len(trace.r) == len(DIMENSIONS) + 1
    assert len(trace.theta) == len(DIMENSIONS) + 1
    assert trace.r[0] == trace.r[-1]
    assert trace.theta[0] == trace.theta[-1]


def test_make_radar_chart_uses_the_full_0_to_10_scale():
    fig = make_radar_chart(DISHES[0]["vector"], DISHES[0]["name"])
    assert fig.layout.polar.radialaxis.range == (0, 10)


def test_make_radar_chart_handles_every_dish_without_crashing():
    for dish in DISHES:
        fig = make_radar_chart(dish["vector"], dish["name"])
        assert isinstance(fig, go.Figure)
