"""Live SQLite-backed Streamlit operational motor monitoring dashboard."""
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from edge_ai_twin.features import vibration_features
from edge_ai_twin.store import DEFAULT_DB

st.set_page_config(page_title="Motor 01 | Digital Twin", page_icon="⚙️", layout="wide")
st.title("⚙️ Edge-AI Predictive Maintenance")
st.caption("MOTOR_01 · Mac-hosted operational Digital Twin · MQTT + SQLite")


def query(sql, params=()):
    if not DEFAULT_DB.exists():
        return []
    try:
        with sqlite3.connect(DEFAULT_DB, timeout=3) as db:
            db.row_factory = sqlite3.Row
            return [dict(r) for r in db.execute(sql, params).fetchall()]
    except sqlite3.Error:
        return []


def latest_snapshot():
    rows = query("SELECT snapshot_json FROM twin_snapshots ORDER BY id DESC LIMIT 1")
    return json.loads(rows[0]["snapshot_json"]) if rows else None


def recent_measurements(limit=120):
    rows = query(
        "SELECT timestamp_ms, topic, quality, source, payload_json FROM sensor_readings ORDER BY id DESC LIMIT ?",
        (limit * 4,),
    )
    points = []
    for row in reversed(rows):
        try:
            payload = json.loads(row["payload_json"])
            sensor = row["topic"].rsplit("/", 1)[-1]
            if payload.get("quality") != "VALID":
                continue
            if sensor == "vibration":
                value = vibration_features(payload)["vibration_rms_g"]
            else:
                value = payload["value"]
            points.append({
                "time": pd.to_datetime(row["timestamp_ms"], unit="ms", utc=True),
                "sensor": sensor, "value": float(value),
                "source": row.get("source") or "PHYSICAL",
            })
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            continue
    return pd.DataFrame(points)


st.warning("Academic demonstration. Rule thresholds are illustrative, not equipment safety limits. "
           "Synthetic data and synthetic ML predictions must not be treated as real fault detection.")


@st.fragment(run_every="2s")
def live():
    snapshot = latest_snapshot()
    now = int(time.time() * 1000)
    if not snapshot:
        st.info("No Digital Twin snapshots yet. Start raspberry-pi/live_service.py and publish sensor telemetry.")
        return
    last = snapshot.get("last_updated_ms")
    fresh = isinstance(last, int) and 0 <= now - last <= 12000
    state = snapshot["health_state"] if fresh else "UNKNOWN"
    metrics = snapshot.get("metrics", {}) if fresh else {}
    source = snapshot.get("source", "UNKNOWN")
    st.subheader("Live machine state")
    a, b, c, d = st.columns(4)
    a.metric("Health state", state)
    b.metric("Telemetry", "LIVE" if fresh else "STALE / OFFLINE")
    c.metric("Data source", source or "UNKNOWN")
    d.metric("Last updated", datetime.fromtimestamp(last / 1000, tz=timezone.utc).strftime("%H:%M:%S UTC") if last else "—")
    if state == "FAULT":
        st.error(snapshot.get("message", "Fault"))
    elif state == "WARNING":
        st.warning(snapshot.get("message", "Warning"))
    elif state == "HEALTHY":
        st.success(snapshot.get("message", "Healthy"))
    else:
        st.info("Telemetry missing, invalid or stale. Last known health is not current.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temperature (°C)", f"{metrics['temperature_c']:.1f}" if "temperature_c" in metrics else "—")
    m2.metric("Current (A)", f"{metrics['current_a']:.3f}" if "current_a" in metrics else "—")
    m3.metric("Speed (RPM)", f"{metrics['rpm']:.0f}" if "rpm" in metrics else "—")
    m4.metric("Dynamic vibration RMS (g)", f"{metrics['vibration_rms_g']:.3f}" if "vibration_rms_g" in metrics else "—")

    st.subheader("Machine-learning output")
    if fresh and snapshot.get("predicted_state") is not None:
        st.write(f"**Prediction:** {snapshot['predicted_state']}  |  "
                 f"**Model:** {snapshot.get('model_version')}  |  "
                 f"**Dataset type:** {snapshot.get('model_data_type', 'UNVERIFIED')}")
        if snapshot.get("confidence") is not None:
            st.write(f"Classifier probability: {snapshot['confidence']:.2%} (not calibrated)")
    else:
        st.caption("ML inference UNAVAILABLE; demonstration rule-based health state is shown above.")

    st.subheader("Sensor history")
    table = recent_measurements(200)
    if table.empty:
        st.info("No sensor history saved yet.")
    else:
        for sensor, title in (
            ("temperature", "Temperature (°C)"),
            ("current", "Current (A)"),
            ("rpm", "Motor speed (RPM)"),
            ("vibration", "Dynamic vibration RMS (g)"),
        ):
            data = table[table.sensor == sensor]
            if not data.empty:
                st.caption(title)
                st.line_chart(data.set_index("time")["value"])
    st.subheader("Maintenance / state alerts")
    alerts = query("SELECT timestamp_ms, previous_state, new_state, message, source FROM alerts ORDER BY id DESC LIMIT 30")
    if alerts:
        report = pd.DataFrame(alerts)
        report["time_utc"] = pd.to_datetime(report.pop("timestamp_ms"), unit="ms", utc=True)
        st.dataframe(report[["time_utc", "previous_state", "new_state", "message", "source"]], use_container_width=True, hide_index=True)
    else:
        st.caption("No alert transitions yet.")


live()
with st.expander("How to interpret this screen"):
    st.markdown(
        "**Digital Twin:** persisted, stateful software representation of MOTOR_01. "
        "The live status changes to UNKNOWN on stale data. "
        "**Health score and rule thresholds:** illustrative demo only; not Remaining Useful Life. "
        "**Model probabilities:** uncalibrated classification probabilities; not certified confidence. "
        "**Historical readings:** may include synthetic tests. "
        "Use validated physical sensor calibration and labelled independent runs before industrial claims."
    )
