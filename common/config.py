"""Loads .env once and exposes a single typed Settings object."""
from __future__ import annotations

from dataclasses import dataclass

from dotenv import load_dotenv
import os

load_dotenv()

# Open-Meteo requires lat/lon per location; not user-configurable via .env
# since adding a city means adding coordinates, not just a name.
CITY_COORDINATES: dict[str, tuple[float, float]] = {
    "Jakarta": (-6.2088, 106.8456),
    "Surabaya": (-7.2575, 112.7521),
    "Bandung": (-6.9175, 107.6191),
    "Medan": (3.5952, 98.6722),
    "Semarang": (-6.9932, 110.4203),
    "Makassar": (-5.1477, 119.4327),
    "Palembang": (-2.9761, 104.7754),
    "Depok": (-6.4025, 106.7942),
    "Tangerang": (-6.1783, 106.6319),
    "Tangerang Selatan": (-6.2884, 106.7183),
    "Bekasi": (-6.2349, 106.9896),
    "Batam": (1.0456, 104.0305),
    "Bogor": (-6.5971, 106.8060),
    "Pekanbaru": (0.5071, 101.4478),
    "Bandar Lampung": (-5.4292, 105.2610),
    "Padang": (-0.9471, 100.4172),
    "Malang": (-7.9666, 112.6326),
    "Denpasar": (-8.6705, 115.2126),
    "Samarinda": (-0.5022, 117.1536),
    "Banjarmasin": (-3.3186, 114.5944),
}


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    s3_endpoint: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str
    s3_use_ssl: bool

    openmeteo_forecast_url: str
    openmeteo_archive_url: str

    cities: list[str]

    def city_coordinates(self, city: str) -> tuple[float, float]:
        try:
            return CITY_COORDINATES[city]
        except KeyError as exc:
            raise ValueError(f"No coordinates configured for city: {city}") from exc


def load_settings() -> Settings:
    return Settings(
        s3_endpoint=os.environ["S3_ENDPOINT"],
        s3_access_key=os.environ["S3_ACCESS_KEY"],
        s3_secret_key=os.environ["S3_SECRET_KEY"],
        s3_bucket=os.environ["S3_BUCKET"],
        s3_use_ssl=os.environ.get("S3_USE_SSL", "false").lower() == "true",
        openmeteo_forecast_url=os.environ["OPENMETEO_FORECAST_URL"],
        openmeteo_archive_url=os.environ["OPENMETEO_ARCHIVE_URL"],
        cities=_split_csv(os.environ["CITIES"]),
    )


settings = load_settings()
