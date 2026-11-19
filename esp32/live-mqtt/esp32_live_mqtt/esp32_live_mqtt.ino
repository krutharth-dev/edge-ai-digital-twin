/*
 * ESP32 -> Mac MQTT -> FastAPI -> React: real sensor telemetry.
 * Standalone, Windows Arduino IDE-ready sketch (no motor control).
 *
 * ESP32-WROOM/DevKit; USB Serial at 115200.
 * ADXL345: 3.3V, GND, SDA=21, SCL=22 (I2C).
 * DS18B20: 3.3V, GND, DATA=4, 4.7k pull-up from DATA to 3.3V.
 * ACS712: sensor power per its module; conditioned 3.3V-SAFE OUT->GPIO35.
 * Hall digital switch: module power per rating; 3.3V-SAFE OUT->GPIO27.
 *
 * Arduino libraries: PubSubClient, ArduinoJson 7, Adafruit ADXL345,
 * Adafruit Unified Sensor (and BusIO dependency), OneWire, DallasTemperature.
 * Copy secrets.example.h to secrets.h (never commit or share secrets.h).
 *
 * Motor power OFF during initial bring-up. This sketch does not drive a motor.
 * No sensor is claimed calibrated or verified until it actually has been.
 */
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <math.h>
#include <time.h>
#include <esp_system.h>
#include "secrets.h"

constexpr int PIN_ONEWIRE = 4;
constexpr int PIN_ADC = 35;
constexpr int PIN_HALL = 27;
constexpr int I2C_SDA = 21;
constexpr int I2C_SCL = 22;

// Do not set these flags true until bench verification/calibration is complete.
#ifndef ACS_INTERFACE_VERIFIED
#define ACS_INTERFACE_VERIFIED false
#endif
constexpr bool ACS_CALIBRATED = false;
constexpr bool HALL_TESTED_AND_PPR_VERIFIED = false;

// MUST match the actual measured ACS712 interface and fitted model.
constexpr float DIVIDER_GAIN = 2.0f;        // Example 10k / 10k divider
constexpr float ACS_ZERO_VOLTS = 2.500f;    // Replace with measured zero-current sensor output
constexpr float ACS_VOLTS_PER_AMP = 0.185f; // 5A=0.185; 20A=0.100; 30A=0.066 nominal
constexpr float HALL_PULSES_PER_REV = 1.0f; // Must match actual magnets/edges per revolution

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
OneWire oneWire(PIN_ONEWIRE);
DallasTemperature ds18(&oneWire);
Adafruit_ADXL345_Unified adxl(12345);

volatile uint32_t hallEdges = 0;
volatile uint32_t lastHallEdgeUs = 0;
uint32_t previousEdges = 0;
uint32_t previousCycleMs = 0;
uint32_t lastWifiAttemptMs = 0;
uint32_t lastMqttAttemptMs = 0;
uint32_t lastClockNoticeMs = 0;
uint32_t sequence = 0;
uint8_t adxlAddress = 0;
bool findAccelerometer() {
  for (uint8_t address : {0x53, 0x1D}) {
    Wire.beginTransmission(address);
    Wire.write((uint8_t)0x00);
    if (Wire.endTransmission(false) != 0) continue;
    if (Wire.requestFrom(address, (uint8_t)1) != 1 || Wire.read() != 0xE5) continue;
    if (address != adxlAddress && !adxl.begin(address)) continue;
    adxlAddress = address;
    return true;
  }
  adxlAddress = 0;
  return false;
}
bool adxlReady = false;
bool dsReady = false;
String bootId;

void IRAM_ATTR onHallEdge() {
  uint32_t now = micros();
  if (lastHallEdgeUs == 0 || (uint32_t)(now - lastHallEdgeUs) >= 5000) {
    ++hallEdges;
    lastHallEdgeUs = now;
  }
}

bool timeReady() {
  return time(nullptr) > 1700000000; // Real Unix epoch required by backend validator.
}

uint64_t timestampMs() {
  struct timeval tv;
  gettimeofday(&tv, nullptr);
  return uint64_t(tv.tv_sec) * 1000ULL + uint64_t(tv.tv_usec) / 1000ULL;
}

