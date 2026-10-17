# MacBook setup, Git pull, execution and safety

This project is a **local Mac + ESP32** academic MVP. Raspberry Pi references
in legacy docs mean the Mac backend service in this version. No Raspberry Pi needed.

## Safe checkout of the entire finished software branch

Run in the **normal macOS Terminal**, not a fresh clone:

    cd ~/edge-ai-digital-twin
    git status

If you have local changes, DO NOT discard or force reset them. Back up first:

    git stash push -u -m "My local backup before full-stack MVP"

Then fetch without changing the current working branch:

    git fetch origin
    git switch -c feature/full-stack-mvp-2026-10 --track origin/feature/full-stack-mvp-2026-10

If that local branch already exists:

    git switch feature/full-stack-mvp-2026-10
    git pull --ff-only

To retrieve any stashed personal changes later, REVIEW first with
    git stash list
    git stash show --stat stash@{0}
and only then consider git stash pop; it may cause conflicts.

## Install Python dependencies

    cd ~/edge-ai-digital-twin
    source .venv/bin/activate
    python -m pip install -r requirements-dev.txt
    python -m pytest -q tests/test_software_mvp.py

On your macOS 13 Intel Mac, the existing Python 3.12 virtualenv is already configured.
Mosquitto 2.1.2 is available from /opt/local/sbin/mosquitto.
Homebrew Mosquitto installation is NOT needed.

## Launch the simulated end-to-end system (three Terminals)

Check that broker port 1883 is open, without launching two brokers:

    lsof -nP -iTCP:1883 -sTCP:LISTEN

If no listener exists, start a local-only development broker (leave open):

    /opt/local/sbin/mosquitto -v

**Terminal A** (Mac backend; replaces old mqtt_receiver.py):

    cd ~/edge-ai-digital-twin
    source .venv/bin/activate
    python raspberry-pi/live_service.py

**Terminal B** (dashboard):

    cd ~/edge-ai-digital-twin
    source .venv/bin/activate
    python -m streamlit run dashboard/app.py

Open the printed localhost URL, normally http://localhost:8501.

**Terminal C** (scenario stimulus):

    cd ~/edge-ai-digital-twin
    source .venv/bin/activate
    python simulator/mqtt_publisher.py --scenario normal --count 20
    python simulator/mqtt_publisher.py --scenario overload --count 20
    python simulator/mqtt_publisher.py --scenario thermal --count 20
    python simulator/mqtt_publisher.py --scenario normal --count 20

Run scenarios sequentially. Dashboard cards update within ~2 seconds.
When data stops for >12 seconds health becomes UNKNOWN (not healthy).
History and alert transitions persist to data/motor_readings.db.
The database is ignored by Git. Do not delete it to upgrade the software.

For vibration imbalance:

    python simulator/mqtt_publisher.py --scenario imbalance --count 20

## Optional synthetic demonstration Random Forest

    python ai/train_model.py
    python raspberry-pi/live_service.py --model ai/models/motor_demo.joblib --allow-demo-model

Stop an already running live_service with Ctrl+C before starting the one with a model.
Generated models are gitignored and remain local. Test metrics are on generated
data ONLY. Never claim they measure industrial predictive accuracy.

## Physical ESP32 integration (not bench tested)

- Final planned sensors: ADXL345 (I2C 21/22), DS18B20 (GPIO4 with 4.7k to 3.3 V),
  ACS712 (ESP32 ADC GPIO35 *through a verified voltage divider*), Hall (GPIO27
  with 3.3 V logic). Actual motor driver is independent; firmware NEVER drives a
  motor pin. Use an appropriately fused rated motor supply and secure guard.
- Copy esp32/firmware/secrets.example.h to secrets.h and configure credentials.
  **Never commit secrets.h**. Add correct third-party Arduino libraries listed
  in the firmware header. Select the correct ESP32 board version.
- For LAN access, the Mac broker must listen on the Mac LAN IP with authenticated
  MQTT users and firewall rules; Mosquitto "local only mode" cannot receive ESP32.
  Do NOT simply set allow_anonymous=true on a public listener. See the Mosquitto
  authentication docs and test from the intended private network.
- ESP32 and Mac need compatible epoch time. The firmware currently calls public
  NTP; an offline-only prototype requires a trusted local time source / alternate
  provisioning. Check physical timestamps before using this backend.
- Tune sensor calibration and actual effective vibration sample rate. Code is
  a reference implementation, **NOT** a verified pinout or safety-rated product.
- Collect multiple independently labelled safe runs for AI training. Do NOT treat
  synthetic model performance as accuracy on real motors.

## Modules

- edge_ai_twin/contracts.py — telemetry validation
- edge_ai_twin/features.py — vibration feature extraction
- edge_ai_twin/twin.py — health state machine and freshness
- edge_ai_twin/store.py — SQLite persistence and alert history
- edge_ai_twin/inference.py — optional RandomForest inference
- raspberry-pi/live_service.py — MQTT ingress and health/alert publishing
- simulator/mqtt_publisher.py — MQTT synthetic scenario publisher
- dashboard/app.py — live Streamlit dashboard
- ai/train_model.py — synthetic-demo run-wise model training
- esp32/wokwi/ — browser-only mock circuit
- esp32/firmware/ — physical hardware reference firmware

## Scope and known limitations

- This is a research/academic **software MVP**, not validated machinery protection.
- Health rule thresholds are illustrative and not physical trip setpoints.
- No validated remaining useful life (RUL) prediction is implemented.
- Missing, disconnected, or stale data must not imply a healthy machine.
- ESP32 physical firmware compilation, calibration and Wokwi execution require
  user hardware/simulator validation and are NOT automatically asserted passed.
