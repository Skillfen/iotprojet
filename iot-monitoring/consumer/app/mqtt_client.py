"""Thin wrapper around paho-mqtt: connection lifecycle and message dispatch."""

import logging
from typing import Callable

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MQTTSubscriber:
    """Subscribes to a topic and forwards raw payloads to a callback."""

    def __init__(
        self,
        broker: str,
        port: int,
        topic: str,
        client_id: str,
        keepalive: int,
        on_payload: Callable[[bytes], None],
    ):
        self._broker = broker
        self._port = port
        self._topic = topic
        self._keepalive = keepalive
        self._on_payload = on_payload

        self._client = mqtt.Client(
            client_id=client_id,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        self._client.on_connect = self._handle_connect
        self._client.on_message = self._handle_message
        self._client.on_disconnect = self._handle_disconnect
        # Auto-reconnect with exponential backoff instead of dying on network blips.
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)

    def _handle_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            logger.info("Connected to MQTT broker %s:%s", self._broker, self._port)
            client.subscribe(self._topic)
            logger.info("Subscribed to topic '%s'", self._topic)
        else:
            logger.error("Failed to connect to MQTT broker, reason code: %s", reason_code)

    def _handle_disconnect(self, client, userdata, reason_code, properties=None):
        logger.warning("Disconnected from MQTT broker (reason code: %s)", reason_code)

    def _handle_message(self, client, userdata, msg):
        self._on_payload(msg.payload)

    def run_forever(self) -> None:
        self._client.connect(self._broker, self._port, self._keepalive)
        logger.info("Starting MQTT loop... (press Ctrl+C to stop)")
        self._client.loop_forever()

    def disconnect(self) -> None:
        self._client.disconnect()
