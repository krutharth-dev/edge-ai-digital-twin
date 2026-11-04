"""SQLite store; reads the original 20-record database without migrating/dropping it."""
import json
import sqlite3
import time
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "motor_readings.db"


class MotorStore:
    def __init__(self, path=DEFAULT_DB):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def initialize(self):
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS sensor_readings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL, asset_id TEXT NOT NULL,
                timestamp_ms INTEGER NOT NULL, sequence INTEGER NOT NULL,
                run_id TEXT, quality TEXT NOT NULL, source TEXT,
                unit TEXT NOT NULL, payload_json TEXT NOT NULL,
                received_at_ms INTEGER NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS twin_snapshots(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ms INTEGER NOT NULL, health_state TEXT NOT NULL,
                snapshot_json TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS alerts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_ms INTEGER NOT NULL, previous_state TEXT NOT NULL,
                new_state TEXT NOT NULL, message TEXT NOT NULL, source TEXT)""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_sensors_time ON sensor_readings(topic,timestamp_ms)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_time ON twin_snapshots(timestamp_ms)")

    def save_sensor(self, topic, payload):
        with self.connect() as db:
            seen = db.execute("""SELECT 1 FROM sensor_readings
                WHERE topic=? AND timestamp_ms=? AND sequence=?
                AND run_id IS ? LIMIT 1""",
                (topic, payload["timestamp_ms"], payload["sequence"], payload.get("run_id"))).fetchone()
            if seen:
                return False
            db.execute("""INSERT INTO sensor_readings
                (topic,asset_id,timestamp_ms,sequence,run_id,quality,source,unit,payload_json,received_at_ms)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (topic, payload["asset_id"], payload["timestamp_ms"],
                 payload["sequence"], payload.get("run_id"), payload["quality"],
                 payload.get("source"), payload["unit"],
                 json.dumps(payload, allow_nan=False), int(time.time() * 1000)))
        return True

    def save_snapshot(self, snapshot):
        with self.connect() as db:
            db.execute("INSERT INTO twin_snapshots(timestamp_ms,health_state,snapshot_json) VALUES(?,?,?)",
                (snapshot["timestamp_ms"], snapshot["health_state"], json.dumps(snapshot)))

    def save_alert(self, previous, snapshot):
        with self.connect() as db:
            db.execute("""INSERT INTO alerts(timestamp_ms,previous_state,new_state,message,source)
                VALUES(?,?,?,?,?)""", (snapshot["timestamp_ms"], previous,
                   snapshot["health_state"], snapshot["message"], snapshot.get("source")))
