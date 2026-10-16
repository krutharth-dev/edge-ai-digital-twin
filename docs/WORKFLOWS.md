# Illustrated implementation workflows

These GitHub-rendered Mermaid diagrams represent the **intended** system and the **current software-only integration path**. They are not evidence that hardware or Edge AI has already been implemented.

## A. Software-first workflow (starting 17 October 2026)

```mermaid
flowchart TD
    A["Intel Mac: install Python, Git and Mosquitto"] --> B["Create virtual environment"]
    B --> C["Run local MQTT broker"]
    C --> D["Publish marked synthetic data"]
    D --> E["Subscribe, inspect and validate JSON"]
    E --> F["Implement CSV storage with timestamps"]
    F --> G["Create MOTOR_01 Digital Twin state"]
    G --> H["Streamlit display with live and stale states"]
    H --> I["Use real ESP32 + sensors when ready"]
    I --> J["Collect real labelled experimental runs"]
    J --> K["Train and evaluate Random Forest"]
    K --> L["Deploy real local inference on Mac"]
    L --> M["Validate alerts and end-to-end latency"]
```

The Mac acts as a local edge host. The physical acquisition path joins the same MQTT interface later; the Raspberry Pi is an **optional future deployment target**, not a prerequisite for software development.

## B. Data and control boundaries

```mermaid
flowchart LR
  subgraph Asset["Physical layer — later integration"]
    MOTOR["Guarded 12 V motor / fan"] --> SENS["Vibration / current / temp / RPM"]
    SENS --> ESP["ESP32 acquisition"]
  end
  subgraph Local["Intel Mac — local Edge AI host"]
    MQTT["Mosquitto broker"] --> ING["Paho subscriber + schema validation"]
    ING --> STORE["CSV / optional SQLite"]
    ING --> FEAT["Windowing + feature extraction"]
    FEAT --> PRED["Local model inference"]
    PRED --> TWIN["MOTOR_01 health + alert state"]
    STORE --> TWIN
    TWIN --> UI["Streamlit dashboard"]
  end
  MOCK["Synthetic MQTT publisher — software tests only"] -.-> MQTT
  ESP -->|"Wi-Fi / MQTT"| MQTT
```

**Never confuse demo data with real sensor evidence.** The mock publisher labels all packets `synthetic: true`. Physically safe motor shutdown must remain independent of MQTT, inference, and the dashboard.

## C. Data-quality and alert workflow

```mermaid
flowchart TD
  RX["Incoming MQTT JSON"] --> CHECK{"Schema, source, timestamp, units and values valid?"}
  CHECK -- No --> BAD["Reject/flag invalid"]
  CHECK -- Yes --> SYN{"Synthetic sample?"}
  SYN -- Yes --> DEMO["Show DEMO state; do not enter real training dataset"]
  SYN -- No --> FRESH{"Fresh and in order?"}
  FRESH -- No --> STALE["Mark STALE/UNKNOWN"]
  FRESH -- Yes --> SAVE["Store with asset + run ID"]
  SAVE --> READY{"Validated ML artifact available?"}
  READY -- No --> NOAI["Prediction unavailable"]
  READY -- Yes --> MODEL["Extract same features as training; infer"]
  MODEL --> HEALTH["Health and maintenance rules"]
  BAD --> TWIN["Update twin with data quality"]
  STALE --> TWIN
  NOAI --> TWIN
  HEALTH --> TWIN
  DEMO --> TWIN
  TWIN --> DISPLAY["Dashboard + audit/event log"]
```

Do not display a fabricated HEALTHY status when the data are stale or the model is unavailable.

## D. Repeatable research and training workflow

```mermaid
flowchart LR
  RUN["Safe independent test runs"] --> LABEL["Manifest, label and run ID"]
  LABEL --> SPLIT["Split by complete runs"]
  SPLIT --> TRAIN["Fit preprocessing + Random Forest"]
  TRAIN --> TEST["Evaluate held-out runs"]
  TEST --> METRICS["Macro-F1, confusion matrix, false alarms"]
  METRICS --> EXPORT["Export model + feature contract"]
  EXPORT --> EDGE["Deploy locally on Mac; optional Pi later"]
```

Version 1 is anomaly/fault classification, **not Remaining Useful Life prediction**. The independent run split prevents adjacent vibration windows leaking into evaluation.

## E. Five-member collaboration workflow

```mermaid
flowchart TD
    ISSUE["Choose a small task / issue"] --> BRANCH["Create feature branch"]
    BRANCH --> CODE["Code or document one module"]
    CODE --> TEST["Run focused tests + note evidence"]
    TEST --> PR["Open PR describing MQTT/schema changes"]
    PR --> REVIEW["Cross-review integration contracts"]
    REVIEW --> MERGE["Merge only after review"]
```

Suggested initial handoffs: acquisition firmware; safe motor + sensors; MQTT subscriber/storage; ML/features; Digital Twin/dashboard. The existing [team responsibilities](../README.md#team-collaboration) provide ownership; share contract changes in PRs.

## F. Demo success sequence

1. Start in software-only mode; demonstrate clearly labelled simulated traffic.
2. Once physical integration exists, show **real** sensor changes during normal operation.
3. Introduce one bounded, guarded abnormal condition.
4. Show updated data, classification and `MOTOR_01` health state.
5. Confirm an alert and a later recovery to normal.
6. Record accuracy, false alarms and sensor-to-dashboard delay from actual experiments.

See [test plan](TEST_PLAN.md), [safety controls](SAFETY.md), and [Mac setup](SOFTWARE_SETUP_MAC.md).
