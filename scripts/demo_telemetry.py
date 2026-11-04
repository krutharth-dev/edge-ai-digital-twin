#!/usr/bin/env python3
"""Publish explicitly synthetic MVP telemetry for local MQTT integration tests.

Not firmware, not real measurements, and not an ML training dataset.
Run from the repository root after starting a local Mosquitto broker:

    python scripts/demo_telemetry.py --mode cycle --count 20 --interval 1
"""
from __future__ import annotations

import argparse
import json
import os
import random
import time
from typing import Any


def make_messages(
    mode: str, timestamp_ms: int, sequence_start: int = 0, rng: random.Random | None = None
) -> list[tuple[str, dict[str, Any]]]:
    """Return V1 MQTT topic suffixes and JSON-compatible synthetic messages.

    The example purposefully publishes only the two MVP modalities. Each payload
    contains `synthetic: true` so downstream consumers can exclude fake data
    from experimentally collected datasets.
    """
    if mode not in ("normal", "abnormal"):
        raise ValueError("mode must be 'normal' or 'abnormal'")
    if timestamp_ms < 0 or sequence_start < 0:
        raise ValueError("timestamp and sequence must be non-negative")

    generator = rng if rng is not None else random.Random()
    abnormal = mode == "abnormal"
    base = {
        "schema_version": 1,
        "asset_id": "MOTOR_01",
        "timestamp_ms": timestamp_ms,
        "run_id": None,
        "quality": "VALID",
        "synthetic": True,
        "simulated_mode": mode.upper(),
    }
    amps = (0.92 if abnormal else 0.38) + generator.uniform(-0.03, 0.03)
    spread = 0.19 if abnormal else 0.025
    count = 25

    current = {
        **base,
        "sequence": sequence_start,
        "value": round(amps, 3),
        "unit": "A",
    }
    vibration = {
        **base,
        "sequence": sequence_start + 1,
        "unit": "g",
        "sample_rate_hz": 25,
        "sample_count": count,
        "x": [round(generator.uniform(-spread, spread), 4) for _ in range(count)],
        "y": [round(generator.uniform(-spread, spread), 4) for _ in range(count)],
        "z": [
            round(1.0 + generator.uniform(-spread, spread), 4)
            for _ in range(count)
        ],
    }
    return [("current", current), ("vibration", vibration)]


def run() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("normal", "abnormal", "cycle"), default="cycle")
    parser.add_argument("--count", type=int, default=20, help="Number of publishing rounds; 0 runs until Ctrl+C")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between rounds")
    args = parser.parse_args()
    if args.count < 0 or args.interval <= 0:
        parser.error("--count must be >= 0 and --interval must be > 0")

    from dotenv import load_dotenv
    import paho.mqtt.client as mqtt

    load_dotenv()
    host = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    base_topic = os.getenv("MQTT_BASE_TOPIC", "motor01").strip("/")
    if not base_topic:
        parser.error("MQTT_BASE_TOPIC must not be empty")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    username = os.getenv("MQTT_USERNAME")
    if username:
        client.username_pw_set(username, os.getenv("MQTT_PASSWORD") or None)
    try:
        client.connect(host, port, 60)
    except OSError as exc:
        print(f"Cannot connect to MQTT at {host}:{port}: {exc}")
        print("Start a local broker first: mosquitto -p 1883 -v")
        return 1

    rng = random.Random()
    iteration = 0
    sequence = 0
    client.loop_start()
    print(f"Publishing SYNTHETIC telemetry to {host}:{port}/{base_topic}/# (Ctrl+C to stop)")
    try:
        while args.count == 0 or iteration < args.count:
            mode = args.mode if args.mode != "cycle" else ("normal" if (iteration // 5) % 2 == 0 else "abnormal")
            timestamp_ms = int(time.time() * 1000)
            messages = make_messages(mode, timestamp_ms, sequence, rng)
            for suffix, payload in messages:
                topic = f"{base_topic}/{suffix}"
                result = client.publish(topic, json.dumps(payload), qos=0, retain=False)
                result.wait_for_publish(timeout=5)
                if not result.is_published():
                    raise RuntimeError(f"MQTT publish timed out on {topic}")
                print(f"{mode.upper():8} {topic} seq={payload['sequence']} synthetic=true")
                sequence += 1
            iteration += 1
            if args.count == 0 or iteration < args.count:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped simulated publisher.")
    finally:
        client.loop_stop()
        client.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
