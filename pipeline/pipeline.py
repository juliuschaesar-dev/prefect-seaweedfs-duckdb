"""Shared extract -> raw -> staging -> mart orchestration for one target date.

Used by both the Prefect flow (steps wrapped as @task for retries/observability)
and the backfill script (steps called directly, no per-city/day Prefect overhead).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable

import polars as pl


def daterange(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


@dataclass(frozen=True)
class PipelineSteps:
    extract: Callable[[str, date], dict]
    load_raw: Callable[[dict, date], None]
    read_raw: Callable[[str, date], pl.DataFrame]
    clean: Callable[[pl.DataFrame], pl.DataFrame]
    load_staging: Callable[[pl.DataFrame, date], None]
    read_staging: Callable[[date], pl.DataFrame]
    finalize: Callable[[pl.DataFrame], pl.DataFrame]
    load_mart: Callable[[pl.DataFrame, date], None]


def run_pipeline_for_date(target_date: date, cities: list[str], steps: PipelineSteps) -> None:
    staging_frames = []
    for city in cities:
        raw = steps.extract(city, target_date)
        steps.load_raw(raw, target_date)
        raw_df = steps.read_raw(city, target_date)
        staging_frames.append(steps.clean(raw_df))

    steps.load_staging(pl.concat(staging_frames), target_date)
    staging_df = steps.read_staging(target_date)
    steps.load_mart(steps.finalize(staging_df), target_date)
