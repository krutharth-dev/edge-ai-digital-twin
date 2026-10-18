# Edge-AI Predictive Maintenance + Digital Twin

[![Software CI](https://github.com/krutharth-dev/edge-ai-digital-twin/actions/workflows/software-tests.yml/badge.svg?branch=main)](https://github.com/krutharth-dev/edge-ai-digital-twin/actions/workflows/software-tests.yml) [![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) ![Python 3.12](https://img.shields.io/badge/python-3.12-blue) ![Academic prototype](https://img.shields.io/badge/status-software%20MVP-orange)

**Local, Mac-hosted condition monitoring for a DC motor/fan.** The software combines ESP32/IoT telemetry, MQTT, SQLite, optional Edge-AI fault classification, an operational Digital Twin, and a live Streamlit dashboard.

**Current stage:** The **software demonstration MVP is implemented and automatically tested**. Physical motor integration, ESP32/Wokwi compilation, calibration, and real-world fault-detection accuracy **have not been verified**.

[Mac runbook](docs/MAC_RUNBOOK.md) · [Workflow diagrams](docs/WORKFLOWS.md) · [Pull-request guide](docs/PR_GUIDE.md) · [Implementation status](docs/IMPLEMENTATION_STATUS.md) · [MQTT contract](docs/MQTT_CONTRACT.md) · [Hardware safety](docs/SAFETY.md)

## Overview

The project models a small rotating asset, **MOTOR_01**, using four types of measurement:

| Measurement | Intended physical sensor | Primary use |
| --- | --- | --- |
| Vibration (3-axis acceleration) | ADXL345 | Identify changes in motor vibration |
| Temperature | DS18B20 | Track motor-casing temperature |
| Current | ACS712 | Monitor electrical load |
| Speed | Hall-effect sensor + magnet | Measure motor RPM |

An **ESP32** is the intended acquisition node. A **MacBook** replaces the Raspberry Pi as the local edge computer and runs data ingestion, feature extraction, inference, storage, and visualization. A Raspberry Pi is **not required** for the current prototype.

For development without physical hardware, a Python simulator publishes **explicitly labelled synthetic data** through the same MQTT sensor topics. The Wokwi circuit is a separate visual/firmware surrogate and is not the final physical DC-motor circuit.

## System architecture

~~~mermaid
flowchart LR
    M["DC motor / fan"] --> S["ADXL345 · DS18B20 · ACS712 · Hall"]
    S --> E["ESP32 sensor node"]
    E --> Q["Wi-Fi / MQTT broker"]
    X["Python scenario simulator<br/>SYNTHETIC DATA"] -.-> Q

    subgraph MAC["MacBook: local edge computer"]
        B["MQTT ingestion<br/>schema and quality checks"]
        DB[("SQLite history")]
        F["Signal features"]
        ML["Optional Random Forest inference"]
        T["Operational Digital Twin<br/>health rules and freshness"]
        UI["Streamlit dashboard"]
        A["Alert / state history"]
        B --> DB
        B --> F --> ML --> T
        B --> T
        T --> DB
        T --> A
        DB --> UI
        T --> UI
    end
    Q --> B
~~~

The Digital Twin is a **stateful software representation**, not just a chart. It tracks available measurements, timestamps, data quality, health status, state changes, and alerts.

## Implementation status

| Capability | Status |
| --- | --- |
| Python MQTT publisher and receiver | Implemented; local publisher/receiver tested |
| Version 1 sensor JSON validation | Implemented; unit tests |
| SQLite telemetry history and Digital Twin snapshots | Implemented; automated integration tests |
| Digital Twin states: UNKNOWN / HEALTHY / WARNING / FAULT | Implemented using illustrative demonstration thresholds |
| Freshness handling, historical trends, alert transitions | Implemented; automated tests |
| Streamlit monitoring dashboard | Implemented; **launch on your Mac to verify appearance** |
| Synthetic scenario generator (normal, imbalance, overload, thermal) | Implemented; simulated data only |
| Random Forest training and optional local inference | Implemented; synthetic model is **not** validated on real faults |
| Export and run-wise training from labelled physical sensor data | Tools implemented; labelled real dataset still required |
| ESP32 physical firmware and Wokwi substitute | Source included; **not confirmed compiled or hardware-tested** |
| Real sensors, calibration, physical motor fault trials | Pending |

All example thresholds and synthetic model results are for **software demonstration**, not motor protection, certified predictive-maintenance accuracy, or Remaining Useful Life (RUL).

## Quick start — Mac software demo

Prerequisites: **Python 3.12**, the dependencies in requirements.txt, and a local MQTT broker such as **Mosquitto**. On the existing Intel Mac setup, Mosquitto was installed using MacPorts at /opt/local/sbin/mosquitto.

### 1. Download and prepare

For a **new checkout**:

~~~bash
git clone https://github.com/krutharth-dev/edge-ai-digital-twin.git
cd edge-ai-digital-twin
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
~~~

If the repository **already exists** on your Mac, do not clone it again. Instead see [safe Git pull instructions](docs/MAC_RUNBOOK.md) and activate your existing environment.

Optional environment diagnostic:

~~~bash
python scripts/check_environment.py
~~~

### 2. Check the MQTT broker

~~~bash
lsof -nP -iTCP:1883 -sTCP:LISTEN
~~~

If **nothing** is listening and you have the previously installed MacPorts Mosquitto, start a local development broker in its own Terminal:

~~~bash
/opt/local/sbin/mosquitto -v
~~~

Leave it running. Do **not** launch a second broker on port 1883 if one is already active. The default local-only broker supports the Mac demo; a physical ESP32 needs a separately configured authenticated LAN listener.

### 3. Start the backend, dashboard, and simulator

Open **three separate Terminal windows** in the project directory. Activate .venv in each window.

**Terminal A — backend and live Digital Twin**

~~~bash
source .venv/bin/activate
python raspberry-pi/live_service.py
~~~

**Terminal B — dashboard**

~~~bash
source .venv/bin/activate
python -m streamlit run dashboard/app.py
~~~

Open the local URL shown by Streamlit (usually [http://localhost:8501](http://localhost:8501)).

**Terminal C — simulator**

~~~bash
source .venv/bin/activate
python simulator/mqtt_publisher.py --scenario normal --count 20
python simulator/mqtt_publisher.py --scenario imbalance --count 20
python simulator/mqtt_publisher.py --scenario overload --count 20
python simulator/mqtt_publisher.py --scenario thermal --count 20
python simulator/mqtt_publisher.py --scenario normal --count 20
~~~

Run those scenarios **one at a time** to see rule-based condition transitions, charts, and alerts. If telemetry stops for more than the configured freshness interval, the current health state becomes **UNKNOWN**, not HEALTHY.

> Use raspberry-pi/live_service.py for the complete system. The older raspberry-pi/mqtt_receiver.py is an introductory receiver/logger; do not run both as active database writers during the same demo.

## Edge-AI model training

### Synthetic model — software demonstration only

~~~bash
python ai/train_model.py
~~~

Then stop the ordinary live service and restart it with the **trusted locally generated model**:

~~~bash
python raspberry-pi/live_service.py --model ai/models/motor_demo.joblib --allow-demo-model
~~~

The training code splits **whole synthetic experimental runs** rather than randomly splitting adjacent samples. Its evaluation **does not establish accuracy on real motors**. Model files and datasets are ignored by Git.

### Physical model — after collecting real experimental data

Record unique run IDs and correct labels for independently repeated, safe physical experiments. See the [data-collection protocol](docs/DATA_COLLECTION_PROTOCOL.md). Prepare a CSV manifest containing run_id,label, then use:

~~~bash
python ai/export_real_features.py --labels data/run_labels.example.csv
python ai/train_real.py --input data/processed/real_features.csv
~~~

The example manifest is a **format template**: replace its entries with IDs and labels actually present in your physical dataset. The real-training script requires enough independent runs per class and reports run-separated evaluation metrics. No valid physical performance claims can be made before collecting and checking those data.

## MQTT data contract

Sensor measurements use the existing **motor01/** topic namespace:

| Topic | Purpose |
| --- | --- |
| motor01/temperature | Temperature in degC |
| motor01/current | Motor current in A |
| motor01/rpm | Rotational speed in rpm |
| motor01/vibration | Three-axis acceleration window in g |
| motor01/status | Device availability and acquisition status |
| motor01/health | Local health assessment and optional ML result |
| motor01/alerts | State-change and maintenance warnings |

The common JSON envelope contains schema_version, asset_id, Unix-epoch timestamp_ms, sequence, run_id, and quality. See the [MQTT contract](docs/MQTT_CONTRACT.md) for full payloads, sampling details and units.

The Mac demo defaults to 127.0.0.1:1883. For a physical ESP32, use the [authenticated Mac LAN MQTT guide](docs/LAN_MQTT_SETUP.md), a reachable Mac LAN address, and synchronized timestamps. Do not commit Wi-Fi passwords, MQTT credentials, or generated private keys.

## Repository guide

~~~text
edge-ai-digital-twin/
├── ai/                # Synthetic and real-data ML training
├── dashboard/         # Streamlit dashboard
├── data/              # Data conventions and ignored local SQLite database
├── digital-twin/      # Digital Twin design notes
├── docs/              # Architecture, runbooks, MQTT, experiments, safety
├── edge_ai_twin/      # Validation, features, state, storage, inference
├── esp32/
│   ├── firmware/      # Physical ESP32 reference code
│   └── wokwi/         # Browser simulation surrogate (not final DC motor)
├── raspberry-pi/      # Legacy folder name; contains Mac-hosted MQTT services
├── scripts/           # Environment diagnostic
├── simulator/         # Synthetic MQTT sensor publisher
├── tests/             # Unit and integration tests
├── requirements.txt
├── requirements-dev.txt
└── README.md
~~~

The raspberry-pi/ folder is retained for backwards compatibility with earlier project paths; the live backend **runs on the Mac**.

## Testing and quality checks

~~~bash
python -m pytest -q tests/test_software_mvp.py tests/test_real_training.py
python -m compileall -q edge_ai_twin ai dashboard raspberry-pi simulator
~~~

The GitHub Actions software workflow runs these checks and an MQTT end-to-end smoke test with a disposable database. To run the same integration test locally, first provide a test broker on port **18884**, then run:

~~~bash
python tests/smoke_mqtt.py --port 18884
~~~

Tests validate **software behavior**, not calibration, physical safety, or the true accuracy of motor-fault classification.

## Hardware and safety

The intended physical prototype uses an ESP32, a low-voltage DC motor/fan, four sensors, a rated motor driver and power supply, a fuse/master cutoff, proper motor mounting, and a guard around rotating components.

- Do **not** supply a 12 V motor directly from ESP32 GPIO.
- Do **not** expose an ESP32 ADC to a 5 V ACS712 output without verified level conditioning.
- Calibrate sensor zero offsets, sampling intervals, RPM pulse count, and measured operating limits before enabling physical monitoring.
- Do not rely on the dashboard, MQTT or machine-learning code as the sole emergency-stop mechanism.

See [safety guidance](docs/SAFETY.md), [physical integration status](docs/IMPLEMENTATION_STATUS.md), and [Wokwi limitations](esp32/wokwi/README.md).

## Documentation

| Document | Contents |
| --- | --- |
| [Mac runbook](docs/MAC_RUNBOOK.md) | Existing checkout, setup, launch, simulator and hardware boundaries |
| [Implementation status](docs/IMPLEMENTATION_STATUS.md) | What is implemented versus requiring validation |
| [MQTT contract](docs/MQTT_CONTRACT.md) | Topics, payload envelope and validity rules |
| [Architecture](docs/ARCHITECTURE.md) | Original system design and engineering constraints |
| [Data protocol](docs/DATA_COLLECTION_PROTOCOL.md) | Run labels, sensor collection and leakage-safe splits |
| [Test plan](docs/TEST_PLAN.md) | Planned physical, embedded and end-to-end evidence |
| [LAN MQTT](docs/LAN_MQTT_SETUP.md) | Private-network ESP32-to-Mac broker authentication |
| [Safety](docs/SAFETY.md) | Electrical and mechanical experiment precautions |

The architecture and roadmap documents also preserve the earlier Raspberry Pi design for research traceability; the **Mac runbook is authoritative for this implementation**.

## Contributing

Changes should be made on a feature branch and submitted through a reviewed pull request. Include tests or reproducible screenshots/logs for the behavior changed. Never commit secrets, private raw recordings, trained binaries, or the local SQLite database. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Released under the [MIT License](LICENSE).

---

**Academic prototype · Software MVP available · Physical validation in progress**
