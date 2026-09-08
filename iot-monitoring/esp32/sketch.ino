/*
 * IoT Monitoring Platform - ESP32 + DHT22 + PIR + MQ2 + LDR + MQTT
 * ------------------------------------------------------------------
 * Reads temperature/humidity (DHT22), motion (PIR), gas concentration
 * (MQ2) and ambient light (LDR) every 5 seconds and publishes the
 * combined reading as a JSON payload to a public MQTT broker
 * (broker.hivemq.com) on topic "iot/sensors". A local LED + buzzer
 * give immediate visual/audible feedback when a threshold is crossed.
 *
 * Board: ESP32 DevKit V1
 * Sensors:
 *   - DHT22            data  -> GPIO 4
 *   - PIR motion       OUT   -> GPIO 13
 *   - MQ2 gas sensor   AOUT  -> GPIO 34, DOUT -> GPIO 27
 *   - Photoresistor    AO    -> GPIO 35
 * Actuators:
 *   - Alert LED               -> GPIO 25 (through a 220 ohm resistor)
 *   - Alert buzzer            -> GPIO 26
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ---- Sensor configuration ----
#define DHTPIN 4
#define DHTTYPE DHT22
#define PIR_PIN 13
#define GAS_AOUT_PIN 34
#define GAS_DOUT_PIN 27
#define LDR_AOUT_PIN 35

// ---- Actuator configuration ----
#define LED_PIN 25
#define BUZZER_PIN 26

// ---- Local alert thresholds (mirrors the consumer's anomaly detector) ----
const float TEMPERATURE_THRESHOLD = 35.0;
const float HUMIDITY_THRESHOLD = 80.0;
const float GAS_PPM_THRESHOLD = 1000.0;

// ---- ESP32 ADC / LDR conversion constants ----
const float ADC_MAX = 4095.0;
const float ADC_VREF = 3.3;
const float LDR_GAMMA = 0.7;
const float LDR_RL10 = 50.0;

// ---- WiFi configuration (Wokwi virtual network) ----
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

// ---- MQTT configuration ----
const char* MQTT_BROKER = "broker.hivemq.com";
const int   MQTT_PORT = 1883;
const char* MQTT_TOPIC = "iot/sensors";
const char* DEVICE_ID = "esp32-01";

// ---- Publish interval ----
const unsigned long PUBLISH_INTERVAL_MS = 5000;

DHT dht(DHTPIN, DHTTYPE);
WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long lastPublish = 0;

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi connected, IP: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Connecting to MQTT broker...");
    String clientId = String(DEVICE_ID) + "-" + String(random(0xffff), HEX);
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 2s");
      delay(2000);
    }
  }
}

// Converts the LDR analog reading into an approximate illuminance (lux).
float readLux() {
  int raw = analogRead(LDR_AOUT_PIN);
  float voltage = raw / ADC_MAX * ADC_VREF;
  float resistance = 2000 * voltage / (1 - voltage / ADC_VREF);
  float lux = pow(LDR_RL10 * 1e3 * pow(10, LDR_GAMMA) / resistance, 1 / LDR_GAMMA);
  return isfinite(lux) ? lux : 0.0;
}

// Converts the MQ2 analog reading into an approximate gas concentration (ppm).
float readGasPpm() {
  int raw = analogRead(GAS_AOUT_PIN);
  return (raw / ADC_MAX) * 10000.0;
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  pinMode(PIR_PIN, INPUT);
  pinMode(GAS_DOUT_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  connectWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastPublish >= PUBLISH_INTERVAL_MS) {
    lastPublish = now;

    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    // DHT22 returns NaN on read failure; skip this cycle if invalid
    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("Failed to read from DHT22 sensor!");
      return;
    }

    bool motion = digitalRead(PIR_PIN) == HIGH;
    float lux = readLux();
    float gasPpm = readGasPpm();
    // MQ2 digital output goes LOW when the gas concentration crosses its threshold.
    bool gasAlert = digitalRead(GAS_DOUT_PIN) == LOW;

    bool alert = temperature > TEMPERATURE_THRESHOLD
              || humidity > HUMIDITY_THRESHOLD
              || gasPpm > GAS_PPM_THRESHOLD
              || gasAlert;
    digitalWrite(LED_PIN, alert ? HIGH : LOW);
    digitalWrite(BUZZER_PIN, alert ? HIGH : LOW);

    StaticJsonDocument<300> doc;
    doc["device"] = DEVICE_ID;
    doc["temperature"] = round(temperature * 10) / 10.0;
    doc["humidity"] = round(humidity * 10) / 10.0;
    doc["motion"] = motion;
    doc["light_lux"] = round(lux * 10) / 10.0;
    doc["gas_ppm"] = round(gasPpm * 10) / 10.0;
    doc["gas_alert"] = gasAlert;

    char payload[300];
    serializeJson(doc, payload);

    Serial.print("Publishing: ");
    Serial.println(payload);

    mqttClient.publish(MQTT_TOPIC, payload);
  }
}
