"""Extract physical, labelled features from the existing SQLite motor sensor history.

Provide a CSV run manifest with exactly: run_id,label.
Only source=PHYSICAL and quality=VALID messages are admitted.
For each vibration window we use prior/current slow readings within --max-gap-ms.
The output never infers labels from sensor values or simulated scenarios.
"""
import argparse
import csv
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from edge_ai_twin.contracts import InvalidTelemetry, validate_sensor
from edge_ai_twin.features import FEATURE_NAMES, extract_features
from edge_ai_twin.store import DEFAULT_DB


def load_manifest(path):
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"run_id", "label"}.issubset(reader.fieldnames or []):
            raise ValueError("Manifest needs run_id,label columns")
        labels = {}
        for row in reader:
            run, label = row["run_id"].strip(), row["label"].strip().upper()
            if not run or not label:
                raise ValueError("Empty run ID or label")
            if run in labels and labels[run] != label:
                raise ValueError(f"Conflicting labels for {run}")
            labels[run] = label
    if not labels:
        raise ValueError("Manifest has no labelled runs")
    return labels


def export_features(database, manifest, max_gap_ms=2000):
    labels = load_manifest(manifest)
    if max_gap_ms < 1:
        raise ValueError("max_gap_ms must be positive")
    by_run = defaultdict(list)
    with sqlite3.connect(database) as db:
        for topic, text in db.execute(
            "SELECT topic, payload_json FROM sensor_readings ORDER BY timestamp_ms, id"
        ):
            try:
                payload = json.loads(text)
                run_id = payload.get("run_id")
                if run_id not in labels or payload.get("source") != "PHYSICAL":
                    continue
                if payload.get("quality") != "VALID":
                    continue
                validate_sensor(topic, payload, now_ms=payload["timestamp_ms"])
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                continue
            by_run[run_id].append((topic.rsplit("/", 1)[-1], payload))
    extracted = []
    for run_id, events in by_run.items():
        slow = {}
        for sensor, payload in sorted(events, key=lambda item: item[1]["timestamp_ms"]):
            if sensor != "vibration":
                slow[sensor] = payload
                continue
            target = payload["timestamp_ms"]
            if any(k not in slow or target - slow[k]["timestamp_ms"] > max_gap_ms
                   or target - slow[k]["timestamp_ms"] < 0
                   for k in ("temperature", "current", "rpm")):
                continue
            try:
                features = extract_features({**slow, "vibration": payload})
            except (ValueError, KeyError, TypeError):
                continue
            extracted.append({
                **features, "run_id": run_id, "label": labels[run_id],
                "source": "PHYSICAL", "timestamp_ms": target,
            })
    if not extracted:
        raise ValueError("No complete PHYSICAL windows matched the labels/quality/gap")
    return pd.DataFrame(extracted, columns=[
        *FEATURE_NAMES, "run_id", "label", "source", "timestamp_ms"
    ])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--database", default=str(DEFAULT_DB))
    p.add_argument("--labels", required=True, help="CSV with run_id,label")
    p.add_argument("--output", default=str(ROOT / "data" / "processed" / "real_features.csv"))
    p.add_argument("--max-gap-ms", type=int, default=2000)
    args = p.parse_args()
    frame = export_features(args.database, args.labels, args.max_gap_ms)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(dest, index=False)
    print(f"Exported {len(frame)} PHYSICAL windows from {frame.run_id.nunique()} runs to {dest}")
    print("Only independently labelled safe experiments support real model evaluation.")


if __name__ == "__main__":
    main()
