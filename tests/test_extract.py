from datetime import date

import httpx
import pytest

from pipeline.tasks.extract import fetch_weather

SAMPLE_RESPONSE = {
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
        "temperature_2m": [25.0, 24.5],
        "precipitation": [0.0, 0.1],
        "windspeed_10m": [5.0, 5.5],
        "cloudcover": [10, 20],
    }
}


def test_fetch_weather_tags_city_and_returns_payload(monkeypatch):
    def fake_get(url, params, timeout):
        return httpx.Response(200, json=SAMPLE_RESPONSE, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    result = fetch_weather(
        city="Jakarta",
        lat=-6.2088,
        lon=106.8456,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
        base_url="https://api.open-meteo.com/v1/forecast",
    )

    assert result["city"] == "Jakarta"
    assert result["hourly"]["temperature_2m"] == [25.0, 24.5]


def test_fetch_weather_raises_on_http_error(monkeypatch):
    def fake_get(url, params, timeout):
        return httpx.Response(500, json={}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError):
        fetch_weather(
            city="Jakarta",
            lat=-6.2088,
            lon=106.8456,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            base_url="https://api.open-meteo.com/v1/forecast",
        )
