"""Anomaly detection based on configurable thresholds."""

from typing import Optional

from .config import Settings


class AnomalyDetector:
    """Flags readings that exceed the configured temperature/humidity/gas thresholds."""

    def __init__(self, settings: Settings):
        self._temperature_threshold = settings.temperature_threshold
        self._humidity_threshold = settings.humidity_threshold
        self._gas_ppm_threshold = settings.gas_ppm_threshold

    def is_anomaly(
        self,
        temperature: float,
        humidity: float,
        gas_ppm: Optional[float] = None,
        gas_alert: bool = False,
    ) -> bool:
        return (
            temperature > self._temperature_threshold
            or humidity > self._humidity_threshold
            or gas_alert
            or (gas_ppm is not None and gas_ppm > self._gas_ppm_threshold)
        )