void setEnvelope(JsonDocument &doc, const char *quality) {
  doc["schema_version"] = 1;
  doc["asset_id"] = "MOTOR_01";
  doc["timestamp_ms"] = timestampMs();
  doc["sequence"] = sequence;
  doc["firmware_version"] = "esp32-react-live-v2";
  doc["run_id"] = nullptr;
  doc["boot_id"] = bootId;
  doc["source"] = "PHYSICAL";
  doc["quality"] = quality;
}

void publish(const char *topic, JsonDocument &doc, bool retain = false) {
  if (!mqtt.connected()) return;
  static char buffer[8192];
  size_t length = measureJson(doc);
  if (length == 0 || length + 1 > sizeof(buffer)) {
    Serial.printf("ERROR: MQTT JSON payload too large for %s\n", topic);
    return;
  }
  serializeJson(doc, buffer, sizeof(buffer));
  if (mqtt.publish(topic, buffer, retain)) {
    Serial.printf("TX %s %s\n", topic, buffer);
  } else {
    Serial.printf("ERROR: MQTT publish failed: %s\n", topic);
  }
}

void publishDeviceStatus() {
  JsonDocument status;
  setEnvelope(status, "VALID");
  status["status"] = "online";
  status["firmware_version"] = "esp32-react-live-v2";
  status["sensors"]["adxl345_detected"] = adxlReady;
  status["sensors"]["ds18b20_detected"] = dsReady;
  status["sensors"]["acs712_calibrated"] = ACS_CALIBRATED;
  status["sensors"]["hall_ppr_verified"] = HALL_TESTED_AND_PPR_VERIFIED;
  publish("motor01/status", status, true);
}

void ensureNetwork() {
  const uint32_t now = millis();
  if (WiFi.status() != WL_CONNECTED) {
    if (now - lastWifiAttemptMs >= 5000) {
      lastWifiAttemptMs = now;
      WiFi.reconnect();
      Serial.println("Wi-Fi not connected; retrying (check 2.4 GHz access and SSID)");
    }
    return;
  }
  if (!timeReady()) {
    if (now - lastClockNoticeMs >= 5000) {
      lastClockNoticeMs = now;
      Serial.println("Waiting for NTP clock; accurate time is REQUIRED for the Digital Twin");
    }
    return;
  }
  if (mqtt.connected()) return;
  if (now - lastMqttAttemptMs < 5000) return;
  lastMqttAttemptMs = now;
  String clientId = "motor01-" + bootId;
  String will = String("{\"asset_id\":\"MOTOR_01\",\"status\":\"offline\",\"source\":\"PHYSICAL\",\"boot_id\":\"") + bootId + "\"}";
  if (mqtt.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD,
                   "motor01/status", 1, true, will.c_str())) {
    Serial.println("MQTT CONNECTED to Mac broker; publishing PHYSICAL sensor data");
    publishDeviceStatus();
  } else {
    Serial.printf("MQTT connection failed, state=%d; check Mac IP, port, firewall and credentials\n", mqtt.state());
  }
}

void setup() {
  Serial.begin(115200);
  delay(900);
  Serial.println("\n=== MOTOR_01 ESP32 -> React live integration ===");
  Serial.println("Motor control is DISABLED by design.");
  bootId = String((uint32_t)ESP.getEfuseMac(), HEX) + "-" + String(esp_random(), HEX);

  Wire.begin(I2C_SDA, I2C_SCL);
  // Boards can strap ADXL345 ADDR/SDO to either supported I2C address.
  adxlReady = findAccelerometer();
  if (adxlReady) adxl.setRange(ADXL345_RANGE_2_G);
  ds18.begin();
  ds18.setWaitForConversion(false);
  ds18.requestTemperatures();
  dsReady = ds18.getDeviceCount() > 0;
  Serial.printf("ADXL345: %s | DS18B20: %s\n",
                adxlReady ? "DETECTED" : "MISSING",
                dsReady ? "DETECTED" : "MISSING");

  pinMode(PIN_HALL, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_HALL), onHallEdge, FALLING);
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_ADC, ADC_11db);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  configTime(0, 0, "pool.ntp.org");
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  if (!mqtt.setBufferSize(8192)) Serial.println("WARNING: cannot allocate MQTT buffer");
  Serial.printf("MQTT target: %s:%u\n", MQTT_HOST, (unsigned)MQTT_PORT);
  Serial.println("Current and RPM are CALIBRATION_REQUIRED until explicitly verified.");
}

