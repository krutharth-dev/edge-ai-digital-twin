# Raspberry Pi Edge Platform

**Status:** Planned scaffold; edge-service code has not yet been committed.

## Responsibility

The Raspberry Pi is the main edge computer. It receives MQTT telemetry, validates and stores it, creates synchronized feature windows, runs local inference, applies health logic, maintains `MOTOR_01`, and serves dashboard/alert data.

## Planned Service Flow

`MQTT subscriber → Schema/freshness validation → Raw storage → Windowing/filtering/features → Model inference → Health logic → Digital Twin state/history → Dashboard/alerts`

Telemetry and storage should continue when the model or dashboard is unavailable. A missing or incompatible model must produce an explicit unavailable/error state, not a guessed result.

## Initial Stack

- Raspberry Pi OS
- Python 3 in a virtual environment
- Mosquitto
- Paho MQTT
- NumPy, Pandas, and SciPy
- scikit-learn and Joblib
- CSV initially
- Streamlit or Node-RED for Version 1

Install the initial Python environment with:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

This command is a setup target, not evidence that the current repository already contains runnable services.

## Planned Layout

```text
raspberry-pi/
├── README.md
├── mqtt/              # Subscriber, validation, and status
├── storage/           # Raw/derived persistence
├── preprocessing/     # Windowing, filtering, and features
├── inference/         # Artifact loading and live prediction
└── health-monitoring/ # Health mapping, alerts, and events
```

## Configuration

Read hostnames, paths, credentials, and deployment settings from local configuration based on `.env.example`. Do not hard-code secrets. Validate MQTT payloads before storage or inference.

## Acceptance Evidence

The edge platform is ready when it can survive restart/reconnect tests, store traceable telemetry, reject malformed/stale data, reproduce training-time features, run the selected model locally, and update the Digital Twin without depending on cloud services.
