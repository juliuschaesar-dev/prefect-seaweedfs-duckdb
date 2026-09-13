"""raw -> staging cleaning, and staging -> mart finalization."""
from __future__ import annotations

import polars as pl


def flatten_weather(raw_df: pl.DataFrame) -> pl.DataFrame:
    """Clean raw layer's columnar hourly data into a tidy staging table."""
    return (
        raw_df.rename(
            {
                "time": "timestamp",
                "temperature_2m": "temperature",
                "windspeed_10m": "windspeed",
            }
        )
        .with_columns(pl.col("timestamp").str.to_datetime())
        .select(["city", "timestamp", "temperature", "precipitation", "windspeed", "cloudcover"])
    )


def finalize_weather(staging_df: pl.DataFrame) -> pl.DataFrame:
    """Dedupe and sort the staging table into the final mart table."""
    return staging_df.unique(subset=["city", "timestamp"]).sort(["city", "timestamp"])
