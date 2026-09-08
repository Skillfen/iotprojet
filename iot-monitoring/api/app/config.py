"""Settings for the read-only query API, loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    elasticsearch_host: str = "http://localhost:9200"
    elasticsearch_index: str = "iot-data"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
