"""Operational digital twin with freshness, provenance, and demo-rule condition states."""
import time
from .features import vibration_features

WARNING = {"temperature": 55.0, "current": 1.1, "vibration": 0.18}
FAULT = {"temperature": 70.0, "current": 1.8, "vibration": 0.40}
SENSORS = ("temperature", "current", "rpm", "vibration")


class MotorTwin:
    def __init__(self, stale_ms=12000):
        self.stale_ms = stale_ms
        self.readings = {}
        self.health_state = "UNKNOWN"
        self.message = "Waiting for valid telemetry"
        self.last_updated_ms = None
        self.source = None
        self.run_id = None
        self.metrics = {}
        self.predicted_state = None
        self.confidence = None
        self.model_version = None
        self.model_data_type = None

    def ingest(self, topic, payload, now_ms=None):
        now = int(time.time() * 1000) if now_ms is None else now_ms
        sensor = topic.split("/")[-1]
        if sensor not in SENSORS:
            raise ValueError("Unsupported sensor")
        self.readings[sensor] = (payload, now)
        self.last_updated_ms = now
        return self.evaluate(now)

    def evaluate(self, now_ms=None):
        now = int(time.time() * 1000) if now_ms is None else now_ms
        previous = self.health_state
        self.metrics = {}
        self.predicted_state = None
        self.confidence = None
        self.model_version = None
        self.model_data_type = None
        unavailable = [
            sensor for sensor in SENSORS
            if sensor not in self.readings
            or self.readings[sensor][0]["quality"] != "VALID"
            or not 0 <= now - self.readings[sensor][1] <= self.stale_ms
        ]
        ids = {self.readings[sensor][0].get("run_id") for sensor in SENSORS if sensor in self.readings}
        sources = {self.readings[sensor][0].get("source", "PHYSICAL") for sensor in SENSORS if sensor in self.readings}
        if unavailable or len(ids) > 1 or len(sources) > 1:
            self.health_state = "UNKNOWN"
            self.message = (
                "Missing/invalid/stale: " + ", ".join(unavailable)
                if unavailable else "Inconsistent run/source across sensors"
            )
            return previous != self.health_state

        values = {s: self.readings[s][0] for s in SENSORS}
        self.run_id = values["vibration"].get("run_id")
        self.source = values["vibration"].get("source", "PHYSICAL")
        temp = float(values["temperature"]["value"])
        current = float(values["current"]["value"])
        rpm = float(values["rpm"]["value"])
        vib = vibration_features(values["vibration"])["vibration_rms_g"]
        self.metrics = {
            "temperature_c": temp, "current_a": current,
            "rpm": rpm, "vibration_rms_g": vib,
        }

        faults, warnings = [], []
        for name, value in [("temperature", temp), ("current", current), ("vibration", vib)]:
            if value >= FAULT[name]:
                faults.append(name)
            elif value >= WARNING[name]:
                warnings.append(name)
        if rpm < 500:
            faults.append("low RPM")
        elif rpm < 1100:
            warnings.append("low RPM")
        if faults:
            self.health_state = "FAULT"
            self.message = "DEMO rule threshold exceeded: " + ", ".join(faults)
        elif warnings:
            self.health_state = "WARNING"
            self.message = "DEMO warning threshold: " + ", ".join(warnings)
        else:
            self.health_state = "HEALTHY"
            self.message = "Within demonstration thresholds"
        return previous != self.health_state

    def inference_input(self):
        if self.health_state == "UNKNOWN":
            return None
        return {sensor: self.readings[sensor][0] for sensor in SENSORS}

    def snapshot(self, now_ms=None):
        now = int(time.time() * 1000) if now_ms is None else now_ms
        return {
            "schema_version": 1, "asset_id": "MOTOR_01",
            "timestamp_ms": now, "last_updated_ms": self.last_updated_ms,
            "source": self.source, "run_id": self.run_id,
            "data_quality": "VALID" if self.health_state != "UNKNOWN" else "STALE",
            "health_state": self.health_state,
            "health_score": {"HEALTHY": 100, "WARNING": 65, "FAULT": 20}.get(self.health_state),
            "metrics": self.metrics,
            "predicted_state": self.predicted_state,
            "confidence": self.confidence,
            "model_version": self.model_version,
            "model_data_type": self.model_data_type,
            "message": self.message,
            "logic_source": "DEMO_RULES",
        }
