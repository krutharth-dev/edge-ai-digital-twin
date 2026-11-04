"""Offline regression tests for the core software MVP."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from edge_ai_twin.contracts import InvalidTelemetry, validate_sensor
from edge_ai_twin.features import FEATURE_NAMES, extract_features
from edge_ai_twin.simulation import generate_batch
from edge_ai_twin.store import MotorStore
from edge_ai_twin.twin import MotorTwin


NOW = 1792230604247


def batch(scenario="normal", sequence=1, run_id="fixture_run"):
    return generate_batch(scenario, sequence, run_id=run_id, seed=123, now_ms=NOW)


def test_contract_accepts_every_sensor():
    for topic, payload in batch().items():
        assert validate_sensor(topic, payload, now_ms=NOW) is payload


def test_contract_rejects_bad_unit_and_clock():
    topic = "motor01/current"
    invalid = batch()[topic]
    invalid["unit"] = "mA"
    with pytest.raises(InvalidTelemetry):
        validate_sensor(topic, invalid, now_ms=NOW)
    with pytest.raises(InvalidTelemetry):
        validate_sensor(topic, batch()[topic], now_ms=NOW + 60000)


def test_contract_rejects_bad_vibration_and_nan():
    vib = batch()["motor01/vibration"]
    vib["x"][0] = float("nan")
    with pytest.raises(InvalidTelemetry):
        validate_sensor("motor01/vibration", vib, now_ms=NOW)


def test_features_deterministic():
    readings = {topic.split("/")[-1]: value for topic, value in batch().items()}
    features = extract_features(readings)
    assert tuple(features) == FEATURE_NAMES
    assert 0.01 < features["vibration_rms_g"] < 0.25


def test_twin_healthy_fault_and_stale():
    twin = MotorTwin(stale_ms=12000)
    for topic, payload in batch("normal").items():
        twin.ingest(topic, payload, now_ms=NOW)
    assert twin.health_state == "HEALTHY"
    for topic, payload in batch("thermal", run_id="thermal_run").items():
        twin.ingest(topic, payload, now_ms=NOW + 1000)
    assert twin.health_state == "FAULT"
    assert twin.snapshot(now_ms=NOW + 1000)["source"] == "SIMULATED"
    twin.evaluate(now_ms=NOW + 15000)
    assert twin.health_state == "UNKNOWN"


def test_mixed_run_not_healthy():
    twin = MotorTwin()
    for topic, payload in batch("normal", run_id="first").items():
        twin.ingest(topic, payload, NOW)
    twin.ingest("motor01/temperature", batch("normal", run_id="second")["motor01/temperature"], NOW)
    assert twin.health_state == "UNKNOWN"


def test_store_saves_and_deduplicates(tmp_path):
    store = MotorStore(tmp_path / "test.db")
    topic, payload = next(iter(batch().items()))
    assert store.save_sensor(topic, payload)
    assert not store.save_sensor(topic, payload)
    snapshot = {"timestamp_ms": NOW, "health_state": "HEALTHY", "message": "demo", "source": "SIMULATED"}
    store.save_snapshot(snapshot)
    store.save_alert("UNKNOWN", snapshot)
    with store.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM sensor_readings").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM twin_snapshots").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0] == 1


def test_demo_scenario_changes_condition():
    normal = batch("normal")
    abnormal = batch("imbalance")
    a = extract_features({t.split("/")[-1]: p for t, p in normal.items()})
    b = extract_features({t.split("/")[-1]: p for t, p in abnormal.items()})
    assert b["vibration_rms_g"] > a["vibration_rms_g"]
