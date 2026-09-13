"""Open-Meteo API calls — one function reused by daily flow and backfill script."""
from __future__ import annotations

from datetime import date

import httpx

HOURLY_FIELDS = "temperature_2m,precipitation,windspeed_10m,cloudcover"


def fetch_weather(
    city: str,
    lat: float,
    lon: float,
    start_date: date,
    end_date: date,
    base_url: str,
) -> dict:
    """Fetch hourly weather for a city/date range from an Open-Meteo endpoint.

    `base_url` selects forecast vs. archive API; both share the same response shape.
    """
    response = httpx.get(
        base_url,
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": HOURLY_FIELDS,
            "timezone": "UTC",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    payload["city"] = city
    return payload
