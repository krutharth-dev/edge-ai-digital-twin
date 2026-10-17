"""Deterministic scenario-based MOCK motor telemetry; not a physical motor simulation."""
import random
import time
from uuid import uuid4

SCENARIOS = ("normal", "imbalance", "overload", "thermal")


def generate_batch(scenario="normal", sequence=1, run_id=None, seed=None, now_ms=None):
    if scenario not in SCENARIOS:
        raise ValueError(f"Scenario must be one of {SCENARIOS}")
    rng = random.Random(seed)
    temp, current, rpm, vibration = {
        "normal": (33.0, 0.45, 1450, 0.05),
        "imbalance": (36.0, 0.60, 1400, 0.32),
        "overload": (48.0, 1.45, 920, 0.18),
        "thermal": (72.0, 0.85, 1250, 0.10),
    }[scenario]
    timestamp = int(time.time() * 1000) if now_ms is None else now_ms
    common = {
        "schema_version": 1, "asset_id": "MOTOR_01", "timestamp_ms": timestamp,
        "sequence": sequence, "run_id": run_id or f"demo_{scenario}",
        "quality": "VALID", "source": "SIMULATED",
    }
    def sample(value, spread):
        return max(0.0, round(rng.gauss(value, spread), 3))
    # 50 samples per axis, measured values expressed in units of gravity.
    x = [round(rng.gauss(0, vibration), 4) for _ in range(50)]
    y = [round(rng.gauss(0, vibration), 4) for _ in range(50)]
    z = [round(rng.gauss(1, vibration), 4) for _ in range(50)]
    return {
        "motor01/temperature": {**common, "value": sample(temp, 0.9), "unit": "degC"},
        "motor01/current": {**common, "value": sample(current, 0.045), "unit": "A"},
        "motor01/rpm": {**common, "value": int(sample(rpm, 26)), "unit": "rpm", "measurement_interval_ms": 1000},
        "motor01/vibration": {**common, "unit": "g", "sample_rate_hz": 100,
                              "sample_count": 50, "x": x, "y": y, "z": z},
    }


def new_run_id(scenario):
    return f"sim_{scenario}_{uuid4().hex[:12]}"
