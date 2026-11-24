# Screw clamp, heater clearance and pressure isolation

Each nominal four-wire chamber has a cold volume of **15.457328 mm³**, measured by subtracting the released STEP solids from nine independent test boxes. Two 0.550 mm strips support the insulated roof at opposite edges of the carrier. The nominal cold wire crown is 0.4834 mm below the liner. The four screws and nuts compress the entire stack between the upper FR-4 cap and rear copper plate. These are geometry and model results. Local contact pressure, wire restraint, thermal deflection and dry gas leakage require measurements on the assembled device. [STEP bearing and volume measurements](step-readback.json) · [Manufacturing-profile and pneumatic readback](seal-results.json)

## Clamp and clearance

|Feature|Released geometry and interpretation|
|---|---|
|Registration|The main sheets, both caps and carrier share four Ø1.40 clearance bores at x = −6.30, +7.28 and y = ±6.65 mm. The hole rim clears the nearest contact-gasket opening by 0.458 mm. Two external strip pockets trap the unperforated spacers.|
|Through fasteners|Each 00-90 × ¼ in button head bears directly on the upper cap and the corresponding hex nut bears on the underside of L01. Direct probes at all 32 sampled bearing locations found metal and plate on the appropriate sides. The smooth screw model has zero positive-volume interference. Nominal grip is 3.5582 mm. The 1.1906 mm nut spans 4.22 pitches. Thread runout or entry chamfers can reduce fully developed engagement. Each tip projects 1.6012 mm beyond its nut.|
|Gap strips|The actual model contains two 11.26 × 1.20 × 0.550 strips. Geometric probes verify bearing on L03 and L07 near all four corners of each strip. Total bearing area is 27.024 mm². Accept a measured 0.540–0.560 mm gap over the active field. The nominal closest top copper is 0.470 mm from a steel strip.|
|Dry compression|L02 floor gasket goes from 0.254 to 0.218 nominal, L05 contact gasket from 0.600 to 0.550 and L10 diaphragm from 0.254 to 0.225 on its lands. Nominal squeeze is 14.2%, 8.33% and 11.4%. At a 35 µm bar and 31.6 µm wire, the L05 local geometric squeeze is 19.4%. Only L05 has a rigid spacer. Measure the actual floor and diaphragm compressed thickness and inspect the assembly for tilt or bow.|
|Face|The two identical 0.400 mm FR-4 cap solids have equal volume to numerical precision. Initial field recess over the relaxed diaphragm is 0.371 mm. The 0.635 mm proud screw heads occupy four corners. A heat sink contacting the flat central copper floor must clear the four screw tips extending 2.792 mm below it.|

Loose screw holes permit more than 0.20 mm of relative displacement between two independently located thin sheets. On two close temporary pins inspect the paired L07/L08 aperture diameters and actual dielectric lip. The specified sizes and a ≤0.025 mm offset give at least 0.0525 mm lip. Clip the inspected pair at the projecting root and use two exterior alignment marks during closure. Floor and screw hardware may conduct to the roof if the shanks touch its bores. Check each of the two copper parts to each heater tap after seating. [Detailed assembly measurements](../../head/Owner-assembly.md)

### Wire clearance at temperature

