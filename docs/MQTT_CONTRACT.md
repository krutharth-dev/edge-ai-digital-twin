# MQTT Contract

## Status

This is the proposed Version 1 interface. Final rates, payload sizes, and QoS settings must be verified on the physical prototype before being marked stable.

Base topic: `motor01`

## Topic Ownership

| Topic | Publisher | Subscriber | Purpose |
|---|---|---|---|
| `motor01/vibration` | ESP32 | Raspberry Pi | Timestamped ADXL345 samples or windows |
| `motor01/temperature` | ESP32 | Raspberry Pi | DS18B20 temperature reading |
| `motor01/current` | ESP32 | Raspberry Pi | ACS712 current reading or sample summary |
| `motor01/rpm` | ESP32 | Raspberry Pi | Hall-derived RPM |
| `motor01/status` | ESP32 | Raspberry Pi/dashboard | Device availability and acquisition health |
| `motor01/health` | Raspberry Pi | Digital Twin/dashboard | Inferred condition, health, confidence, and data quality |
| `motor01/alerts` | Raspberry Pi | Dashboard/operator service | New or cleared warnings and maintenance messages |

Only the listed owner should publish to a topic in the core design.

## Common Envelope

Every JSON payload should contain:

```json
{
  "schema_version": 1,
  "asset_id": "MOTOR_01",
  "timestamp_ms": null,
  "clock_status": "UNSYNCED",
  "boot_id": "example-boot-001",
  "uptime_ms": 0,
  "sequence": 0,
  "run_id": null,
  "quality": "VALID"
}
```

Rules:

- `timestamp_ms` is UTC Unix epoch milliseconds **only after** device clock synchronization; use JSON `null` when unavailable, never a fictitious epoch `0`.
- `clock_status` is `SYNCED` or `UNSYNCED`. `uptime_ms` is monotonic device uptime (not UTC time).
- `boot_id` identifies the publisher's boot/session; use a new ID after restart. `sequence` increments on each topic within that boot and helps detect duplicates and reordering.
- The Raspberry Pi records an ingestion/receipt timestamp for each message and distinguishes it from source time. Freshness policy must account for unsynchronized clocks.
- `run_id` is required during labelled data collection and null during ordinary monitoring.
- `quality` is one of `VALID`, `INVALID`, `STALE`, or `CALIBRATION_REQUIRED`.
- Unknown schema versions must be rejected explicitly.
- Numeric fields must include or inherit a documented SI unit.

## Example Sensor Payloads

### Current

```json
{
  "schema_version": 1,
  "asset_id": "MOTOR_01",
  "timestamp_ms": null,
  "clock_status": "UNSYNCED",
  "boot_id": "example-boot-001",
  "uptime_ms": 0,
  "sequence": 0,
  "run_id": "normal_speed1_run01",
  "quality": "VALID",
  "value": 0.0,
  "unit": "A"
}
```

### Temperature

```json
{
  "schema_version": 1,
  "asset_id": "MOTOR_01",
  "timestamp_ms": null,
  "clock_status": "UNSYNCED",
  "boot_id": "example-boot-001",
  "uptime_ms": 0,
  "sequence": 0,
  "run_id": "normal_speed1_run01",
  "quality": "VALID",
  "value": 0.0,
  "unit": "degC"
}
```

### RPM

```json
{
  "schema_version": 1,
  "asset_id": "MOTOR_01",
  "timestamp_ms": null,
  "clock_status": "UNSYNCED",
  "boot_id": "example-boot-001",
  "uptime_ms": 0,
  "sequence": 0,
  "run_id": "normal_speed1_run01",
  "quality": "VALID",
  "value": 0.0,
  "unit": "rpm",
  "measurement_interval_ms": 0
}
```

### Vibration Window

```json
{
  "schema_version": 1,
  "asset_id": "MOTOR_01",
  "timestamp_ms": null,
  "clock_status": "UNSYNCED",
  "boot_id": "example-boot-001",
  "uptime_ms": 0,
  "sequence": 0,
  "run_id": "normal_speed1_run01",
  "quality": "VALID",
  "unit": "g",
  "sample_rate_hz": 0,
  "sample_count": 0,
  "x": [],
  "y": [],
  "z": []
}
```

The numeric zeros and empty arrays above are **schema placeholders**, not measured sensor readings or suggested sampling rates. Choose realistic values only after hardware tests.

The team may change raw vibration transport after measuring ESP32 memory, MQTT payload size, and achievable sample rate. Any change must be versioned and reflected in both firmware and Raspberry Pi parsers.

## Health Payload

```json
{
  "schema_version": 1,
  "asset_id": "MOTOR_01",
  "timestamp_ms": null,
  "clock_status": "UNSYNCED",
  "boot_id": "example-boot-001",
  "uptime_ms": 0,
  "sequence": 0,
  "quality": "VALID",
  "predicted_state": "NORMAL",
  "confidence": null,
  "health_state": "HEALTHY",
  "health_score": null,
  "model_version": null,
  "feature_version": null,
  "message": "No validated maintenance warning."
}
```

A null value is preferable to an invented confidence, score, or version.

## Status and Last Will

The ESP32 should publish a retained online status after connecting and configure an MQTT Last Will that marks it offline after an unexpected disconnect. Status should include firmware version, boot/session identifier, and sensor availability without exposing secrets.

## QoS and Retention

Initial guidance:

- High-rate vibration telemetry: QoS 0, not retained
- Slow telemetry: QoS 0 or 1 after measurement
- Status and health state: QoS 1, retained
- Alerts: QoS 1, not retained; alert state remains available through `health`

Final settings must be justified by packet loss, latency, duplicate handling, and resource tests.

## MQTT Session and Time Handling

- A reconnect within the same boot must not create a new `boot_id`. A physical reboot must.
- Use bounded queueing; QoS 1 may redeliver messages, so subscribers must deduplicate safely.
- A retained status or health message represents the most recently published state, not necessarily the current state. Apply the freshness timeout before displaying `HEALTHY`.
- Do not permit telemetry to trigger physical motor-control outputs without separately reviewed safety controls.

## Validation

The Raspberry Pi subscriber must check JSON validity, schema version, asset ID, required fields, types, ranges, units, freshness, sequence behaviour, and maximum payload size before storing or using a message for inference.
