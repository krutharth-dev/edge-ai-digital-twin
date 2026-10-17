
import json
import random
import time

import paho.mqtt.client as mqtt

BROKER = "127.0.0.1"
PORT = 1883
BASE_TOPIC = "motor01"

# Give each simulation execution its own run ID.
RUN_ID = f"simulation_{int(time.time() * 1000)}"


def generate_readings():
    return {
        "temperature": {
            "value": round(random.uniform(30, 35), 2),
            "unit": "degC",
        },
        "current": {
            "value": round(random.uniform(0.35, 0.55), 3),
            "unit": "A",
        },
        "rpm": {
            "value": random.randint(1400, 1500),
            "unit": "rpm",
            "measurement_interval_ms": 1000,
        },
        "vibration": {
            "unit": "g",
            "sample_rate_hz": 10,
            "sample_count": 10,
            "x": [
                round(random.gauss(0, 0.05), 3)
                for _ in range(10)
            ],
            "y": [
                round(random.gauss(0, 0.05), 3)
                for _ in range(10)
            ],
            "z": [
                round(random.gauss(1, 0.05), 3)
                for _ in range(10)
            ],
        },
    }


def main():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="motor01_simulator",
    )

    print("Connecting simulator to MQTT...")

    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()

        for _ in range(50):
            if client.is_connected():
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("MQTT connection timed out")

        print("CONNECTED!")
        print("Publishing simulated motor readings...\n")

        for sequence in range(1, 6):
            common = {
                "schema_version": 1,
                "asset_id": "MOTOR_01",
                "timestamp_ms": int(time.time() * 1000),
                "sequence": sequence,
                "run_id": RUN_ID,
                "quality": "VALID",
                "source": "SIMULATED",
            }

            readings = generate_readings()

            for sensor, values in readings.items():
                topic = f"{BASE_TOPIC}/{sensor}"
                payload = {**common, **values}

                qos = 0 if sensor == "vibration" else 1

                result = client.publish(
                    topic,
                    json.dumps(payload),
                    qos=qos,
                )

                result.wait_for_publish(timeout=5)

                if not result.is_published():
                    raise RuntimeError(
                        f"Publish timed out: {topic}"
                    )

                print(f"Published: {topic}")

            print(f"Completed reading #{sequence}\n")
            time.sleep(1)

        print("SIMULATION COMPLETED!")

    except (OSError, RuntimeError) as error:
        print(f"Publisher error: {error}")

    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
