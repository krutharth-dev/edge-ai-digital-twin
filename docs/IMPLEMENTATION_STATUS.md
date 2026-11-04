# Software implementation status (October 2026)

## Implemented in Git

- Existing v1 MQTT JSON producer, receiver and SQLite storage preserved.
- Scenario-configurable synthetic MQTT publisher (normal/imbalance/overload/thermal).
- Common v1 telemetry validator (units, schema, asset, timestamps, quality, arrays).
- Dynamic vibration RMS, standard deviation, peak, kurtosis and ML feature pipeline.
- SQLite raw sensor rows plus timestamped Digital Twin snapshots and alerts.
- Optional local RandomForest live inference with feature-version metadata.
- Group-separated synthetic-data demonstration training and evaluation.
- Stateful rule-based twin with UNKNOWN/HEALTHY/WARNING/FAULT and staleness.
- Local Streamlit dashboard with cards, trends, alert history and provenance.
- Arduino reference firmware and browser Wokwi circuit/code for surrogate sensors.
- Python regression tests and a GitHub Actions workflow.

## Requires on-device/manual validation

- Mac Mosquitto + dashboard + live service launch after pulling changes.
- Physical ESP32 firmware compilation, correct GPIO, 5V-to-3.3V interface,
  current calibration, correct actual sensor library/part variants.
- Wokwi circuit compilation and tested wiring. Wokwi is not physical calibration.
- LAN MQTT credential and firewall configuration, and local time synchronization.
- Safe reproducible real motor experiments and independently labelled datasets.
- Real model evaluation, false-alarm and detection-latency metrics.
- Comparison between physically induced condition labels and classifier results.

Existing main docs retain historical Raspberry Pi references; for this Mac
version use docs/MAC_RUNBOOK.md. Do not merge other open documentation PRs
without checking the MQTT contract revisions for compatibility.
