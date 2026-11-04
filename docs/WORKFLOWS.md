# Workflows and system boundaries

These diagrams show the **implemented Mac software MVP** and the **planned physical integration**. They are architectural illustrations, not proof that Wokwi or ESP32 hardware has been validated.

## End-to-end telemetry and software monitoring

~~~mermaid
flowchart LR
    subgraph Inputs["Telemetry sources"]
      ESP["Physical motor + sensors + ESP32<br/>(hardware validation pending)"]
      SIM["Python scenario publisher<br/>(SIMULATED / labelled)"]
    end
    ESP --> MQTT["Mosquitto MQTT broker"]
    SIM --> MQTT
    subgraph Mac["MacBook · local edge computer"]
      MQTT --> IN["live_service.py<br/>JSON validation, quality, units, timing"]
      IN --> SQL[("SQLite<br/>sensor history")]
      IN --> FE["Feature extraction"]
      FE --> RF["Optional Random Forest inference<br/>(model provenance shown)"]
      IN --> TWIN["Operational Digital Twin<br/>freshness + rule-based health"]
      RF --> TWIN
      TWIN --> SQL2[("SQLite snapshots + alerts")]
      SQL --> UI["Streamlit dashboard"]
      SQL2 --> UI
      TWIN --> UI
      TWIN --> OUT["motor01/health + motor01/alerts"]
    end
~~~

The Mac is the current edge host; Raspberry Pi is **not a requirement**. An alternate Raspberry Pi deployment would require testing and configuration. Only locally trusted model artifacts should be loaded.

## Data quality and loss of communication

~~~mermaid
flowchart TD
    RX["MQTT motor01/sensor message"] --> SIZE{"Payload <= 128 KiB?"}
    SIZE -- No --> DROP["Reject and log"]
    SIZE -- Yes --> JSON{"JSON parse succeeds?"}
    JSON -- No --> DROP
    JSON -- Yes --> VALID{"Contract, timestamp,<br/>sequence, unit, values valid?"}
    VALID -- No --> DROP
    VALID -- Yes --> STORE["Store measurement in SQLite<br/>(deduplicate)"]
    STORE --> TWIN["Update MOTOR_01 twin"]
    TWIN --> CHECK{"All four inputs<br/>fresh and valid?"}
    CHECK -- No --> UNK["UNKNOWN: no false HEALTHY"]
    CHECK -- Yes --> RULES["Illustrative health thresholds"]
    RULES --> EVT["Snapshot / alert transition"]
    UNK --> EVT
    EVT --> DASH["Streamlit dashboard"]
    CLOCK["Periodic freshness check"] --> CHECK
~~~

The software currently rejects stale timestamps and unsupported schema versions. It records health-state transitions and distinguishes explicitly synthetic traffic from physical sensor data. Thresholds are a **teaching/demo aid**, not a physical safety shutdown.

## From simulation to physical model evaluation

~~~mermaid
flowchart TD
    DEMO["Synthetic normal / imbalance / overload / thermal scenarios"] --> MOCK["Exercise MQTT, storage, twin and UI"]
    MOCK --> HARD["Assemble guarded, fused physical motor<br/>(pending)"]
    HARD --> CAL["Verify GPIO, voltage levels,<br/>sensor calibration and accurate timestamps"]
    CAL --> RUNS["Multiple independent controlled runs<br/>with explicit run_id and ground-truth label"]
    RUNS --> VALID["Validate sensor quality and store raw telemetry"]
    VALID --> FEATS["Extract identical training/inference features"]
    FEATS --> SPLIT["Split by full experiment run<br/>never by adjacent windows"]
    SPLIT --> TRAIN["Train / select ML model"]
    TRAIN --> TEST["Held-out physical run metrics<br/>precision, recall, F1, confusion matrix"]
    TEST --> DEPLOY["Deploy trusted local artifact<br/>and verify detection latency"]
~~~

Synthetic-held-out accuracy is **not** physical fault classification accuracy. The prototype does not make a Remaining Useful Life prediction.

## Pull-request workflow

~~~mermaid
flowchart LR
    ISSUE["Choose scoped task"] --> BR["Branch off latest main"]
    BR --> CODE["Write code and documentation"]
    CODE --> TEST["Run tests and capture evidence"]
    TEST --> DRAFT{"Ready for review?"}
    DRAFT -- No --> WIP["Draft PR; keep updating"]
    WIP --> TEST
    DRAFT -- Yes --> PR["Ready PR → CI and peer review"]
    PR --> FIX{"Checks + contract review pass?"}
    FIX -- No --> CODE
    FIX -- Yes --> MERGE["Squash merge to main"]
    MERGE --> PULL["git pull --ff-only origin main"]
~~~

Never merge a PR that silently changes telemetry units, MQTT schemas, model feature order, motor control or safety rules. See [the practical PR guide](PR_GUIDE.md).

## Reproduce the software demonstration

~~~bash
# Separate terminals (after activating .venv in each):
python raspberry-pi/live_service.py
python -m streamlit run dashboard/app.py
python simulator/mqtt_publisher.py --scenario normal --count 20
python simulator/mqtt_publisher.py --scenario overload --count 20
python simulator/mqtt_publisher.py --scenario normal --count 20
~~~

The simulator must be run with a reachable MQTT broker. No physical motor or ESP32 is needed for this software-only test.

Related reading: [Mac runbook](MAC_RUNBOOK.md) · [MQTT contract](MQTT_CONTRACT.md) · [Data-collection protocol](DATA_COLLECTION_PROTOCOL.md) · [Safety plan](SAFETY.md).
