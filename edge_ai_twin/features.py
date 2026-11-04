"""Training and live inference share precisely the same feature calculation."""
import math
import numpy as np

FEATURE_NAMES = (
    "vibration_rms_g", "vibration_std_g", "vibration_peak_g",
    "vibration_peak_to_peak_g", "vibration_crest_factor",
    "vibration_kurtosis", "temperature_c", "current_a", "rpm",
)


def vibration_features(payload):
    axes = np.asarray([payload["x"], payload["y"], payload["z"]], dtype=float)
    if axes.ndim != 2 or axes.shape[1] < 2 or not np.isfinite(axes).all():
        raise ValueError("Expected a finite, three-axis vibration window")
    # Remove per-axis offset, including the approximately 1 g gravity component.
    dynamic = axes - axes.mean(axis=1, keepdims=True)
    magnitudes = np.sqrt(np.sum(dynamic ** 2, axis=0))
    rms = float(np.sqrt(np.mean(magnitudes ** 2)))
    peak = float(magnitudes.max())
    flat = dynamic.ravel()
    variance = float(np.mean((flat - flat.mean()) ** 2))
    kurtosis = (
        float(np.mean((flat - flat.mean()) ** 4) / variance ** 2)
        if variance > 1e-15 else 0.0
    )
    return {
        "vibration_rms_g": rms,
        "vibration_std_g": float(np.std(magnitudes)),
        "vibration_peak_g": peak,
        "vibration_peak_to_peak_g": float(np.ptp(magnitudes)),
        "vibration_crest_factor": peak / rms if rms > 1e-12 else 0.0,
        "vibration_kurtosis": kurtosis,
    }


def extract_features(readings):
    result = vibration_features(readings["vibration"])
    result.update({
        "temperature_c": float(readings["temperature"]["value"]),
        "current_a": float(readings["current"]["value"]),
        "rpm": float(readings["rpm"]["value"]),
    })
    if any(not math.isfinite(v) for v in result.values()):
        raise ValueError("Nonfinite extracted feature")
    return {key: result[key] for key in FEATURE_NAMES}
