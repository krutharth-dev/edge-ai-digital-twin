"""Run-group separation tests, without pretending synthetic data is real."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai"))
sys.path.insert(0, str(ROOT))
from train_real import split_runs
from edge_ai_twin.features import FEATURE_NAMES


def example_data(source="PHYSICAL"):
    rows = []
    for label in ("NORMAL", "FAULT"):
        for run in range(6):
            for window in range(4):
                rows.append({
                    **{f: 1.0 + run + window for f in FEATURE_NAMES},
                    "run_id": f"{label}_run{run}", "label": label,
                    "source": source,
                })
    return pd.DataFrame(rows)


def test_classwise_group_split_has_no_leakage():
    train, val, test = split_runs(example_data())
    assert not set(train.run_id) & set(val.run_id)
    assert not set(test.run_id) & set(train.run_id)
    assert not set(test.run_id) & set(val.run_id)
    for data in (train, val, test):
        assert set(data.label) == {"NORMAL", "FAULT"}


def test_reject_simulated_data():
    with pytest.raises(ValueError, match="PHYSICAL"):
        split_runs(example_data("SIMULATED"))


def test_insufficient_runs_rejected():
    frame = example_data()
    frame = frame[~frame.run_id.str.endswith("_run5")]
    with pytest.raises(ValueError, match=">=6"):
        split_runs(frame)
