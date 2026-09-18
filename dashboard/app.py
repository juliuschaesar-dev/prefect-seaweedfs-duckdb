"""Streamlit dashboard: multi-city weather trends, queried via DuckDB + httpfs."""
from __future__ import annotations

import altair as alt
import polars as pl
import streamlit as st

from common.config import settings
from common.duckdb_conn import get_connection

st.set_page_config(page_title="Weather Analytics", layout="wide")
st.title("Weather Analytics Dashboard")

MART_GLOB = f"s3://{settings.s3_bucket}/mart/weather/dt=*/data.parquet"

MUTED_TEXT = "#8b93a1"
LIGHT_TEXT = "#e5e5e5"
CARD_BG = "#1c1f27"
CELL_BORDER = "#11141c"

con = get_connection()


def query_day(select: str, group_by: str = "", order_by: str = "") -> pl.DataFrame:
    """Run a SELECT against the mart, scoped to `selected_day` via a WHERE clause."""
    sql = f"SELECT {select} FROM read_parquet('{MART_GLOB}', hive_partitioning=1) WHERE date_trunc('day', timestamp) = ?"
    if group_by:
        sql += f" GROUP BY {group_by}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    return con.execute(sql, [selected_day]).pl()


available_days = sorted(
    con.execute(
        f"SELECT DISTINCT date_trunc('day', timestamp) AS day FROM read_parquet('{MART_GLOB}', hive_partitioning=1)"
    )
    .pl()["day"]
    .to_list()
)
selected_day = st.selectbox(
    "Date",
    available_days,
    index=len(available_days) - 1,
    format_func=lambda d: d.strftime("%Y-%m-%d"),
)
st.caption(f"Showing data for **{selected_day.strftime('%Y-%m-%d')}**")

st.subheader("Temperature Heatmap by City")
st.caption(
    "Hourly temperature averaged into 3-hour buckets and colored by range — "
    "rows sorted by highest daily average first."
)

heat_df = query_day(
    select="city, CAST(FLOOR(extract(hour from timestamp) / 3.0) * 3 AS INTEGER) AS hour_bucket, avg(temperature) AS avg_temp",
    group_by="city, hour_bucket",
    order_by="city, hour_bucket",
)
city_avg_df = query_day(select="city, avg(temperature) AS avg_temp", group_by="city", order_by="avg_temp DESC")

city_order = city_avg_df["city"].to_list()
coldest_city = city_order[-1]
bucket_labels = [f"{h:02d}:00" for h in range(0, 24, 3)]
heat_df = heat_df.with_columns(
    pl.Series("hour_label", [f"{h:02d}:00" for h in heat_df["hour_bucket"].to_list()])
)
peak_hour_label = (
    heat_df.group_by("hour_label").agg(pl.col("avg_temp").mean().alias("m")).sort("m", descending=True)["hour_label"][0]
)

TEMP_COLOR_SCALE = alt.Scale(
    type="threshold",
    domain=[22, 25, 27, 29, 31, 33, 35],
    range=["#1a2a6c", "#2f5fdb", "#7ba1f5", "#cfe0fb", "#fddca0", "#f6a35c", "#ee6c4d", "#c81d25"],
)
ROW_HEIGHT = 26
n_cities = len(city_order)
x_domain = bucket_labels + ["Avg"]

simple_x = alt.X("hour_label:N", sort=x_domain)
simple_y = alt.Y("city:N", sort=city_order)

heatmap = alt.Chart(heat_df).mark_rect(stroke=CELL_BORDER, strokeWidth=1).encode(
    x=alt.X("hour_label:N", sort=x_domain, title=None, axis=alt.Axis(labelAngle=0)),
    y=alt.Y(
        "city:N",
        sort=city_order,
        title=None,
        axis=alt.Axis(labelOverlap=False, domain=True, domainColor=MUTED_TEXT, ticks=True, tickSize=6, tickColor=MUTED_TEXT),
    ),
    color=alt.Color(
        "avg_temp:Q",
        scale=TEMP_COLOR_SCALE,
        title="Temp (°C)",
        legend=alt.Legend(orient="top", direction="horizontal"),
    ),
    tooltip=[
        alt.Tooltip("city:N", title="City"),
        alt.Tooltip("hour_label:N", title="Hour"),
        alt.Tooltip("avg_temp:Q", title="Avg Temp (°C)", format=".1f"),
    ],
)

