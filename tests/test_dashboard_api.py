"""Regression checks for the read-only dashboard API."""
import time

from fastapi.testclient import TestClient

from edge_ai_twin.store import MotorStore
from web_api.main import app

client = TestClient(app)


def test_no_database_returns_unknown(monkeypatch, tmp_path):
    monkeypatch.setenv("EDGE_AI_DB_PATH", str(tmp_path / "missing.db"))
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["snapshot"]["health_state"] == "UNKNOWN"
    assert body["snapshot"]["is_fresh"] is False
    assert body["history"] == []
    assert body["alerts"] == []
    assert not (tmp_path / "missing.db").exists()


def test_fresh_snapshot_is_visible(monkeypatch, tmp_path):
    path = tmp_path / "motor.db"
    store = MotorStore(path)
    now = int(time.time() * 1000)
    store.save_snapshot({
        "timestamp_ms": now, "last_updated_ms": now,
        "health_state": "HEALTHY", "health_score": 100,
        "metrics": {"temperature_c": 32.5, "rpm": 1750},
        "source": "SIMULATED", "message": "Within demonstration thresholds",
    })
    monkeypatch.setenv("EDGE_AI_DB_PATH", str(path))
    snapshot = client.get("/api/dashboard").json()["snapshot"]
    assert snapshot["is_fresh"] is True
    assert snapshot["health_state"] == "HEALTHY"
    assert snapshot["metrics"]["rpm"] == 1750
    assert snapshot["source"] == "SIMULATED"


def test_stale_snapshot_cannot_look_healthy(monkeypatch, tmp_path):
    path = tmp_path / "motor.db"
    store = MotorStore(path)
    old = int(time.time() * 1000) - 30_000
    store.save_snapshot({
        "timestamp_ms": old, "last_updated_ms": old,
        "health_state": "HEALTHY", "health_score": 100,
        "metrics": {"temperature_c": 32.5},
        "source": "SIMULATED", "message": "Healthy",
        "predicted_state": "NORMAL", "confidence": .99,
    })
    monkeypatch.setenv("EDGE_AI_DB_PATH", str(path))
    snapshot = client.get("/api/dashboard").json()["snapshot"]
    assert snapshot["health_state"] == "UNKNOWN"
    assert snapshot["metrics"] == {}
    assert snapshot["health_score"] is None
    assert snapshot["predicted_state"] is None
    assert snapshot["is_fresh"] is False
