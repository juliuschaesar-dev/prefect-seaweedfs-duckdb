"""Prefect flow: extract -> raw -> staging -> mart, for the daily incremental case."""
from __future__ import annotations

from datetime import date, timedelta

from prefect import flow

from common.config import settings
from pipeline.flows.prefect_tasks import build_pipeline_steps
from pipeline.pipeline import run_pipeline_for_date


@flow(name="weather-daily-flow")
def weather_flow(target_date: date | None = None) -> None:
    target_date = target_date or date.today() - timedelta(days=1)
    steps = build_pipeline_steps(settings.openmeteo_forecast_url)
    run_pipeline_for_date(target_date, settings.cities, steps)


if __name__ == "__main__":
    weather_flow()
