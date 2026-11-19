# Windows setup: run the four ESP32 sensor tests

This guide is for a friend's **Windows 10/11 PC + Arduino IDE 2 + a classic ESP32 DevKit (ESP32-WROOM-32)**. The sensor sketches run locally on the microcontroller and print diagnostics through USB Serial. **No Python, MQTT broker, MacBook or motor power is required for these tests.** Verify the exact board and sensor module pinouts before wiring.

## 1. Install Arduino IDE and ESP32 support (one time)

1. Install **Arduino IDE 2 for Windows** from https://www.arduino.cc/en/software .
2. Open **File > Preferences**. Under **Additional Boards Manager URLs**, add:
   `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
3. Open **Tools > Board > Boards Manager**, search `esp32`, install **esp32 by Espressif Systems**.
4. Open **Tools > Manage Libraries** (Library Manager), search and install:
   - **Adafruit ADXL345** (also install its **Adafruit Unified Sensor** and **Adafruit BusIO** dependencies if prompted)
   - **OneWire**
   - **DallasTemperature**
5. No special Arduino libraries are needed for ACS712 or Hall tests.

Official Arduino upload guide: https://support.arduino.cc/hc/en-us/articles/4733418441116-Upload-a-sketch-in-Arduino-IDE .

## 2. Get the sensor-test files on Windows

**Easiest (no Git required):**

1. Open https://github.com/krutharth-dev/edge-ai-digital-twin/tree/feature/esp32-sensor-diagnostics
2. Click **Code > Download ZIP**, extract the ZIP (do **not** run the .ino directly from the ZIP).
3. In the extracted repository, open `esp32/sensor-tests/`.

**Alternative with Git installed**, in PowerShell:

```powershell
cd "$env:USERPROFILE\Desktop"
git clone --branch feature/esp32-sensor-diagnostics --single-branch https://github.com/krutharth-dev/edge-ai-digital-twin.git
cd edge-ai-digital-twin\esp32\sensor-tests
```

The four sketches are:
- `adxl345_test/adxl345_test.ino`
- `ds18b20_test/ds18b20_test.ino`
- `hall_rpm_test/hall_rpm_test.ino`
- `acs712_test/acs712_test.ino`

## 3. USB connection and first upload

1. **Turn OFF and disconnect the motor supply.** Test one sensor at a time, power down before rewiring.
2. Connect ESP32 to the Windows laptop with a **USB data cable** (some phone charging cables have no data wires).
3. Open **Windows Device Manager > Ports (COM & LPT)**. Plug/unplug the ESP32 and note which `COMx` appears. If none appears, try a different data cable/port and inspect Device Manager; some ESP32 boards require the correct **CP210x / CH340 / CH9102 USB-to-UART driver**, depending on the USB bridge chip. Install the driver from the chip manufacturer if Windows cannot identify it.
4. In Arduino IDE select **Tools > Board > esp32 > ESP32 Dev Module** for a generic *classic* ESP32 DevKit, **or select the exact model shown on your board**. Do not select an ESP32-C3/S3 model for an ESP32-WROOM board.
5. Select **Tools > Port > COMx** matching Device Manager. If multiple COM ports exist, identify the one that appears only when the ESP32 is connected.
6. Open one of the four .ino files with **File > Open**. Keep the .ino inside its matching folder, as provided.
7. Click **Verify** (check mark) to compile; if successful, click **Upload** (right arrow). Wait for **Done uploading**. If stuck at `Connecting...`, press/hold **BOOT** during connection and release once flashing starts, if your board requires it.
8. Open **Tools > Serial Monitor**, choose **115200 baud**; reset the ESP32 with **EN/RST** if the boot banner is not displayed. Note the **PASS / CHECK / FAIL** messages. Each new upload *replaces* the sketch previously flashed to the ESP32.

**First upload sanity-check:** If you aren't sure USB and board selection work, upload Arduino's **File > Examples > 01.Basics > Blink** first, but note generic ESP32 DevKits vary in onboard LED pin (so a failed LED blink is not proof that USB/upload is bad). The sensor sketches' Serial output is the real test.

## 4. Test sensors in this order

### A. ADXL345 accelerometer (first)

With power disconnected, connect sensor **VCC to 3.3 V, GND to GND, SDA to GPIO21, SCL to GPIO22**; confirm the breakout's **CS/SDO I2C straps** in its documentation. Upload `adxl345_test.ino`.

Expected Serial clues:
- `PASS: ADXL345 initialized` and readings of X, Y, Z in **g**.
- When resting still, vector magnitude is *roughly* 1 g; moving/tilting the sensor produces **PASS: sensor responds to movement/tilt**.
- `FAIL: no I2C response`: fix power, ground, SDA/SCL, or address settings. A responding I2C bus alone is not validation of accurate vibration measurement.

### B. DS18B20 temperature sensor

Power OFF before wiring: **VDD to 3.3 V, GND to GND, DATA to GPIO4**, and a **4.7 kΩ resistor from DATA to 3.3 V**. Verify the actual probe pin order; wire colours vary.

Upload `ds18b20_test.ino`. Expect **PASS: DS18B20 detected** and a plausible `xx.xx C` reading. Gently warm the probe with your fingertips: a gradual increase supports operation. `-127 C`, no probe found, or repeated `85 C` is a warning to inspect wiring/conversion.

### C. Hall-effect switch (RPM)

Power OFF before wiring: connect GND, module supply **per module rating**, and a **3.3 V-safe digital output** to **GPIO27**. Use a 3.3 V pull-up for an open-collector output; the sketch enables the ESP32 internal pull-up. Do not connect a 5 V logic output to GPIO27.

Upload `hall_rpm_test.ino`. **With motor OFF**, move a magnet slowly past the sensor a few times. The **total** and **new_pulses** values should increase and Serial should show **PASS: Hall transitions detected**. No pulses without passing a magnet is inconclusive. The displayed RPM is only approximate until `PULSES_PER_REV` is set to the actual trigger count and shaft speed is independently checked.

### D. ACS712 current sensor (last; additional electrical safety)

**Do not** connect raw ACS712 OUT to GPIO35: the 5 V-powered sensor can output **above 3.3 V**, which can damage the ESP32. Use a suitable divider / level conditioning verified with a **multimeter**. The demo assumes **10 kΩ ACS OUT -> GPIO35, and 10 kΩ GPIO35 -> GND** (`DIVIDER_GAIN=2.0`). **Verify GPIO35 signal voltage remains safe across the full expected sensor output range BEFORE joining it to the ESP32.** Sensor supply is per its module rating (usually 5 V), with a correct common signal ground. The divider is an *example*, not verified for all modules.

With **motor and load OFF**, upload `acs712_test.ino`. It records an ADC voltage baseline and displays output voltage, change, and *uncalibrated current estimate*. A plausible baseline is **not a full sensor PASS**. To verify current measurement later, use a **separately fused, appropriately rated, known low-voltage DC test load** in the sensor's specified IP+/IP- path, and compare changes against a trusted multimeter. **Never route load/motor current through a solderless breadboard** or intentionally stall a motor to test current.

The ACS712 nominal sensitivity in code defaults to **5 A variant, 0.185 V/A**; for other models inspect the sensor datasheet and change the constant before interpreting amperes. Calibrate zero and gain against a meter before using this value in the Digital Twin.

## 5. If you see a problem

| Problem | First checks |
| --- | --- |
| No COM port | USB **data** cable, alternate USB port, Device Manager, correct USB bridge driver |
| Upload stuck at `Connecting...` | Correct board/COM port; disconnect external wiring; try BOOT during connection |
| `Adafruit_ADXL345_U.h: No such file` | Install **Adafruit ADXL345** and dependencies through Library Manager |
| `OneWire.h` / `DallasTemperature.h` missing | Install those two libraries |
| Serial Monitor blank | Right COM port, 115200 baud, press EN/RST, close competing Serial Monitor apps |
| ADXL345 not detected | SDA21, SCL22, 3.3V, GND, module's I2C address/mode |
| DS18B20 -127 C / 85 C | DATA4, correct 4.7k pull-up, supply and pin order |
| Hall always 0 | Confirm digital Hall switch, magnet orientation, 3.3 V logic, power/GND |
| ACS712 reading doesn't change | First verify **electrical safety and divider**; check known load, variant, and external meter |

**A successful Arduino compile/upload is not a verified physical PASS.** Please capture the Serial Monitor output for each sensor and mark **PASS**, **CHECK**, or **FAIL** in [the test results checklist](README.md). Stop immediately if any component becomes hot, smells, sparks, or wires loosen.

## 6. What comes after these checks?

When all four sensors respond under safe, controlled tests, review the calibration, ESP32-to-Mac connectivity, MQTT credentials and actual wiring against `esp32/firmware/esp32_motor_monitor.ino` and `docs/MAC_RUNBOOK.md`. The four independent sketches intentionally do **not** send data to the Mac.

