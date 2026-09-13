import os

os.environ.setdefault("S3_ENDPOINT", "http://localhost:8333")
os.environ.setdefault("S3_ACCESS_KEY", "test_access_key")
os.environ.setdefault("S3_SECRET_KEY", "test_secret_key")
os.environ.setdefault("S3_BUCKET", "weather-bucket-test")
os.environ.setdefault("S3_USE_SSL", "false")
os.environ.setdefault("OPENMETEO_FORECAST_URL", "https://api.open-meteo.com/v1/forecast")
os.environ.setdefault("OPENMETEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive")
os.environ.setdefault("CITIES", "Jakarta,Bandung")
