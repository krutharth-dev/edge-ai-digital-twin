# ESP32 real sensors -> React + FastAPI (Windows uploader + Mac host)

**Branch:** feature/esp32-react-live-integration

This combines the physical ESP32 MQTT sketch, individual sensor diagnostics, Python Digital Twin, FastAPI/WebSocket API and React dashboard. Physical Wi-Fi, Arduino compilation, sensor wiring and calibration **must be tested on the real hardware** before the project is considered validated.

## Architecture

    ADXL345 + DS18B20 + ACS712 + Hall (physical)
                    |
            ESP32, 2.4 GHz Wi-Fi
                    |
        Mac's Mosquitto MQTT broker :1884
                    |
          raspberry-pi/live_service.py
              (only SQLite writer)
                    |
           data/motor_readings.db
                    |
           web_api/main.py :8000
                    |
          React/Vite frontend :5173
            (OPEN ON THE MAC)

Windows is used **only to upload firmware**. ESP32 can then be powered by an appropriate USB supply; it does not need a USB connection to your Mac or the friend's Windows PC. **ESP32 and Mac must be on the same reachable, trusted LAN.** Do not expose MQTT or the localhost development servers to the public internet.

## 1. Mac: pull the combined branch

Use normal macOS Terminal. The React runbook used ~/Documents/edge-ai-digital-twin; if yours is elsewhere, use your actual repository path.

    cd ~/Documents/edge-ai-digital-twin
    git status --short
    git fetch origin
    git switch --track origin/feature/esp32-react-live-integration

If the branch exists locally, use git switch feature/esp32-react-live-integration followed by git pull --ff-only. Preserve local changes first; never force-reset your work.

Create or activate Python 3.12 environment and install dependencies:

    python3.12 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements-dev.txt

Also install Node.js 20.19+ or 22.12+ and npm if absent, for Vite 7.

## 2. Mac: secure private-network MQTT broker on 1884

Your older 1883 demo broker is localhost-only and cannot accept ESP32 Wi-Fi clients. Follow docs/LAN_MQTT_SETUP.md: it uses a **separate password-protected listener on 1884**, not an anonymous port. This is unencrypted MQTT, suitable ONLY for a trusted isolated network; use TLS/certificates for untrusted or production setups.

Find Mac LAN IP and check for an existing listener:

    ipconfig getifaddr en0
    lsof -nP -iTCP:1884 -sTCP:LISTEN

If en0 shows no IP, find your Wi-Fi interface with networksetup -listallhardwareports and check that interface instead. Record the Mac's IPv4 address for MQTT_HOST in Windows. It may change later.

One-time create private broker credentials (the -c flag OVERWRITES an existing password file; omit it if one already exists):

    mkdir -p "$HOME/.config/edge-ai"
    /opt/local/bin/mosquitto_passwd -c "$HOME/.config/edge-ai/passwords" motor01
    chmod 600 "$HOME/.config/edge-ai/passwords"

Keep the chosen MQTT password secret. Create a broker config:

    cat > "$HOME/.config/edge-ai/mosquitto-lan.conf" <<EOF
    listener 1884
    allow_anonymous false
    password_file $HOME/.config/edge-ai/passwords
    persistence false
    EOF

**Terminal 1 — broker** (leave running):

    /opt/local/sbin/mosquitto -c "$HOME/.config/edge-ai/mosquitto-lan.conf" -v

If port 1884 was already listening, inspect that service instead of starting another. If the broker cannot read the password file, fix local filesystem/process access; **do not disable authentication**. Allow incoming traffic in macOS Firewall only from your trusted LAN.

## 3. Windows: install Arduino IDE and upload

