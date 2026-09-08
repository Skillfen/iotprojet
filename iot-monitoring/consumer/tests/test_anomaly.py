from app.anomaly import AnomalyDetector
from app.config import Settings


def _detector(temp_threshold=35.0, humidity_threshold=80.0):
    settings = Settings(temperature_threshold=temp_threshold, humidity_threshold=humidity_threshold)
    return AnomalyDetector(settings)


def test_normal_reading_is_not_an_anomaly():
    detector = _detector()
    assert detector.is_anomaly(temperature=25.0, humidity=50.0) is False


def test_high_temperature_is_an_anomaly():
    detector = _detector()
    assert detector.is_anomaly(temperature=36.0, humidity=50.0) is True


def test_high_humidity_is_an_anomaly():
    detector = _detector()
    assert detector.is_anomaly(temperature=25.0, humidity=85.0) is True


def test_threshold_boundary_is_not_an_anomaly():
    detector = _detector(temp_threshold=35.0)
    assert detector.is_anomaly(temperature=35.0, humidity=50.0) is False


def test_high_gas_ppm_is_an_anomaly():
    detector = _detector()
    assert detector.is_anomaly(temperature=25.0, humidity=50.0, gas_ppm=1500.0) is True


def test_gas_alert_flag_is_an_anomaly():
    detector = _detector()
    assert detector.is_anomaly(temperature=25.0, humidity=50.0, gas_alert=True) is True


def test_no_gas_data_is_not_an_anomaly():
    detector = _detector()
    assert detector.is_anomaly(temperature=25.0, humidity=50.0) is False
