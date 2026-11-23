# Thermopneumatic tactile pixel display

**Revision K · Yon Visell**. Four straight nickel–chromium wires per row heat nine individually addressable gas cavities. A continuous silicone diaphragm forms the tactile surface. Four M1.2 screws align and clamp the dry array layers into a tapped backing. A ten-conductor cable connects the passive array to a 6 V driver.

**[Download the owner design book (PDF, main text)](https://github.com/yonvisell/TppDesign/releases/download/R2K/Owner-design-book.pdf)** · [Read the PDF on GitHub](Owner-design-book.pdf)

| Design material | Contents |
|---|---|
| [Assembly drawings](head/TA-drawings.pdf) · [owner assembly](head/Owner-assembly.md) · [full-size patterns](head/Lab-templates-1to1.pdf) | Exploded view, component dimensions, screw seats, heated spans and foldable copper tabs. |
| [Mechanical STEP files](head/Mechanical-CAD.zip) · [manufacturing packets](head/jobs) | Screwed array, winding fixture and clamp parts. Editable KiCad PCB layouts and sheet-cutting DXFs are under head. |
| [Driver circuit](eb/Schematic.pdf) · [editable electronics](eb/Controller.kicad_pro) · [EB assembly files](eb/EB-supplier.zip) | 73 × 35 mm PCB. USB logic power, separate 6 V heater input, current and terminal voltage measurement. |
| [Bill of materials](purchasing/Integrated-BOM.csv) · [editable budget](purchasing/Build-budget.xlsx) | Stock, machining and electronics, with first-lot and repeat-build costs. |
| [Firmware and commissioning](firmware/Controller.md) · [OSC and Python API](software/OSC.md) | Compiled C++ on XIAO ESP32-C6, flash image, Python client, numerical receiver and message examples. |
| [Address sweep](release/four-wire-direct.json) · [pressure replays](supplement/controlled-gas.json) · [seal and clearance analysis](analysis/seal/Seal-validation.md) | Reference operating settings, simulated output and mechanical limits. |

## Operating conditions

The models use 5.8 V at the EB, nominal cold paths and a 25 °C start. All nine single addresses and 28 of 36 two-pixel selections can use direct available-power actuation on the four-wire reference. Larger patterns can use successive groups. A calibrated 1 ms full-scale sweep delivered at least 4.29 W per selected site for every completed single and pair. The center-pixel simulations predict 16.6 and 37.6 kPa at the 450 and 750 °C wire limits, equivalent to 169 and 381 mN over the 10.13 mm² aperture. The curves assume sealed, fixed-volume cells. Actual leakage, force under a finger, contact temperatures and surface temperature have yet to be measured. A deteriorated electrical contact can heat locally during its first measurement pulse.

## Mechanical model readback

The CAD download contains the two-, three- and four-wire assemblies, the separate clamp parts and winding fixture. To reproduce the seal geometry check, unpack the ZIP into head/mechanics from the checkout root. Use a Python environment with CadQuery/OCP, NumPy, SciPy, Shapely, ezdxf and Gerbonara.

```sh
unzip -o head/Mechanical-CAD.zip -d head/mechanics
python3 analysis/seal/step_chambers.py
```

## Local robot example

From the checkout root, start the numerical receiver in one terminal. The fixture requires Python 3.10+, NumPy and a C++17 compiler. The client uses the Python standard library.

```sh
python3 software/fixture.py --wires 4 --rail 5.8
```

In a second terminal, request status, select a wire-temperature limit and actuate the center pixel. For a commissioned physical board, substitute its IP address for the loopback address.

```sh
python3 software/client.py 127.0.0.1 --status
python3 software/client.py 127.0.0.1 --configure --limit 450
python3 software/client.py 127.0.0.1 --actuate --ms 20 --pixels 22
```
