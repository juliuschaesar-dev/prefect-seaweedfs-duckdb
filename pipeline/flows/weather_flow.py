"""Prefect flow: extract -> raw -> staging -> mart, for the daily incremental case."""
from __future__ import annotations

from datetime import date, timedelta

import polars as pl
from prefect import flow, task

from common.config import settings
from pipeline.pipeline import PipelineSteps, run_pipeline_for_date
from pipeline.tasks.extract import fetch_weather
from pipeline.tasks.load import read_raw, read_staging, write_mart, write_raw, write_staging
from pipeline.tasks.transform import finalize_weather, flatten_weather


@task(retries=3, retry_delay_seconds=30)
def extract_task(city: str, target_date: date) -> dict:
    lat, lon = settings.city_coordinates(city)
    return fetch_weather(
        city=city,
        lat=lat,
        lon=lon,
        start_date=target_date,
        end_date=target_date,
        base_url=settings.openmeteo_forecast_url,
    )


@task
def load_raw_task(raw: dict, target_date: date) -> None:
    write_raw(raw, target_date)


@task
def read_raw_task(city: str, target_date: date) -> pl.DataFrame:
    return read_raw(city, target_date)


@task
def clean_task(raw_df: pl.DataFrame) -> pl.DataFrame:
    return flatten_weather(raw_df)


@task
def load_staging_task(df: pl.DataFrame, target_date: date) -> None:
    write_staging(df, target_date)


@task
def read_staging_task(target_date: date) -> pl.DataFrame:
    return read_staging(target_date)


@task
def finalize_task(staging_df: pl.DataFrame) -> pl.DataFrame:
    return finalize_weather(staging_df)


@task
def load_mart_task(df: pl.DataFrame, target_date: date) -> None:
    write_mart(df, target_date)


@flow(name="weather-daily-flow")
def weather_flow(target_date: date | None = None) -> None:
    target_date = target_date or date.today() - timedelta(days=1)
    steps = PipelineSteps(
        extract=extract_task,
        load_raw=load_raw_task,
        read_raw=read_raw_task,
        clean=clean_task,
        load_staging=load_staging_task,
        read_staging=read_staging_task,
        finalize=finalize_task,
        load_mart=load_mart_task,
    )
    run_pipeline_for_date(target_date, settings.cities, steps)


if __name__ == "__main__":
    weather_flow()
