"""Data models shared across the consumer layers."""

import math
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SensorReading(BaseModel):
    """A validated reading published by a sensor node (DHT22 + PIR + MQ2 + LDR)."""

    device: str = "unknown"
    temperature: float
    humidity: float
    motion: bool = False
    light_lux: Optional[float] = None
    gas_ppm: Optional[float] = None
    gas_alert: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    anomaly: bool = False

    @field_validator("temperature", "humidity", "light_lux", "gas_ppm")
    @classmethod
    def must_be_finite(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and (math.isnan(value) or math.isinf(value)):
            raise ValueError("value must be a finite number")
        return value

    def to_document(self) -> dict:
        """Serialize to the flat dict shape stored in Elasticsearch."""
        return {
            "device": self.device,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "motion": self.motion,
            "light_lux": self.light_lux,
            "gas_ppm": self.gas_ppm,
            "gas_alert": self.gas_alert,
            "timestamp": self.timestamp.isoformat(),
            "anomaly": self.anomaly,
        }
