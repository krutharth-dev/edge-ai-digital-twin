/*
  Standalone ACS712 analog signal and zero-offset diagnostic for ESP32.
  Sensor OUT -> VERIFIED voltage divider / level shifter -> GPIO35 (ADC1).
  IMPORTANT: ESP32 pins are NOT 5 V tolerant. Never attach raw 5 V ACS712 OUT.
  Start with NO LOAD CURRENT; the first reading is the zero-current reference.
  Motor power OFF. This does not validate accuracy or substitute for a meter.
*/
#include <Arduino.h>
#include <math.h>

constexpr uint8_t ADC_PIN = 35;
constexpr float DIVIDER_GAIN = 2.0f;    // Example: 10k top / 10k bottom => 2x
constexpr float SENSITIVITY_V_PER_A = 0.185f; // 5A=0.185; 20A=0.100; 30A=0.066
constexpr unsigned SAMPLES = 64;
float zeroSensorVolts = 0.0f;
bool baselineValid = false;

float averageAdcVolts() {
  double millivolts = 0;
  for (unsigned i = 0; i < SAMPLES; ++i) {
    millivolts += analogReadMilliVolts(ADC_PIN);
    delay(4);
  }
  return float(millivolts / SAMPLES / 1000.0);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== ACS712 independent ADC signal test ===");
  Serial.println("REQUIRED: check with a meter that voltage at GPIO35 NEVER exceeds 3.3 V.");
  Serial.println("Motor/load OFF now; capturing zero-current reference in 3 seconds.");
  analogReadResolution(12);
  analogSetPinAttenuation(ADC_PIN, ADC_11db);
  delay(3000);
  float adcVolts = averageAdcVolts();
  if (!isfinite(adcVolts) || adcVolts < 0.05f || adcVolts > 3.05f) {
    Serial.printf("CHECK: ADC %.3f V is near a rail. Verify power, OUT, GND and divider.\n", adcVolts);
    return;
  }
  zeroSensorVolts = adcVolts * DIVIDER_GAIN;
  baselineValid = true;
  Serial.printf("ADC zero=%.3f V; sensor zero~%.3f V (divider gain %.2f)\n",
                adcVolts, zeroSensorVolts, DIVIDER_GAIN);
  Serial.println("PASS: plausible ADC baseline ONLY; NOT proof of current measurement.");
  Serial.println("For a full check, apply a known SAFE fused DC load through ACS712 IP+/IP-.");
  Serial.println("Compare measured current with a multimeter and verify change and direction.");
}

void loop() {
  if (!baselineValid) { delay(2000); return; }
  float adcVolts = averageAdcVolts();
  if (!isfinite(adcVolts) || adcVolts < 0.05f || adcVolts > 3.05f) {
    Serial.printf("FAIL/CHECK: ADC input %.3f V near rail; stop and inspect connections.\n", adcVolts);
    delay(800);
    return;
  }
  float sensorVolts = adcVolts * DIVIDER_GAIN;
  float estimateA = (sensorVolts - zeroSensorVolts) / SENSITIVITY_V_PER_A;
  Serial.printf("ADC=%.3f V  ACS_OUT~%.3f V  delta=%+.3f V  estimate=%+.2f A  ",
                adcVolts, sensorVolts, sensorVolts-zeroSensorVolts, estimateA);
  if (fabsf(sensorVolts-zeroSensorVolts) > 0.03f) {
    Serial.println("CHANGE detected; compare against known load/meter (NOT calibrated)");
  } else {
    Serial.println("No clear load change; zero load or wrong wiring/low signal");
  }
  delay(800);
}
