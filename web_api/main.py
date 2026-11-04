"""Local-only read-only API and WebSocket feed backed by the existing SQLite store.

This module intentionally does not subscribe to MQTT or write motor data.
Keep raspberry-pi/live_service.py as the sole SQLite writer.
"""
from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import time
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from edge_ai_twin.features import vibration_features
from edge_ai_twin.store import DEFAULT_DB

ALLOWED_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}
TOPICS = {"temperature", "current", "rpm", "vibration"}
FRESHNESS_MS = 12_000

app = FastAPI(title="Edge AI Digital Twin API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(ALLOWED_ORIGINS),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)


def now_ms() -> int:
    return int(time.time() * 1000)


def database_path() -> Path:
    """Optional override is useful for isolated tests; never expose it via API."""
    return Path(os.getenv("EDGE_AI_DB_PATH", str(DEFAULT_DB)))


def select_rows(sql: str, args: tuple = ()) -> list[dict]:
    path = database_path()
    if not path.is_file():
        return []
    try:
        # Strictly read only. Never create or migrate the existing database.
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2) as db:
            db.row_factory = sqlite3.Row
            return [dict(row) for row in db.execute(sql, args).fetchall()]
    except (sqlite3.Error, OSError):
        return []


def latest_snapshot(now: int) -> dict:
    rows = select_rows(
        "SELECT snapshot_json FROM twin_snapshots ORDER BY id DESC LIMIT 1"
    )
    if rows:
        try:
            snapshot = json.loads(rows[0]["snapshot_json"])
            if not isinstance(snapshot, dict):
                raise ValueError("Invalid snapshot")
            last = snapshot.get("last_updated_ms")
            fresh = isinstance(last, int) and 0 <= now - last <= FRESHNESS_MS
            snapshot["is_fresh"] = fresh
            if not fresh:
                # Never display stale readings as live operational measurements.
                snapshot["health_state"] = "UNKNOWN"
                snapshot["metrics"] = {}
                snapshot["health_score"] = None
                snapshot["predicted_state"] = None
                snapshot["confidence"] = None
                snapshot["message"] = "Telemetry stale or offline"
            return snapshot
        except (ValueError, TypeError, KeyError):
            pass
    return {
        "asset_id": "MOTOR_01",
        "health_state": "UNKNOWN",
        "metrics": {},
        "source": "UNKNOWN",
        "health_score": None,
        "message": "Waiting for the first Digital Twin snapshot",
        "last_updated_ms": None,
        "is_fresh": False,
        "predicted_state": None,
        "confidence": None,
        "model_version": None,
        "model_data_type": None,
    }


def measurements() -> list[dict]:
    rows = select_rows(
        """SELECT timestamp_ms, topic, quality, source, payload_json
        FROM sensor_readings ORDER BY id DESC LIMIT 480"""
    )
    output = []
    for row in reversed(rows):
        try:
            if row["quality"] != "VALID":
                continue
            sensor = row["topic"].rsplit("/", 1)[-1]
            if sensor not in TOPICS:
                continue
            payload = json.loads(row["payload_json"])
            value = (
                vibration_features(payload)["vibration_rms_g"]
                if sensor == "vibration" else float(payload["value"])
            )
            output.append({
                "time_ms": row["timestamp_ms"],
                "sensor": sensor,
                "value": round(float(value), 5),
                "source": row["source"] or "PHYSICAL",
            })
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return output[-400:]


def dashboard_data() -> dict:
    now = now_ms()
    alerts = select_rows(
        """SELECT timestamp_ms, previous_state, new_state, message, source
        FROM alerts ORDER BY id DESC LIMIT 30"""
    )
    return {
        "server_time_ms": now,
        "asset_id": "MOTOR_01",
        "snapshot": latest_snapshot(now),
        "history": measurements(),
        "alerts": alerts,
    }


@app.get("/api/health")
def health() -> dict:
    # Health of the API process, not of the physical motor.
    return {"status": "ok", "service": "dashboard-api"}


@app.get("/api/dashboard")
def dashboard() -> dict:
    return dashboard_data()


@app.websocket("/ws")
async def live_dashboard(websocket: WebSocket):
    origin = websocket.headers.get("origin")
    if origin not in ALLOWED_ORIGINS:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(dashboard_data())
            await asyncio.sleep(2)
    except (WebSocketDisconnect, RuntimeError, OSError):
        pass
