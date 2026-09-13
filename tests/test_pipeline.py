from datetime import date

import polars as pl

from pipeline.pipeline import PipelineSteps, run_pipeline_for_date


def test_run_pipeline_for_date_calls_steps_in_order():
    calls = []

    def extract(city, target_date):
        calls.append(("extract", city, target_date))
        return {"city": city}

    def load_raw(raw, target_date):
        calls.append(("load_raw", raw["city"], target_date))

    def read_raw(city, target_date):
        calls.append(("read_raw", city, target_date))
        return pl.DataFrame({"city": [city]})

    def clean(raw_df):
        calls.append(("clean", raw_df["city"][0]))
        return raw_df

    def load_staging(df, target_date):
        calls.append(("load_staging", df["city"].to_list(), target_date))

    def read_staging(target_date):
        calls.append(("read_staging", target_date))
        return pl.DataFrame({"city": ["Jakarta", "Bandung"]})

    def finalize(staging_df):
        calls.append(("finalize", staging_df["city"].to_list()))
        return staging_df

    def load_mart(df, target_date):
        calls.append(("load_mart", df["city"].to_list(), target_date))

    steps = PipelineSteps(
        extract=extract,
        load_raw=load_raw,
        read_raw=read_raw,
        clean=clean,
        load_staging=load_staging,
        read_staging=read_staging,
        finalize=finalize,
        load_mart=load_mart,
    )

    target_date = date(2024, 1, 1)
    run_pipeline_for_date(target_date, ["Jakarta", "Bandung"], steps)

    assert calls == [
        ("extract", "Jakarta", target_date),
        ("load_raw", "Jakarta", target_date),
        ("read_raw", "Jakarta", target_date),
        ("clean", "Jakarta"),
        ("extract", "Bandung", target_date),
        ("load_raw", "Bandung", target_date),
        ("read_raw", "Bandung", target_date),
        ("clean", "Bandung"),
        ("load_staging", ["Jakarta", "Bandung"], target_date),
        ("read_staging", target_date),
        ("finalize", ["Jakarta", "Bandung"]),
        ("load_mart", ["Jakarta", "Bandung"], target_date),
    ]
