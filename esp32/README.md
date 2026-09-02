# ESP32 Sensor Node

**Status:** Planned scaffold; firmware has not yet been committed.

## Responsibility

The ESP32 acquires physical measurements and publishes structured telemetry. It should remain simple, deterministic, and independent of dashboard or model-training concerns.

Planned sensors:

- ADXL345 — three-axis vibration
- ACS712 — motor current/load
- DS18B20 — casing temperature
- Hall-effect sensor + magnet — RPM

The first MVP may enable only vibration and current. RPM should be added early where practical.

## Required Firmware Behaviour

- Initialize and self-check enabled sensors
- Use documented units, ranges, sample rates, and calibration
- Maintain asset ID, schema version, sequence, run ID, timestamp, and quality
- Publish using [the MQTT contract](../docs/MQTT_CONTRACT.md)
- Reconnect with bounded retry behaviour
- Publish online/offline device status
- Mark invalid readings explicitly
- Avoid blocking code that destroys the intended sampling rate
- Never contain real Wi-Fi or MQTT credentials in tracked source

## Suggested Development Order

1. Build a standalone test for each sensor.
2. Record verified wiring/pins and calibration.
3. Integrate the chosen MVP sensors.
4. Add structured payloads without networking.
5. Add Wi-Fi and MQTT.
6. Test broker restart, reconnect, malformed sensor data, and long runs.
7. Measure the actual vibration sample rate and payload size.
8. Freeze a firmware/data-contract version before dataset collection.

## Planned Layout

```text
esp32/
├── README.md
├── firmware/        # Integrated application
└── sensor-tests/    # One minimal test per sensor
```

Pin assignments are intentionally not invented here. Add them only after the exact ESP32 board and wiring have been verified.

## Acceptance Evidence

Firmware is ready for the next stage when real readings repeatedly reach Raspberry Pi storage with correct units, timestamps/sequences, quality flags, asset ID, and run ID, while disconnects and invalid reads are visible.
