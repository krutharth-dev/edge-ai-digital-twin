/*
 * Hardware-target ESP32 telemetry firmware (not bench-tested).
 * Final DC motor/fan + ADXL345 + DS18B20 + ACS712 + Hall switch.
 * Uses local MQTT topics from docs/MQTT_CONTRACT.md.
 * Requires a calibrated ACS712 + ESP32-safe ADC divider and a secure motor driver.
 * Wiring and sensor calibration MUST be verified before powering the motor.
 * No automated motor actuation is performed by this firmware.
 *
 * Arduino libraries:
 *   PubSubClient by Nick O'Leary, ArduinoJson 7,
 *   Adafruit ADXL345, Adafruit Unified Sensor,
 *   OneWire, DallasTemperature
 */
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <time.h>
#include "secrets.h"

constexpr int PIN_ONEWIRE = 4;
constexpr int PIN_ACS712_ADC = 35;  // ADC input: MUST NOT exceed 3.3 V
constexpr int PIN_HALL = 27;        // Digital 3.3 V Hall output
constexpr float DIVIDER_GAIN = 2.0f;  // Example 1:1 divider: adjust to measured value!
constexpr bool ACS_CALIBRATED = false; // Set true only AFTER measurement/calibration
constexpr float ACS_ZERO_V = 2.500f;   // Measure with motor OFF
constexpr float ACS_SENSITIVITY_V_PER_A = 0.185f; // Example ACS712 5 A model
constexpr int PULSES_PER_REV = 1;

WiFiClient net;
PubSubClient mqtt(net);
OneWire oneWire(PIN_ONEWIRE);
DallasTemperature ds18(&oneWire);
Adafruit_ADXL345_Unified adxl = Adafruit_ADXL345_Unified(112233);
volatile uint32_t pulses = 0;
bool accelReady = false;
unsigned long lastMeasure = 0;
uint32_t seq = 0;
uint32_t bootNumber = 0;
String bootId;
uint32_t lastPulses = 0;

void IRAM_ATTR onPulse() { pulses++; }

bool clockReady() {
  time_t now = time(nullptr);
  return now > 1600000000;
}

uint64_t epochMs() {
  struct timeval tv;
  gettimeofday(&tv, nullptr);
  return (uint64_t)tv.tv_sec * 1000ULL + (uint64_t)tv.tv_usec / 1000ULL;
}

void common(JsonDocument &doc, const char* quality) {
  doc["schema_version"] = 1;
  doc["asset_id"] = "MOTOR_01";
  doc["timestamp_ms"] = epochMs();
  doc["sequence"] = seq;
  doc["run_id"] = nullptr;  // Labelled experiments: supply documented unique run_id.
  doc["boot_id"] = bootId;
  doc["quality"] = quality;
  doc["source"] = "PHYSICAL";
}

void publishDoc(const char *topic, JsonDocument &doc, bool retained = false) {
  if (!mqtt.connected()) return;
  char json[8192];
  size_t len = serializeJson(doc, json, sizeof(json));
  if (len == 0 || len >= sizeof(json)) {
    Serial.println("JSON buffer overflow; message dropped");
    return;
  }
  if (!mqtt.publish(topic, json, retained)) {
    Serial.printf("MQTT publish failed on %s\n", topic);
  }
}

void publishStatus(const char* status) {
  JsonDocument doc;
  common(doc, "VALID");
  doc["status"] = status;
  doc["firmware_version"] = "esp32-hardware-v1-unvalidated";
  doc["sensors"]["adxl345"] = accelReady;
  doc["sensors"]["ds18b20"] = ds18.getDeviceCount() > 0;
  doc["sensors"]["acs712_calibrated"] = ACS_CALIBRATED;
  publishDoc("motor01/status", doc, true);
}

