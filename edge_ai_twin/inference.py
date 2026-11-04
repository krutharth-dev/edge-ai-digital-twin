"""Optional ML inference. Synthetic model disabled by default."""
import json
from pathlib import Path

import joblib
import pandas as pd
from .features import FEATURE_NAMES, extract_features


class ModelPredictor:
    def __init__(self, model_path=None, allow_demo_model=False):
        self.enabled = False
        if model_path is None:
            return
        path = Path(model_path)
        metadata_path = path.with_suffix(".json")
        if not path.is_file() or not metadata_path.is_file():
            raise FileNotFoundError("Model and adjacent metadata .json required")
        self.metadata = json.loads(metadata_path.read_text())
        if tuple(self.metadata.get("features", [])) != FEATURE_NAMES:
            raise ValueError("Model feature contract mismatch")
        if self.metadata.get("data_type") != "REAL" and not allow_demo_model:
            raise ValueError("Synthetic model requires --allow-demo-model")
        # Never unpickle models from unknown sources.
        self.model = joblib.load(path)
        self.enabled = True

    def predict(self, readings):
        if not self.enabled:
            return None
        row = pd.DataFrame([extract_features(readings)], columns=list(FEATURE_NAMES))
        label = str(self.model.predict(row)[0])
        conf = float(max(self.model.predict_proba(row)[0])) if hasattr(self.model, "predict_proba") else None
        return {
            "predicted_state": label, "confidence": conf,
            "model_version": self.metadata.get("model_version"),
            "model_data_type": self.metadata.get("data_type"),
        }
