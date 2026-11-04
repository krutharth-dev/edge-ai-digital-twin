"""Version 1 telemetry validation. Range limits are broad sanity checks, not safety limits."""
import math
import time

SENSOR_UNITS = {
    "motor01/temperature": "degC",
    "motor01/current": "A",
    "motor01/rpm": "rpm",
    "motor01/vibration": "g",
}
SENSOR_TOPICS = tuple(SENSOR_UNITS)
QUALITIES = {"VALID", "INVALID", "STALE", "CALIBRATION_REQUIRED"}
RANGES = {"motor01/temperature": (-40, 125), "motor01/current": (0, 100), "motor01/rpm": (0, 50000)}


class InvalidTelemetry(ValueError):
    pass


def validate_sensor(topic, payload, now_ms=None, max_age_ms=30000):
    if topic not in SENSOR_UNITS:
        raise InvalidTelemetry("Unknown sensor topic")
    if not isinstance(payload, dict):
        raise InvalidTelemetry("Expected JSON object")
    if type(payload.get("schema_version")) is not int or payload["schema_version"] != 1:
        raise InvalidTelemetry("Unsupported schema version")
    if payload.get("asset_id") != "MOTOR_01":
        raise InvalidTelemetry("Unexpected asset ID")
    if payload.get("unit") != SENSOR_UNITS[topic]:
        raise InvalidTelemetry("Wrong sensor unit")
    if type(payload.get("sequence")) is not int or payload["sequence"] < 0:
        raise InvalidTelemetry("Invalid sequence")
    ts = payload.get("timestamp_ms")
    if type(ts) is not int or ts <= 0:
        raise InvalidTelemetry("Invalid Unix millisecond timestamp")
    if payload.get("quality") not in QUALITIES:
        raise InvalidTelemetry("Invalid quality flag")
    if payload.get("run_id") is not None and not isinstance(payload["run_id"], str):
        raise InvalidTelemetry("Invalid run ID")
    if payload.get("boot_id") is not None and not isinstance(payload["boot_id"], str):
        raise InvalidTelemetry("Invalid boot ID")
    if payload.get("source") is not None and not isinstance(payload["source"], str):
        raise InvalidTelemetry("Invalid source")
    now = int(time.time() * 1000) if now_ms is None else now_ms
    if not -10000 <= now - ts <= max_age_ms:
        raise InvalidTelemetry("Old or future timestamp; synchronize ESP32 clock")
    if payload["quality"] != "VALID":
        return payload
    if topic == "motor01/vibration":
        count, rate = payload.get("sample_count"), payload.get("sample_rate_hz")
        if type(count) is not int or not 2 <= count <= 4096:
            raise InvalidTelemetry("Invalid vibration sample_count")
        if type(rate) not in (int, float) or not math.isfinite(rate) or not 0 < rate <= 2000:
            raise InvalidTelemetry("Invalid vibration sample_rate_hz")
        for axis in ("x", "y", "z"):
            values = payload.get(axis)
            if not isinstance(values, list) or len(values) != count:
                raise InvalidTelemetry(f"Invalid vibration axis {axis}")
            if any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 32 for v in values):
                raise InvalidTelemetry(f"Invalid vibration values {axis}")
    else:
        value = payload.get("value")
        if type(value) not in (int, float) or not math.isfinite(value):
            raise InvalidTelemetry("Invalid numeric measurement")
        lo, hi = RANGES[topic]
        if not lo <= value <= hi:
            raise InvalidTelemetry("Outside broad measurement sanity range")
    return payload
