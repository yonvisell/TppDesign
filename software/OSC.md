# Sending commands to the pixel display

The client application sends Open Sound Control (OSC) datagrams to UDP port 5054 on the XIAO. The XIAO replies to the IP address and UDP port that sent the request. A status query reads the instrument. A configuration request changes a setting. An actuation request starts one finite exposure and returns its measured and estimated delivery. On a physical R2L display, use USB to select the physical wire count, calibrate the assembled display and cable at measured ambient, confirm cold and arm. A full-image installation starts fresh. An application-only upgrade can reuse a valid K-format electrical record for the identical installed array, board, cable and wire count. Newly assembled or reclamped hardware requires fresh local calibration, cold confirmation and arming. [Local commissioning](../firmware/Controller.md)

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

## Nine-pixel control and pulse trains

The case-sensitive OSC prefix is `/tpp/ta/<unit>`. The unit number (1–999) is a separate path segment. Requests and replies for unit 1 use `/tpp/ta/1`. Each command is sent to UDP port 5054. Bind or connect one sending socket and receive the reply on that socket.

With the four-wire fixture running, enter these commands in another terminal. Each invocation sends one status query and one protected transaction. The driver times all four windows of the last command.

```sh
python3 software/client.py 127.0.0.1 --configure --mode staggered
python3 software/client.py 127.0.0.1 --dose --level .25 --ms 2 --pixels 11 12 13 21 22 23 31 32 33
python3 software/client.py 127.0.0.1 --ms 2 --pixels 21 22 --levels .28 .25
python3 software/client.py 127.0.0.1 --train 4 --ms 2 --duty .5 --level .25 --pixels 11 12 13 21 22 23 31 32 33
```

```python
from time import monotonic
from software.client import Client

ids = (11, 12, 13, 21, 22, 23, 31, 32, 33)
display = Client("127.0.0.1")  # use the board address after local commissioning
try:
    state = display.status()
    if not state["armed"] or state["fault"]:
        raise RuntimeError("Check the local driver state")
    settings = display.set_mode("staggered")
    if settings["outcome"] != "configured":
        raise RuntimeError(settings)
    levels = dict.fromkeys(ids, .25)
    acquisition_time = monotonic()
    report = display.train(4, 2.0, .5, levels, observed=acquisition_time)
    print(report["outcome"], report.get("pulses_completed"), report.get("energy_uJ"))
finally:
    display.close()
```

### Staggered power delivery

Set `/config/mode` to the string `staggered` or use mode number 4 in the combined settings command. The existing bare command accepts `F level, F on_ms, I pixel…`, and `/pattern` accepts `F on_ms, (I pixel, F level)…`. In staggered mode both accept 1–9 distinct pixels. Modes 0–3 all use the same calibrated dose scheduler, with 1–3 selected IDs for the base, pattern and train operations. `/actuate` in staggered mode uses the same available-power group rotation as `rotate-group`.

A calibrated request assigns each site's entire energy budget to the same wall-time window. Its target in µJ is `4.36 × level × 1000 × on_ms`. The requested mean power is 4.36 × level W in the window and 4.36 × level × duty W over whole start periods. A complete window can have a residual because pulse widths are finite. Divide delivered energy by the measurement interval for the delivered mean. When its window budget funds an isolated resistance measurement the firmware obtains one. A smaller dose can use the bounded allowance after a recent observation. The firmware then forms groups of up to three whose source and tap currents satisfy 8 A and 5 A. Each site with an outstanding budget gets one turn per pass before a site is revisited. Staggered joint slots are at most 128 µs, with shorter durations as individual budgets fill. The first selected address advances across commands and train windows. The controller stops if the original budgets cannot fit the time or thermal limits. Read the partial delivery in the receipt.

