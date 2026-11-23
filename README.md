# Thermopneumatic tactile pixel display

**Revision J · 23 November 2026.** A 3 × 3 passive tactile array uses four straight nickel–chromium wires per row and a continuous silicone diaphragm. A ten-conductor cable connects its heater terminals to a 6 V electronic driver board. Compiled ESP32-C6 firmware adjusts pulse duration using measured resistance and a wire-temperature model.

**[Download the illustrated owner design book (PDF)](https://github.com/yonvisell/TppDesign/releases/download/R2J/Owner-design-book.pdf)** · [View the book on GitHub](Owner-design-book.pdf)

| Design files | Contents |
|---|---|
| [Tactile array drawings](head/TA-drawings.pdf) · [assembly instructions](head/Owner-assembly.md) · [full-size patterns](head/Lab-templates-1to1.pdf) | Numbered stack, heater layout, copper tab joint and lab fabrication. |
| [Mechanical CAD](head/Mechanical-CAD.zip) · [board and sheet manufacturing packets](head/jobs) | Four-wire tactile array and winding fixture STEP models, plus fabrication files for the carrier, cap, tooling and cut sheets. Native PCB layouts are in the carrier, cap, jig and frame directories under head. |
| [Driver schematic](eb/Schematic.pdf) · [editable driver design](eb/Controller.kicad_pro) · [assembly packet](eb/EB-supplier.zip) | 73 × 35 mm board with nine driven terminals, one return, current sensing and terminal voltage measurement. |
| [Bill of materials](purchasing/Integrated-BOM.csv) · [editable build budget](purchasing/Build-budget.xlsx) | Stock and component identities, quantities, sources and estimated build costs. |
| [Firmware and commissioning](firmware/Controller.md) · [robot API and OSC messages](software/OSC.md) | Target image, C++ control software, Python client and numerical receiver. |
| [Direct pixel selection](release/four-wire-direct.json) · [pressure response](supplement/controlled-gas.json) · [seal assessment](analysis/seal/Seal-validation.md) | Command-level results from the compiled receiver and independent physical models. |

## Operating evidence

With four wires, a nominal 5.8 V supply and a 25 °C start, all nine single-pixel addresses and 28 of the 36 two-pixel combinations were directly admitted in the simulation. The other pairs and all direct three-pixel combinations exceeded an electrical limit. A larger pattern is serviced in successive groups.

The simulated center pixel received 31.4 mJ under a 750 °C wire limit. Its predicted fixed-volume peak was 38.4 kPa, equivalent to 389 mN over the 10.13 mm² aperture. The smaller port transmitted the pressure rise within 0.012 kPa in the two center-pixel replays. Actual gas retention, loaded tactile force, diaphragm temperature and heat at a faulty contact remain unmeasured on Revision J.

## Local example

Run the receiver in one terminal from the repository root, using Python 3.10 or newer, NumPy and a C++17 compiler.

```sh
python3 software/fixture.py --wires 4 --rail 5.8
```

In a second terminal, run the following. The client uses only Python's standard library. For hardware, substitute the commissioned driver's IP address.

```sh
python3 software/client.py 127.0.0.1 --status
python3 software/client.py 127.0.0.1 --configure --limit 450
python3 software/client.py 127.0.0.1 --actuate --ms 20 --pixels 22
```
