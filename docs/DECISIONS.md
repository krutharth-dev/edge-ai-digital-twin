# Architecture Decisions

This file records accepted project decisions. A change that affects one of these decisions should be discussed by the team and documented in a pull request.

## AD-001 — Prototype Asset

**Status:** Accepted

Use a small, securely mounted 12 V DC motor/fan as the initial rotating-machine testbed. The prototype is designed to demonstrate the complete monitoring pipeline at low cost before any industrial-scale extension.

## AD-002 — Split ESP32 and Raspberry Pi Responsibilities

**Status:** Accepted

The ESP32 performs sensor acquisition and MQTT communication. The Raspberry Pi performs storage, preprocessing, feature extraction, local inference, health logic, Digital Twin services, and dashboard hosting.

**Reason:** This keeps real-time acquisition simple while placing heavier and more changeable software on the edge computer.

## AD-003 — Local Edge Inference

**Status:** Accepted

Live inference must run locally on the Raspberry Pi. Cloud processing is not required for the core system.

## AD-004 — Classical ML First

**Status:** Accepted

Start with engineered features and a Random Forest baseline. Compare Gradient Boosting or SVM only when useful. Attempt CNN/LSTM models only if the dataset and baseline results justify the added complexity.

## AD-005 — Staged Sensor and Class Scope

**Status:** Accepted

The first complete loop may use ADXL345 vibration and ACS712 current for `Normal` versus `Abnormal`. The complete prototype adds temperature, RPM, and the controlled classes `Normal`, `Controlled imbalance`, `Increased load / overload`, and `Thermal abnormality`.

RPM should be captured early where practical because speed can alter vibration and current without representing a fault.

## AD-006 — Operational Digital Twin

**Status:** Accepted

Version 1 maintains live telemetry, inferred state, confidence, health state/score, history, alerts, and maintenance messages. A 3D motor or physics simulation is optional and cannot delay the operational twin.

## AD-007 — No Unsupported RUL Claim

**Status:** Accepted

The project dataset is intended for condition monitoring and fault/anomaly classification. It is not a run-to-failure degradation dataset and cannot support a validated Remaining Useful Life claim. An optional RUL demonstration must use a suitable public dataset and be reported separately.

## AD-008 — Run-Based Evaluation

**Status:** Accepted

Training, validation, and test sets are separated by complete experimental runs or sessions. Adjacent windows from one recording cannot appear across training and test sets.

## AD-009 — Simple Infrastructure First

**Status:** Accepted

Use MQTT, Python, CSV, scikit-learn, and a lightweight dashboard first. Introduce SQLite, InfluxDB, Grafana, ONNX, TensorFlow Lite, or 3D visualization only when a measured need exists.

## AD-010 — Safety Is Independent of Software

**Status:** Accepted

A guard, secure mounting, fuse, physical master/emergency switch, rated operation, and separate motor/control power are required. ML, MQTT, or dashboard behaviour must never be the only safety control.
