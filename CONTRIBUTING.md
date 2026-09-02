# Contributing to Edge-AI Digital Twin

This repository supports a five-member academic project building a low-cost rotating-machine condition-monitoring prototype. Contributions should move the project toward a reliable end-to-end path:

`Motor/fan → Sensors → ESP32 → MQTT → Raspberry Pi → Preprocessing/features → Edge-AI inference → Health logic → Digital Twin → Dashboard/alerts`

Do not describe planned work as implemented or report estimated results as measurements.

## Before You Start

- Read the README and the documents in `docs/`.
- Search existing issues and pull requests.
- Open or claim an issue before a substantial change.
- Keep optional 3D, deep-learning, cloud, or RUL work behind the core pipeline.
- Use the security policy for vulnerabilities; never disclose credentials publicly.
- Confirm the safety plan before changing hardware or abnormal-condition experiments.

## Branch and Pull-Request Workflow

1. Create a focused branch from the current `main`.
2. Use a descriptive name such as `feature/esp32-adxl345`, `feature/mqtt-ingestion`, `feature/run-split-training`, or `docs/data-protocol`.
3. Make one logically related change at a time.
4. Add or update tests, interface documentation, and configuration examples.
5. Commit using a clear conventional prefix such as `feat:`, `fix:`, `docs:`, `test:`, or `chore:`.
6. Push the branch and open a reviewed pull request.
7. Do not merge until affected interfaces and validation evidence are recorded.

## Architecture Rules

- The ESP32 owns sensor acquisition, basic validation/timestamping, telemetry packaging, Wi-Fi, and MQTT publishing.
- The Raspberry Pi owns storage, signal preprocessing, feature extraction, live inference, health logic, Digital Twin state, dashboard services, and alerts.
- The core live path must operate locally without cloud inference.
- Training may run on a development laptop, but exported preprocessing and feature definitions must match Raspberry Pi inference.
- Version 1 uses an operational Digital Twin; a 3D model is optional.
- The project does not claim Remaining Useful Life from its short-duration experimental dataset.

Any change to these boundaries requires a documented architecture decision and team review.

## Interface Requirements

Document every changed:

- Sensor pin, calibration method, unit, sampling rate, and valid range
- MQTT topic, payload field, schema version, QoS, retained-message behaviour, and publisher
- CSV/database column, data type, label, timestamp convention, and missing-value rule
- Feature name, window definition, preprocessing step, and expected unit
- Digital Twin field, state transition, health rule, and alert condition
- Configuration key, default, and secret-handling requirement

## Data and Machine-Learning Requirements

- Collect repeated independent runs with run IDs and experimental metadata.
- Preserve raw data as immutable local evidence; derived data must be reproducible.
- Split training, validation, and test sets by complete runs or sessions.
- Never place adjacent windows from the same run in both training and test data.
- Report class distribution, split method, accuracy, macro-F1, per-class precision/recall, confusion matrix, false alarms, and latency where applicable.
- Compare the Random Forest baseline before adding a more complex model.
- Store model metadata with the artifact: feature order, preprocessing version, labels, training commit, and dataset/run manifest.
- Never fabricate performance, hardware behaviour, or validation outcomes.

## Code and Documentation Quality

- Keep modules small and responsibilities explicit.
- Prefer configuration over hard-coded hostnames, credentials, units, labels, or thresholds.
- Use SI units in stored and transmitted data unless a documented reason requires otherwise.
- Include useful error messages and safe failure behaviour.
- Add unit tests for deterministic processing and contract tests for schemas.
- Update the README and relevant module documentation when behaviour changes.

## Hardware and Experimental Safety

- Keep motor power separate from ESP32 and Raspberry Pi power.
- Never route motor current through a solderless breadboard.
- Use a stable mount, rotating guard, fuse, master/emergency switch, insulated connections, and strain relief.
- Secure any imbalance mass and operate within rated electrical, mechanical, and thermal limits.
- Define stop conditions before each run and stop immediately for instability, excessive heat/current/vibration, loose hardware, or unexpected noise.
- Do not perform destructive fault injection.

## Files That Must Not Be Committed

- Wi-Fi or MQTT credentials, tokens, keys, or private configuration
- Raw/full datasets unless the team approves a small public example
- Trained model binaries without an explicit artifact policy
- Local databases, logs, cache directories, virtual environments, and generated reports
- Personal data, sensitive images, or third-party material without permission

By contributing, you agree to follow the Code of Conduct and license your contribution under the repository's MIT License.