peak_highlight = alt.Chart(
    pl.DataFrame({"city": city_order, "hour_label": [peak_hour_label] * n_cities})
).mark_rect(fill=None, stroke="black", strokeDash=[4, 2], strokeWidth=1.5).encode(x=simple_x, y=simple_y)
cold_highlight = alt.Chart(
    pl.DataFrame({"city": [coldest_city] * len(bucket_labels), "hour_label": bucket_labels})
).mark_rect(fill=None, stroke="black", strokeDash=[4, 2], strokeWidth=1.5).encode(x=simple_x, y=simple_y)

avg_cells_df = city_avg_df.with_columns(pl.Series("hour_label", ["Avg"] * n_cities))
avg_rect = alt.Chart(avg_cells_df).mark_rect(stroke=CELL_BORDER, strokeWidth=1).encode(
    x=simple_x,
    y=simple_y,
    color=alt.Color("avg_temp:Q", scale=TEMP_COLOR_SCALE, legend=None),
)
avg_text = alt.Chart(avg_cells_df).mark_text(fontWeight="bold", color="black").encode(
    x=simple_x,
    y=simple_y,
    text=alt.Text("avg_temp:Q", format=".1f"),
)

heatmap_chart = (heatmap + peak_highlight + cold_highlight + avg_rect + avg_text).properties(
    height=ROW_HEIGHT * n_cities
)
st.altair_chart(heatmap_chart, use_container_width=True)

st.subheader("Precipitation Comparison by City")
precip_day_df = query_day(
    select="city, sum(precipitation) AS total_precipitation_mm",
    group_by="city",
    order_by="total_precipitation_mm DESC",
)

st.caption("Total precipitation (mm), sorted highest to lowest — cities with no recorded rainfall are hidden from the chart.")

avg_precip = precip_day_df["total_precipitation_mm"].mean()
precip_nonzero_df = precip_day_df.filter(precip_day_df["total_precipitation_mm"] > 0)

if precip_nonzero_df.height == 0:
    st.info("No precipitation recorded for any city on this day.")
