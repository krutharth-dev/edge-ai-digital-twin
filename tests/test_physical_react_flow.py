"""Physical-format ESP32 -> SQLite Digital Twin -> React API integration checks.

These use offline PHYSICAL-labelled test fixtures. They do NOT prove ESP32 firmware
compilation, sensor calibration, motor fault accuracy, or actual Wi-Fi/MQTT connectivity.
"""
import importlib.util
import time
from pathlib import Path

from fastapi.testclient import TestClient

from edge_ai_twin.store import MotorStore
from web_api.main import app

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("live_service_for_test", ROOT / "raspberry-pi" / "live_service.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
LiveService = module.LiveService

client = TestClient(app)


def physical_payload(topic, sequence, stamp, quality="VALID"):
    unit = {
        "motor01/temperature": "degC",
        "motor01/current": "A",
        "motor01/rpm": "rpm",
        "motor01/vibration": "g",
    }[topic]
    payload = {
        "schema_version": 1,
        "asset_id": "MOTOR_01",
        "timestamp_ms": stamp,
        "sequence": sequence,
        "run_id": None,
        "boot_id": "esp32-test-boot",
        "quality": quality,
        "source": "PHYSICAL",
        "unit": unit,
    }
    if topic == "motor01/vibration":
        payload.update({
            "sample_count": 8,
            "sample_rate_hz": 95.0,
            "x": [0.01, 0.02, 0.01, -0.01, -0.02, 0.01, 0.0, 0.01],
            "y": [0.0, 0.01, 0.0, -0.01, 0.01, -0.01, 0.0, 0.0],
            "z": [1.00, 1.01, 0.99, 1.00, 1.01, 1.00, 0.99, 1.00],
        })
    else:
        payload["value"] = {
            "motor01/temperature": 32.5,
            "motor01/current": 0.45,
            "motor01/rpm": 1650.0,
        }[topic] if quality == "VALID" else None
    return payload


def test_physical_format_flows_to_dashboard_and_websocket(tmp_path, monkeypatch):
    path = tmp_path / "live.db"
    service = LiveService(db_path=path)
    stamp = int(time.time() * 1000)
    for topic in ("motor01/temperature", "motor01/current", "motor01/rpm", "motor01/vibration"):
        service.process(topic, physical_payload(topic, 1, stamp))
    monkeypatch.setenv("EDGE_AI_DB_PATH", str(path))
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["snapshot"]["is_fresh"] is True
    assert body["snapshot"]["health_state"] == "HEALTHY"
    assert body["snapshot"]["source"] == "PHYSICAL"
    assert body["sensors"]["temperature"]["value"] == 32.5
    assert body["sensors"]["temperature"]["source"] == "PHYSICAL"
    assert body["sensors"]["vibration"]["is_fresh"] is True
    assert len(body["history"]) == 4
    assert all(row["source"] == "PHYSICAL" for row in body["history"])
    with client.websocket_connect("/ws", headers={"origin": "http://localhost:5173"}) as ws:
        frame = ws.receive_json()
        assert frame["snapshot"]["source"] == "PHYSICAL"
        assert frame["sensors"]["rpm"]["quality"] == "VALID"


def test_uncalibrated_current_does_not_masquerade_as_live_motor_health(tmp_path, monkeypatch):
    path = tmp_path / "uncalibrated.db"
    service = LiveService(db_path=path)
    stamp = int(time.time() * 1000)
    for topic in ("motor01/temperature", "motor01/current", "motor01/rpm", "motor01/vibration"):
        quality = "CALIBRATION_REQUIRED" if topic == "motor01/current" else "VALID"
        service.process(topic, physical_payload(topic, 1, stamp, quality=quality))
    monkeypatch.setenv("EDGE_AI_DB_PATH", str(path))
    body = client.get("/api/dashboard").json()
    assert body["snapshot"]["health_state"] == "UNKNOWN"
    assert body["sensors"]["current"]["quality"] == "CALIBRATION_REQUIRED"
    assert body["sensors"]["current"]["value"] is None
    assert body["sensors"]["temperature"]["value"] == 32.5
    assert not any(reading["sensor"] == "current" for reading in body["history"])


def test_sensor_status_does_not_expose_stale_value(tmp_path, monkeypatch):
    path = tmp_path / "stale.db"
    store = MotorStore(path)
    old = int(time.time() * 1000) - 45000
    store.save_sensor("motor01/temperature", physical_payload("motor01/temperature", 1, old))
    monkeypatch.setenv("EDGE_AI_DB_PATH", str(path))
    sensors = client.get("/api/dashboard").json()["sensors"]
    assert sensors["temperature"]["is_fresh"] is False
    assert sensors["temperature"]["value"] is None
    assert sensors["current"]["quality"] == "MISSING"
