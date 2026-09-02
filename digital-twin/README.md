# Operational Digital Twin

**Status:** Planned scaffold; backend code has not yet been committed.

## Definition

The Version 1 Digital Twin is the stateful software representation of `MOTOR_01`. It is not merely a chart, and it does not require a 3D motor model.

Minimum state:

- Latest valid sensor values and timestamps
- Data quality and freshness
- Predicted operating class
- Confidence/probability only when supported by the model
- Health state and optional rule-based score
- Current alert and maintenance message
- Model/feature version
- Historical telemetry and event references

## State Principles

- Sensor data, model output, health rules, and operator messages remain distinguishable.
- Invalid or stale data cannot appear as `HEALTHY`.
- Null is used when a value is unavailable; the system does not invent confidence or health scores.
- State transitions are timestamped and testable.
- A health score is initially a transparent rule-based project aid, not remaining life.
- The twin never provides the sole physical safety control.

## Planned Health States

`UNKNOWN → HEALTHY → WARNING → FAULT`

Exact transitions and recovery rules must be based on collected baseline data and documented validation. The project may initially use only `UNKNOWN`, `HEALTHY`, and `WARNING`.

## Inputs and Outputs

Inputs come from validated Raspberry Pi telemetry and inference services. Outputs feed the dashboard, alert history, and project demonstration. See [the architecture](../docs/ARCHITECTURE.md) and [test plan](../docs/TEST_PLAN.md).

## Acceptance Evidence

The twin is ready when safe physical changes update the correct asset automatically, stale/invalid data is visible, state history is traceable, alerts appear and clear according to documented rules, and the behaviour is repeatable.
