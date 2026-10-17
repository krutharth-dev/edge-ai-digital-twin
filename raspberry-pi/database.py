
import json
import math
import sqlite3
import time
from pathlib import Path

# Database is stored in the project's data folder.
DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "motor_readings.db"
)

SENSOR_UNITS = {
    "motor01/temperature": "degC",
    "motor01/current": "A",
    "motor01/rpm": "rpm",
    "motor01/vibration": "g",
}

VALID_QUALITIES = {
    "VALID",
    "INVALID",
    "STALE",
    "CALIBRATION_REQUIRED",
}


def initialize_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                timestamp_ms INTEGER NOT NULL,
                sequence INTEGER NOT NULL,
                run_id TEXT,
                quality TEXT NOT NULL,
                source TEXT,
                unit TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                received_at_ms INTEGER NOT NULL
            )
        """)

    print(f"SQLite database ready: {DB_PATH}")


def validate_reading(topic, payload):
    if topic not in SENSOR_UNITS:
        raise ValueError("Unknown sensor topic")

    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")

    if type(payload.get("schema_version")) is not int:
        raise ValueError("Invalid schema version")

    if payload["schema_version"] != 1:
        raise ValueError("Unsupported schema version")

    if payload.get("asset_id") != "MOTOR_01":
        raise ValueError("Unexpected asset ID")

    if payload.get("unit") != SENSOR_UNITS[topic]:
        raise ValueError("Incorrect sensor unit")

    timestamp = payload.get("timestamp_ms")
    if type(timestamp) is not int or timestamp <= 0:
        raise ValueError("Invalid timestamp")

    sequence = payload.get("sequence")
    if type(sequence) is not int or sequence < 0:
        raise ValueError("Invalid sequence")

    quality = payload.get("quality")
    if quality not in VALID_QUALITIES:
        raise ValueError("Invalid quality flag")

    run_id = payload.get("run_id")
    if run_id is not None and not isinstance(run_id, str):
        raise ValueError("Invalid run ID")

    source = payload.get("source")
    if source is not None and not isinstance(source, str):
        raise ValueError("Invalid source")

    # Non-valid readings may have missing measurement values.
    # Store their quality flags, but do not treat them as healthy.
    if quality != "VALID":
        return

    if topic == "motor01/vibration":
        count = payload.get("sample_count")
        rate = payload.get("sample_rate_hz")

        if type(count) is not int or count <= 0:
            raise ValueError("Invalid vibration sample count")

        if (
            type(rate) not in (int, float)
            or not math.isfinite(rate)
            or rate <= 0
        ):
            raise ValueError("Invalid vibration sample rate")

        for axis in ("x", "y", "z"):
            values = payload.get(axis)

            if not isinstance(values, list):
                raise ValueError(f"Missing vibration axis {axis}")

            if len(values) != count:
                raise ValueError(f"Wrong sample count on axis {axis}")

            for value in values:
                if (
                    type(value) not in (int, float)
                    or not math.isfinite(value)
                ):
                    raise ValueError(f"Invalid sample on axis {axis}")
    else:
        value = payload.get("value")

        if (
            type(value) not in (int, float)
            or not math.isfinite(value)
        ):
            raise ValueError("Invalid sensor value")

        if topic == "motor01/rpm" and value < 0:
            raise ValueError("RPM cannot be negative")

        if topic == "motor01/current" and value < 0:
            raise ValueError("Current magnitude cannot be negative")


def save_reading(topic, payload):
    validate_reading(topic, payload)

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO sensor_readings (
                topic,
                asset_id,
                timestamp_ms,
                sequence,
                run_id,
                quality,
                source,
                unit,
                payload_json,
                received_at_ms
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                topic,
                payload["asset_id"],
                payload["timestamp_ms"],
                payload["sequence"],
                payload.get("run_id"),
                payload["quality"],
                payload.get("source"),
                payload["unit"],
                json.dumps(payload, allow_nan=False),
                int(time.time() * 1000),
            ),
        )


def count_readings():
    with sqlite3.connect(DB_PATH) as connection:
        result = connection.execute(
            "SELECT COUNT(*) FROM sensor_readings"
        ).fetchone()

    return result[0]


if __name__ == "__main__":
    initialize_database()
    print(f"Total saved readings: {count_readings()}")
