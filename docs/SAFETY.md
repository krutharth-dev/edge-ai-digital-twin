# Safety Plan

## Scope

This plan covers the low-voltage motor/fan prototype, sensors, ESP32, Raspberry Pi, power supplies, controlled abnormal-condition experiments, and nearby operators. It does not replace component datasheets, laboratory rules, supervisor instructions, or qualified electrical/mechanical review.

## Non-Negotiable Controls

- Secure the motor/fan to a stable base.
- Install a robust transparent guard around every rotating component.
- Secure any imbalance mass so it cannot detach.
- Keep the 12 V motor power path separate from ESP32 and Raspberry Pi power.
- Never route motor current through a solderless breadboard.
- Use an appropriately rated fuse and accessible physical master/emergency switch.
- Insulate exposed conductors and strain-relieve wires.
- Operate within every motor, controller, sensor, wire, connector, and power-supply rating.
- Keep hands, hair, clothing, cables, tools, and loose objects outside the guarded area.
- Never rely on MQTT, AI, the Digital Twin, or the dashboard as the sole stop mechanism.

## Before-Energization Checklist

- [ ] Motor, bracket, base, shaft/fan/load, and guard are secure
- [ ] Imbalance/load apparatus is retained and cannot detach
- [ ] Motor voltage, polarity, current path, fuse, and switch are verified
- [ ] ESP32/Raspberry Pi are not carrying motor current
- [ ] Connections are insulated and strain-relieved
- [ ] Sensors and cables cannot contact the rotating assembly
- [ ] The emergency/master switch is reachable
- [ ] The test area is clear and supervised as required
- [ ] Rated current, temperature, vibration, speed, and qualitative stop conditions are defined
- [ ] Data collection is ready before the motor starts

## Stop Conditions

Immediately isolate motor power for:

- Loose or shifting mounts, guard, magnet, load, or imbalance mass
- Unexpected noise, rubbing, smoke, smell, arcing, or visible damage
- Excessive vibration or movement of the base
- Current, temperature, speed, or supply behaviour outside the approved limit
- Damaged insulation, hot wiring, unstable connectors, or power-supply distress
- Loss of operator visibility or emergency-switch access
- Any condition not covered by the approved test procedure

Software may raise an alert, but the operator uses the physical switch to make the rig safe.

## Controlled Abnormal Conditions

### Imbalance

Use only a small securely retained off-centre mass behind the guard. Increase severity only through an approved procedure and remain within mechanical limits. Do not use loose objects.

### Increased Load

Apply a repeatable method within motor, controller, supply, shaft, and mounting ratings. Do not manually grab, obstruct, or contact rotating parts.

### Thermal Abnormality

Treat temperature as a slow supporting signal. Do not exceed component ratings, disable necessary cooling, or use an uncontrolled heat source. Allow cooling between runs.

## Power and Wiring

- Use a supply suited to the motor's startup and operating current.
- Select fuse, switch, wiring, and connectors for the expected current.
- Establish a correct common reference only where the circuit design requires it.
- Prevent motor electrical noise from entering logic power through careless wiring.
- Power down before changing wiring or mechanical configuration.
- Do not probe moving hardware or exposed live conductors unnecessarily.

## Incident and Near-Miss Record

Stop work, make the system safe, record the hardware revision and conditions, preserve relevant logs without secrets, and open a private or public issue as appropriate. Do not resume the same test until the cause and corrective action are reviewed.
