"""Shared Prefect @task wrappers and PipelineSteps factory used by both
weather_flow and backfill_flow.

Only the extract step differs between the two flows (forecast vs. archive API
base URL), so it takes base_url as an explicit argument, bound via
functools.partial in build_pipeline_steps().
"""
from __future__ import annotations

import functools
from datetime import date

import polars as pl
from prefect import task

from pipeline.pipeline import PipelineSteps
from pipeline.tasks.extract import extract_weather_for_city
from pipeline.tasks.load import read_raw, read_staging, write_mart, write_raw, write_staging
from pipeline.tasks.transform import finalize_weather, flatten_weather


@task(retries=3, retry_delay_seconds=30)
def extract_task(city: str, target_date: date, base_url: str) -> dict:
    return extract_weather_for_city(city, target_date, base_url)


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


def build_pipeline_steps(base_url: str) -> PipelineSteps:
    return PipelineSteps(
        extract=functools.partial(extract_task, base_url=base_url),
        load_raw=load_raw_task,
        read_raw=read_raw_task,
        clean=clean_task,
        load_staging=load_staging_task,
        read_staging=read_staging_task,
        finalize=finalize_task,
        load_mart=load_mart_task,
    )
