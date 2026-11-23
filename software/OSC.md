# Sending commands to the pixel display

The client application sends Open Sound Control (OSC) datagrams to UDP port 5054 on the XIAO. The XIAO replies to the IP address and UDP port that sent the request. A status query reads the instrument. A configuration request changes a setting. An actuation request starts one finite exposure and returns its measured and estimated delivery. On a physical display, confirm the installed wire count, calibrate the tactile array at ambient temperature and arm the driver over USB first. [Local commissioning](../firmware/Controller.md)

## Try a four-wire display on one computer

From the directory containing `software/`, run the following in a terminal on a computer with Python 3.10+, NumPy and a C++17 compiler. The simulated four-wire receiver uses the production C++ control code and a separate circuit and thermal model. It listens only on the loopback interface.

```sh
python3 software/fixture.py --wires 4 --rail 5.8
```

In a second terminal in the same directory, query the display, select the 450 °C effective wire limit and command the centre pixel. The maximum duration is 20 ms. The controller may stop earlier. The CLI prints the reply as JSON.

```sh
python3 software/client.py 127.0.0.1 --status
python3 software/client.py 127.0.0.1 --configure --limit 450
python3 software/client.py 127.0.0.1 --actuate --ms 20 --pixels 22
```

To operate hardware, connect the computer to the XIAO access point and substitute `192.168.4.1`, or use the station IP reported by the USB `ID` command on a shared network. The sender uses only Python's standard library. Set `--unit N` for a unit other than 1 and `--port P` for a different receiver port. Rows and columns are numbered from 1. Pixel codes in row-major order are 11, 12, 13, 21, 22, 23, 31, 32, 33.

## A request and its reply

Each line below shows a decoded OSC message. Request bundles carry the guard first, then the operation. The numerical example uses the cold, four-wire P22 simulation above. The address prefix `/TPP/TA1` identifies unit 1.

| Sender → receiver | Decoded message or result |
|---|---|
| App → XIAO | `/TPP/TA1/status 3` asks for instrument and network settings. |
| XIAO → app | `/TPP/TA1/status 881122 0 1000 7 1 5.8 4 450.0 0 1 100`. The unit is armed and calibrated, with four wires, a 450 °C limit, simultaneous mode, the guard enabled and a 100 ms observation budget. |
| App → XIAO | One immediate bundle containing `/TPP/TA1/guard 881122 1 1100` and `/TPP/TA1/config/mode "simultaneous"`. |
| XIAO → app | `/TPP/TA1/receipt` returns sequence 1, outcome `configured` and zero delivered energy. |
| App → XIAO | One immediate bundle containing `/TPP/TA1/guard 881122 2 1100` and `/TPP/TA1/actuate 20.0 22`. |
| XIAO → app | `/TPP/TA1/receipt` returns sequence 2 and `temperature_limit`. Four isolated observations were accepted over 937 µs elapsed. P22 received an estimated 13.39 mJ. Peak wire estimate was 285.4 °C and peak accepted current was 3.338 A. |

The examples show selected receipt fields. The complete ordered layout appears below. The 450 °C setting limits the upper plausible wire temperature including margin and the next measurement pulse. It can stop heating while the point estimate remains substantially lower. [Time-resolved example](../firmware/actuation-trace.json)

## Settings

Use the suffixes below after `/TPP/TA1`. An OSC type tag starts with a comma. Types `i`, `f` and `s` mean signed 32-bit integer, 32-bit float and padded string. The Python client builds the request envelope and validates the reply automatically.

| Setting and example | Effect |
|---|---|
| `/config/wires ,i 4` | Set the physical count per row, 2, 3 or 4. A changed count persists, erases the calibration and clears cold initialization and arm authorization. Recommission over USB. A blank board defaults to 2. |
| `/config/limit ,f 450.0` | Set the effective wire-temperature limit to 100–750 °C. The default is 450 °C. |
| `/config/mode ,s "rotate-group"` | Select the available-power schedule. The default is `simultaneous`. |
| `/config/guard ,i 0` | Allow plain full-power actuation messages for a client that cannot generate OSC bundles. Value 1 restores the guarded default. Every configuration write requires a guarded bundle, including this one. |
| `/config/max_age_ms ,i 40` | Set the maximum age budget for a guarded actuation, in whole milliseconds from 1 to 1000. Default 100. Settings writes retain a 100 ms transaction budget. |
| `/config ,ifi 4 450.0 0` | Set wire count, limit and numeric mode together in one transaction. Mode numbers in table order below are 0–3. |

