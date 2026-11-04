"""Unit checks for the explicitly synthetic MQTT demo publisher."""
import importlib.util
import json
import random
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "demo_telemetry.py"
spec = importlib.util.spec_from_file_location("demo_telemetry", MODULE_PATH)
assert spec and spec.loader
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


def test_demo_payloads_match_mvp_topic_contract():
    messages = demo.make_messages("normal", 1_700_000_000_000, 8, random.Random(5))
    assert [name for name, _ in messages] == ["current", "vibration"]
    assert [payload["sequence"] for _, payload in messages] == [8, 9]
    for _, payload in messages:
        assert payload["asset_id"] == "MOTOR_01"
        assert payload["schema_version"] == 1
        assert payload["timestamp_ms"] == 1_700_000_000_000
        assert payload["quality"] == "VALID"
        assert payload["run_id"] is None
        assert payload["synthetic"] is True
        json.dumps(payload)

    assert messages[0][1]["unit"] == "A"
    vibration = messages[1][1]
    assert vibration["unit"] == "g"
    assert vibration["sample_count"] == 25
    for axis in ("x", "y", "z"):
        assert len(vibration[axis]) == 25


def test_abnormal_demo_changes_expected_synthetic_measurements():
    normal = demo.make_messages("normal", 1000, 0, random.Random(123))
    abnormal = demo.make_messages("abnormal", 1000, 0, random.Random(123))
    assert abnormal[0][1]["value"] > normal[0][1]["value"]
    assert abnormal[1][1]["simulated_mode"] == "ABNORMAL"
    assert normal[1][1]["simulated_mode"] == "NORMAL"
    assert abnormal[1][1]["x"] != normal[1][1]["x"]


def test_bad_mode_and_invalid_sequence_rejected():
    import pytest

    with pytest.raises(ValueError):
        demo.make_messages("thermal", 1000)
    with pytest.raises(ValueError):
        demo.make_messages("normal", 1000, -1)
