# Eight-Week Core Roadmap

The objective is to complete the working prototype in approximately eight weeks, leaving remaining academic time for stronger validation and optional improvements.

## Week 1 — Freeze Design and Prepare Hardware

**Work**

- Confirm architecture decisions and team responsibilities
- Finalize bill of materials and rated component specifications
- Create wiring, mounting, power-isolation, and safety plans
- Define initial MQTT and data schemas
- Prepare the base, motor mount, guard, fuse, and master/emergency switch

**Exit criteria**

- Architecture and interfaces reviewed
- Safety plan accepted
- Components available or ordered
- No unresolved uncertainty that blocks individual sensor testing

## Week 2 — Build Rig and Test Sensors Individually

**Work**

- Assemble the motor/fan rig safely
- Test ADXL345, ACS712, DS18B20, and Hall sensor separately
- Record pin assignments, units, sample rates, calibration, valid ranges, and disconnect behaviour
- Decide which sensors enter the first MVP

**Exit criteria**

- Motor runs safely within ratings
- Each MVP sensor produces stable, interpretable readings
- Sensor test evidence is committed or linked

## Week 3 — ESP32 Acquisition

**Work**

- Implement structured acquisition
- Add timestamps, sequence, asset ID, run ID, quality flags, and schema version
- Validate sampling consistency and memory behaviour
- Test reconnect and sensor-failure handling

**Exit criteria**

- ESP32 continuously emits valid telemetry for the selected sensors
- No credentials are committed
- The payload matches the documented contract

## Week 4 — MQTT, Raspberry Pi, and Storage

**Work**

- Configure Mosquitto and Paho MQTT
- Validate payloads before storage
- Store live data in CSV with run metadata
- Handle reconnect, duplicates, stale messages, and malformed input

**Exit criteria**

- Physical sensor values travel through ESP32 and MQTT to Raspberry Pi storage reliably
- The core milestone is demonstrated repeatedly
- Data can be traced to asset, timestamp, and run

## Week 5 — Dataset Collection

**Work**

- Collect repeated normal runs across intended settings
- Collect safe controlled abnormal runs
- Maintain run manifest and exclusion log
- Inspect signal quality and class coverage

**Exit criteria**

- Multiple independent runs exist per selected class
- Labels and metadata are complete
- No unsafe or untraceable recording is used for ML

## Week 6 — Features and Baseline Models

**Work**

- Implement versioned windows, filtering, and features
- Split by complete runs
- Train Random Forest first; compare Gradient Boosting or SVM if useful
- Report macro-F1, class metrics, confusion matrix, false alarms, and limitations
- Export model and preprocessing metadata

**Exit criteria**

- Reproducible baseline evaluated without run leakage
- Deployed feature contract is defined
- Model choice is evidence-based

## Week 7 — Edge Inference, Digital Twin, and Dashboard

**Work**

- Deploy matching preprocessing/features/model on Raspberry Pi
- Maintain `MOTOR_01` state and data quality
- Add rule-based health and alert logic
- Build live dashboard with values, trends, state, confidence when valid, and history

**Exit criteria**

- Inference operates locally
- Live physical changes update the Digital Twin
- Stale or invalid telemetry is visible
- Dashboard makes no unsupported RUL claim

## Week 8 — Integration and Demonstration

**Work**

- Run the end-to-end test sequence repeatedly
- Measure classification, latency, false alarms, resource use, and state accuracy
- Record failure cases and limitations
- Capture approved photos/screenshots/video
- Finalize report and presentation evidence

**Exit criteria**

- Demonstration is repeatable
- Results are measured, not estimated
- Safety, architecture, source code, data manifest, model metadata, and presentation agree

## Parallel Team Workstreams

Five members may own workstreams, but every interface requires cross-review:

1. Motor rig, power, and sensor integration
2. ESP32 acquisition and MQTT publishing
3. Raspberry Pi ingestion, storage, and edge deployment
4. Data processing, features, and ML evaluation
5. Digital Twin, dashboard, testing, and documentation

Ownership should be recorded in issues and pull requests rather than fabricated in the README.

## Definition of Done

The core project is done when a safe physical condition change produces a measurable sensor response, local Raspberry Pi inference detects the condition, the Digital Twin changes automatically, the dashboard displays the correct health/alert state, and the team can reproduce and explain the result with traceable evidence.
