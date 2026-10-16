# First software-development session — 17 October 2026

**Goal:** establish a reproducible **local MQTT data path on the Intel Mac**, not build the whole Edge-AI model in one day.

## Practical session (roughly 2–3 hours)

| Order | Approx. duration | Action | Evidence |
|---|---:|---|---|
| 1 | 20–30 min | Check macOS, Python, Git and editor; clone repo | `git status`, Python version |
| 2 | 20–40 min | Create `.venv`, install Python dependencies | `pip list`; no install errors |
| 3 | 20–30 min | Install/start Mosquitto; open topic subscriber | Broker running; subscriber terminal |
| 4 | 20–30 min | Run marked synthetic current + vibration publisher | Received messages with timestamp, sequence and units |
| 5 | 20–30 min | Run tests; record troubleshooting notes | `pytest` output |
| 6 | 20–30 min | Create small development issue/branch, commit documentation or fixes | Git commit or PR |

These are planning estimates, not measured build times. If a prerequisite fails, record the specific error and resolve it before moving to the next step.

## Commands to start with

```bash
git clone https://github.com/krutharth-dev/edge-ai-digital-twin.git
cd edge-ai-digital-twin
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

See [full Mac setup](SOFTWARE_SETUP_MAC.md) for Mosquitto and publisher commands.

## What not to do on Day 1

- Do not label generated synthetic data as a real experimental dataset.
- Do not report AI accuracy without a trained/tested model.
- Do not start a 3D twin, cloud deployment or RUL prediction.
- Do not connect a motor or unverified power/sensor wiring merely to rush the demo.
- Do not put Wi-Fi or MQTT passwords in GitHub.

## Next software milestones

**Session 2:** create a schema-checking MQTT subscriber and CSV log.

**Session 3:** show a live `MOTOR_01` state that distinguishes SIMULATED, UNKNOWN, HEALTHY (once validated) and STALE; prototype a simple Streamlit dashboard.

**After hardware readiness:** replace the mock publisher with ESP32 telemetry, gather controlled experimental runs and develop the first defensible Random Forest classifier.

Work proceeds in this sequence even if members take on individual modules in parallel.
