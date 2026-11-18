/*
  Standalone ADXL345 vibration/acceleration diagnostic for ESP32.
  I2C: SDA GPIO21, SCL GPIO22. Power the module with 3.3 V.
  Requires: Adafruit ADXL345, Adafruit Unified Sensor.
  Motor power OFF. Output is SERIAL ONLY (no Wi-Fi/MQTT or motor control).
*/
#include <Arduino.h>
#include <Wire.h>
#include <math.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>

constexpr uint8_t SDA_PIN = 21;
constexpr uint8_t SCL_PIN = 22;
constexpr float EARTH_GRAVITY = 9.80665f;
Adafruit_ADXL345_Unified accelerometer(12345);
bool ready = false;
bool havePrevious = false;
bool movementObserved = false;
float previousX = 0, previousY = 0, previousZ = 0;

bool responds(uint8_t address) {
  Wire.beginTransmission(address);
  return Wire.endTransmission() == 0;
}

void setup() {
  Serial.begin(115200);
  delay(1200);
  Serial.println("\n=== ADXL345 independent sensor test ===");
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  uint8_t address = 0;
  if (responds(0x53)) address = 0x53;
  else if (responds(0x1D)) address = 0x1D;
  if (!address) {
    Serial.println("FAIL: no I2C response at 0x53 or 0x1D. Check 3.3V, GND, SDA=21, SCL=22.");
    return;
  }
  Serial.printf("I2C device answered at 0x%02X\n", address);
  if (!accelerometer.begin(address)) {
    Serial.println("FAIL: device responded but ADXL345 ID/initialization failed.");
    return;
  }
  accelerometer.setRange(ADXL345_RANGE_2_G);
  ready = true;
  Serial.println("PASS: ADXL345 initialized. Keep it still, then gently tilt each axis.");
}

void loop() {
  if (!ready) { delay(2000); return; }
  sensors_event_t event;
  accelerometer.getEvent(&event);
  float x = event.acceleration.x / EARTH_GRAVITY;
  float y = event.acceleration.y / EARTH_GRAVITY;
  float z = event.acceleration.z / EARTH_GRAVITY;
  float total = sqrtf(x*x + y*y + z*z);
  if (!isfinite(total) || total > 20.0f) {
    Serial.println("FAIL: invalid acceleration data; check sensor and wiring.");
    delay(500);
    return;
  }
  if (havePrevious &&
      (fabsf(x-previousX) > 0.15f || fabsf(y-previousY) > 0.15f ||
       fabsf(z-previousZ) > 0.15f)) {
    movementObserved = true;
  }
  havePrevious = true;
  previousX = x; previousY = y; previousZ = z;
  Serial.printf("x=%+.2f g  y=%+.2f g  z=%+.2f g  |a|=%.2f g  ",
                x, y, z, total);
  if (movementObserved) Serial.println("PASS: sensor responds to movement/tilt");
  else Serial.println("CHECK: data received; tilt sensor to confirm changing axes");
  // When stationary |a| should be roughly 1 g. This is not calibration.
  delay(500);
}
