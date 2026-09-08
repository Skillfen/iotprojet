from unittest.mock import patch

from app.alerting import AlertNotifier


def test_disabled_when_no_webhook_url():
    notifier = AlertNotifier(webhook_url="")
    assert notifier.enabled is False


def test_notify_skips_when_disabled():
    notifier = AlertNotifier(webhook_url="")
    with patch("urllib.request.urlopen") as mocked:
        notifier.notify({"device": "esp32-01", "temperature": 40.0})
    mocked.assert_not_called()


def test_notify_sends_webhook_when_enabled():
    notifier = AlertNotifier(webhook_url="https://example.com/webhook")
    with patch("urllib.request.urlopen") as mocked:
        notifier.notify({"device": "esp32-01", "temperature": 40.0})
    mocked.assert_called_once()


def test_notify_respects_cooldown_per_device():
    notifier = AlertNotifier(webhook_url="https://example.com/webhook", cooldown_seconds=60)
    with patch("urllib.request.urlopen") as mocked:
        notifier.notify({"device": "esp32-01", "temperature": 40.0})
        notifier.notify({"device": "esp32-01", "temperature": 41.0})
    mocked.assert_called_once()


def test_notify_allows_different_devices_independently():
    notifier = AlertNotifier(webhook_url="https://example.com/webhook", cooldown_seconds=60)
    with patch("urllib.request.urlopen") as mocked:
        notifier.notify({"device": "esp32-01", "temperature": 40.0})
        notifier.notify({"device": "esp32-02", "temperature": 40.0})
    assert mocked.call_count == 2
