import shutil
import subprocess
from pathlib import Path

import pytest


def test_integrated_firmware_calibration_math(tmp_path):
    compiler = shutil.which("c++")
    if compiler is None:
        pytest.skip("Host C++ compiler unavailable")
    root = Path(__file__).resolve().parents[1]
    include = root / "esp32/live-mqtt/esp32_live_mqtt"
    source = tmp_path / "calibration.cpp"
    source.write_text("""
#include "measurement_math.h"
#include <cassert>
#include <initializer_list>
int main() {
    for (float sensitivity : {0.185f, 0.100f, 0.066f}) {
        assert(currentMagnitude(1.25f, 2, 2.5f, sensitivity) == 0);
        float adc = (2.5f + 2 * sensitivity) / 2;
        assert(std::fabs(currentMagnitude(adc, 2, 2.5f, sensitivity) - 2) < 0.00001f);
    }
    assert(windowRpm(0, 1040, 2) == 0);
    assert(windowRpm(5, 1250, 2) == 120);
}
""")
    executable = tmp_path / "calibration"
    subprocess.run([compiler, "-std=c++11", "-I", include, source, "-o", executable], check=True)
    subprocess.run([executable], check=True)
