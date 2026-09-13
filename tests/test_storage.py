import io

import polars as pl

from common import storage


class FakeS3Client:
    def __init__(self):
        self.objects: dict[str, bytes] = {}

    def put_object(self, Bucket, Key, Body):
        self.objects[Key] = Body

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key])}


def test_write_then_read_parquet_roundtrip(monkeypatch):
    fake_client = FakeS3Client()
    monkeypatch.setattr(storage, "get_s3_client", lambda: fake_client)

    df = pl.DataFrame({"city": ["Jakarta"], "temperature": [25.0]})
    storage.write_parquet(df, "mart/weather/dt=2024-01-01/data.parquet")

    result = storage.read_parquet("mart/weather/dt=2024-01-01/data.parquet")

    assert result.equals(df)
