"""Outbound alert notifications (generic Slack/Discord/Teams-compatible webhook)."""

import json
import logging
import time
import urllib.request
from typing import Dict

logger = logging.getLogger(__name__)


class AlertNotifier:
    """Posts a JSON alert to a webhook URL, throttled per device to avoid spam."""

    def __init__(self, webhook_url: str, cooldown_seconds: int = 60):
        self._webhook_url = webhook_url
        self._cooldown_seconds = cooldown_seconds
        self._last_sent: Dict[str, float] = {}

    @property
    def enabled(self) -> bool:
        return bool(self._webhook_url)

    def _should_send(self, device: str) -> bool:
        last = self._last_sent.get(device, 0.0)
        return (time.monotonic() - last) >= self._cooldown_seconds

    def notify(self, document: dict) -> None:
        """Send an alert for an anomalous document, respecting the per-device cooldown."""
        device = document.get("device", "unknown")
        if not self.enabled or not self._should_send(device):
            return

        message = (
            f"Anomaly detected on {device} | temperature={document.get('temperature')}C "
            f"humidity={document.get('humidity')}% gas_ppm={document.get('gas_ppm')} "
            f"motion={document.get('motion')} at {document.get('timestamp')}"
        )
        # "text" is read by Slack/Teams, "content" is read by Discord; harmless if unused.
        body = json.dumps({"text": message, "content": message}).encode("utf-8")
        request = urllib.request.Request(
            self._webhook_url, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(request, timeout=5)
            self._last_sent[device] = time.monotonic()
            logger.info("Alert webhook sent for device=%s", device)
        except Exception as exc:
            logger.error("Failed to send alert webhook: %s", exc)
