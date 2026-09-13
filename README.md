# prefect-seaweedfs-duckdb

End-to-end weather analytics pipeline: Open-Meteo → Prefect → SeaweedFS (S3-compatible) → DuckDB → Streamlit.

## Architecture

![Architecture](docs/architecture.svg)

Storage layout:
```
s3://weather-bucket/
├── raw/openmeteo/city=<city>/dt=YYYY-MM-DD/data.parquet
├── staging/weather/dt=YYYY-MM-DD/data.parquet
└── mart/weather/dt=YYYY-MM-DD/data.parquet
```

## Setup

1. Copy `.env.example` to `.env` and fill in values (defaults work for the local SeaweedFS compose stack).
2. `docker compose up -d --build` — brings up SeaweedFS (master, volume, filer, s3 gateway on `:8333`), the Prefect server/UI (`:4200`), builds the `app` image, creates the bucket (`bucket-init`, idempotent), then starts the Streamlit dashboard on `:8501`.

## Running the backfill (historical load)

```
docker compose run --rm app python -m scripts.backfill --start-date 2021-01-01 --end-date 2025-12-31
```

Loops over `CITIES` × `[--start-date, --end-date]` (both required), pulling from the Open-Meteo Archive API and writing through `raw/` → `staging/` → `mart/`.

## Running the daily flow

```
docker compose run --rm app python -m pipeline.flows.weather_flow
```

Runs the Prefect flow for yesterday's date (forecast API), with retries on the extract step. To schedule it, create a Prefect deployment from `weather_flow` and attach a daily schedule.

## Prefect UI

Available at [http://localhost:4200](http://localhost:4200) — shows flow runs, task runs, logs, and state history for every run of `weather_flow` (backed by a persistent `prefect-server` service, not the ephemeral local server Prefect falls back to when no server is configured).

## Dashboard

Already running at [http://localhost:8501](http://localhost:8501) once `docker compose up -d --build` finishes. Shows temperature trend by city, precipitation comparison by city, and summary stats — all queried live from `mart/` via DuckDB's `httpfs`.

## Tests

```
pytest
```

Unit tests cover `extract`, `transform`, and `storage`, with the API/S3 calls mocked.
