import math

import pytest
from pydantic import ValidationError

from app.models import SensorReading


def test_to_document_has_expected_shape():
    reading = SensorReading(device="esp32-01", temperature=28.5, humidity=60.0)
    document = reading.to_document()

    assert document["device"] == "esp32-01"
    assert document["temperature"] == 28.5
    assert document["humidity"] == 60.0
    assert document["anomaly"] is False
    assert "timestamp" in document


def test_default_device_is_unknown():
    reading = SensorReading(temperature=20.0, humidity=40.0)
    assert reading.device == "unknown"


def test_optional_sensor_fields_default_to_safe_values():
    reading = SensorReading(temperature=20.0, humidity=40.0)
    assert reading.motion is False
    assert reading.light_lux is None
    assert reading.gas_ppm is None
    assert reading.gas_alert is False


def test_to_document_includes_extra_sensors():
    reading = SensorReading(
        device="esp32-01", temperature=28.5, humidity=60.0,
        motion=True, light_lux=120.5, gas_ppm=350.0, gas_alert=False,
    )
    document = reading.to_document()
    assert document["motion"] is True
    assert document["light_lux"] == 120.5
    assert document["gas_ppm"] == 350.0


def test_nan_temperature_is_rejected():
    with pytest.raises(ValidationError):
        SensorReading(device="esp32-01", temperature=math.nan, humidity=40.0)
