"""Streamlit dashboard: multi-city weather trends, queried via DuckDB + httpfs."""
from __future__ import annotations

import altair as alt
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
st.line_chart(temp_df, x="timestamp", y="temperature", color="city", x_label="Time", y_label="Temperature (°C)")

st.subheader("Precipitation Comparison by City")
precip_df = con.execute(
    f"""
    SELECT city, date_trunc('day', timestamp) AS day, sum(precipitation) AS total_precipitation_mm
    FROM read_parquet('{MART_GLOB}', hive_partitioning=1)
    GROUP BY city, day
    ORDER BY day
    """
).pl()

available_days = sorted(precip_df["day"].unique().to_list())
selected_day = st.selectbox(
    "Select day",
    available_days,
    index=len(available_days) - 1,
    format_func=lambda d: d.strftime("%Y-%m-%d"),
)
precip_day_df = precip_df.filter(precip_df["day"] == selected_day).sort(
    "total_precipitation_mm", descending=True
)
precip_base = alt.Chart(precip_day_df).encode(
    x=alt.X("city:N", sort="-y", title="City"),
    y=alt.Y("total_precipitation_mm:Q", title="Total Precipitation (mm)"),
)
precip_bars = precip_base.mark_bar().encode(color=alt.Color("city:N", legend=None))
precip_labels = precip_base.mark_text(dy=-8, color="white").encode(
    text=alt.Text("total_precipitation_mm:Q", format=".1f")
)
st.altair_chart(precip_bars + precip_labels, use_container_width=True)

st.subheader("Summary Stats")
summary_df = con.execute(
    f"""
    SELECT
        city AS "City",
        avg(temperature) AS "Avg Temperature (°C)",
        max(temperature) AS "Max Temperature (°C)",
        min(temperature) AS "Min Temperature (°C)",
        sum(precipitation) AS "Total Precipitation (mm)",
        avg(windspeed) AS "Avg Windspeed (km/h)"
    FROM read_parquet('{MART_GLOB}', hive_partitioning=1)
    GROUP BY city
    ORDER BY avg(temperature) DESC
    """
).pl()
st.dataframe(summary_df, use_container_width=True)
