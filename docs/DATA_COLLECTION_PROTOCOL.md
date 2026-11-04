# Data-Collection Protocol

## Objective

Create a reproducible labelled dataset for condition monitoring and fault classification without leaking adjacent samples from the same recording across model-development splits.

## Planned Classes

| Label | Controlled condition | Notes |
|---|---|---|
| `NORMAL` | Stable operation within the selected baseline range | Collect across repeated runs and intended speed/load settings |
| `IMBALANCE` | Small securely attached off-centre mass behind the guard | Must remain mechanically secure and within approved vibration limits |
| `INCREASED_LOAD` | Repeatable load within motor/controller ratings | Record load method, current, RPM, and stop thresholds |
| `THERMAL_ABNORMALITY` | Temperature above baseline but within rated limits | Do not block cooling or exceed approved temperature limits |

The first MVP may map all safely controlled abnormal runs to `ABNORMAL` until multi-class data quality is sufficient.

## Before Each Run

1. Complete the safety checklist and inspect the mount, guard, wiring, fuse, switch, and rotating assembly.
2. Confirm motor, sensor, ESP32, Raspberry Pi, and MQTT status.
3. Record hardware revision, firmware commit, configuration, sensor calibration, units, and sampling settings.
4. Assign a unique run ID before recording.
5. Confirm the intended class, speed/PWM setting, load/imbalance method, planned duration, and stop conditions.
6. Start telemetry storage before energizing the motor.
7. Do not begin if any sensor is invalid or time/run identification is missing.

## During Each Run

- Do not change the assigned class silently.
- Record event markers for start, steady-state period, condition introduction/removal, and stop.
- Observe current, temperature, vibration, RPM, mounting stability, and unexpected noise.
- Stop immediately when a predefined safety threshold or qualitative stop condition is reached.
- Mark interrupted or questionable runs; do not relabel them later merely to improve model performance.

## After Each Run

1. Stop and isolate motor power.
2. Record outcome, interruptions, anomalies, and whether the label remains valid.
3. Verify that files are readable and contain the expected timestamps, units, samples, and run ID.
4. Preserve the raw file unchanged.
5. Calculate and store a checksum in the run manifest where practical.
6. Allow cooling or mechanical reset before the next run when required.

## Run Metadata

At minimum:

| Field | Example format |
|---|---|
| `run_id` | `normal_speed1_run01` |
| `label` | `NORMAL` |
| `started_at_utc` | ISO 8601 |
| `duration_s` | Numeric |
| `motor_id` | `MOTOR_01` |
| `hardware_revision` | Team-defined |
| `firmware_commit` | Git SHA |
| `sensor_configuration` | Versioned configuration reference |
| `speed_setting` | PWM setting and measured RPM |
| `condition_configuration` | Load/imbalance/thermal setup |
| `sample_rates_hz` | Per sensor |
| `operator_notes` | Short factual notes |
| `valid_for_ml` | Boolean plus reason |

## File and Table Conventions

Suggested raw file name:

`YYYYMMDDTHHMMSSZ_MOTOR_01_<label>_<run_id>.csv`

Suggested slow-telemetry columns:

`timestamp_ms,run_id,asset_id,label,current_a,temperature_c,rpm,current_quality,temperature_quality,rpm_quality`

Vibration may use a separate long-format file:

`timestamp_ms,run_id,asset_id,label,sample_index,accel_x_g,accel_y_g,accel_z_g,vibration_quality`

Do not mix units within a column.

## Windowing and Features

Window length, overlap, filtering, and sample rate must be fixed in a versioned feature configuration. Candidate vibration features include RMS, standard deviation, peak, peak-to-peak, kurtosis, crest factor, dominant frequency, and FFT-band energy. Temperature, current, and RPM may be joined by timestamp/window.

## Leakage-Safe Splitting

- Assign complete run IDs to training, validation, or test sets.
- Never randomly split adjacent windows from one run across sets.
- Fit scalers, imputers, feature selectors, and other learned preprocessing only on training runs.
- Keep a final test set untouched until model choices are complete.
- Report split membership and class distribution.

## Quality Control

Exclude a run only for a documented reason such as invalid label, unsafe interruption, sensor failure, missing metadata, corrupted storage, or schema mismatch. Keep an exclusion log. Do not remove difficult but valid runs solely because they reduce accuracy.

## Storage Policy

Raw and processed datasets remain local unless the team approves a small de-identified example. Git should contain schemas, manifests, scripts, and documentation—not full raw recordings.
