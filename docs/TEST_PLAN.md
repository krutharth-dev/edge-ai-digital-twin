# Test and Validation Plan

## Principles

- Validate from the sensor outward.
- Record evidence for each test.
- Separate planned acceptance criteria from measured results.
- Do not optimize AI or dashboard appearance before the physical-to-storage pipeline is reliable.
- Safety controls are tested independently of software.

## Validation Layers

### 1. Physical Rig and Electrical System

Verify secure mounting, guard, imbalance retention, power separation, fuse, switch, insulation, strain relief, polarity, and rated operation. Record the inspection and stop conditions. No destructive test is required.

### 2. Individual Sensors

For each sensor, record:

- Wiring and pin assignment
- Library/driver version
- Units, range, sample rate, and calibration method
- Stable baseline output
- Response to a safe known change
- Missing/disconnected behaviour
- Repeatability across restarts

Do not integrate all sensors until each passes its individual test.

### 3. ESP32 Telemetry

Check timestamps, sequences, run ID, asset ID, units, quality flags, schema version, reconnect behaviour, and memory stability. Confirm invalid sensor reads are not replaced with normal-looking values.

### 4. MQTT and Raspberry Pi Ingestion

Test:

- Correct topics and publisher ownership
- Payload validation and maximum size
- Broker restart and ESP32 reconnect
- Duplicate, missing, delayed, malformed, out-of-order, and unknown-schema messages
- Status/Last-Will behaviour
- Storage continuity and explicit stale state

### 5. Storage and Dataset Integrity

Confirm raw data is immutable, filenames and schemas are consistent, run metadata is complete, interrupted runs are marked, and transformations can be reproduced from code/configuration.

### 6. Feature Pipeline

Use deterministic fixture data to test window boundaries, filtering, RMS, standard deviation, peak, peak-to-peak, kurtosis, crest factor, FFT frequency axis, dominant frequency, and band energy. Verify training and Raspberry Pi implementations produce matching feature values and order.

### 7. Machine Learning

Use run-based train/validation/test splits. Record:

- Number of runs and windows by class and split
- Accuracy and macro-F1
- Per-class precision and recall
- Confusion matrix
- False alarms and missed conditions
- Comparison with a simple baseline
- Inference latency and resource use
- Model, feature, and dataset versions
- Limitations and failure cases

No target accuracy should be invented before representative data exists.

### 8. Digital Twin and Health Logic

Verify:

- Telemetry fields update the correct asset
- Stale/invalid data changes data quality and does not appear healthy
- Model output, confidence, rule-based health state, and alerts remain distinguishable
- State timestamps and history are consistent
- Removing a controlled abnormal condition allows recovery according to documented rules
- Missing model or feature mismatch produces an explicit unavailable/error state

### 9. Dashboard and Alerts

Check live values, units, timestamps, trends, predicted class, confidence when available, health state, warning text, event history, reconnect/stale indication, and readability. The dashboard must not imply RUL or industrial certification.

### 10. End-to-End Demonstration

Required sequence:

`Normal operation → Live readings → HEALTHY → Safe controlled abnormal condition → Sensor change → Local Edge-AI detection → Digital Twin update → Warning → Remove condition → Return toward normal`

Record sensor-to-dashboard latency and whether every expected state transition occurred.

## Evidence Record

Each validation record should include test ID, date, operator, commit, hardware revision, configuration, run IDs, expected result, actual result, evidence path, pass/fail, and follow-up issue.
