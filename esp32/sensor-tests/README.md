# ESP32 sensor bring-up tests (separate from main firmware)

**Purpose:** Verify **each physical sensor independently** before attempting ESP32-to-Mac MQTT or motor fault detection. Each test is a standalone Arduino sketch in its own same-named folder. These diagnostics only print to **Serial Monitor at 115200 baud**. They do **not** enable motor power, connect Wi-Fi, publish MQTT, or claim that physical hardware has already been tested.

## Test preparation

1. Disconnect the motor's power supply. Power the ESP32 from USB while testing one sensor at a time.
2. Disconnect USB/power before changing wires. Verify the actual sensor module's datasheet and pin labels, not only the chip name; module pin orders vary.
3. Use a compatible **ESP32 DevKit / ESP32-WROOM** board, Arduino IDE 2.x, and Espressif **esp32** board package. Select the exact board/USB port in **Tools**.
4. Open **only one** of the four .ino files below using Arduino IDE. If asked, keep it in the included same-named folder. Upload, open **Serial Monitor**, set **115200 baud**, and reset the ESP32.
5. Check the expected behavior and record observations. One meaningful changing reading (or several counted pulses) is stronger evidence than simply a successful library initialization.

## Wiring and tests

| Test sketch | ESP32 wiring | Required libraries | Positive evidence |
| --- | --- | --- | --- |
| [ADXL345](adxl345_test/adxl345_test.ino) | VCC -> **3.3 V**, GND -> GND, SDA -> **GPIO21**, SCL -> **GPIO22**; verify CS/SDO breakout straps per datasheet | **Adafruit ADXL345**, **Adafruit Unified Sensor** | I2C found at **0x53 or 0x1D**, initialization passes, axis readings vary when gently tilted; still orientation approximately 1 g magnitude |
| [DS18B20](ds18b20_test/ds18b20_test.ino) | VDD -> **3.3 V**, GND -> GND, DATA -> **GPIO4**, add **4.7 kΩ** resistor DATA to **3.3 V** | **OneWire**, **DallasTemperature** | Probe ROM detected, reasonable Celsius reading, gentle fingertip warmth changes temperature |
| [ACS712](acs712_test/acs712_test.ino) | ACS712 powered per **module's rating** (typically 5 V); OUT -> **verified level divider** -> **GPIO35**; common GND for signal | ESP32 Arduino core only | ADC reports believable non-rail baseline with zero current; **known safe DC load** produces appropriate voltage change and agrees with external meter after calibration |
| [Hall switch / RPM](hall_rpm_test/hall_rpm_test.ino) | Sensor VCC per **module rating**, GND -> GND, **3.3 V-safe** OUT -> **GPIO27**; open collector output needs pull-up to **3.3 V** | ESP32 Arduino core only | Counts rising total pulse count when a magnet passes sensor repeatedly; approximate RPM only after correct pulses/rev is configured |

**Do not wire a 5 V output directly to any ESP32 GPIO.** This is especially important for the **ACS712**, whose output voltage can be higher than 3.3 V, and for 5 V Hall modules whose output may not be 3.3 V compatible.

### ACS712 protective divider and calibration

The sketch assumes a **1:1 resistor divider**, for example **10 kΩ between ACS OUT and ADC GPIO35** plus **10 kΩ between GPIO35 and GND**, so that **DIVIDER_GAIN = 2.0**. **Measure GPIO35 with a multimeter before connecting the ESP32** and confirm the **entire expected signal voltage range** is safely at/below 3.3 V. A 1:1 divider is an example, **not** a verified solution for every ACS712 module or installation. Avoid supplying motor current during the initial baseline test. If you modify the resistor ratio, update `DIVIDER_GAIN`. Select the real ACS712 sensitivity: 5 A = 0.185 V/A, 20 A = 0.100 V/A, 30 A = 0.066 V/A nominal; check the variant. Compare to a known fused low-voltage DC test load and meter, never to a bare motor stall. ADC readings and the baseline alone cannot prove the ACS712 is healthy or accurate. **Do not pass motor current through a solderless breadboard.**

### Hall pulse count

The test counts **falling** edges with a 5 ms chatter filter. Use an appropriately rated digital Hall **switch** with logic output, not an analog linear Hall sensor. Before powering the motor, move a small magnet past the sensor **by hand**; do not hold a loose magnet near a running shaft. A 0 RPM with no intentional magnetic passes is **inconclusive**, not an automatic sensor failure. `PULSES_PER_REV = 1` is only an example and must match the physical magnets/trigger arrangement before RPM can be trusted.

## Troubleshooting

- **Upload fails:** confirm ESP32 board, USB data cable, port, boot-mode button if required, and remove other programs using the serial port.
- **ADXL345 not found:** check power and GND, swap incorrect SDA/SCL connections, verify breakout I2C mode and 0x53/0x1D address selection, and confirm library installation.
- **DS18B20 -127 C / not found:** check 4.7 kΩ pull-up, DATA wiring and probe orientation. Repeated 85 C may indicate a conversion/power issue.
- **ACS712 stuck near 0 V / 3.3 V:** **stop** and check voltage levels, divider, sensor power, common ground and ADC pin; a steady baseline without a known load is not a pass.
- **Hall stays at zero:** check correct Hall type, supply, magnet polarity/orientation, safe output logic level, 3.3 V pull-up if open collector, and GPIO27; try repeated passes.

## Results record (fill this out when testing)

| Sensor | Upload succeeded | Serial result / values | Changed when stimulated? | Result |
| --- | --- | --- | --- | --- |
| ADXL345 | | | | PASS / CHECK / FAIL |
| DS18B20 | | | | PASS / CHECK / FAIL |
| ACS712 | | | | PASS / CHECK / FAIL |
| Hall / RPM | | | | PASS / CHECK / FAIL |

Capture a **Serial Monitor screenshot or copied output for each sensor** (no private Wi-Fi credentials) so we can debug one sensor at a time and then integrate the real data. **PASS means a limited diagnostic check was observed, not full calibration or validation**. The existing main firmware at `esp32/firmware/esp32_motor_monitor.ino` remains unchanged.

Follow the repository [hardware safety plan](../../docs/SAFETY.md) and [Mac runbook](../../docs/MAC_RUNBOOK.md) before any physical motor run.
