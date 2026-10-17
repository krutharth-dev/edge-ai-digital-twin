"""Scenario-driven sensor DEMO. Same MQTT topics as the ESP32 contract.

python simulator/mqtt_publisher.py --scenario normal --count 5
python simulator/mqtt_publisher.py --scenario overload --count 20
"""
import argparse
import json
import os
import time

import paho.mqtt.client as mqtt

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from edge_ai_twin.simulation import SCENARIOS, generate_batch, new_run_id


def main():
    p = argparse.ArgumentParser(description="Publish explicitly simulated motor telemetry")
    p.add_argument("--scenario", choices=SCENARIOS, default="normal")
    p.add_argument("--count", type=int, default=5, help="Number of batches; 0 means unlimited")
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--host", default=os.getenv("MQTT_HOST", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
    args = p.parse_args()
    if args.count < 0 or args.interval <= 0:
        p.error("--count must be >= 0 and --interval must be > 0")
    run_id = new_run_id(args.scenario)
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"motor01_demo_{run_id[-12:]}",
    )
    def status(value):
        return json.dumps({
            "schema_version": 1, "asset_id": "MOTOR_01",
            "timestamp_ms": int(time.time() * 1000),
            "run_id": run_id, "source": "SIMULATED", "status": value,
        })
    client.will_set("motor01/status", status("offline"), qos=1, retain=True)
    try:
        client.connect(args.host, args.port, 60)
        client.loop_start()
        for _ in range(60):
            if client.is_connected():
                break
            time.sleep(0.1)
        else:
            raise TimeoutError("Broker connection not established")
        client.publish("motor01/status", status("online"), qos=1, retain=True).wait_for_publish(timeout=5)
        print(f"CONNECTED: {args.host}:{args.port} | {args.scenario} | {run_id}", flush=True)
        seq = 1
        while args.count == 0 or seq <= args.count:
            batch = generate_batch(args.scenario, seq, run_id, seed=seq + 143 * len(run_id))
            for topic, payload in batch.items():
                qos = 0 if topic.endswith("/vibration") else 1
                result = client.publish(topic, json.dumps(payload), qos=qos, retain=False)
                result.wait_for_publish(timeout=5)
                if not result.is_published():
                    raise TimeoutError(f"Publish timed out: {topic}")
                print(f"Published {topic} #{seq}", flush=True)
            seq += 1
            time.sleep(args.interval)
        print("SIMULATION COMPLETED", flush=True)
    except (OSError, TimeoutError) as error:
        print(f"PUBLISHER ERROR: {error}", flush=True)
        raise SystemExit(1) from error
    except KeyboardInterrupt:
        print("Stopping simulator", flush=True)
    finally:
        if client.is_connected():
            client.publish("motor01/status", status("offline"), qos=1, retain=True).wait_for_publish(timeout=5)
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
