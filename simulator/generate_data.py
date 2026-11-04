
import json
import random
import time

print("EDGE-AI MOTOR SENSOR SIMULATOR")
print("--------------------------------")

for sequence in range(1, 11):
    reading = {
        "schema_version": 1,
        "asset_id": "MOTOR_01",
        "timestamp_ms": int(time.time() * 1000),
        "sequence": sequence,
        "run_id": "simulation_001",
        "quality": "VALID",
        "temperature_c": round(random.uniform(30, 35), 2),
        "vibration_rms_g": round(random.uniform(0.10, 0.25), 3),
        "current_a": round(random.uniform(0.35, 0.55), 3),
        "rpm": random.randint(1400, 1500),
    }

    print(json.dumps(reading, indent=2))
    time.sleep(1)

print("Simulation completed!")
  