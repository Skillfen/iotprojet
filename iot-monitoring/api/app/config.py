"""Settings for the read-only query API, loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    elasticsearch_host: str = "http://localhost:9200"
    elasticsearch_index: str = "iot-data"
    # A device with no reading for longer than this is reported as "stale" in /stats/summary.
    stale_after_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