At 5.8 V from 25 °C with four wires, all nine sites requested at level .25 for 2 ms returned `complete`, with 2.144–2.184 mJ estimated per site against 2.180 mJ requested. The first explicitly selected electrical edges spanned 0.848 ms. Unselected paths can already dissipate energy and gas pressure evolves on its own timescale. A 1 ms all-nine full-scale request returned `timing_limit` at 0.988 ms and included its partial delivery. These are numerical circuit, converter and switching results. Board timing requires measurement. [Compiled controller cases and switching times](../release/staggered-trains.json)

### Repeated pattern under the local clock

| Message | Arguments in wire order |
|---|---|
| `/tpp/ta/1/train` | I count, F on_ms, F duty, followed by 1–9 (I pixel, F level) pairs. Every train uses a guard. Pixel count follows the active calibrated mode. |
| `/tpp/ta/1/train/receipt` | The complete ordinary receipt layout (47 fields), followed by I pulses_requested and I pulses_completed. Data, including energy and counts, accumulate across the whole train and any partially executed window. |

Use count 1–32, on_ms 1–100, normalized duty 0.05–1.0 and levels 0–1 inclusive. The total schedule is at most 2,000,000 µs. The board rounds on_ms × 1000 to the nearest whole microsecond, then rounds on_us/duty to the nearest whole microsecond, with positive half-microseconds rounded upward. Pulse j begins its scheduling window at `j × period_us` for j starting at zero. The exposure window lasts on_us. No drive is scheduled after its end and before the next onset. The last window has no trailing off interval. At duty 0.5, off time equals on_ms. Electrical RUN edges occupy only parts of each window.

A first thermal, time, observation, current, hardware or local disarm stop terminates the train. An all-zero train returns `idle` immediately, with zero energized time, zero full windows and zero energy. Firmware processing can still contribute to elapsed_us. The completed count records full windows only. The two train counts alone cannot establish whether a subsequent window energized. The nine energy_uJ entries include estimated partial-window work. unknown_upper_uJ bounds unresolved selected work after an energized interval lacked a valid electrical reading. The receipt sums event counts, takes maxima for the two peaks and includes waits in elapsed_us. The protected expiry applies on receipt and immediately before the train's first energized edge. Later windows follow the admitted local schedule and retain wire/support temperatures and observation history. The driver checks local OFF and hardware faults between every finite electrical slot and about once per millisecond during waits. Hardware fault gating remains asynchronous. Other USB commands received during drive are declined. UDP status and subsequent commands wait for the active transaction to finish.

The initial guard deadline sets acquisition freshness. Extending the client receive timeout for the train does not extend this deadline. `Client.train(count, on_ms, duty, levels, observed=None)` sends once and listens for its normal timeout plus the scheduled span. Lost connectivity can leave an already admitted train running. `no_confirmed_receipt` means the delivery is unknown. Local USB `OFF` stops further slots. The interrupted terminal receipt retains its originating session identity, then the board opens a new session. Network drive cannot arm the display.

For the four-window example, window onsets were 0, 4, 8 and 12 ms, each with a 2 ms budget. The cold compiled simulation returned `complete` at 14 ms with pulses_requested=4, pulses_completed=4, 36 isolated observations, 24 shared slots and 8.564–8.730 mJ cumulative estimated energy per pixel. For the first window, P11's first explicitly selected RUN edge was at 18 µs and P33's at 866 µs. ADC observations occur later inside their powered intervals. [Per-site energy and four-window records](../release/staggered-trains.json)

## A request and its reply

Each line below shows a decoded OSC message. Request bundles carry the guard first, then the operation. The numerical example uses the cold, four-wire P22 simulation above. The address prefix `/tpp/ta/1` identifies unit 1.

