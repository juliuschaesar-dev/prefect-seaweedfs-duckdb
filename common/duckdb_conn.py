"""Shared DuckDB connection: loads httpfs and sets S3 credentials from Settings."""
from __future__ import annotations

import duckdb

from common.config import settings


def get_connection() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    endpoint = settings.s3_endpoint.split("://", 1)[-1]
    con.execute(
        """
        CREATE OR REPLACE SECRET seaweedfs (
            TYPE s3,
            KEY_ID ?,
            SECRET ?,
            ENDPOINT ?,
            USE_SSL ?,
            URL_STYLE 'path'
        )
        """,
        [settings.s3_access_key, settings.s3_secret_key, endpoint, settings.s3_use_ssl],
    )
    return con
