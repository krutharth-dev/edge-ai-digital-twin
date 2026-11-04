"""Read-only diagnostic for the Mac software MVP.

Run: python scripts/check_environment.py
Add --broker to test a TCP listener on MQTT_HOST:MQTT_PORT.
The tool never starts services, modifies your files, or prints secrets.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import socket
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULES = {
    "Paho MQTT": "paho",
    "NumPy": "numpy",
    "Pandas": "pandas",
    "SciPy": "scipy",
    "scikit-learn": "sklearn",
    "joblib": "joblib",
    "Streamlit": "streamlit",
    "pytest": "pytest",
}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only development environment check")
    parser.add_argument("--broker", action="store_true", help="Check TCP reachability on configured MQTT port")
    args = parser.parse_args(argv)

    problems = []
    print("Edge-AI Digital Twin — local environment check")
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 12):
        problems.append("Use Python 3.12 or newer for the tested setup")

    if not (ROOT / "README.md").exists() or not (ROOT / "requirements.txt").exists():
        problems.append("Run inside the expected repository checkout")
    else:
        print(f"Repository: {ROOT}")

    for label, module in MODULES.items():
        available = importlib.util.find_spec(module) is not None
        print(f"{'OK' if available else 'MISSING'}: {label}")
        if not available:
            problems.append(f"Missing Python package: {label}")

    db = ROOT / "data" / "motor_readings.db"
    print(f"SQLite database: {'present (existing readings preserved)' if db.is_file() else 'not created yet (normal before first run)'}")

    broker_path = shutil.which("mosquitto")
    if broker_path is None and Path("/opt/local/sbin/mosquitto").exists():
        broker_path = "/opt/local/sbin/mosquitto"
    print(f"Mosquitto executable: {broker_path or 'not found in known paths'}")
    if args.broker:
        host = os.getenv("MQTT_HOST", "127.0.0.1")
        try:
            port = int(os.getenv("MQTT_PORT", "1883"))
            with socket.create_connection((host, port), timeout=2):
                print(f"MQTT TCP reachable: {host}:{port}")
        except (ValueError, OSError) as exc:
            problems.append(f"MQTT TCP check failed (broker may be offline): {exc}")
        # Successful TCP connection is not proof of MQTT authentication.
    if problems:
        for problem in problems:
            print("ACTION NEEDED:", problem)
        return 1
    print("Core Python environment appears ready. No runtime or hardware validation is implied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
