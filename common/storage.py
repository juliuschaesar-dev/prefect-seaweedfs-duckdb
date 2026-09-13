"""Shared S3/SeaweedFS client and Parquet read/write helpers."""
from __future__ import annotations

import io

import boto3
import polars as pl

from common.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        use_ssl=settings.s3_use_ssl,
    )


def write_parquet(df: pl.DataFrame, path: str) -> None:
    buffer = io.BytesIO()
    df.write_parquet(buffer)
    buffer.seek(0)
    get_s3_client().put_object(Bucket=settings.s3_bucket, Key=path, Body=buffer.getvalue())


def read_parquet(path: str) -> pl.DataFrame:
    obj = get_s3_client().get_object(Bucket=settings.s3_bucket, Key=path)
    return pl.read_parquet(io.BytesIO(obj["Body"].read()))
