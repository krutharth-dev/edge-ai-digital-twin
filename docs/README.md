# Project Documentation

These documents define the current baseline for the Edge-AI Predictive Maintenance + Digital Twin prototype.

| Document | Purpose |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Component boundaries, data flow, deployment model, and system invariants |
| [DECISIONS.md](DECISIONS.md) | Accepted scope and architecture decisions |
| [MQTT_CONTRACT.md](MQTT_CONTRACT.md) | Proposed topics, payload envelope, QoS, and ownership |
| [DATA_COLLECTION_PROTOCOL.md](DATA_COLLECTION_PROTOCOL.md) | Safe repeated experiments, labels, metadata, and dataset splitting |
| [TEST_PLAN.md](TEST_PLAN.md) | Sensor, communication, ML, Digital Twin, dashboard, and end-to-end validation |
| [ROADMAP.md](ROADMAP.md) | Eight-week core plan, exit criteria, and definition of done |
| [SAFETY.md](SAFETY.md) | Electrical, mechanical, thermal, and experimental controls |

## Document Status

These are design and implementation-control documents. They distinguish between:

- **Accepted design** — agreed architecture or scope
- **Planned** — not yet implemented
- **Implemented** — present in code or hardware
- **Validated** — tested with recorded evidence

A document must not call a feature implemented or validated until the corresponding code, experiment, or test evidence exists.
