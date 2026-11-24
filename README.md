# Thermopneumatic tactile pixel display

A 3 × 3 tactile display produces localized pressure pulses at a fingertip. Each pixel contains nickel–chromium wires that heat a small air cavity. The expanding air deflects a continuous silicone membrane above the selected pixel.

**[Owner design book (PDF)](Owner-design-book.pdf)** · Revision L · Yon Visell

The book covers the system design, dimensioned assembly, model-based temperature control, predicted tactile response and client interface. The appendices include the circuit schematics, complete OSC API and design file index.

| Subsystem | Design and files |
|---|---|
| Tactile array | Nine pixels on a 4.2 mm pitch in a screw-clamped 17.8 × 15.9 mm body. [Assembly drawings](head/TA-drawings.pdf) · [Full-size templates](head/Lab-templates-1to1.pdf) · [STEP models](head/Mechanical-CAD.zip) |
| Driver board | A nominal 6 V power stage drives the passive array through ten conductors. The ESP32-C6 runs the C++ controller and uses voltage and current measurements to estimate wire temperature. [Circuit schematic](eb/Schematic.pdf) · [Firmware and installation](firmware/Controller.md) |
| Client interface | Open Sound Control (OSC) over Wi-Fi/UDP supports individual pulses, simultaneous or temporally staggered pixel patterns, pulse trains and configuration. [OSC API](software/OSC.md) · [Python client](software/client.py) |
| Fabrication | [Tactile array fabrication files](head/jobs) · [Driver-board assembly package](eb/EB-supplier.zip) · [Bill of materials](purchasing/Integrated-BOM.csv) · [Build budget](purchasing/Build-budget.xlsx) |

## Predicted response

For the center pixel of the array starting at 25 °C, a 5.8 V drive request of up to 20 ms produces predicted peak gauge pressures of about 17 kPa and 38 kPa at the low and high NiCr temperature limits (450 °C and 750 °C). These values come from a sealed, fixed-volume gas model driven by the simulated controller. The book gives the corresponding pulse durations, wire temperatures and pressure histories. [Pressure response data](supplement/controlled-gas.json)
