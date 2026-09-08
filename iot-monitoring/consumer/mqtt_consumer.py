"""Entrypoint for the MQTT consumer service. Actual logic lives in the `app` package."""

from app.main import run

if __name__ == "__main__":
    run()
