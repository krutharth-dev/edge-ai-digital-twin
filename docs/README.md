# Documentation index

The authoritative setup for the **Mac-hosted software MVP** is the [Mac runbook](MAC_RUNBOOK.md). Older research documents preserve the original Raspberry Pi proposal; they are not proof of completed hardware validation.

| Document | What it explains |
| --- | --- |
| [Mac runbook](MAC_RUNBOOK.md) | Setup, safe Git pull and the three local services |
| [Workflow diagrams](WORKFLOWS.md) | Data flow, quality checks, physical validation and PR workflow |
| [Pull-request guide](PR_GUIDE.md) | Draft versus ready, review, CI and squash merge |
| [Implementation status](IMPLEMENTATION_STATUS.md) | Implemented modules versus manual validation |
| [MQTT contract](MQTT_CONTRACT.md) | JSON schema, topics, ownership, units |
| [LAN MQTT setup](LAN_MQTT_SETUP.md) | Authenticated ESP32-to-Mac communication |
| [Architecture](ARCHITECTURE.md) | Engineering boundaries and original architecture |
| [Decisions](DECISIONS.md) | Research-stage design decisions |
| [Data protocol](DATA_COLLECTION_PROTOCOL.md) | Runs, labels and run-separated evaluation |
| [Test plan](TEST_PLAN.md) | Physical and software evidence requirements |
| [Roadmap](ROADMAP.md) | Academic milestones |
| [Safety](SAFETY.md) | Mechanical and electrical safeguards |

## Evidence levels

- **Designed** — a documented idea, protocol or circuit.
- **Implemented** — source is committed.
- **Software-tested** — tests verify software behavior.
- **Hardware-validated** — physical data, wiring and calibration were actually checked.

A passing GitHub Action does not establish motor classification accuracy. Synthetic data must stay explicitly identified as simulated.