else:
    precip_city_order = precip_nonzero_df["city"].to_list()
    top_city = precip_city_order[0]
    precip_nonzero_df = precip_nonzero_df.with_columns(
        pl.Series(
            "group", ["Highest precipitation" if c == top_city else "Other cities" for c in precip_city_order]
        )
    )

    precip_base = alt.Chart(precip_nonzero_df).encode(
        x=alt.X("city:N", sort=precip_city_order, title="City", axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("total_precipitation_mm:Q", title="Total Precipitation (mm)"),
    )
    precip_bars = precip_base.mark_bar().encode(
        color=alt.Color(
            "group:N",
            title=None,
            scale=alt.Scale(domain=["Other cities", "Highest precipitation"], range=["#6c63ff", "#f2994a"]),
            legend=alt.Legend(orient="top-right"),
        )
    )
    precip_labels = precip_base.mark_text(dy=-8, color=MUTED_TEXT).encode(
        text=alt.Text("total_precipitation_mm:Q", format=".1f")
    )

    avg_rule = alt.Chart(pl.DataFrame({"avg_mm": [avg_precip]})).mark_rule(
        strokeDash=[4, 4], color=MUTED_TEXT
    ).encode(y="avg_mm:Q")
    precip_avg_text = alt.Chart(
        pl.DataFrame(
            {"city": [precip_city_order[-1]], "avg_mm": [avg_precip], "label": [f"Average: {avg_precip:.1f} mm"]}
        )
    ).mark_text(align="right", dy=-6, color=MUTED_TEXT, fontSize=11).encode(
        x=alt.X("city:N", sort=precip_city_order),
        y="avg_mm:Q",
        text="label:N",
    )

    precip_chart = (precip_bars + precip_labels + avg_rule + precip_avg_text).properties(height=450)
    st.altair_chart(precip_chart, use_container_width=True)

st.subheader("Summary Stats")
summary_df = query_day(
    select="""
        city AS "City",
        avg(temperature) AS "Avg Temperature (°C)",
        max(temperature) AS "Max Temperature (°C)",
        min(temperature) AS "Min Temperature (°C)",
        sum(precipitation) AS "Total Precipitation (mm)",
        avg(windspeed) AS "Avg Windspeed (km/h)"
    """,
    group_by="city",
    order_by="avg(temperature) DESC",
)

st.caption(f"Averages and extremes for {selected_day.strftime('%Y-%m-%d')} — sorted by highest average temperature.")

BAR_METRICS = [
    ("Avg Temperature (°C)", "🌡️", "#f2994a"),
    ("Max Temperature (°C)", "🔺", "#eb5757"),
    ("Min Temperature (°C)", "🔻", "#6c8eef"),
    ("Total Precipitation (mm)", "💧", "#56ccf2"),
    ("Avg Windspeed (km/h)", "🌬️", "#6fcf97"),
]
col_ranges = {col: (summary_df[col].min(), summary_df[col].max()) for col, _, _ in BAR_METRICS}


def bar_cell(value: float, col: str, color: str) -> str:
    lo, hi = col_ranges[col]
    pct = 100.0 if hi == lo else (value - lo) / (hi - lo) * 100
    pct = max(pct, 4)  # keep a sliver visible even at the column min
    return (
        f'<div style="display:flex;align-items:center;gap:8px;" title="{col}: {value}">'
        '<div style="flex:1;height:6px;border-radius:3px;background:rgba(255,255,255,0.08);overflow:hidden;">'
        f'<div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:3px;"></div>'
        "</div>"
        f'<span style="min-width:44px;text-align:right;font-variant-numeric:tabular-nums;color:{LIGHT_TEXT};">{value:.1f}</span>'
        "</div>"
    )


header_cells = "".join(
    f'<th style="text-align:left;padding:0 14px 8px;font-weight:500;color:{MUTED_TEXT};font-size:0.85em;white-space:nowrap;">{icon} {col}</th>'
    for col, icon, _ in BAR_METRICS
)

row_html_parts = []
for rank, row in enumerate(summary_df.iter_rows(named=True), start=1):
    metric_cells = "".join(
        f'<td style="padding:10px 14px;">{bar_cell(row[col], col, color)}</td>' for col, _, color in BAR_METRICS
    )
    row_html_parts.append(
        '<tr class="summary-row" style="border-top:1px solid rgba(255,255,255,0.06);">'
        f'<td style="padding:10px 14px;color:{MUTED_TEXT};">{rank}</td>'
        f'<td style="padding:10px 14px;font-weight:700;white-space:nowrap;color:{LIGHT_TEXT};">{row["City"]}</td>'
        f"{metric_cells}"
        "</tr>"
    )

table_html = (
    "<style>.summary-row:hover{background:rgba(255,255,255,0.05);}</style>"
    f'<div style="background:{CARD_BG};color:{LIGHT_TEXT};border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px 8px;">'
    '<table style="width:100%;border-collapse:collapse;font-size:0.9em;">'
    "<thead><tr>"
    '<th style="padding:0 14px 8px;width:32px;"></th>'
    f'<th style="text-align:left;padding:0 14px 8px;font-weight:500;color:{MUTED_TEXT};font-size:0.85em;">City</th>'
    f"{header_cells}"
    "</tr></thead>"
    f"<tbody>{''.join(row_html_parts)}</tbody>"
    "</table>"
    "</div>"
)
st.markdown(table_html, unsafe_allow_html=True)
st.caption("Bars in each column are scaled to that column's own min–max range.")
