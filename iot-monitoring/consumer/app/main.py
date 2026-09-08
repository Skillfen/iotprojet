"""Wires together config, MQTT ingestion, anomaly detection and ES persistence."""

import json
import logging
import os
import sys

from .anomaly import AnomalyDetector
from .config import settings
from .es_repository import ElasticsearchRepository
from .models import SensorReading
from .mqtt_client import MQTTSubscriber


def _configure_logging(level: str) -> None:
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s")


def _resolve_mapping_path() -> str:
    if settings.elasticsearch_mapping_path:
        return settings.elasticsearch_mapping_path
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "elasticsearch", "init_index.json",
    )


def run() -> None:
    _configure_logging(settings.log_level)
    logger = logging.getLogger("mqtt_consumer")

    repository = ElasticsearchRepository(
        settings.elasticsearch_host, settings.elasticsearch_index, _resolve_mapping_path()
    )
    detector = AnomalyDetector(settings)

    try:
        repository.wait_until_ready()
    except Exception as exc:
        logger.error("Cannot reach Elasticsearch at %s: %s", settings.elasticsearch_host, exc)
        sys.exit(1)

    repository.ensure_index_exists()

    def handle_payload(raw_payload: bytes) -> None:
        try:
            data = json.loads(raw_payload.decode("utf-8"))
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON payload: %s", raw_payload)
            return

        try:
            reading = SensorReading(
                device=data.get("device", "unknown"),
                temperature=data["temperature"],
                humidity=data["humidity"],
                motion=data.get("motion", False),
                light_lux=data.get("light_lux"),
                gas_ppm=data.get("gas_ppm"),
                gas_alert=data.get("gas_alert", False),
            )
        except (KeyError, ValueError) as exc:
            logger.warning("Invalid sensor payload %s: %s", data, exc)
            return

        reading.anomaly = detector.is_anomaly(
            reading.temperature, reading.humidity, reading.gas_ppm, reading.gas_alert
        )

        try:
            repository.save(reading.to_document())
        except Exception as exc:
            logger.error("Failed to store document in Elasticsearch: %s", exc)
            return

        logger.info(
            "Stored reading | device=%s temp=%.1f humidity=%.1f motion=%s gas_ppm=%s anomaly=%s",
            reading.device, reading.temperature, reading.humidity,
            reading.motion, reading.gas_ppm, reading.anomaly,
        )
        if reading.anomaly:
            logger.warning(
                "ANOMALY DETECTED | device=%s temperature=%.1f humidity=%.1f gas_ppm=%s gas_alert=%s",
                reading.device, reading.temperature, reading.humidity,
                reading.gas_ppm, reading.gas_alert,
            )

    subscriber = MQTTSubscriber(
        broker=settings.mqtt_broker,
        port=settings.mqtt_port,
        topic=settings.mqtt_topic,
        client_id=settings.mqtt_client_id,
        keepalive=settings.mqtt_keepalive,
        on_payload=handle_payload,
    )

    try:
        subscriber.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down consumer.")
        subscriber.disconnect()


if __name__ == "__main__":
    run()
