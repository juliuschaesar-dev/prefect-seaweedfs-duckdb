"""Streamlit dashboard: multi-city weather trends, queried via DuckDB + httpfs."""
from __future__ import annotations

import streamlit as st

from common.config import settings
from common.duckdb_conn import get_connection

st.set_page_config(page_title="Weather Analytics", layout="wide")
st.title("Weather Analytics Dashboard")

MART_GLOB = f"s3://{settings.s3_bucket}/mart/weather/dt=*/data.parquet"

con = get_connection()

st.subheader("Temperature Trend by City")
temp_df = con.execute(
    f"""
    SELECT city, timestamp, temperature
    FROM read_parquet('{MART_GLOB}', hive_partitioning=1)
    ORDER BY timestamp
    """
).pl()
st.line_chart(temp_df, x="timestamp", y="temperature", color="city")

st.subheader("Precipitation Comparison by City")
precip_df = con.execute(
    f"""
    SELECT city, date_trunc('day', timestamp) AS day, sum(precipitation) AS total_precipitation
    FROM read_parquet('{MART_GLOB}', hive_partitioning=1)
    GROUP BY city, day
    ORDER BY day
    """
).pl()
st.bar_chart(precip_df, x="day", y="total_precipitation", color="city")

st.subheader("Summary Stats")
summary_df = con.execute(
    f"""
    SELECT
        city,
        avg(temperature) AS avg_temperature,
        max(temperature) AS max_temperature,
        min(temperature) AS min_temperature,
        sum(precipitation) AS total_precipitation,
        avg(windspeed) AS avg_windspeed
    FROM read_parquet('{MART_GLOB}', hive_partitioning=1)
    GROUP BY city
    ORDER BY city
    """
).pl()
st.dataframe(summary_df, use_container_width=True)