| Sender → receiver | Decoded message or result |
|---|---|
| App → XIAO | `/tpp/ta/1/status 3` asks for instrument and network settings. |
| XIAO → app | `/tpp/ta/1/status 881122 0 1000 7 1 5.8 4 450.0 0 1 100`. The unit is armed and calibrated, with four wires, a 450 °C limit, simultaneous mode, the guard enabled and a 100 ms observation budget. |
| App → XIAO | One immediate bundle containing `/tpp/ta/1/guard 881122 1 1100` and `/tpp/ta/1/config/mode "simultaneous"`. |
| XIAO → app | `/tpp/ta/1/receipt` returns sequence 1, outcome `configured` and zero delivered energy. |
| App → XIAO | One immediate bundle containing `/tpp/ta/1/guard 881122 2 1100` and `/tpp/ta/1/actuate 20.0 22`. |
| XIAO → app | `/tpp/ta/1/receipt` returns sequence 2 and `temperature_limit`. Four isolated observations were accepted over 937 µs elapsed. P22 received an estimated 13.39 mJ. Peak wire estimate was 285.4 °C and peak accepted current was 3.338 A. |

The examples show selected receipt fields. The complete ordered layout appears below. The 450 °C setting limits the upper plausible wire temperature including margin and the next measurement pulse. It can stop heating while the point estimate remains substantially lower. [Time-resolved example](../firmware/actuation-trace.json)

## Settings

Use the suffixes below after `/tpp/ta/1`. An OSC type tag starts with a comma. Types `i`, `f` and `s` mean signed 32-bit integer, 32-bit float and padded string. The Python client builds the request envelope and validates the reply automatically.

| Setting and example | Effect |
|---|---|
| `/config/wires ,i 4` | Set the physical count per row, 2, 3 or 4. A changed count persists, erases the calibration and clears cold initialization and arm authorization. Recommission over USB. A blank board defaults to 2. |
| `/config/limit ,f 450.0` | Set the effective wire-temperature limit to 100–750 °C. The default is 450 °C. |
| `/config/mode ,s "rotate-group"` | Select the available-power schedule or staggered calibrated delivery. The default is `simultaneous`. |
| `/config/guard ,i 0` | Allow plain full-power actuation messages for a client that cannot generate OSC bundles. Value 1 restores the guarded default. Every configuration write requires a guarded bundle, including this one. |
| `/config/max_age_ms ,i 40` | Set the maximum age budget for a guarded actuation, in whole milliseconds from 1 to 1000. Default 100. Settings writes retain a 100 ms transaction budget. |
| `/config ,ifi 4 450.0 0` | Set wire count, limit and numeric mode together in one transaction. Mode numbers in table order below are 0–4. |

A wire change returns `recalibration_required`. Other accepted settings return `configured`. Changing mode, limit or transport policy preserves accumulated heat and calibration. Limit and mode return to their defaults on reboot. Guard and age return to their defaults on each new local arming session, including boot, `OFF` and `ARM`. The local model, cold confirmation, arm latch, current, temperature and timing checks apply in every network mode.

| Mode | Available-power schedule for `/tpp/ta/1/actuate` |
|---|---|
| `simultaneous` | 1–3 selected sites. First check predicted source and tap currents for the entire group. Take an isolated resistance measurement at each site, then energize the group together. A group that exceeds an electrical limit is declined. |
| `rotate-single` | 1–9 sites, one at a time, in row-major order. The current and terminal voltage are measured on each pulse. |
| `rotate-group` | 1–9 sites, grouped in address order into electrically admissible sets of up to three. Revisit the same groups in turn. |
| `temperature-priority` | 1–9 sites. Form admissible groups beginning with the coolest estimated site, then reorder after one complete visit to all groups. |
| `staggered` | Calibrated equal or unequal exposures reach up to nine sites by sharing the on-window across current-admissible groups. Available-power requests in this mode use the rotate-group schedule. |

## Actuation commands

