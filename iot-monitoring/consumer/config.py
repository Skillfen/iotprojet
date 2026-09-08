"""Configuration constants for the IoT MQTT consumer."""

# ---- MQTT broker settings ----
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "iot/sensors"
MQTT_CLIENT_ID = "python-iot-consumer"
MQTT_KEEPALIVE = 60

# ---- Elasticsearch settings ----
ELASTICSEARCH_HOST = "http://localhost:9200"
ELASTICSEARCH_INDEX = "iot-data"

# ---- Anomaly detection thresholds ----
TEMPERATURE_THRESHOLD = 35.0
HUMIDITY_THRESHOLD = 80.0
