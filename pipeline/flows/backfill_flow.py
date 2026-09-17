"""Prefect flow version of the historical backfill, so it can be deployed and
triggered from the Prefect UI (with start_date/end_date as run parameters),
the same way weather_flow is."""
from __future__ import annotations

from datetime import date, timedelta

from prefect import flow

from common.config import settings
from pipeline.flows.prefect_tasks import build_pipeline_steps
from pipeline.pipeline import daterange, run_pipeline_for_date


@flow(name="weather-backfill-flow")
def backfill_flow(start_date: date, end_date: date) -> None:
    steps = build_pipeline_steps(settings.openmeteo_archive_url)
    for target_date in daterange(start_date, end_date):
        run_pipeline_for_date(target_date, settings.cities, steps)


if __name__ == "__main__":
    backfill_flow(start_date=date.today() - timedelta(days=7), end_date=date.today() - timedelta(days=1))