| Message | Arguments and delivery |
|---|---|
| `/actuate ,fi 20.0 22` | Apply the available power to P22 with a maximum envelope of 20 ms. The allowed maximum time is 1–100 ms. Append one `i` tag per additional selected site. Group drive inserts the isolated measurement pulses. The first thermal stop ends the whole request. |
| `/tpp/ta/1 ,ffii 0.5 30.0 21 22` | Equal calibrated dose at 1–3 sites or 1–9 in staggered mode. Arguments are normalized mean-power level, envelope in ms and unique IDs. Full scale is 4.36 W per selected site. The level for a 4.20 W target is 4.20/4.36. |
| `/pattern ,fifif 1.0 11 0.25 33 0.5` | Calibrated dose with unequal levels. Give the duration in ms followed by 1–3 ID/level pairs, up to 9 in staggered mode. All levels are between 0 and 1. |

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

Use `display.set_wires(4)`, `display.set_limit(450)`, `display.set_guard(True)` or `display.configure(4, 450, "simultaneous")` for the corresponding settings. `display.command(level, ms, pixels)` sends an equal calibrated-dose request. `display.pattern(ms, {11: 0.25, 33: 0.5})` sends unequal doses. Both accept an optional observation timestamp. For a stream of calibrated patterns, `Latest(display, callback)` maintains the newest pending observation while the preceding request is in progress. Call `submit(ms, levels, observed)` and finally `close()`. [Client implementation](client.py) · [Stream adapter](stream.py)

## Plain OSC clients and command age

Most applications can use the guarded Python API above. A music or interactive control application that only sends individual messages can use the following setup on an already armed unit. Start the simulator before trying this example on loopback.

```sh
python3 software/client.py 127.0.0.1 --configure --guard off
python3 software/client.py 127.0.0.1 --actuate --raw --ms 20 --pixels 22
python3 software/client.py 127.0.0.1 --configure --guard on
```

The middle command sends a single `/tpp/ta/1/actuate ,fi 20.0 22` datagram and reads the reply on its sending socket. `display.actuate(20, [22], raw=True)` provides the same operation. A plain full-power request with the guard enabled returns `guard_required`. Plain equal and unequal calibrated-dose messages remain supported for existing applications. The firmware suppresses recently seen plain commands with the same operation, pixels, duration and levels for 100 ms using a 16-entry cache. Packets outside that cache or time window can execute again. Plain replies have sequence zero. A plain datagram has no source timestamp and the receiver cannot determine how long it traveled.

A guarded sender first reads the receiver's monotonic clock. Its immediate OSC bundle has timetag 1 and two length-prefixed messages. The first is `/tpp/ta/1/guard ,iii` followed by the current session ID (epoch), a strictly increasing positive sequence and an expiry time in receiver milliseconds modulo 2³². The second is the requested operation. The Python client subtracts the time since acquisition, including the status round trip, from the configured observation budget. The firmware checks the resulting expiry on arrival and again before the first energized edge. Any supplied guard is checked even when plain messages are allowed. Sequence state belongs to one controlling application per unit. A settings write consumes a sequence and leaves the session ID unchanged. A new USB arming session retires the previous sequence space. Use `OFF` then `ARM` before the positive sequence range is exhausted.

The firmware validates the deadline supplied by the sender. Accurate acquisition timestamps are the responsibility of the client. Commands with a lost reply may have energized the display. The Python client sends each actuation once and returns `no_confirmed_receipt` when its reply times out. A failed status query returns `status_unavailable` before transmission of the actuation.

## Return messages

The common `/status ,i 3` query returns eleven fields with tags `,iiiiififiii`.

| In order | Values |
|---|---|
| 1–3 | Current epoch, last consumed sequence, receiver clock in milliseconds. |
| 4–6 | State flags, simulator indicator, idle heater rail in volts. Bits 0–3 of flags represent armed, calibrated, cold-initialized and fault. The cold bit records the initial condition of the thermal model. |
| 7–11 | Installed wire count, limit in °C, numeric mode, guard-enabled flag, maximum observation age in ms. |

