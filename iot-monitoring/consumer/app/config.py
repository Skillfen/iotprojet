"""Application settings, loaded from environment variables or a .env file."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- MQTT broker settings ----
    mqtt_broker: str = "broker.hivemq.com"
    mqtt_port: int = 1883
    mqtt_topic: str = "iot/sensors"
    mqtt_client_id: str = "python-iot-consumer"
    mqtt_keepalive: int = 60

    # ---- Elasticsearch settings ----
    elasticsearch_host: str = "http://localhost:9200"
    elasticsearch_index: str = "iot-data"
    # Overrides the auto-resolved path to elasticsearch/init_index.json (used in Docker).
    elasticsearch_mapping_path: Optional[str] = None

    # ---- Anomaly detection thresholds ----
    temperature_threshold: float = 35.0
    humidity_threshold: float = 80.0
    gas_ppm_threshold: float = 1000.0

    # ---- Alerting (optional outbound webhook, e.g. Slack/Discord/Teams) ----
    alert_webhook_url: Optional[str] = None
    alert_cooldown_seconds: int = 60

    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
