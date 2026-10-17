"""Mac-hosted MQTT ingest -> SQLite -> operational twin -> health/alerts MQTT.

Run this INSTEAD OF the old mqtt_receiver.py to avoid two competing writers.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from edge_ai_twin.contracts import InvalidTelemetry, SENSOR_TOPICS, validate_sensor
from edge_ai_twin.inference import ModelPredictor
from edge_ai_twin.store import DEFAULT_DB, MotorStore
from edge_ai_twin.twin import MotorTwin


class LiveService:
    def __init__(self, host="127.0.0.1", port=1883, db_path=DEFAULT_DB,
                 model_path=None, allow_demo_model=False):
        self.store = MotorStore(db_path)
        self.twin = MotorTwin()
        self.predictor = ModelPredictor(model_path, allow_demo_model)
        self.sequence = 0
        self.seen_sequences = {}
        self.broker, self.port = host, port
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="motor01_mac_live_service")
        if os.getenv("MQTT_USERNAME"):
            self.client.username_pw_set(os.environ["MQTT_USERNAME"], os.getenv("MQTT_PASSWORD", ""))
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            print(f"MQTT connection rejected: {reason_code}", flush=True)
            return
        for topic in SENSOR_TOPICS:
            client.subscribe(topic, qos=0)
        print("CONNECTED; listening to motor01 sensor telemetry", flush=True)

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        print(f"MQTT disconnected: {reason_code}", flush=True)

    def publish_health(self, snapshot):
        self.sequence += 1
        health = {
            "schema_version": 1, "asset_id": "MOTOR_01",
            "timestamp_ms": snapshot["timestamp_ms"], "sequence": self.sequence,
            "run_id": snapshot.get("run_id"), "quality": snapshot["data_quality"],
            "predicted_state": snapshot["predicted_state"],
            "confidence": snapshot["confidence"],
            "health_state": snapshot["health_state"],
            "health_score": snapshot["health_score"],
            "model_version": snapshot["model_version"],
            "feature_version": "v1_dynamic_acceleration",
            "message": snapshot["message"], "logic_source": snapshot["logic_source"],
            "source": snapshot.get("source"),
        }
        self.client.publish("motor01/health", json.dumps(health), qos=1, retain=True)

    def transition_alert(self, previous, snapshot):
        state = snapshot["health_state"]
        if previous == state or not ({previous, state} & {"WARNING", "FAULT"}):
            return
        self.store.save_alert(previous, snapshot)
        self.client.publish("motor01/alerts", json.dumps({
            "schema_version": 1, "asset_id": "MOTOR_01",
            "timestamp_ms": snapshot["timestamp_ms"],
            "previous_state": previous, "new_state": state,
            "message": snapshot["message"], "source": snapshot.get("source"),
        }), qos=1, retain=False)

    def process(self, topic, payload):
        validate_sensor(topic, payload)
        key = (topic, payload.get("boot_id"), payload.get("run_id"))
        seq = payload["sequence"]
        if seq <= self.seen_sequences.get(key, -1):
            raise InvalidTelemetry("Duplicate or out-of-order sequence")
        if not self.store.save_sensor(topic, payload):
            raise InvalidTelemetry("Duplicate database record")
        self.seen_sequences[key] = seq
        previous = self.twin.health_state
        self.twin.ingest(topic, payload)
        if self.predictor.enabled and self.twin.inference_input() is not None:
            result = self.predictor.predict(self.twin.inference_input())
            self.twin.predicted_state = result["predicted_state"]
            self.twin.confidence = result["confidence"]
            self.twin.model_version = result["model_version"]
            self.twin.model_data_type = result["model_data_type"]
        snapshot = self.twin.snapshot()
        self.store.save_snapshot(snapshot)
        self.publish_health(snapshot)
        self.transition_alert(previous, snapshot)
        return snapshot

    def on_message(self, client, userdata, message):
        if len(message.payload) > 131072:
            print("Rejected oversized MQTT message", flush=True)
            return
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            snapshot = self.process(message.topic, payload)
        except (ValueError, TypeError, KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            print(f"Rejected {message.topic}: {exc}", flush=True)
            return
        print(f"{message.topic}: {snapshot['health_state']} / {snapshot['message']}", flush=True)

    def run(self):
        self.client.connect(self.broker, self.port, keepalive=60)
        self.client.loop_start()
        last_state = self.twin.health_state
        try:
            while True:
                time.sleep(2)
                previous = self.twin.health_state
                changed = self.twin.evaluate()
                if changed:
                    snapshot = self.twin.snapshot()
                    self.store.save_snapshot(snapshot)
                    self.publish_health(snapshot)
                    self.transition_alert(previous, snapshot)
                    print(f"Updated state: {snapshot['health_state']}", flush=True)
        except KeyboardInterrupt:
            print("Stopping service", flush=True)
        finally:
            self.client.disconnect()
            self.client.loop_stop()


def main():
    parser = argparse.ArgumentParser(description="Mac-hosted Edge AI MQTT backend")
    parser.add_argument("--host", default=os.getenv("MQTT_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    parser.add_argument("--database", default=str(DEFAULT_DB))
    parser.add_argument("--model", help="Local trusted .joblib model (optional)")
    parser.add_argument("--allow-demo-model", action="store_true")
    args = parser.parse_args()
    LiveService(args.host, args.port, args.database, args.model, args.allow_demo_model).run()


if __name__ == "__main__":
    main()
