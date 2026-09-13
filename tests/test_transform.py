import polars as pl

from pipeline.tasks.transform import finalize_weather, flatten_weather

RAW_DF = pl.DataFrame(
    {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
        "temperature_2m": [25.0, 24.5],
        "precipitation": [0.0, 0.1],
        "windspeed_10m": [5.0, 5.5],
        "cloudcover": [10, 20],
        "city": ["Jakarta", "Jakarta"],
    }
)


def test_flatten_weather_produces_tidy_rows():
    df = flatten_weather(RAW_DF)

    assert df.columns == ["city", "timestamp", "temperature", "precipitation", "windspeed", "cloudcover"]
    assert df.height == 2
    assert df["city"].to_list() == ["Jakarta", "Jakarta"]
    assert df["temperature"].to_list() == [25.0, 24.5]


def test_finalize_weather_dedupes_and_sorts():
    staging_df = pl.DataFrame(
        {
            "city": ["Jakarta", "Bandung", "Jakarta", "Jakarta"],
            "timestamp": [
                "2024-01-01T01:00",
                "2024-01-01T00:00",
                "2024-01-01T00:00",
                "2024-01-01T00:00",
            ],
            "temperature": [24.5, 22.0, 25.0, 25.0],
            "precipitation": [0.1, 0.0, 0.0, 0.0],
            "windspeed": [5.5, 4.0, 5.0, 5.0],
            "cloudcover": [20, 15, 10, 10],
        }
    ).with_columns(pl.col("timestamp").str.to_datetime())

    df = finalize_weather(staging_df)

    assert df.height == 3
    assert df["city"].to_list() == ["Bandung", "Jakarta", "Jakarta"]
