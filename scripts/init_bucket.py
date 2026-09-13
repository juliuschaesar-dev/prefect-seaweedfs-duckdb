"""One-off script: idempotently create the S3 bucket used by this pipeline.

Retries while SeaweedFS's s3 gateway is still starting up (used as a docker-compose init step).
"""
from __future__ import annotations

import time

import botocore

from common.config import settings
from common.storage import get_s3_client


def create_bucket(retries: int = 30, delay_seconds: float = 2.0) -> None:
    client = get_s3_client()
    last_error: Exception | None = None

    for _ in range(retries):
        try:
            client.create_bucket(Bucket=settings.s3_bucket)
            print(f"Bucket '{settings.s3_bucket}' ready.")
            return
        except client.exceptions.BucketAlreadyOwnedByYou:
            print(f"Bucket '{settings.s3_bucket}' already exists.")
            return
        except botocore.exceptions.ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou"):
                print(f"Bucket '{settings.s3_bucket}' already exists.")
                return
            last_error = exc
        except Exception as exc:  # s3 gateway not accepting connections yet
            last_error = exc

        time.sleep(delay_seconds)

    raise RuntimeError(f"Could not create bucket '{settings.s3_bucket}' after {retries} retries: {last_error}")


if __name__ == "__main__":
    create_bucket()
