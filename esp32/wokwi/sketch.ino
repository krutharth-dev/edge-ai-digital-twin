/* WOKWI SERIAL-ONLY integration substitute.
 * MPU6050 is not ADXL345. A4988+stepper is not a DC motor.
 * Current is MOCK; RPM is a command-derived approximation, not a Hall measurement.
 * All messages are tagged SIMULATED and printed on Serial; see Mac simulator
 * for MQTT transport verification. No remote broker connectivity is claimed.
 */
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>

constexpr int PIN_ONEWIRE = 4;
constexpr int PIN_STEP = 18;
constexpr int PIN_DIR = 19;
Adafruit_MPU6050 imu;
OneWire ow(PIN_ONEWIRE);
DallasTemperature thermometer(&ow);
bool imuOK = false;
unsigned long sequence = 0;

void publish(const char *topic, JsonDocument &doc) {
  doc["schema_version"] = 1;
  doc["asset_id"] = "MOTOR_01";
  doc["timestamp_ms"] = (uint64_t)millis(); // uptime, NOT synchronized epoch
  doc["clock_status"] = "UNSYNCED";
  doc["sequence"] = sequence;
  doc["run_id"] = "wokwi_demo";
  doc["quality"] = "VALID";
  doc["source"] = "SIMULATED";
  Serial.print(topic); Serial.print(" ");
  serializeJson(doc, Serial); Serial.println();
}

void setup() {
  Serial.begin(115200);
  Wire.begin(21,22);
  imuOK = imu.begin();
  thermometer.begin();
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  digitalWrite(PIN_DIR, HIGH);
  Serial.println("WOKWI MOCK simulation started; local-only Serial telemetry");
}

void loop() {
  sequence++;
  for (int i=0; i<100; ++i) {
    digitalWrite(PIN_STEP, HIGH); delayMicroseconds(750);
    digitalWrite(PIN_STEP, LOW); delayMicroseconds(750);
  }
  thermometer.requestTemperatures();
  JsonDocument temp;
  temp["unit"] = "degC";
  temp["value"] = thermometer.getTempCByIndex(0);
  publish("motor01/temperature", temp);

  JsonDocument current;
  current["unit"] = "A";
  current["value"] = 0.45; // simulated; no ACS712 component in this circuit
  publish("motor01/current", current);

  JsonDocument speed;
  speed["unit"] = "rpm";
  speed["value"] = 300; // simulated only, not measured from the motor
  speed["measurement_interval_ms"] = 1000;
  publish("motor01/rpm", speed);

  JsonDocument vibration;
  vibration["unit"] = "g";
  vibration["sample_rate_hz"] = 20;
  vibration["sample_count"] = 20;
  JsonArray x = vibration["x"].to<JsonArray>();
  JsonArray y = vibration["y"].to<JsonArray>();
  JsonArray z = vibration["z"].to<JsonArray>();
  for (int i=0; i<20; ++i) {
    sensors_event_t a, gyro, t;
    if (imuOK) {
      imu.getEvent(&a, &gyro, &t);
      x.add(a.acceleration.x/9.80665f);
      y.add(a.acceleration.y/9.80665f);
      z.add(a.acceleration.z/9.80665f);
    } else {
      x.add(0); y.add(0); z.add(1);
    }
    delay(50);
  }
  publish("motor01/vibration", vibration);
}
