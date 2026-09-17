"""Registers deployments for both flows and serves them, so they show up in the
Prefect UI as runnable/schedulable jobs (like DAGs in Airflow) instead of only
being runnable from the command line.

Run with: python -m pipeline.serve
"""
from __future__ import annotations

from prefect import serve

from pipeline.flows.backfill_flow import backfill_flow
from pipeline.flows.weather_flow import weather_flow

if __name__ == "__main__":
    daily_deployment = weather_flow.to_deployment(
        name="daily-weather-ingest",
        cron="0 6 * * *",  # 06:00 daily; also runnable on-demand from the UI
    )
    backfill_deployment = backfill_flow.to_deployment(
        name="weather-backfill",
    )
    serve(daily_deployment, backfill_deployment)
