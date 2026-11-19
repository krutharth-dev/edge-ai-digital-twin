# React + FastAPI monitoring dashboard (feature branch)

This is a **parallel replacement UI** for the existing Streamlit screen.
The original \`dashboard/app.py\`, MQTT receiver, motor Digital Twin, sensor
contracts, SQLite data and ML code are unchanged. Do not run both
\`raspberry-pi/mqtt_receiver.py\` and \`raspberry-pi/live_service.py\`.

## Architecture

\`\`\`text
ESP32 or simulated MQTT publisher
            |
        Mosquitto 1883
            |
raspberry-pi/live_service.py  (sole SQLite writer)
            |
data/motor_readings.db (existing, preserved)
            |
web_api/main.py (FastAPI read-only :8000)
            | GET /api/dashboard and WS /ws every 2 seconds
frontend/ (React + TypeScript / Vite :5173)
\`\`\`

### Prerequisites

- A Python virtual environment with \`requirements-dev.txt\` installed.
- Node.js **20.19+ or 22.12+** (Vite 7 requirement), and npm.
- Existing Mosquitto broker for actual simulated live data. No real motor needed.
- Keep all services bound to localhost during development.

## Run on the existing Mac

From \`~/Documents/edge-ai-digital-twin\` (NOT \`~/edge-ai-digital-twin\`):

**One-time Python dependencies**
\`\`\`bash
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
\`\`\`

**Terminal 1** — check broker and only start if not already listening:
\`\`\`bash
lsof -nP -iTCP:1883 -sTCP:LISTEN
/opt/local/sbin/mosquitto -v
\`\`\`
Use the second command ONLY when the first command shows no listener.
If Mosquitto is not installed there, inspect the error rather than reinstalling.

**Terminal 2** — sole MQTT receiver / Digital Twin:
\`\`\`bash
cd ~/Documents/edge-ai-digital-twin
source .venv/bin/activate
python raspberry-pi/live_service.py
\`\`\`

**Terminal 3** — API:
\`\`\`bash
cd ~/Documents/edge-ai-digital-twin
source .venv/bin/activate
python -m uvicorn web_api.main:app --host 127.0.0.1 --port 8000
\`\`\`
Test API: http://127.0.0.1:8000/api/health
The API never writes to the motor database.

**Terminal 4** — React frontend:
\`\`\`bash
cd ~/Documents/edge-ai-digital-twin/frontend
node --version
npm install
npm run dev
\`\`\`
Open http://127.0.0.1:5173 . The Vite dev server proxies REST + WebSocket
to the API. Port 5173 is deliberately bound to localhost.

**Terminal 5** — publish test scenarios:
\`\`\`bash
cd ~/Documents/edge-ai-digital-twin
source .venv/bin/activate
python simulator/mqtt_publisher.py --scenario normal --count 20
python simulator/mqtt_publisher.py --scenario imbalance --count 20
python simulator/mqtt_publisher.py --scenario overload --count 20
python simulator/mqtt_publisher.py --scenario thermal --count 20
python simulator/mqtt_publisher.py --scenario normal --count 20
\`\`\`

The home screen renders the persisted twin state, current metrics and
history. Use Telemetry for expanded charts and Alerts for transition history.
State becomes **UNKNOWN** if telemetry is stale (>12 seconds). Historical
graphs may remain visible, but are **not presented as live readings**.
The dashboard shows source provenance; it must not imply simulated readings
are physical measurements. Synthetic ML confidence is not calibrated.

## Tests

\`\`\`bash
python -m pytest -q tests/test_dashboard_api.py
cd frontend && npm run build
\`\`\`

The FastAPI integration tests validate empty databases, fresh snapshots and
stale-state safety. Frontend build checks TypeScript. **Neither establishes
real-motor performance**. Validate actual UI on your Mac before merging the PR.

## API endpoints

- \`GET /api/health\`: process is reachable (not motor health)
- \`GET /api/dashboard\`: snapshot + up to 400 recent history points and 30 alerts
- \`WS /ws\`: same JSON approximately every 2 seconds; same-origin dev Vite proxy

The read-only API uses the existing SQLite schema. If nothing is running, it
returns UNKNOWN with empty history instead of manufacturing data.

## Safety / limitations

This is an academic demo; no real-world motor fault accuracy, RUL model,
closed-loop control or safety-rated alerting is claimed. No public deployment,
login or TLS is included. The API should remain local-only unless security,
authentication and infrastructure are deliberately designed and audited.
