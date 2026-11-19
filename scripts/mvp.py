"""Foreground Mac service supervisor. Status and stop use a private Unix socket."""
import argparse
import fcntl
import getpass
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
STATE = Path.home() / ".local/state/edge-ai-twin"
SOCKET = STATE / "control.sock"
PYTHON = ROOT / ".venv/bin/python"
URL = "http://127.0.0.1:5173"


def listening(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=.5):
            return True
    except OSError:
        return False


def start():
    STATE.mkdir(parents=True, mode=0o700, exist_ok=True)
    lock = (STATE / "lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit("MVP already running. Use ./status_mvp.sh")
    if listening(8000) or listening(5173):
        sys.exit("Port 8000 or 5173 is occupied. Check its owner with lsof.")
    if not PYTHON.exists() or not (ROOT / "frontend/node_modules/.bin/vite").exists():
        sys.exit("Install .venv requirements and frontend npm dependencies first.")
    subprocess.run([PYTHON, "-c", "import paho.mqtt.client, uvicorn, web_api.main"], cwd=ROOT, check=True)
    port = int(os.environ.get("MQTT_PORT", 1884))
    children = {}
    def launch(name, args, cwd=ROOT, env=None):
        with (STATE / (name + ".log")).open("a") as log:
            children[name] = subprocess.Popen(args, cwd=cwd, env=env, stdout=log,
                                               stderr=subprocess.STDOUT, start_new_session=True)
    def check():
        for name, proc in children.items():
            if proc.poll() is not None:
                raise RuntimeError(f"{name} exited. See {STATE}/{name}.log")
    def wait_port(port):
        for _ in range(100):
            check()
            if listening(port):
                return
            time.sleep(.1)
        raise RuntimeError(f"Timed out waiting for port {port}")
    def shutdown(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, shutdown)
    with socket.socket(socket.AF_UNIX) as control:
        SOCKET.unlink(missing_ok=True)
        control.bind(str(SOCKET))
        control.listen(4)
        control.settimeout(.5)
        try:
            if not listening(port):
                config = Path.home() / ".config/edge-ai/mosquitto-lan.conf"
                if not config.exists():
                    sys.exit("Configure authenticated Mosquitto per docs/ESP32_REACT_LIVE_SETUP.md")
                launch("broker", [shutil.which("mosquitto") or "/opt/local/sbin/mosquitto", "-c", config])
                wait_port(port)
            env = dict(os.environ, MQTT_HOST="127.0.0.1", MQTT_PORT=str(port))
            env.setdefault("MQTT_USERNAME", "motor01")
            if not env.get("MQTT_PASSWORD"):
                env["MQTT_PASSWORD"] = getpass.getpass("MQTT password: ")
            launch("receiver", [PYTHON, "raspberry-pi/live_service.py", "--database", str(Path(env.get("EDGE_AI_DB_PATH", ROOT / "data/motor_readings.db")).resolve())], env=env)
            launch("api", [PYTHON, "-m", "uvicorn", "web_api.main:app", "--port", "8000"])
            wait_port(8000)
            with urlopen("http://127.0.0.1:8000/api/health", timeout=2) as response:
                print(response.read().decode())
            launch("frontend", ["node", "node_modules/vite/bin/vite.js", "--host", "127.0.0.1", "--strictPort"], ROOT / "frontend")
            wait_port(5173)
            print(f"Dashboard {URL} | logs {STATE} | Ctrl-C to stop", flush=True)
            while True:
                check()
                try:
                    conn, _ = control.accept()
                except socket.timeout:
                    continue
                with conn:
                    conn.settimeout(2)
                    command = conn.recv(32)
                    conn.sendall((" ".join(children) + " | " + URL + "\n").encode())
                    if command == b"stop":
                        break
        except KeyboardInterrupt:
            pass
        finally:
            for proc in reversed(list(children.values())):
                if proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=4)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
            SOCKET.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "status"])
    action = parser.parse_args().action
    if action == "start":
        start()
    else:
        with socket.socket(socket.AF_UNIX) as client:
            try:
                client.connect(str(SOCKET))
            except (FileNotFoundError, ConnectionRefusedError):
                sys.exit("MVP supervisor is stopped")
            client.sendall(action.encode())
            print(client.recv(1024).decode().strip())
