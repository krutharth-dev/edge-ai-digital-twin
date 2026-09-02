# System Architecture

## Purpose

The project is a low-cost academic prototype for monitoring a 12 V DC motor/fan. It combines IoT sensing, local Edge-AI inference, an operational Digital Twin, and a live dashboard.

The core path is:

`Motor/fan → Sensors → ESP32 → Wi-Fi/MQTT → Raspberry Pi → Preprocessing/features → ML inference → Health logic → Digital Twin → Dashboard/alerts`

The earliest integration milestone ends at reliable storage of real telemetry on the Raspberry Pi. AI and dashboard work must not hide an unstable acquisition pipeline.

## Physical and Sensor Layer

The complete prototype plans to use:

| Measurement | Sensor | Primary purpose |
|---|---|---|
| Vibration | ADXL345 | Detect changes associated with imbalance and other abnormal motion |
| Temperature | DS18B20 | Track casing temperature and slow thermal changes |
| Current/load | ACS712 | Observe electrical demand and increased-load behaviour |
| RPM | Hall-effect sensor + magnet | Measure speed and separate speed effects from actual faults |

The first end-to-end MVP may begin with vibration and current and classify `Normal` versus `Abnormal`. RPM should be captured early where practical because it is an important confounder. Temperature and multi-class inference follow once the core pipeline is stable.

## ESP32 Boundary

The ESP32 is responsible for:

- Reading and timestamping sensors
- Applying only essential acquisition-time calibration or validity checks
- Maintaining sequence numbers and device status
- Packaging telemetry using the agreed schema
- Publishing over local Wi-Fi and MQTT
- Reconnecting safely after network interruptions

The ESP32 is not responsible for model training, the main ML inference pipeline, historical storage, or the Digital Twin backend.

## Raspberry Pi Boundary

The Raspberry Pi is the edge platform and is responsible for:

- Hosting or connecting to the local MQTT broker
- Subscribing to telemetry and checking schema, freshness, units, ranges, and asset ID
- Persisting raw and derived data locally
- Windowing, filtering, and extracting features
- Running the exported ML pipeline locally
- Applying health and alert logic
- Maintaining the `MOTOR_01` Digital Twin state and history
- Serving the dashboard and alerts

The core live system must not require a cloud service.

## Offline Training Boundary

Development laptops may be used for exploratory analysis and training. The deployed artifact must include or reference:

- Feature names and order
- Window and overlap definitions
- Preprocessing parameters
- Class labels
- Compatible library versions
- Dataset/run manifest
- Source commit
- Evaluation results and limitations

The Raspberry Pi must reproduce the same preprocessing and feature definitions.

## Digital Twin Boundary

Version 1 is an operational state model, not a mandatory 3D simulation. Its minimum state includes:

```json
{
  "schema_version": 1,
  "asset_id": "MOTOR_01",
  "last_updated": null,
  "telemetry": {
    "vibration": null,
    "temperature_c": null,
    "current_a": null,
    "rpm": null
  },
  "predicted_state": null,
  "confidence": null,
  "health_state": "UNKNOWN",
  "health_score": null,
  "alert_state": null,
  "data_quality": "UNKNOWN",
  "model_version": null
}
```

A dashboard visualizes this state but is not itself the complete Digital Twin.

## Required System Invariants

- Every stored measurement has an asset ID, timestamp, unit, quality indicator, and traceable run/session.
- Sensor units and sampling settings are explicit.
- Stale, malformed, or out-of-range telemetry cannot silently become a healthy state.
- Training/test separation is performed by complete experimental run.
- Model inputs on the Raspberry Pi match training-time feature definitions.
- Health and maintenance messages distinguish rule-based logic from model output.
- No short-duration project dataset is presented as validated Remaining Useful Life evidence.
- Physical safety controls do not depend on the dashboard, network, or ML model.

## Failure Behaviour

| Failure | Required behaviour |
|---|---|
| Sensor read failure | Mark the field invalid; do not substitute a believable value |
| MQTT disconnect | Buffer only within defined limits, reconnect, and expose stale status |
| Duplicate or out-of-order message | Detect using timestamp/sequence; handle deterministically |
| Missing model | Continue telemetry/storage with inference state unavailable |
| Feature/schema mismatch | Reject inference and report an explicit error |
| Stale telemetry | Change data quality and Digital Twin state to stale/unknown |
| Dashboard failure | Acquisition, storage, and safe motor control remain independent |
| Unsafe physical condition | Stop motor power using physical controls |

## Planned Deployment

All core services run on the local ESP32–Raspberry Pi network. CSV is the initial storage format. SQLite or InfluxDB may be introduced only if live history or query requirements justify the added complexity. Streamlit or Node-RED is suitable for Version 1; Grafana and 3D views are optional later enhancements.