void loop() {
  ensureNetwork();
  mqtt.loop();
  if (!mqtt.connected() || !timeReady()) {
    delay(25);
    return;
  }

  const uint32_t now = millis();
  if (previousCycleMs != 0 && now - previousCycleMs < 1000) {
    delay(20);
    return;
  }
  const uint32_t elapsedMs = previousCycleMs == 0 ? 1000 : now - previousCycleMs;
  const bool havePulseWindow = previousCycleMs != 0;
  previousCycleMs = now;
  ++sequence;

  const float tempC = ds18.getTempCByIndex(0);
  dsReady = tempC != DEVICE_DISCONNECTED_C;
  ds18.requestTemperatures();
  const bool tempValid = dsReady && isfinite(tempC) &&
    tempC >= -40.0f && tempC <= 125.0f && tempC != DEVICE_DISCONNECTED_C;
  JsonDocument temperature;
  setEnvelope(temperature, tempValid ? "VALID" : "INVALID");
  if (!dsReady) temperature["sensor_status"] = "SENSOR_DISCONNECTED";
  temperature["unit"] = "degC";
  if (tempValid) temperature["value"] = tempC;
  else temperature["value"] = nullptr;
  publish("motor01/temperature", temperature);

  const float adcV = ACS_INTERFACE_VERIFIED ? analogReadMilliVolts(PIN_ADC) / 1000.0f : NAN;
  const bool adcSafe = isfinite(adcV) && adcV > 0.05f && adcV < 3.05f;
  const bool currentValid = ACS_CALIBRATED && adcSafe && ACS_VOLTS_PER_AMP > 0;
  JsonDocument current;
  setEnvelope(current, currentValid ? "VALID" : "CALIBRATION_REQUIRED");
  if (isfinite(adcV)) current["adc_voltage_v"] = adcV;
  current["unit"] = "A";
  if (currentValid) {
    const float sensorV = adcV * DIVIDER_GAIN;
    current["value"] = fabsf(sensorV - ACS_ZERO_VOLTS) / ACS_VOLTS_PER_AMP;
  } else {
    current["value"] = nullptr;
  }
  publish("motor01/current", current);

  noInterrupts();
  const uint32_t edges = hallEdges;
  interrupts();
  const uint32_t newEdges = edges - previousEdges;
  previousEdges = edges;
  const bool hallValid = havePulseWindow && HALL_TESTED_AND_PPR_VERIFIED && HALL_PULSES_PER_REV > 0;
  JsonDocument speed;
  setEnvelope(speed, hallValid ? "VALID" : "CALIBRATION_REQUIRED");
  speed["pulse_count"] = newEdges;
  speed["total_pulses"] = edges;
  speed["unit"] = "rpm";
  speed["measurement_interval_ms"] = elapsedMs;
  if (hallValid) speed["value"] = 60000.0f * newEdges / (elapsedMs * HALL_PULSES_PER_REV);
  else speed["value"] = nullptr;
  publish("motor01/rpm", speed);

  adxlReady = findAccelerometer();
  JsonDocument vibration;
  setEnvelope(vibration, adxlReady ? "VALID" : "INVALID");
  if (!adxlReady) vibration["sensor_status"] = "SENSOR_DISCONNECTED";
  vibration["unit"] = "g";
  JsonArray x = vibration["x"].to<JsonArray>();
  JsonArray y = vibration["y"].to<JsonArray>();
  JsonArray z = vibration["z"].to<JsonArray>();
  const uint32_t startUs = micros();
  if (adxlReady) {
    for (int i = 0; i < 50; ++i) {
      sensors_event_t event;
      adxl.getEvent(&event);
      x.add(event.acceleration.x / 9.80665f);
      y.add(event.acceleration.y / 9.80665f);
      z.add(event.acceleration.z / 9.80665f);
      delay(10);
    }
  }
  const uint32_t durationUs = micros() - startUs;
  vibration["sample_count"] = adxlReady ? 50 : 0;
  vibration["sample_rate_hz"] = adxlReady && durationUs > 0
    ? (50.0f * 1000000.0f / durationUs) : 0.0f;
  publish("motor01/vibration", vibration);
  mqtt.loop();
}
