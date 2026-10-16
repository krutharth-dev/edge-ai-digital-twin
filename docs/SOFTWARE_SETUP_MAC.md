# Software-first setup — Intel Mac edge host

**Status:** Development instructions for the initial Mac-based proof of concept. The physical rig, trained model, and live dashboard are **not yet implemented**.

For the current phase, your 2017 Intel Mac replaces the Raspberry Pi as the **local edge computer**. The ESP32 will still be the sensor node when hardware is connected. A Raspberry Pi can be added later without changing the MQTT interface. No cloud server is required.

## 1. Download/install checklist

| Software | Need now? | Use | Installation / verification |
|---|---|---|---|
| **Git** | Required | Clone and collaborate | `git --version`; install Xcode Command Line Tools if prompted |
| **Python 3.11 (or compatible Python 3.12)** | Required | Telemetry, ML, twin, dashboard | `python3 --version`; use an appropriate macOS-compatible Python installer if missing |
| **VS Code** | Recommended | Edit code and inspect files | Download from [code.visualstudio.com](https://code.visualstudio.com/) |
| **Mosquitto** | Required for local MQTT | Broker and command-line MQTT clients | With compatible Homebrew: `brew install mosquitto` |
| **Homebrew** | Optional | Simplifies software installation | [brew.sh](https://brew.sh/) — check support for the Mac's installed macOS version first |
| **Python packages** | Required | MQTT, data science and eventual dashboard | Installed from the repository's `requirements.txt` in a virtual environment |
| **Arduino IDE or PlatformIO** | Later | Flash ESP32 firmware | Install when starting real sensor integration |
| **Wokwi** | Optional | Virtual ESP32/circuit prototyping | Browser: [wokwi.com](https://wokwi.com/) |
| **Node.js, Docker, InfluxDB, Grafana, TensorFlow** | Not for Day 1 | Optional future expansions | Do not install until a concrete requirement exists |

**Compatibility note:** A 2017 Intel Mac's supported software depends on its **installed macOS version**, not just the processor. Confirm OS/Python/Homebrew compatibility before downloading packages. For now, Python 3.11 is a conservative target rather than a tested claim for this machine.

## 2. Mac terminal setup

Open Terminal:

```bash
sw_vers
uname -m
git --version
python3 --version
brew --version
```

It is normal for `brew --version` to fail if Homebrew is not yet installed.

Clone the project:

```bash
git clone https://github.com/krutharth-dev/edge-ai-digital-twin.git
cd edge-ai-digital-twin
```

Create and activate a local Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

If your OS installs multiple Python versions, use `python3.11 -m venv .venv` to explicitly select 3.11. Keep the `.venv` directory out of Git.

Prepare local settings:

```bash
cp .env.example .env
```

Default `MQTT_HOST=localhost` is correct when the MQTT broker and demo publisher both run on your Mac. Never commit `.env` or passwords.

## 3. Start Mosquitto on the Mac

With Homebrew already installed and supported:

```bash
brew install mosquitto
mosquitto -p 1883 -v
```

Leave that Terminal running. This direct command is suitable for a **local development broker**. On another Terminal, check that the command-line subscriber is available:

```bash
mosquitto_sub -h localhost -p 1883 -t 'motor01/#' -v
```

If the broker port is already occupied, inspect the existing broker process rather than starting a second one. Do **not** expose an unauthenticated MQTT broker to a public network. When a physical ESP32 connects over your Wi-Fi, separately configure broker listening interfaces, credentials and firewall access.

## 4. Publish simulated sensor messages

Use a third Terminal with the virtual environment activated, from the repository root:

```bash
source .venv/bin/activate
python scripts/demo_telemetry.py --mode cycle --count 20 --interval 1
```

Expected: the subscriber prints JSON on `motor01/vibration` and `motor01/current`. The publisher includes `synthetic: true` and `quality: "VALID"` **only to indicate valid demo formatting**; that does not imply a real calibrated sensor. Mock values are for testing the transport and downstream UI, **not for claiming ML accuracy or generating experimental training evidence**.

Other useful commands:

```bash
python scripts/demo_telemetry.py --mode normal --count 5
python scripts/demo_telemetry.py --mode abnormal --count 5
python -m pytest -q
```

For `--mode cycle`, the mocked mode switches periodically. The script and tests are intentionally small so each team member can understand the message contract.

## 5. Day 1 acceptance checklist

- [ ] Git repository cloned and visible in VS Code
- [ ] Working Python virtual environment created
- [ ] `requirements-dev.txt` installed without errors
- [ ] Local Mosquitto broker running
- [ ] `mosquitto_sub` receives both sensor topics
- [ ] Normal and abnormal synthetic messages are distinguishable
- [ ] Demo payloads match the proposed MQTT contract
- [ ] `python -m pytest -q` succeeds
- [ ] First development branch and pull request created with screenshots/log notes

**Day 1 is successful when local MQTT messages move through the Mac reproducibly.** A physical sensor, AI model, or finished dashboard is **not** required on Day 1.

## 6. Known limitations and next steps

1. The demo publisher is not ESP32 firmware. Its output does not prove sensor timing, acquisition accuracy, network stability or fault detection.
2. Create a Python subscriber next, validate JSON types/timestamps/units/sequence, and save to CSV.
3. Implement the operational `MOTOR_01` state and dashboard only after the subscriber can reject malformed and stale data.
4. Collect *real, labelled experimental runs* before training a classifier. Separate training/testing by complete run ID.
5. Wokwi's browser-based simulation does not automatically connect to a broker bound to `localhost` on your Mac. Its network routing needs a separately verified setup.

See [workflow diagrams](WORKFLOWS.md), [MQTT contract](MQTT_CONTRACT.md), [architecture](ARCHITECTURE.md), [roadmap](ROADMAP.md), and [safety plan](SAFETY.md).
