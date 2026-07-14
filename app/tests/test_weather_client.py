"""Tests for weather_client.py — mocked requests.get, no real network calls."""

import requests

import weather_client
from weather_client import PRESET_CITIES, get_current_weather


class _FakeResponse:
    def __init__(self, json_data, status_ok=True):
        self._json_data = json_data
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            raise requests.exceptions.HTTPError("bad status")

    def json(self):
        return self._json_data


def test_preset_cities_has_a_custom_location_option():
    assert "Custom location" in PRESET_CITIES
    assert PRESET_CITIES["Custom location"] is None


def test_get_current_weather_returns_parsed_dict_on_success(monkeypatch):
    fake_payload = {
        "current": {
            "temperature_2m": 28.5,
            "precipitation": 0.0,
            "weather_code": 1,
            "is_day": 1,
        }
    }
    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(fake_payload))

    result = get_current_weather(19.076, 72.8777)

    assert result == {
        "temperature_c": 28.5,
        "precipitation_mm": 0.0,
        "weather_code": 1,
        "is_day": True,
    }


def test_get_current_weather_returns_none_on_connection_error(monkeypatch):
    def _raise(*args, **kwargs):
        raise requests.exceptions.ConnectionError("no network")

    monkeypatch.setattr(requests, "get", _raise)

    assert get_current_weather(19.076, 72.8777) is None


def test_get_current_weather_returns_none_on_bad_http_status(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse({}, status_ok=False))

    assert get_current_weather(19.076, 72.8777) is None


def test_get_current_weather_returns_none_on_malformed_payload(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse({"unexpected": "shape"}))

    assert get_current_weather(19.076, 72.8777) is None
