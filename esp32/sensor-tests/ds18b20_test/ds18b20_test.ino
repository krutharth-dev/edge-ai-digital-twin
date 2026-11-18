/*
  Standalone DS18B20 temperature diagnostic for ESP32.
  DATA GPIO4 with a 4.7k pull-up resistor to 3.3 V, VDD 3.3 V, common GND.
  Requires: OneWire and DallasTemperature.
  Motor power OFF. Serial-only, no Wi-Fi/MQTT or motor control.
*/
#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <math.h>

constexpr uint8_t DATA_PIN = 4;
OneWire bus(DATA_PIN);
DallasTemperature temperature(&bus);
DeviceAddress probeAddress;
bool ready = false;

void printAddress(const DeviceAddress address) {
  for (uint8_t i = 0; i < 8; ++i) {
    if (address[i] < 16) Serial.print('0');
    Serial.print(address[i], HEX);
  }
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  delay(1200);
  Serial.println("\n=== DS18B20 independent sensor test ===");
  temperature.begin();
  if (temperature.getDeviceCount() == 0 || !temperature.getAddress(probeAddress, 0)) {
    Serial.println("FAIL: no 1-Wire temperature probe found. Check 4.7k pull-up and GPIO4.");
    return;
  }
  Serial.print("PASS: DS18B20 detected, ROM=");
  printAddress(probeAddress);
  temperature.setResolution(probeAddress, 12);
  ready = true;
  Serial.println("Gently warm the probe with your fingers; temperature should rise.");
}

void loop() {
  if (!ready) { delay(2000); return; }
  temperature.requestTemperatures(); // waits for conversion
  float celsius = temperature.getTempC(probeAddress);
  if (celsius == DEVICE_DISCONNECTED_C || !isfinite(celsius) ||
      celsius < -55.0f || celsius > 125.0f) {
    Serial.println("FAIL: disconnected probe or invalid temperature (often -127 C).");
  } else if (fabsf(celsius - 85.0f) < 0.01f) {
    Serial.println("CHECK: 85 C can indicate the DS18B20 power-on default; verify wiring/conversion.");
  } else {
    Serial.printf("PASS: %.2f C (%.2f F). Confirm it changes when gently warmed.\n",
                  celsius, celsius * 9.0f / 5.0f + 32.0f);
  }
  delay(1000);
}
