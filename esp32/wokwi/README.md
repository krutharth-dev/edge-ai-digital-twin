# Browser Wokwi circuit — demonstration substitute

Open https://wokwi.com/projects/new/esp32 and copy the provided sketch.ino,
diagram.json and libraries.txt into the editor's matching files.

Parts: ESP32 DevKit-C V4, MPU6050, DS18B20 with 4.7k pull-up,
A4988 driver and a bipolar stepper motor. These are listed Wokwi components,
but the precise project has NOT been executed on Wokwi yet: verify all wire pin
names and compilation in Wokwi before describing it as tested.

**Not the final hardware:** stepper is a visual surrogate for the actual DC motor.
MPU6050 is used in place of ADXL345. Current and RPM are mock values. The
Serial output includes topic-prefixed JSON with *uptime* timestamps and is NOT
the real MQTT Unix epoch format. Do not publish that Serial output unmodified
into the production backend: it will be rejected as unsynchronized.

For a reproducible *end-to-end MQTT* demo, use the Mac Python simulator:
python simulator/mqtt_publisher.py --scenario normal --count 20

Actual ESP32 MQTT firmware and wiring guidance:
esp32/firmware/esp32_motor_monitor.ino and docs/MAC_RUNBOOK.md.
