"""End-to-end integration smoke test against an already-started local Mosquitto broker.

CI starts Mosquitto on 18884; this verifies:
publisher -> MQTT broker -> live service -> SQLite sensor/twin/alert rows.
It uses a disposable database and never interferes with data/motor_readings.db.
"""
import argparse
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(port):
    with tempfile.TemporaryDirectory() as folder:
        db_path = Path(folder) / "smoke.db"
        command = [
            sys.executable, str(ROOT / "raspberry-pi" / "live_service.py"),
            "--host", "127.0.0.1", "--port", str(port), "--database", str(db_path),
        ]
        receiver = subprocess.Popen(
            command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )
        try:
            time.sleep(1.5)
            if receiver.poll() is not None:
                raise RuntimeError("Live service exited immediately")
            for scenario in ("normal", "overload"):
                publisher = subprocess.run(
                    [
                        sys.executable, str(ROOT / "simulator" / "mqtt_publisher.py"),
                        "--host", "127.0.0.1", "--port", str(port),
                        "--scenario", scenario, "--count", "5", "--interval", "0.08",
                    ],
                    cwd=ROOT, text=True, capture_output=True, timeout=30,
                )
                if publisher.returncode:
                    raise RuntimeError(
                        f"Publisher {scenario} failed:\n{publisher.stdout}\n{publisher.stderr}"
                    )
            time.sleep(1.0)
            with sqlite3.connect(db_path) as db:
                count = db.execute("SELECT COUNT(*) FROM sensor_readings").fetchone()[0]
                states = {
                    item[0] for item in db.execute("SELECT DISTINCT health_state FROM twin_snapshots")
                }
                alerts = db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
            print("MQTT smoke:", count, "sensor messages; states:", states, "; alerts:", alerts)
            if count < 40 or "HEALTHY" not in states or "WARNING" not in states or alerts < 1:
                raise RuntimeError("End-to-end MQTT or alert pipeline incomplete")
            print("MQTT END-TO-END SOFTWARE SMOKE PASSED")
        finally:
            receiver.terminate()
            try:
                receiver.wait(timeout=5)
            except subprocess.TimeoutExpired:
                receiver.kill()
                receiver.wait(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=18884)
    args = parser.parse_args()
    main(args.port)