For a fixed chord of length L, a wire of available hot length S has transverse excursion h ≤ ½√(S²−L²). This follows from bounding the two wire subarcs on either side of the apex by the corresponding straight lines. Use S = (L + 0.010 mm)[1 + α(T−25 °C)] with α = 17.2 × 10⁻⁶ K⁻¹. The calculation allows the full wire to buckle toward the liner even when assembly tension disappears. The settings and failure assumptions are for an intact, retained wire. A 2.90 mm routed opening beneath the wire does not restrain its upward motion. [NiCr80 thermal expansion data](https://prodshop.kanthal.com/en/products/datasheets/material-datasheets/wire/resistance-heating-wire-and-resistance-wire/nikrothal-80/) · [Wire calculation](wire_clearance.py)

|Wire temperature|Maximum bow for 4.20 mm chord|Clearance for 4.20 mm chord|Clearance for 4.55 mm chord|
|---|---:|---:|---:|
|25 °C|0.1450 mm|0.2710 mm|0.2651 mm|
|450 °C|0.2933 mm|0.1224 mm|0.1010 mm|
|600 °C|0.3303 mm|0.0854 mm|0.0605 mm|
|750 °C|0.3636 mm|0.0520 mm|0.0241 mm|

The clearance subtracts the calculated bow, a 0.040 mm land, 0.034 mm wire including an additional allowance for hot diameter growth, and **0.050 mm combined inward displacement** of the PI and metal roof from the 0.540 minimum installed board-to-liner gap. The longer chord permits contact at opposite outer bar edges. Check retention and cold excess length on a sacrificial row, and measure inward motion including assembly distortion. Loss of grip, material entering from an adjacent span or trapped debris can defeat the bound.

## Chamber and seal geometry

![Gas openings, spacer pockets, fastener holes, wire lanes and carrier vias](seal-map.png)

The floor gasket/PCB window, contact gasket opening and cap aperture measure 5.6594, 10.2094 and 10.1304 mm² respectively. The stepped port connects only the two volumes of its own pixel. The analytic gross volume is 15.46814 mm³. Net volumes for two, three and four wires are 15.46274, 15.46003 and 15.45733 mm³. All nine four-wire STEP cavities extend from z = −1.0180 to +1.1024. The separate two- and three-wire center STEP results agree with the profile calculation within 0.000003 mm³. Four blind interstitial pockets, approximately 2.225 mm² × 0.550 mm each, are distinct from the gas cells and the two strip pockets.

The shortest contact-gasket web to an external/non-cell boundary is 0.325 mm nominal, or 0.245 after allowing two adverse 0.040 mm cut edges. Horizontal and vertical intercell webs are 0.75 and 1.20 mm. The lower route lies within the upper gasket opening by 0.275 nominal, leaving 0.055 after allocating 0.10 route, 0.08 registration and 0.04 gasket contour error. The four-wire array has 48 wire/bar crossings. The twelve Ø0.30 carrier vias are clear of the gas openings by ≥0.266 mm and of the lower routes by ≥0.741. Floor gasket cover at the rear via mouths is ≥0.500 mm. Each of two deliberately introduced 0.020 mm slits, between neighboring cells or from a cell to the skirt, creates the expected connection in the geometric calculation. The finished stack depends on actual conformity to the wires and each dry interface.

|Common-time blocked condition|Sum of nine gauge pressures|Cap/diaphragm opening load|Contact gasket opening load|Floor opening load|
|---|---:|---:|---:|---:|
|Largest of 42 emitted-control cases|345.52 kPa|3.500 N|3.528 N|1.955 N|
|Largest ideal 750 °C schedule|483.29 kPa|4.896 N|4.934 N|2.735 N|
|Nine sites at 60 kPa|540.00 kPa|5.470 N|5.513 N|3.056 N|

The two cap apertures have identical free areas. For nine cells at 60 kPa, 5.470 N of normal hydraulic load on the membrane corresponds to 1.37 N per screw under equal sharing. This omits rubber squeeze and plate flexure. For scale, an illustrative 0.20 MPa mean compression gives 15.56 N over 77.78 mm² of contact gasket, 39.93 N over 199.64 mm² of floor gasket and 31.88 N over 159.40 mm² of diaphragm contact. These are separate-plane calculations. In a series stack the external bolt tension is shared globally and the strips bypass part of the contact-gasket force. Stock compression curves and real seating determine the distribution. Hardware torque and measured membrane force cannot be inferred from those illustrative figures.

## Pulse transmission and leakage

Dividing the throat volume between its two ends gives 11.3854/4.0719 mm³ for the lower/upper gas regions. The short-port model includes viscous and entrance losses, inertance with end corrections and finite-amplitude discharge. With the stated bore and loss uncertainties, the small-signal frequency is 14.1–21.9 kHz, nominally 19.0 kHz. Across the two center-pixel control traces the largest modeled departure of upper pressure from the single-pressure history is 0.0029 kPa at 450 °C and 0.0060 kPa at 750 °C. These results assume unobstructed ports. [Numerical model and input traces](pressure_seal.py) · [Short-aperture impedance](https://arxiv.org/abs/2001.04904)

![Illustrative atmosphere and intercell leak sensitivity](leak-sensitivity.png)

For a long shallow isothermal gap, volume conductance at reference pressure is G = bh³/(12µL), with width b, height h, viscosity µ and path length L. Sixteen hypothetical 40 µm-wide wire-flank channels of 0.245 mm length give about 1.2% or 27.4% loss in 55 ms from a hot blocked cell starting at 60 kPa gauge for 1 or 3 µm gap heights. An inactive neighbor with eight 0.670 mm paths rises by about 0.22% or 5.70% of the initial pressure. A chosen 5% loss criterion corresponds to total G ≤4.95 × 10⁻¹⁴ m³/(Pa·s), or about 0.254 µL/s of reference flow at 5 kPa cold test pressure. These calculations illustrate interpretation of a measured pressure-decay trace. No physical R2L pressure or friction measurement is recorded.

Reproduce from the repository root in the scientific/CAD Python environment.

```sh
python analysis/seal/step_chambers.py > analysis/seal/step-readback.json
python analysis/seal/pressure_seal.py
python analysis/seal/plot_seal.py
```
