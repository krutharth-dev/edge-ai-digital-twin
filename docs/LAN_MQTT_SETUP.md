# Secure MQTT access from ESP32 to Mac (optional physical-hardware phase)

Your existing MacPorts Mosquitto 2.1.2 test broker works locally on port **1883**.
Do not stop or reinstall it just to try this procedure.

A physical ESP32 cannot access the Mac broker when it prints "local only mode":
its own 127.0.0.1 would mean the ESP32, **not** your Mac.

This guide starts a SECOND authentication-protected listener on **1884** for
private LAN use. Never expose this port to the public internet. MQTT on 1884
is NOT TLS-encrypted; use an isolated trusted network/hotspot, not public Wi-Fi.

## 1. Check prerequisites in normal macOS Terminal

    command -v mosquitto_passwd
    /opt/local/sbin/mosquitto -h
    lsof -nP -iTCP:1884 -sTCP:LISTEN

If 1884 is already in use, identify the existing service before starting another.

## 2. Generate a local MQTT user (do not commit the password)

    mkdir -p "$HOME/.config/edge-ai"
    /opt/local/bin/mosquitto_passwd -c "$HOME/.config/edge-ai/passwords" motor01
    chmod 600 "$HOME/.config/edge-ai/passwords"

You'll be prompted to choose a password. Copy it into your **untracked**
esp32/firmware/secrets.h for physical firmware setup; never upload that file.

## 3. Create a broker config for the LAN listener

    cat > "$HOME/.config/edge-ai/mosquitto-lan.conf" <<EOF
    listener 1884
    allow_anonymous false
    password_file $HOME/.config/edge-ai/passwords
    persistence false
    EOF

Start it in a dedicated Terminal and leave it open:

    /opt/local/sbin/mosquitto -c "$HOME/.config/edge-ai/mosquitto-lan.conf" -v

If macOS asks for incoming-network permission, allow it only on your private
network. If startup fails, read the broker output before changing settings.

## 4. Set credentials for Mac Python processes

In **each Terminal** running the receiver or simulator on this second broker:

    export MQTT_HOST=127.0.0.1
    export MQTT_PORT=1884
    export MQTT_USERNAME=motor01
    read -s 'MQTT_PASSWORD?MQTT password: '
    export MQTT_PASSWORD

Then run the usual Mac service or simulator:

    python raspberry-pi/live_service.py
    python simulator/mqtt_publisher.py --scenario normal --count 5

The password remains only in that Terminal process environment until its
session ends. Do not place it in Git or screenshot it.

## 5. Set the actual ESP32 MQTT address

    ipconfig getifaddr en0

Use your Mac's **actual reachable LAN IP** for MQTT_HOST inside
esp32/firmware/secrets.h, and set MQTT_PORT to 1884, MQTT_USERNAME to motor01,
and the chosen password. If en0 has no IP, check the active Wi-Fi interface.
The ESP32 and Mac must be on the same reachable network.

The physical ESP32 also requires reachable synchronized epoch time for
docs/MQTT_CONTRACT.md; it currently uses NTP. See docs/MAC_RUNBOOK.md
for calibration and safe-wiring constraints.

## 6. Stop the second listener

Press Control+C in its Terminal. The original localhost Mosquitto
service on 1883 remains untouched.

## Security notes

- MQTT username/password on unencrypted Wi-Fi can be intercepted. For
  a production or untrusted network, configure TLS and certificate verification.
- Restrict firewall rules to your private network, never port-forward 1884.
- Never power a 12 V motor from ESP32 GPIO or expose its ADC to 5 V.
- None of these steps are needed to run the software-only demonstration.
