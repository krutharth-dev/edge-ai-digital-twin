"""Train an actual-data baseline on pre-labelled physical feature windows.

Requires at least six *independent physical runs per class*.
No sample-level shuffling across train/validation/test.
The user must verify the accuracy of the run manifest and experimental safety.
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from train_model import ROOT
import sys
sys.path.insert(0, str(ROOT))
from edge_ai_twin.features import FEATURE_NAMES


def split_runs(frame, seed=42):
    required = {"run_id", "label", "source", *FEATURE_NAMES}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if frame.empty or not frame["source"].eq("PHYSICAL").all():
        raise ValueError("Only explicitly PHYSICAL windows are supported here")
    if frame[["run_id", "label"]].isna().any().any():
        raise ValueError("Missing run IDs or labels")
    if frame.groupby("run_id")["label"].nunique().max() != 1:
        raise ValueError("A run may not have multiple class labels")
    if frame["label"].nunique() < 2:
        raise ValueError("At least two classes are required")
    train_runs, val_runs, test_runs = set(), set(), set()
    rng = np.random.default_rng(seed)
    for label, group in frame.groupby("label"):
        runs = np.array(sorted(group["run_id"].unique()), dtype=str)
        if len(runs) < 6:
            raise ValueError(f"{label}: need >=6 independent runs, found {len(runs)}")
        rng.shuffle(runs)
        n_test = max(1, len(runs) // 5)
        n_val = max(1, len(runs) // 5)
        test_runs.update(runs[:n_test])
        val_runs.update(runs[n_test:n_test + n_val])
        train_runs.update(runs[n_test + n_val:])
    return tuple(frame[frame["run_id"].isin(group)].copy() for group in
                 (train_runs, val_runs, test_runs))


def train(input_csv, output):
    df = pd.read_csv(input_csv)
    train_set, val_set, test_set = split_runs(df)
    cols = list(FEATURE_NAMES)
    for part in (train_set, val_set, test_set):
        if not np.isfinite(part[cols].to_numpy(dtype=float)).all():
            raise ValueError("Nonfinite features; clean or exclude invalid physical runs")
    model = RandomForestClassifier(
        n_estimators=150, min_samples_leaf=2, class_weight="balanced",
        random_state=42, n_jobs=-1
    )
    model.fit(train_set[cols], train_set["label"])
    labels = sorted(df["label"].unique().tolist())
    def evaluate(part):
        preds = model.predict(part[cols])
        return {
            "accuracy": float(accuracy_score(part["label"], preds)),
            "classification_report": classification_report(
                part["label"], preds, labels=labels, output_dict=True, zero_division=0
            ),
            "confusion_matrix": confusion_matrix(part["label"], preds, labels=labels).tolist(),
            "runs": sorted(part.run_id.unique().tolist()),
            "samples": len(part),
        }
    evaluation = {"validation": evaluate(val_set), "test": evaluate(test_set)}
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    metadata = {
        "model_version": "physical-run-rf-v1",
        "data_type": "REAL",
        "features": cols,
        "classes": labels,
        "sklearn_version": sklearn.__version__,
        "numpy_version": np.__version__,
        "source_feature_file": str(input_csv),
        "limitations": "Run-held-out evaluation only; performance depends on real run labels and operating coverage.",
        **evaluation,
    }
    path.with_suffix(".json").write_text(json.dumps(metadata, indent=2))
    print("Saved REAL-data model:", path)
    print("Independent-run test accuracy:", round(evaluation["test"]["accuracy"], 3))
    print("Verify confusion matrix, recall, false alarms, operating coverage before any physical decision.")
    return metadata


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="CSV from ai/export_real_features.py")
    p.add_argument("--output", default=str(ROOT / "ai" / "models" / "motor_real.joblib"))
    args = p.parse_args()
    train(args.input, args.output)


if __name__ == "__main__":
    main()
