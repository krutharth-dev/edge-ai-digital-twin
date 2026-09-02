# Testing

**Status:** Planned scaffold; automated tests have not yet been committed.

Testing follows [the project test plan](../docs/TEST_PLAN.md).

Planned categories:

- Sensor-driver and calibration checks
- MQTT payload/schema contract tests
- Raspberry Pi ingestion and stale-data tests
- Deterministic feature-extraction unit tests
- Training-to-inference feature parity tests
- Run-split leakage checks
- Model artifact/schema compatibility tests
- Digital Twin transition and alert tests
- Dashboard state/rendering checks
- End-to-end hardware-in-the-loop demonstration records

Tests that require physical hardware should be clearly marked and must follow the safety plan. Deterministic processing tests should use small synthetic fixtures rather than committed full experimental datasets.