A wire change returns `recalibration_required`. Other accepted settings return `configured`. Changing mode, limit or transport policy preserves accumulated heat and calibration. Limit and mode return to their defaults on reboot. Guard and age return to their defaults on each new local arming session, including boot, `OFF` and `ARM`. The local model, cold confirmation, arm latch, current, temperature and timing checks apply in every network mode.

| Available-power mode | What the display energizes |
|---|---|
| `simultaneous` | 1–3 selected sites. First check predicted source and tap currents for the entire group. Take an isolated resistance measurement at each site, then energize the group together. A group that exceeds an electrical limit is declined. |
| `rotate-single` | 1–9 sites, one at a time, in row-major order. The current and terminal voltage are measured on each pulse. |
| `rotate-group` | 1–9 sites, grouped in address order into electrically admissible sets of up to three. Revisit the same groups in turn. |
| `temperature-priority` | 1–9 sites. Form admissible groups beginning with the coolest estimated site, then reorder after one complete visit to all groups. |

## Actuation commands

| Message | Arguments and delivery |
|---|---|
| `/actuate ,fi 20.0 22` | Apply the available power to P22 with a maximum envelope of 20 ms. The allowed maximum time is 1–100 ms. Append one `i` tag per additional selected site. Group drive inserts the isolated measurement pulses. The first thermal stop ends the whole request. |
| `/TPP/TA1 ,ffii 0.5 30.0 21 22` | Equal calibrated dose at 1–3 sites. Arguments are normalized mean-power level, envelope in ms and unique IDs. Full scale is 4.36 W per selected site. The level for a 4.20 W target is 4.20/4.36. |
| `/pattern ,fifif 1.0 21 0.25 22 0.5` | Calibrated dose with unequal levels. Give the duration in ms followed by 1–3 ID/level pairs. All levels are between 0 and 1. |

For example, the following code runs in a client application on the display network. The timestamp records when the source observation was acquired. The driver accounts for elapsed communication time before admitting the command.

```python
from time import monotonic
from software.client import Client

display = Client("192.168.4.1")
try:
    print(display.status())
    print(display.set_mode("rotate-group")["outcome"])
    print(display.set_max_age_ms(40)["outcome"])
    acquired = monotonic()
    result = display.actuate(20, [11, 13, 22, 31, 33], observed=acquired)
    print(result["outcome"], result.get("elapsed_us"), result.get("energy_uJ"))
    print(display.dose(4.20, 1, [22])["outcome"])
finally:
    display.close()
```

Use `display.set_wires(4)`, `display.set_limit(450)`, `display.set_guard(True)` or `display.configure(4, 450, "simultaneous")` for the corresponding settings. `display.command(level, ms, pixels)` sends an equal calibrated-dose request. `display.pattern(ms, {21: 0.25, 22: 0.5})` sends unequal doses. Both accept an optional observation timestamp. For a stream of calibrated patterns, `Latest(display, callback)` maintains the newest pending observation while the preceding request is in progress. Call `submit(ms, levels, observed)` and finally `close()`. [Client implementation](client.py) · [Stream adapter](stream.py)

## Plain OSC clients and command age

Most applications can use the guarded Python API above. A music or interactive control application that only sends individual messages can use the following setup on an already armed unit. Start the simulator before trying this example on loopback.

```sh
python3 software/client.py 127.0.0.1 --configure --guard off
python3 software/client.py 127.0.0.1 --actuate --raw --ms 20 --pixels 22
python3 software/client.py 127.0.0.1 --configure --guard on
```

The middle command sends a single `/TPP/TA1/actuate ,fi 20.0 22` datagram and reads the reply on its sending socket. `display.actuate(20, [22], raw=True)` provides the same operation. A plain full-power request with the guard enabled returns `guard_required`. Plain equal and unequal calibrated-dose messages remain supported for existing applications. The firmware suppresses recently seen plain commands with the same operation, pixels, duration and levels for 100 ms using a 16-entry cache. Packets outside that cache or time window can execute again. Plain replies have sequence zero. A plain datagram has no source timestamp and the receiver cannot determine how long it traveled.

