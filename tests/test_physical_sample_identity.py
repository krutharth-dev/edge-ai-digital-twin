"""Offline transport fixture with a newer simulated row in the same database."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from edge_ai_twin.store import MotorStore
from web_api.main import app, now_ms


class SampleIdentityTest(unittest.TestCase):
    def test_physical_latest_history_and_websocket(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "test.db"
            with patch.dict(os.environ, EDGE_AI_DB_PATH=str(db)):
                store = MotorStore(db)
                stamp = now_ms()
                for seq, source, value in [(42, "PHYSICAL", 22.875), (43, "SIMULATED", 90)]:
                    store.save_sensor("motor01/temperature", dict(
                        asset_id="MOTOR_01", timestamp_ms=stamp, sequence=seq,
                        run_id=None, boot_id="fixture", source=source,
                        quality="VALID", value=value, unit="degC"))
                client = TestClient(app)
                latest = client.get("/api/physical/latest").json()["temperature"]
                self.assertEqual((latest["value"], latest["sequence"], latest["last_updated_ms"]),
                                 (22.875, 42, stamp))
                self.assertEqual([r["value"] for r in client.get("/api/physical/history").json()], [22.875])
                with client.websocket_connect("/ws", headers={"origin": "http://localhost:5173"}) as ws:
                    self.assertEqual(ws.receive_json()["sensors"]["temperature"], latest)