The empty `/status ,` query returns fields 1–6. Version 2 returns fields 1–9. Downstream applications can read these formats unchanged. `Client.status()` returns named fields including `guard_enabled`, `max_age_ms`, `armed`, `calibrated`, `cold_initialized` and `fault`.

A terminal `/receipt` is sent to the requesting endpoint after each processed actuation or settings transaction. An early guard or parser rejection can return a zero mask. The first two integers and string are the current epoch, request sequence and outcome. Next are six integers: simulator flag, requested pixel mask, accepted direct probe count, shared/group slot count, accepted current samples and elapsed µs. Bit 0 of the mask is P11. Two floats give peak effective wire estimate in °C and peak sampled current in A. Zero in either peak field with no accepted sample means unavailable. Four vectors of nine floats follow in physical row-major order.

| Vector in order | Meaning (µJ per pixel) |
|---|---|
| `energy_uJ` | Estimated NiCr energy, including modeled heating at unselected sites. |
| `probe_uJ` | Direct isolated-measurement contribution to the energy estimate. |
| `unknown_upper_uJ` | Allowance for an energized interval whose electrical reading was unusable. |
| `selected_timed_upper_uJ` | Upper allowance from the intact-load power bound times the selected energized durations and their 5 µs timing margins. |

`temperature_limit` or `duration_limit` normally ends one available-power actuation. `complete` acknowledges a completed calibrated dose. `idle`, `below_resolution` and `probe_required` identify zero level, insufficient energy for a slot and a depleted short-dose observation allowance. A `timing_limit` may include partial delivery. A predicted `current_limit` before the first exposure declines the group. A current fault during drive, `hardware_fault`, `invalid_sample`, `ambiguous_R` or `inconsistent_R` inhibits subsequent heating. Inspect the installation before cold initialization. `calibration_required`, `disarmed`, `storage_error` and `recalibration_required` identify local prerequisites. `epoch`, `sequence`, `stale`, `duplicate`, `invalid`, `guard_required` and `wrong_unit` explain rejected packets. The sender can also return `observation_expired` or `sequence_exhausted` before commanding drive. [Parser and receipt encoder](../firmware/src/osc.h) · [Checked settings, delivery and packet behavior](../release/actuation-matrix.json)

## Compact binary example

The equal calibrated-dose message `/tpp/ta/1 ,ffii 0.5 30.0 21 22` has 36 bytes. The OSC strings are null-terminated and padded to four-byte boundaries. Numeric arguments use network byte order.

```text
2f 74 70 70 2f 74 61 2f 31 00 00 00
2c 66 66 69 69 00 00 00
3f 00 00 00 41 f0 00 00 00 00 00 15 00 00 00 16
```

## Four-wire application examples

A separate cold start at 25 °C precedes each example. The Python client sends UDP to the production controller code running with a numerical circuit, 5.8 V at J1, four wires and a 450 °C wire limit. In a continuous experiment, each command inherits the preceding thermal state.

| Python on an open Client named display | Result |
|---|---|
| `display.status()` | Read the receiver clock, epoch, sequence, flags, rail and settings. The simulated unit reported armed, calibrated, cold-initialized and free of faults. |
| `display.actuate(20, [22])` | `temperature_limit` after 937 µs. Four isolated observations, no group interval, 13.389 mJ at P22. |
| `display.dose(4.20, 1, [22])` | `complete` after 1,000 µs. Target 4.200 mJ, receipt estimate 4.219 mJ. |
| `display.pattern(1, {11: .25, 33: .5})` | `complete` after 1,000 µs. P11 reported 1.023 mJ and P33 2.184 mJ. |
| `display.set_mode("rotate-group")`, then `display.actuate(20, [11,13,22,31,33])` | `configured`, then `temperature_limit` after 3,409 µs. Fifteen isolated observations and six group intervals served the pattern. |
| `display.pattern(1, {21: .25, 22: .5})` | `current_limit` after 106 µs. An isolated P22 probe deposited 1.291 mJ before rejection of the shared group. A current stop in a command that already energized the array latches a fault. |

