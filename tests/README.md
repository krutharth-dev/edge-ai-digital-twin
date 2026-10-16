# Testing

**Status:** Planned scaffold; automated tests have not yet been committed.

Testing follows [the project test plan](../docs/TEST_PLAN.md).

## Available Checks

From the repository root, install the development dependencies and run:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check .
```

`test_repository_quality.py` checks internal documentation file paths, the GitHub templates/workflow YAML, and the presence of the core design contracts. These are **scaffold checks only**, not proof that hardware, model inference, or the dashboard works.

## Future Validation


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
