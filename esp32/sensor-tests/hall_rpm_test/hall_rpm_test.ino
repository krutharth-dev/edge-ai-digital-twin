/*
  Standalone Hall switch / RPM pulse diagnostic for ESP32.
  Digital Hall OUT -> GPIO27 (3.3 V logic ONLY), GND common.
  Open-collector outputs need a 3.3 V pull-up; INPUT_PULLUP is enabled.
  PULSES_PER_REV must equal actual magnets/trigger events per revolution.
  First test by moving a secure magnet by hand with motor power OFF.
*/
#include <Arduino.h>

constexpr uint8_t HALL_PIN = 27;
constexpr uint32_t MIN_EDGE_INTERVAL_US = 5000; // reject chatter within 5 ms
constexpr float PULSES_PER_REV = 1.0f;            // adjust to YOUR magnet setup
volatile uint32_t totalEdges = 0;
volatile uint32_t previousEdgeUs = 0;
uint32_t lastWindowMs = 0;
uint32_t previousCount = 0;
bool everTriggered = false;

void IRAM_ATTR onMagnetEdge() {
  const uint32_t now = micros();
  if (previousEdgeUs == 0 || uint32_t(now - previousEdgeUs) >= MIN_EDGE_INTERVAL_US) {
    ++totalEdges;
    previousEdgeUs = now;
  }
}

void setup() {
  Serial.begin(115200);
  delay(1200);
  Serial.println("\n=== Hall-effect RPM pulse test ===");
  pinMode(HALL_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(HALL_PIN), onMagnetEdge, FALLING);
  lastWindowMs = millis();
  Serial.println("Move a magnet slowly past the fixed sensor; do NOT power the motor yet.");
  Serial.println("No pulses does NOT alone prove failure unless you supplied known magnetic transitions.");
}

void loop() {
  const uint32_t nowMs = millis();
  const uint32_t elapsedMs = nowMs - lastWindowMs;
  if (elapsedMs < 2000) { delay(10); return; }
  noInterrupts();
  const uint32_t count = totalEdges;
  interrupts();
  const uint32_t delta = count - previousCount;
  const float rpm = (60000.0f * delta) / (elapsedMs * PULSES_PER_REV);
  if (delta > 0) everTriggered = true;
  Serial.printf("GPIO27=%s  new_pulses=%lu  total=%lu  RPM~%.1f  ",
                digitalRead(HALL_PIN) ? "HIGH" : "LOW",
                (unsigned long)delta, (unsigned long)count, rpm);
  if (delta > 0) Serial.println("PASS: Hall transitions detected");
  else if (everTriggered) Serial.println("No transitions in this interval; magnet may be stationary");
  else Serial.println("CHECK: no transitions yet; move the magnet close to sensor face");
  previousCount = count;
  lastWindowMs = nowMs;
}