1. Download Arduino IDE 2 from https://www.arduino.cc/en/software .
2. File > Preferences > Additional Boards Manager URLs: add https://espressif.github.io/arduino-esp32/package_esp32_index.json . Then Boards Manager > install **esp32 by Espressif Systems**.
3. Library Manager > install **PubSubClient** (Nick O'Leary), **ArduinoJson 7**, **Adafruit ADXL345**, **Adafruit Unified Sensor** (and **Adafruit BusIO** dependency), **OneWire** and **DallasTemperature**.
4. Download the combined GitHub branch as ZIP (Code > Download ZIP), extract it. FIRST test each individual sensor via esp32/sensor-tests/WINDOWS_SETUP.md.
5. From **esp32/live-mqtt/esp32_live_mqtt/** copy **secrets.example.h** to **secrets.h** in the SAME folder. Edit the new file with YOUR real credentials:

       #define WIFI_SSID "YOUR_2_4_GHZ_WIFI"
       #define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
       #define MQTT_HOST "YOUR_MAC_LAN_IP"
       #define MQTT_PORT 1884
       #define MQTT_USERNAME "motor01"
       #define MQTT_PASSWORD "YOUR_MQTT_PASSWORD"

   A classic ESP32 uses 2.4 GHz Wi-Fi. The Mac and ESP32 need a reachable shared network; do not use 127.0.0.1 on the ESP32. Never commit or share secrets.h.

6. With the **motor power disconnected**, connect each verified sensor (power OFF when changing wiring):

   | Sensor | ESP32 pins | Critical condition |
   | --- | --- | --- |
   | ADXL345 | 3.3V, GND, SDA=21, SCL=22 | I2C strap/address per module |
   | DS18B20 | 3.3V, GND, DATA=4 | 4.7 kΩ pull-up DATA->3.3V |
   | ACS712 | conditioned OUT->GPIO35 | **NEVER raw 5V output**; verify divider by meter before attaching ESP32 ADC |
   | Hall switch | 3.3V-safe digital OUT->GPIO27 | check sensor supply and output levels |

7. On Arduino IDE: **File > Open > esp32_live_mqtt.ino** (folder name already matches sketch name), choose correct **ESP32 Dev Module / exact board** and Windows COM port. Click **Verify**, then **Upload**. Open Serial Monitor at **115200 baud**.

Expected types of messages (examples, not actual test results):

    === MOTOR_01 ESP32 -> React live integration ===
    ADXL345: DETECTED | DS18B20: DETECTED
    MQTT target: 192.168.x.x:1884
    MQTT CONNECTED to Mac broker; publishing PHYSICAL sensor data
    TX motor01/temperature: ... bytes
    TX motor01/current: ... bytes
    TX motor01/rpm: ... bytes
    TX motor01/vibration: ... bytes

The sketch does **not** drive a motor. It requires reachable **NTP time** and will NOT send invalid unsynchronized timestamps. If a classroom network blocks NTP, configure a trusted reachable NTP source; do not fabricate time values.

**IMPORTANT:** the integrated firmware deliberately starts with ACS_CALIBRATED=false and HALL_TESTED_AND_PPR_VERIFIED=false. Until verified, those topics send **CALIBRATION_REQUIRED**, and motor health correctly stays **UNKNOWN**. Do not flip these flags merely to make the screen green. Calibrate ACS712 zero/sensitivity/divider with an external meter and verify Hall pulse count before setting the flags true.

## 4. Start the demo on the Mac

After installing the documented broker configuration, Python environment and frontend dependencies, run `./start_mvp.sh` from the repository. Stop any manually launched receiver first. The launcher prompts for the MQTT password and stays in the foreground. Open http://127.0.0.1:5173. Use Ctrl-C or `./stop_mvp.sh` to stop the managed services, and `./status_mvp.sh` to list the processes. Logs are under ~/.local/state/edge-ai-twin. A pre-existing broker stays running.

On Windows, if your Mac already allows SSH from the trusted hotspot, run `ssh -N -L 5173:127.0.0.1:5173 MAC_USER@MAC_LAN_IP` and open http://127.0.0.1:5173 there too. Both browsers then use the same Mac API and database.

With the motor power isolated, compare a Serial TX temperature record with /api/physical/latest and the temperature card. Match sequence, timestamp and value. After unplugging the ESP32 wait 13 seconds and check that the live number disappears. When the board reconnects, check that the boot ID changes and fresh samples appear. To collect raw ADC diagnostics after electrical verification, enable ACS_INTERFACE_VERIFIED in secrets.h. Leave ACS_CALIBRATED false until offset, divider ratio and sensitivity are measured.

### Manual startup for troubleshooting

Leave broker Terminal 1 running. Open three more terminal windows in the SAME repository.

**Terminal 2 — MQTT receiver / Digital Twin, the only database writer:**

    cd ~/Documents/edge-ai-digital-twin
    source .venv/bin/activate
    export MQTT_HOST=127.0.0.1
    export MQTT_PORT=1884
    export MQTT_USERNAME=motor01
    read -s 'MQTT_PASSWORD?MQTT password: '
    export MQTT_PASSWORD
    echo
    python raspberry-pi/live_service.py

This should print CONNECTED; listening to motor01 sensor telemetry, followed by sensor topic messages when ESP32 publishes. Do NOT also run raspberry-pi/mqtt_receiver.py, and stop the synthetic simulator while verifying real PHYSICAL-only data.

**Terminal 3 — FastAPI read-only API:**

    cd ~/Documents/edge-ai-digital-twin
    source .venv/bin/activate
    python -m uvicorn web_api.main:app --host 127.0.0.1 --port 8000

Test http://127.0.0.1:8000/api/health and http://127.0.0.1:8000/api/dashboard on the Mac. /api/health says the **API** works, not that the motor is healthy. /api/dashboard shows snapshot, **per-sensor quality and freshness**, history and alerts.

**Terminal 4 — React:**

    cd ~/Documents/edge-ai-digital-twin/frontend
    npm install
    npm run dev

Open **http://127.0.0.1:5173** on your **MAC**. This is the React application, not Streamlit (:8501). Vite proxies /api and /ws to FastAPI:8000. A green WebSocket connection in React does NOT by itself prove ESP32 connectivity; check incoming backend topics and live PHYSICAL statuses.

## 5. Interpret readings and run checks

The updated React cards can show individual **VALID / PHYSICAL**, **CALIBRATION_REQUIRED / PHYSICAL**, **MISSING**, and **STALE / OFFLINE** states even if the overall twin is **UNKNOWN**. Fresh individual valid sensor values are displayed independently, but UNKNOWN stays UNKNOWN until all four sensors are valid and consistent. The physical history endpoint excludes SIMULATED rows. Health thresholds, predictions and scores are academic demonstrations, **not** machine protection.

Optional software-only checks on the Mac:

    python -m pytest -q tests/test_software_mvp.py tests/test_dashboard_api.py tests/test_physical_react_flow.py
    cd frontend
    npm run build

These tests cannot establish real motor accuracy, calibration, Wi-Fi performance, or ESP32 compilation.

## Troubleshooting checklist

- **No COM port or upload**: correct USB data cable, Windows USB-to-UART driver, board/port, BOOT button if needed.
- **Missing Arduino headers**: install libraries above in Library Manager.
- **Wi-Fi retrying**: ESP32 needs 2.4 GHz, proper SSID/password and no AP client isolation.
- **Waiting for NTP**: no reachable time server; fix networking/time, do not spoof telemetry timestamps.
- **MQTT connection failed**: correct Mac LAN IP, port 1884, credentials, Mac Firewall and same trusted LAN; inspect broker terminal.
- **MQTT connected but backend sees no topics**: check backend uses port 1884 and same broker; check Serial TX messages.
- **Backend rejects timestamps**: ESP32 NTP and Mac clocks must agree (Unix epoch milliseconds).
- **API responds, React reconnecting**: check FastAPI :8000, Vite :5173, WebSocket proxy in frontend/vite.config.ts.
- **Only temperature and vibration appear**: current and Hall are intentionally flagged CALIBRATION_REQUIRED until safely verified.
- **Health stays UNKNOWN**: correct during missing, stale, uncalibrated, or inconsistent measurements; don't invent sensor data.

For any motor testing: isolate motor power while wiring; use appropriately rated fuse, wiring, motor driver, physical cutoff, shaft guard and the repository's docs/SAFETY.md. The software is not an emergency stop.
