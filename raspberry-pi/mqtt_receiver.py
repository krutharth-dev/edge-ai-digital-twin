
import json
import sqlite3

import paho.mqtt.client as mqtt

from database import initialize_database, save_reading

BROKER = "127.0.0.1"
PORT = 1883

TOPICS = [
    "motor01/temperature",
    "motor01/current",
    "motor01/rpm",
    "motor01/vibration",
]


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"MQTT connection failed: {reason_code}")
        return

    print("\nCONNECTED TO MQTT BROKER!")

    for topic in TOPICS:
        client.subscribe(topic)
        print(f"Listening to: {topic}")


def on_message(client, userdata, message):
    if len(message.payload) > 131072:
        print("Rejected oversized MQTT message")
        return

    try:
        payload = json.loads(
            message.payload.decode("utf-8")
        )

        # Validate and store the received data.
        save_reading(message.topic, payload)

    except (UnicodeDecodeError, json.JSONDecodeError):
        print(f"Invalid JSON on {message.topic}")
        return

    except (
        ValueError,
        TypeError,
        KeyError,
        sqlite3.Error,
    ) as error:
        print(f"Reading rejected on {message.topic}: {error}")
        return

    print(f"\nReceived: {message.topic}")
    print(json.dumps(payload, indent=2))
    print(f"SAVED TO DATABASE: {message.topic}")


def main():
    initialize_database()

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="motor01_mac_receiver",
    )

    client.on_connect = on_connect
    client.on_message = on_message

    print("\nEDGE-AI PREDICTIVE MAINTENANCE")
    print("Starting MQTT receiver...")
    print("--------------------------------")

    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_forever()

    except KeyboardInterrupt:
        print("\nMQTT receiver stopped by user.")

    except OSError as error:
        print(f"MQTT connection error: {error}")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
