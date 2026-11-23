# R2K manufacturing dimensions

Use the [drawing set](TA-drawings.pdf), [size-true patterns](Lab-templates-1to1.pdf) and [machine shop notes](order-notes/05-machine.md). Coordinates below are millimetres in face view, origin at the middle pixel, +x toward the copper tabs. A dimension stated as an acceptance condition is measured on the finished parts or first article.

| Part | Nominal definition |
|---|---|
| L01 tapped backing | One 6061-T6 piece. Rear plane to copper seat 2.000. Four through M1.2×0.25-6H holes and nine 2.90×2.00 R0.40 rear windows that expose L02. |
| L02 copper floor | 0.127 annealed C110. Continuous below the nine cells. Four clearance scallops at the sides pass the board bearing shelves. |
| L03 floor gasket | Plain 35A silicone, 0.254 free, 0.218 at hard closure. Nine windows match the L04 lower apertures. Four side scallops and a +0.60 insulating tab-root tongue. |
| L04 carrier | Four-layer ENIG, 0.800 finished FR-4, 17.80×15.50. Twelve 0.35×1.65 contact bars. Nine 2.90×2.00 R0.40 openings at 4.20 pitch. Ten Ø0.65 plated electrode terminals at x=−8.50, 1.20 pitch. |
| L05 heater | AWG48 bare Ni80Cr20, Ø0.0316 nominal. Four straight wires per row. Two- and three-wire alternate cut/STEP arrangements use the corresponding subsets of the four lanes. |
| L06 contact gasket | One continuous bare 0.600 silicone sheet with six bridges, four integral screw ears and isolated 3.45×3.00 R0.40 openings. Installed 0.550 gap gives 8.3% nominal flat compression and about 19.4% locally around the bar plus wire. |
| L07 upper dielectric | Plain Kapton HN 0.0254. Nine Ø0.425 ports and a +0.60 insulating tab-root tongue. |
| L08 copper roof | 0.127 C110; nine Ø0.600 ports. L02 and L08 have the same 10.00-wide tab outline at y=±5.00. Flat projection 3.00, x=8.30–11.30. |
| L09 aperture cap | 0.400 bare FR-4, nine 3.45×3.00 R0.50 apertures. Four outboard ears bear on L01 and establish the gas volume above L08. |
| L10 diaphragm | Plain 0.254 silicone. Captured ~0.225 thick on the lands, modeled relaxed at 0.254 over the cap openings. |
| L11 face clamp grid | Polished 304 stainless; active field 0.350, Ø2.40 corner islands 0.800. Nine 3.69×3.24 R0.52 apertures. Recess to relaxed membrane 0.321. |
| L12 clamp screws | Four NBK SNZ-M1.2-4-TZB. Chromate-finished steel, M1.2×0.25, 4.00 under head, Ø1.80×0.50 head, No. 0 cross recess. All tighten into L01. |

## Fit and hard closure

- Four common holes at x=−6.30, +7.28 and y=±6.65. Outside L01 threads, nominal Ø1.40 gives 0.10 radial shank clearance. This clearance is too large to set the upper dielectric lip by itself. Use the close-pin optical method in the [assembly sequence](Owner-assembly.md).
- Each board shelf measures 1.20×0.65 at x=±3.65, y=±7.26. Cap stops measure 1.25×0.60 at x=±4.55, y=±8.15. Grid stops have the same size at x=±2.85, y=±8.15. Nominal elevations above the copper seat are 0.3450, 1.8474 and 2.4724, respectively.
- Order the carrier, cap and foil before final height finishing. Board shelf = measured floor copper + target 0.218 lower gasket gap. Cap stop = board shelf + actual board thickness + 0.550 target chamber + measured L07 and L08. Grid stop = cap stop + actual cap + 0.225 diaphragm land. Match the stop differences within ±0.010; all four stations of a given tier must seat. Directly check the 0.540–0.560 installed heater gap and the material compression on the bench. Lot thickness variation can exceed the machining tolerance.
- Each face island has an Ø2.00 flat counterbore 0.580 deep over the Ø1.40 through bore. The 0.220 remaining seat, 0.080 head recess, 1.3076 thread engagement envelope and 0.6924 clearance from the screw tip to the rear surface are nominal. Measure the actual 4 mm screws and cap/PCB stack. Require ≥1.00 mm of fully formed mating threads after chamfers, tip entirely inside L01, heads at or below the islands and head bearing on the full annular shoulder. The screw envelopes in STEP are smooth major diameters, and the L01 shop callout defines the thread.
- The assembled body is 17.80×17.00, x=−9.25…+8.55 and y=±8.50. The flat-tab assembly is 20.55×17.00×5.2724. The insulating tongues reach x=8.90. At the terminal terrace the minimum nominal horizontal distance from the backing edge to the Ø0.98 terminal lands is 0.71; keep solder and cable clear. The Ø1.40 screw-bore rim clears carrier copper by at least 0.2873 across all four plotted layers, and the L01 board shelves clear plotted bottom copper by 1.3995. No screw extends into a conductor hole.
- The open lower PCB window is 2.90 long along x, with 2.70–3.10 allowed after routing. The upper restraint is instead measured bar to bar. With ≤0.010 mm cold excess length per captured 4.20 mm span, NiCr expansion can bow a wire upward by roughly 0.36 mm at 750 °C. Accept the finished contact only if the wires cannot slide from adjoining spans, wire ≤0.034 mm, bar ≤0.040 mm, and combined roof/liner inward excursion ≤0.050 mm. The 0.540 mm minimum gap provides about 0.052 mm residual clearance. At 4.55 mm between adverse outer contact edges it falls to 0.024 mm. No hot tensile force is credited. See [independent calculations and loading conditions](../analysis/seal/Seal-validation.md).
- For a representative cold cell, gross volume 15.4681 mm³. Subtract the straight cylinders crossing the 3.45 mm contact-gasket window for nominal 2/3/4-wire net volumes 15.4627 / 15.4600 / 15.4573 mm³. The pressure-deflected diaphragm changes this volume.

## Sheet preparation

Cut silicone from uncoated, unreinforced material on a clean sacrificial backing, using a supported blade/punch or a material-approved bench laser with stock-specific kerf trials. Hand shear or mill C110 against a support. Sandwich the thin copper between backing strips for drilling. Deburr and flatten with a smooth burnisher. Cut PI with sharp supported tooling. Inspect complete apertures, every 0.325 mm minimum nominal contact gasket band, four screw holes and the sub-millimetre wire exits under magnification.

Make the four screw holes through matched blanks using an unchanged hard template. At two diagonals finish **L07/L08 together** to Ø1.40 with a matched close-fit smooth Ø1.39 pin pair. Use a supported XY table to perforate upper copper Ø0.600 ±0.010. Locate and punch plain PI Ø0.425 ±0.010 against the same fixture, then optically inspect the stacked parts on the two pins. Maximum center offset 0.025 leaves ≥0.0525 worst-case calculated rim. Require ≥0.050 continuous actual rim at all nine. Do not drill PI with a Ø0.600 tool through it. Form two aligned edge fiducials on the tabs while fixtured. The [owner instructions](Owner-assembly.md) explain the clamped transfer.

[Carrier drawings and CAM tolerance limits](carrier/routing-tolerance.json) and the [independent geometry review](../analysis/seal/Seal-validation.md) give the window clearance, electrical mapping and seal boundaries.
