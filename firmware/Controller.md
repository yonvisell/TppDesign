# Driver installation and commissioning

The XIAO ESP32-C6 runs compiled C++ firmware. A separate regulated 6 V input powers the heaters. This revision supports two, three or four straight NiCr wires per row. The owner design book describes the four-wire configuration.

From the root of this repository, with esptool v5 and the board connected by USB, substitute the serial port for PORT.

```sh
python3 -m esptool --chip esp32c6 --port PORT write-flash 0x0 firmware/image/R2J-ESP32C6.bin
```

The merged image includes the bootloader, partitions and application and spans the calibration storage. Configure and calibrate after a full-image installation. Ordinary reboots retain the stored count and calibration. [Compiled image and digest](image/build.json) · [Owner design book](../Owner-design-book.pdf)

## How the driver applies heater power

J1 supplies the heater power and return. Current from J1+ crosses the 10 mΩ shunt R1 into the common heater supply VM. Three TI DRV8962 devices each contain four independently controlled half bridges, each formed by high-side and low-side MOSFETs. The board uses three channels per device to drive J2 taps T1 through T9. Its fourth channel is disabled. T0 is permanently connected to the J1 return. The three package pins bonded to a used OUT channel share one copper net and drive the same tap.  [TI DRV8962, §7.4 and Table 7-2](https://www.ti.com/lit/ds/symlink/drv8962.pdf#page=15)

With the bridge awake, EN = 0 leaves that tap at high impedance. With EN = 1 and IN = 1, the high-side transistor sources current from VM. With EN = 1 and IN = 0, the low-side transistor connects the tap to return. A selected resistive segment heats when a voltage difference appears between its adjacent electrode bars. Electrical current can reverse between neighboring active segments; dissipated heat depends on I²R. The controller blanks the enables before latching a different direction pattern. R1 and U8 measure aggregate supply current. Per-tap operating limits are checked with a calibrated electrical model and the measured aggregate. The board grounds IPROPI and applies positive VREF, the TI configuration that disables the internal current chopper. The independent hardware fault gate remains active.  [TI DRV8962, §7.5.3](https://www.ti.com/lit/ds/symlink/drv8962.pdf#page=17)

## Commission a cold display

Open the USB CDC serial console on the XIAO. With pySerial installed, list attached ports using `python3 -m serial.tools.list_ports -v`, then run `python3 -m serial.tools.miniterm PORT 115200 --eol LF` after substituting the listed port. Each local command is a line ending in LF. The OSC sender itself requires no serial dependency.

With heater power off, complete continuity and absence-of-short checks. Commission acquisition with known resistors first. Compare the board’s differential voltage, corrected shunt current and RUN time against independent acquisition on a dummy load. Verify conversions fall between the physical switching edges, the arm latch clears on driver fault, and the actual 6 V rail, sensor residuals and temperatures satisfy the operating model. Apply the rail with current limiting and allow the assembled array and leads to equilibrate at measured ambient.

| USB command (115200 baud) | Effect |
|---|---|
| `ID` | Read unit address, link information, rail, idle shunt reading, calibration, cold/armed/fault flags, thermal settings and per-pixel series offsets. |
| `UNIT 1` | Persist ID 1–999. The default OSC path is `/TPP/TA1`. Local disarm and arm transitions begin a new receiver epoch. |
| `ARRAY 821` | Select and persist the numeric label printed on the attached passive TA. Default 1. Changing it disarms the unit, resets cold confirmation and invalidates a mismatched calibration. |
| `WIRES 4` | Set the physically installed count (2, 3 or 4). Default 2. A count change erases the calibration, clears cold/arm and persists the new count. The guarded network configuration supports the same count change. |
| `CAL COLD 25` | Operator confirms an equilibrated intact TA at 25 °C. Measure all nine paths twice. Save the complete calibration in XIAO NVS only after both sweeps pass. |
| `CAL COLD 25 1.447` | For a four-wire example, use 1.447 Ω as the externally established **wire-only parallel bundle resistance at 25 °C**, common to this TA, in place of the manufacturer/gauge estimate. Supplied ambient range is 20–40 °C. The firmware normalizes to 20 °C using the stock curve. |
| `COLD` | Operator confirms the installed array has actually returned to the stored calibration ambient. Initialize both modeled temperatures. A two-second minimum quiet interval is also enforced. Determine physical equilibrium independently. |
| `ARM` | Check saved calibration, cold initialization, fault state, rail, timer and hardware latch. Authorize network heating. |
| `OFF` | Disable the drive and retire the previous network epoch. |
| `LIMIT 450` | Set the effective wire-temperature ceiling in °C for this session, range 100–750. Disarms. Baseline 450 °C. |
| `MODEL 0.20 2 6` | Set two-wire reference wire-to-surroundings conductance in mW/K, two-wire surroundings response coefficient β in s⁻¹ and ambient-loss rate γ in s⁻¹. Disarms and requires new cold confirmation. Defaults are commissioning estimates. |
| `WIFI ssid<TAB>password` | Join a client LAN for this session. Enter one literal tab between the values. The private local access point also supports commissioning. `ID` reports access-point credentials and station IP. |

On first installation label the TA and enter `ARRAY n` (or retain label 1), set `WIRES n` to the physical wire count, then use `CAL COLD 25`, wait for thermal equilibrium, then `COLD` and `ARM`. After a power cycle the board reads the versioned checksummed calibration but remains disarmed and requires explicit local cold confirmation. Use the measured ambient in place of 25. Recalibrate after changing the TA, wire, solder joints, cabling, reference resistance or operating ambient. The record binds the physical board eFuse identity, operator-selected TA label and wire count. The passive TA has no electronic identity. Starting an accepted calibration retires the old NVS record before taking samples. A failed sweep inhibits operation. A handling, cable or contact fault calls for inspection before cold reinitialization.


The Python client sends requests to the commissioned board and reports delivered energy per site. [Open Sound Control protocol and client](../software/OSC.md)
