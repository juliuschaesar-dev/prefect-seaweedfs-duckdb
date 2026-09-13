"""Write/read raw, staging, and mart Parquet files on SeaweedFS."""
from __future__ import annotations

from datetime import date

import polars as pl

from common.storage import read_parquet, write_parquet


def raw_path(city: str, dt: date) -> str:
    return f"raw/openmeteo/city={city}/dt={dt.isoformat()}/data.parquet"


def staging_path(dt: date) -> str:
    return f"staging/weather/dt={dt.isoformat()}/data.parquet"


def mart_path(dt: date) -> str:
    return f"mart/weather/dt={dt.isoformat()}/data.parquet"


def write_raw(raw: dict, dt: date) -> None:
    df = pl.DataFrame(raw["hourly"]).with_columns(city=pl.lit(raw["city"]))
    write_parquet(df, raw_path(raw["city"], dt))


def read_raw(city: str, dt: date) -> pl.DataFrame:
    return read_parquet(raw_path(city, dt))


def write_staging(df: pl.DataFrame, dt: date) -> None:
    write_parquet(df, staging_path(dt))


def read_staging(dt: date) -> pl.DataFrame:
    return read_parquet(staging_path(dt))


def write_mart(df: pl.DataFrame, dt: date) -> None:
    write_parquet(df, mart_path(dt))