The P22 available-power receipt starts with epoch, sequence, `temperature_limit`, simulated=1, mask=16, probe_count=4, group_slots=0, current_samples=4, elapsed_us=937, peak_estimated_C=285.4 and peak_sampled_A=3.338. Four nine-float energy vectors follow. P22 is element 4 when counting from zero. `probe_uJ` is included in `energy_uJ`. Each receipt records electrical delivery. Contact temperature, diaphragm temperature, gas pressure and fingertip force require independent measurements. [Compiled example receipts](../release/actuation-matrix.json)

## Packet and session constraints

Requests occupy at most 256 bytes, with length divisible by four. The physical board drops oversized UDP datagrams. OSC strings, including addresses, type tags and named modes, are NUL-terminated and zero-padded. Numeric words use big-endian byte order. A protected bundle with timetag 1 contains exactly two messages, each prefixed by its byte length. A status query must be sent as a plain message. An accepted positive sequence may skip values. The receiver consumes the sequence before display-state and load admission, so a well-formed request that returns disarmed or temperature_limit still advances the sequence.

The signed deadline wire word encodes receiver milliseconds modulo 2³². The positive difference between deadline and receiver time must fit the configured age (100 ms for any setting). The final pre-edge check includes setup time. Once a command begins, local duration, electrical and thermal bounds govern the remaining slots. The state flag cold_initialized records the initialized thermal history and remains set during normal hot operation.

## Python interface

Use `Client(host, unit=1, port=5054, timeout=.30)`. Pixel inputs are distinct decimal integers or (row, column) pairs with coordinates 1–3. Invalid arguments can raise ValueError and status() can raise socket errors. Use one writer per unit and serialize calls sharing a socket.

| Operation | Signature |
|---|---|
| Status and settings | `status()`, `configure(wires, limit_C, mode)`, `set_wires(wires)`, `set_limit(limit_C)`, `set_mode(mode)`, `set_guard(enabled)`, `set_max_age_ms(ms)`. Use a Python bool for the guard, integers for count and age. |
| Available rail power | `actuate(ms, pixels, observed=None, raw=False)`. One to nine sites, at most three in simultaneous mode. |
| Common dose | `command(level, ms, pixels, observed=None, raw=False)` or `dose(watts, ms, pixels, observed=None)`. One to three sites, or nine in staggered mode. |
| Unequal calibrated dose | `pattern(ms, levels, observed=None)`. A mapping with one to three addresses and normalized levels, or up to nine in staggered mode. Always guarded. |
| Repeated windows | `train(count, on_ms, duty, levels, observed=None)` returns the nine cumulative energies and counts for requested and completed windows. |
| Observation stream | `Latest(client, report).submit(ms, levels, observed)` requires increasing monotonic acquisition times. `report(observed, result)` receives each outcome, including `superseded` for displaced pending work. close() drains accepted work and joins the worker. The caller closes the Client. |
| Disconnection | `close()` closes the Client socket. |

Status keys are `epoch, last_sequence, receiver_ms, flags, simulated, rail_V, wires, limit_C, mode, guard_enabled, max_age_ms, armed, calibrated, cold_initialized, fault`. Mode is a name and `receiver_ms` is the unsigned 32-bit clock word. Arm, calibration, cold initialization, guard, simulation and fault are booleans. Receipt keys are `epoch, sequence, outcome, simulated, mask, probe_count, group_slots, current_samples, elapsed_us, peak_estimated_C, peak_sampled_A, energy_uJ, probe_uJ, unknown_upper_uJ, selected_timed_upper_uJ`. Host failures can contain only an outcome, or an outcome and sequence. A reply from another session fails guarded correlation. If the correct reply does not arrive, the delivery remains unconfirmed.
