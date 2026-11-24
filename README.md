# Thermopneumatic tactile pixel display

A 3 × 3 fingertip display uses electrically heated air cavities to deflect a silicone membrane at selected pixels. A 6 V driver controls the passive tactile array through ten conductors.

Max Linnander, Yon Visell, “Thermopneumatic Pixels: Fast, Localized, Robust, Low-Voltage Touch Feedback,” *IEEE Transactions on Haptics*, 2026. [journal](https://ieeexplore.ieee.org/document/11771129) · [arxiv](https://arxiv.org/abs/2603.16750)

**[Owner design book (PDF)](Owner-design-book.pdf)** · Revision L. System specifications, assembly drawings, model-based temperature control, predicted pressure response and complete client API.

| Subsystem | Design files |
|---|---|
| Tactile array | [Drawings](head/TA-drawings.pdf) · [Full-size templates](head/Lab-templates-1to1.pdf) · [STEP models](head/Mechanical-CAD.zip) · [Fabrication packages](head/jobs) |
| Driver board | [Schematic](eb/Schematic.pdf) · [Assembly package](eb/EB-supplier.zip) · [Firmware and installation](firmware/Controller.md) |
| Client interface | [OSC over UDP](software/OSC.md) · [Python client](software/client.py). Unit 1 uses the address prefix `/tpp/ta/1`. |
| Purchasing | [Bill of materials](purchasing/Integrated-BOM.csv) · [Build budget](purchasing/Build-budget.xlsx) |
