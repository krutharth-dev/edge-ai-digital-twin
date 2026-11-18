# ESP32 -> Mac MQTT -> React real sensor firmware

Open **esp32_live_mqtt/esp32_live_mqtt.ino** in Arduino IDE on the Windows laptop. The sketch and folder names already match.

Copy **secrets.example.h** to **secrets.h**, fill Wi-Fi credentials and the **Mac LAN IPv4**, port **1884**, MQTT username/password. Do not commit secrets.h. Install Arduino libraries listed in the sketch.

The firmware publishes PHYSICAL data from ADXL345, DS18B20, ACS712 and Hall. **Motor actuation is never performed.** Unverified ACS712 and Hall readings are explicitly marked CALIBRATION_REQUIRED, not made up.

Before use, run each of the standalone sensor sketches in [sensor-tests](../sensor-tests/README.md).

**Full Windows + Mac instructions:** [ESP32 React live setup](../../docs/ESP32_REACT_LIVE_SETUP.md).

Actual ESP32 compilation, wiring and Wi-Fi connectivity have not yet been bench-verified.