void ensureNetwork() {
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.reconnect();
    return;
  }
  if (!clockReady()) return; // timestamps MUST be Unix epoch millis.
  if (mqtt.connected()) return;
  String clientId = "motor01-" + bootId;
  String offline = String("{\"schema_version\":1,\"asset_id\":\"MOTOR_01\",\"status\":\"offline\",\"source\":\"PHYSICAL\",\"boot_id\":\"") + bootId + "\"}";
  if (mqtt.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD,
                   "motor01/status", 1, true, offline.c_str())) {
    publishStatus("online");
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);
  bootId = String((uint32_t)ESP.getEfuseMac(), HEX) + "-" + String(millis());
  pinMode(PIN_HALL, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_HALL), onPulse, FALLING);
  analogReadResolution(12);
  Wire.begin(21, 22);
  accelReady = adxl.begin();
  if (accelReady) adxl.setRange(ADXL345_RANGE_16_G);
  ds18.begin();
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  // NTP first synchronization needs a reachable NTP service.
  // For offline-only deployment configure a trusted local time source.
  configTime(0, 0, "pool.ntp.org");
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(8192);
  Serial.println("Hardware monitoring firmware starting (motor control remains external)");
}

void loop() {
  ensureNetwork();
  mqtt.loop();
  if (!mqtt.connected() || !clockReady() || millis() - lastMeasure < 1000) {
    delay(20);
    return;
  }
  uint32_t elapsed = lastMeasure == 0 ? 1000 : millis() - lastMeasure;
  lastMeasure = millis();
  seq++;

  // Temperature conversion; invalid/disconnected readings are explicit.
  ds18.requestTemperatures();
  float temp = ds18.getTempCByIndex(0);
  bool temperatureValid = temp > -55.0f && temp <= 125.0f && temp != DEVICE_DISCONNECTED_C;
  JsonDocument temperature;
  common(temperature, temperatureValid ? "VALID" : "INVALID");
  temperature["unit"] = "degC";
  if (temperatureValid) temperature["value"] = temp;
  else temperature["value"] = nullptr;
  publishDoc("motor01/temperature", temperature);

  // ACS712 output must be reduced to ESP32-safe ADC voltage with divider.
  // Reporting uncalibrated data as VALID is deliberately disabled.
  float adcV = analogReadMilliVolts(PIN_ACS712_ADC) / 1000.0f;
  float sensorV = adcV * DIVIDER_GAIN;
  float amperes = fabs(sensorV - ACS_ZERO_V) / ACS_SENSITIVITY_V_PER_A;
  JsonDocument current;
  common(current, ACS_CALIBRATED ? "VALID" : "CALIBRATION_REQUIRED");
  current["unit"] = "A";
  if (ACS_CALIBRATED) current["value"] = amperes;
  else current["value"] = nullptr;
  publishDoc("motor01/current", current);

  // Hall pulses must be measured and checked against real shaft speed.
  noInterrupts();
  uint32_t pulseTotal = pulses;
  interrupts();
  uint32_t delta = pulseTotal - lastPulses;
  lastPulses = pulseTotal;
  float rpm = 60000.0f * delta / (elapsed * PULSES_PER_REV);
  JsonDocument speed;
  common(speed, "VALID");
  speed["unit"] = "rpm";
  speed["measurement_interval_ms"] = elapsed;
  speed["value"] = rpm;
  publishDoc("motor01/rpm", speed);

  JsonDocument vibration;
  common(vibration, accelReady ? "VALID" : "INVALID");
  vibration["unit"] = "g";
  vibration["sample_rate_hz"] = 100; // target, verify real effective rate
  vibration["sample_count"] = accelReady ? 50 : 0;
  JsonArray x = vibration["x"].to<JsonArray>();
  JsonArray y = vibration["y"].to<JsonArray>();
  JsonArray z = vibration["z"].to<JsonArray>();
  if (accelReady) {
    for (int i = 0; i < 50; ++i) {
      sensors_event_t event;
      adxl.getEvent(&event);
      x.add(event.acceleration.x / 9.80665f);
      y.add(event.acceleration.y / 9.80665f);
      z.add(event.acceleration.z / 9.80665f);
      delay(10);
    }
  }
  publishDoc("motor01/vibration", vibration);
  mqtt.loop();
}