A guarded sender first reads the receiver's monotonic clock. Its immediate OSC bundle has timetag 1 and two length-prefixed messages. The first is `/TPP/TA1/guard ,iii` followed by the current session ID (epoch), a strictly increasing positive sequence and an expiry time in receiver milliseconds modulo 2³². The second is the requested operation. The Python client subtracts the time since acquisition, including the status round trip, from the configured observation budget. The firmware checks the resulting expiry on arrival and again before the first energized edge. Any supplied guard is checked even when plain messages are allowed. Sequence state belongs to one controlling application per unit. A settings write consumes a sequence and leaves the session ID unchanged. A new USB arming session retires the previous sequence space. Use `OFF` then `ARM` before the positive sequence range is exhausted.

The firmware validates the deadline supplied by the sender. Accurate acquisition timestamps are the responsibility of the client. Commands with a lost reply may have energized the display. The Python client sends each actuation once and returns `no_confirmed_receipt` when its reply times out. A failed status query returns `status_unavailable` before transmission of the actuation.

## Return messages

The common `/status ,i 3` query returns eleven fields with tags `,iiiiififiii`.

| In order | Values |
|---|---|
| 1–3 | Current epoch, last consumed sequence, receiver clock in milliseconds. |
| 4–6 | State flags, simulator indicator, idle heater rail in volts. Bits 0–3 of flags represent armed, calibrated, cold-initialized and fault. The cold bit records the initial condition of the thermal model. |
| 7–11 | Installed wire count, limit in °C, numeric mode, guard-enabled flag, maximum observation age in ms. |

The empty `/status ,` query returns fields 1–6. Version 2 returns fields 1–9. Downstream applications can read these formats unchanged. `Client.status()` returns named fields including `guard_enabled`, `max_age_ms`, `armed`, `calibrated`, `cold_initialized` and `fault`.

A terminal `/receipt` is sent to the requesting endpoint after each processed actuation or settings transaction. The first two integers and string are the current epoch, request sequence and outcome. Next are six integers: simulator flag, requested pixel mask, accepted direct probe count, shared/group slot count, accepted current samples and elapsed µs. Bit 0 of the mask is P11. Two floats give peak effective wire estimate in °C and peak sampled current in A. Zero in either peak field with no accepted sample means unavailable. Four vectors of nine floats follow in physical row-major order.

| Vector in order | Meaning (µJ per pixel) |
|---|---|
| `energy_uJ` | Estimated NiCr energy, including modeled heating at unselected sites. |
| `probe_uJ` | Direct isolated-measurement contribution to the energy estimate. |
| `unknown_upper_uJ` | Allowance for an energized interval whose electrical reading was unusable. |
| `selected_timed_upper_uJ` | Upper allowance from the intact-load power bound times the selected energized durations and their 5 µs timing margins. |

`temperature_limit` or `duration_limit` normally ends one available-power actuation. `complete` acknowledges a completed calibrated dose. `idle`, `below_resolution` and `probe_required` identify zero level, insufficient energy for a slot and a depleted short-dose observation allowance. A `timing_limit` may include partial delivery. A predicted `current_limit` before the first exposure declines the group. A current fault during drive, `hardware_fault`, `invalid_sample`, `ambiguous_R` or `inconsistent_R` inhibits subsequent heating. Inspect the installation before cold initialization. `calibration_required`, `disarmed`, `storage_error` and `recalibration_required` identify local prerequisites. `epoch`, `sequence`, `stale`, `duplicate`, `invalid`, `guard_required` and `wrong_unit` explain rejected packets. The sender can also return `observation_expired` or `sequence_exhausted` before commanding drive. [Parser and receipt encoder](../firmware/src/osc.h) · [Checked settings, delivery and packet behavior](../release/actuation-matrix.json)

## Compact binary example

The equal calibrated-dose message `/TPP/TA1 ,ffii 0.5 30.0 21 22` has 36 bytes. The OSC strings are null-terminated and padded to four-byte boundaries. Numeric arguments use network byte order.

```text
2f 54 50 50 2f 54 41 31 00 00 00 00
2c 66 66 69 69 00 00 00
3f 00 00 00 41 f0 00 00 00 00 00 15 00 00 00 16
```
