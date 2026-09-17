"""One-off script: historical load via the Open-Meteo Archive API.

Reuses the shared run_pipeline_for_date() orchestration (also used by the Prefect flow) —
only the extract step differs (Archive API + custom date range, instead of Forecast API).
"""
from __future__ import annotations

import argparse
import functools
from datetime import date

from common.config import settings
from pipeline.pipeline import PipelineSteps, daterange, run_pipeline_for_date
from pipeline.tasks.extract import extract_weather_for_city
from pipeline.tasks.load import read_raw, read_staging, write_mart, write_raw, write_staging
from pipeline.tasks.transform import finalize_weather, flatten_weather

STEPS = PipelineSteps(
    extract=functools.partial(extract_weather_for_city, base_url=settings.openmeteo_archive_url),
    load_raw=write_raw,
    read_raw=read_raw,
    clean=flatten_weather,
    load_staging=write_staging,
    read_staging=read_staging,
    finalize=finalize_weather,
    load_mart=write_mart,
)


def backfill(start_date: date, end_date: date) -> None:
    for day in daterange(start_date, end_date):
        run_pipeline_for_date(day, settings.cities, STEPS)
        print(f"Backfilled {day.isoformat()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill historical weather data into raw/mart.")
    parser.add_argument("--start-date", type=date.fromisoformat, required=True, help="YYYY-MM-DD")
    parser.add_argument("--end-date", type=date.fromisoformat, required=True, help="YYYY-MM-DD")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    backfill(args.start_date, args.end_date)
