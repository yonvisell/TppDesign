# Pixel display fabrication dimensions

The cable exits at negative x. The nine pixel centres have 4.20 mm pitch about P22 at (0,0). The four-layer carrier measures 17.80 × 15.50 × 0.80 mm. The assembled tactile array with its two flat coincident copper tabs measures 20.55 × 15.50 × 2.3508 mm nominal. The 0.4 mm cap is a commercial PCB thickness. An actual cap near either end of the supplier's ±0.1 mm thickness range changes the assembled height by the same amount and the free cavity volume by approximately ±1.01 mm³ per pixel. Measure the first parts before comparing thermal or pneumatic recovery.

## PCB fabrication

| Board | Manufacturing task and acceptance |
|---|---|
| Electrical carrier | Four-layer high-Tg glass epoxy, 0.80 mm. Request 35 µm finished copper on all layers and 20 µm minimum via barrel wall. Electroless nickel with immersion gold on the 12 bare contact bars. Ten Ø0.65 finished through-holes, four Ø0.55 nonplated datums, nine 2.90 × 2.00 R0.40 routed apertures. Obtain supplier agreement on the internal contour tolerance and cutter. |
| Guide frame | Two-layer reusable 0.80 mm PCB. 40.00 × 25.50 mm outside, 22.30 × 16.90 mm opening. Two different guide pairs at each row end. Install 24 Ø0.30 pins in Ø0.40 finished plated holes after fabrication. Two 2.20 × 3.40 nonplated M2 slots allow the frame to slide in y. |
| Winding base | 1.60 mm bare PCB. Two Ø2.10 clamp holes. Six 5.55 × 2.90 mm R0.60 clearance windows receive the guide-pin groups throughout travel. Four Ø0.65 holes hold the stationary display datums. The 1.85 × 13.35 cable slot clears the wired board. Both tooling boards fit the same M2 hardware. |
| Aperture cap | 0.40 mm two-layer FR-4 process with both copper layers completely etched off the part. No solder mask, legend, plating, identification or copper on either bonding face. Four Ø0.55 nonplated holes and nine 3.45 × 3.00 R0.50 through-windows, 0.75 mm minimum web in x. Supplier manual review covers copper-free dielectric, thickness, tooling panel, router limits, warp and clean bond faces. If the bare-board process is declined, a lab-milled 0.40 mm unclad FR-4 cap uses the same DXF. |

The carrier calls for a total ±0.10 mm profile-to-pattern tolerance at each internal window edge relative to the copper and registration holes, including positional error. Request separate sacrificial panel rails, ≥50 × 50 mm panel outline and at least three Ø1.5 mm tooling holes on different rail corners. A 0.20 mm outward contour error together with +20% symmetric growth of the limiting 0.36 mm trace could expose 0.016 mm of copper. At ±0.10 mm the computed residual copper clearance is 0.084 mm. Inspect the finished sidewalls. The clean copper and mask readback resolves four bar-width contact intervals per installed lane, all nine windows and all ten isolated terminal nets. [Routing calculation](carrier/routing-tolerance.json) · [JLCPCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities/)

## Layer stack and fabrication route

The following identifiers apply to the native assembly, fabrication drawings, cut patterns and inspection record. They run from the lower copper to the tactile face. L07–L09 and L10 occupy adjacent areas in the same installed gap. Thickness excludes release liners.

| Layer | Material and nominal thickness, mm | Construction |
|---|---|---|
| L01 | C110, 0.127 | Continuous lower pressure boundary. |
| L02 | 467MP, 0.0584 | Copper-facing adhesive. Nine windows and 0.60 mm tab-root projection. |
| L03 | Plain PI, 0.0254 | Lower insulation, including the inward-facing tab root. |
| L04 | 467MP, 0.0584 | Board-facing adhesive, windowed, ending at the main laminate edge. |
| L05 | Four-layer FR-4, 0.80 | Electrode board including twelve exposed 0.035 mm thick contact bars. |
| L06 | Ni80Cr20, Ø0.0316 | Four straight wires per row in the reference build. Three K retainers cut from L11/L12 offcuts hold the trimmed right-hand ends. |
| L07 | 467MP, 0.0584 | Lower adhesive of the six spacers. |
| L08 | Plain PI, 0.1016 | Six spacer cores. |
| L09 | 467MP, 0.0584 | Upper spacer adhesive. L07–L09 together establish a nominal 0.2184 mm gap. |
| L10 | Silicone, 0.254 free thickness | Connected nine-cell gasket. Three 0.85 mm bridges per row gap. |
| L11 | Plain PI, 0.0254 | Upper dielectric. Ø0.425 ports and inward-facing tab-root insulation. |
| L12 | 467MP, 0.0584 | Liner adhesive against copper. Cut and perforate with L11. |
| L13 | C110, 0.127 | Upper heat spreader. Nine Ø0.600 gas ports, coaxial with L11/L12. |
| L14 | 467MP, 0.0584 | Aperture cap attachment film. |
| L15 | Unclad FR-4, 0.400 | Cap with nine 3.45 × 3.00 windows. |
| L16 | 3M 9731, 0.140 | Acrylic side against the cap and silicone adhesive against the membrane. |
| L17 | Silicone, 0.254 | Continuous tactile diaphragm. |

## Coincident tabs and optional heat-transfer joint

Both 10.00 mm-wide tabs are centred on y = 0, 2.75–12.75 mm from the lower edge of the 15.50 mm carrier. Each projects 3.00 mm from the laminate edge x = +8.30 to +11.30. Stacked foil profiles match through the full tab. Inward-facing PI covers the first 0.60 mm at each root. The bare inward faces are 1.2444 mm apart nominally and their neutral planes are 1.3714 mm apart. Order both foils flat. Choose one of the following options after confirming electrical isolation on the unbridged tactile array.

| Connection | Dimensions and fabrication | Calculated thermal resistance |
|---|---|---|
| Formed lap | Using a coupon from the same annealed C110 sheet, form opposing 90° bends on 0.40 mm inside radii. Put the nominal start of the bends 0.650 and 0.777 mm beyond the laminate edge. The 0.127 mm stagger brings the vertical faces together. With 0.347 mm terminal legs, overlap is approximately 0.25 mm. Developed tab lengths are approximately 1.73 and 1.85 mm. Trim while supported, then lap-solder or weld across the width using tooling that shields the polymer. Finished geometric projection is 1.30 mm plus joint bead. | Along two 0.127 × 10 mm foil sections to the lap centre, approx. 6.7 K/W at room temperature, excluding joint resistance and heat spreading in the sheets. |
| Vertical shim | Keep the foils flat. Trim both to 1.50 mm. Fit an 8.0 mm wide × 0.75 mm long C110 block between them at x = +8.95 to +9.70. Size the thickness to the measured gap. At 1.2444 mm nominal, a 1.20 mm block leaves 0.0222 mm per solder bond line. Strain-relieve the block outside the laminate. | Approx. 0.51 K/W through the block and 0.13 K/W through two ideal SAC305 layers over 6.0 mm². Lateral conduction along the two thin tabs to the middle of the joint adds approx. 4.1 K/W for full 10 mm width. Spreading, voids and imperfect bonding add resistance. |

These estimates use R = length/(conductivity × area), C110 conductivity 391 W/(m·K) and SAC305 conductivity 58 W/(m·K). The vertical shim offers a larger nominal bonded area and avoids loading the adhesive with bend tooling. The folded option uses the existing foil. A bend of 0.40 mm inner radius in 0.127 mm annealed stock implies approximately 14% nominal outer-fibre strain with the neutral axis at mid-thickness. Form once on same-lot coupons and inspect for cracking or delamination. Local soldering or welding can damage nearby acrylic or silicone bonds. Characterize the joining process thermally on a same-stack witness, restrain the root with a heat sink, inspect sections, and recheck pressure retention and foil-to-heater isolation. Dry clamp pressure or room-temperature electrical continuity alone does not establish thermal conductance. Measure transferred heat and the foil-to-foil temperature difference under the intended mounting load. [C110 properties](https://alloys.copper.org/alloy/C11000) · [SAC305 properties](https://dm.henkel-dam.com/is/content/henkel/LT-8270_Wirebond_Brochure_2-18_A4%20Folder_LT-8270_Wirebond_Brochure_2-18_A4_LRpdf)

## Aperture registration

Coaxial Ø0.600/0.425 mm metal/dielectric ports give a nominal 0.0875 mm radial dielectric overlap. With ±0.010 mm on both diameters and ≤0.025 mm centre error, the calculated worst-case lip is (0.590 − 0.435)/2 − 0.025 = 0.0525 mm. Measure a continuous ≥0.050 mm lip around each of the nine bonded ports, with measurement uncertainty included. Reject burrs, adhesive intrusion and local loss of overlap. The [assembly procedure](Owner-assembly.md) uses the predrilled copper openings to locate the smaller dielectric holes individually after lamination.

Inspect the gasket and dielectric profiles at all nine sites. Nominal gasket-to-spacer clearance is 0.157 mm. Gasket window profile error ≤0.04 mm and relative assembly error ≤0.08 mm leave 0.055 mm nominal allowance at the ends of the lower window when the ±0.10 routed-edge tolerance is met. The three 0.60 × 1.48 mm wire-tail retainers occupy only the inactive exits. Each is at least 0.399 mm from the nominal gasket and 0.140 mm from a trimmed spacer. This permits pretrimming at +8.33 mm before the broad upper tab covers the wire exits.

## Contact bars and preload

The 0.35 × 1.65 mm bars are conventional smooth plated copper. A 31.6 µm wire already concentrates load along a narrow line. Nickel–chromium develops an adherent chromium-rich surface oxide. Metallic current constriction and film resistance both contribute to measured contact resistance. In an idealized film-free circular contact of radius a, constriction resistance is approximately (ρ₁ + ρ₂)/(4a). Local peak stress alone does not determine the conducting area or the voltage drop across an intact oxide. [Kanthal on NiCr oxidation](https://www.kanthal.com/en/knowledge-hub/heating-material-knowledge/design-factors/general-factors-and-furnace-specific-factors/) · [Contact resistance and oxide penetration](https://link.springer.com/article/10.1007/s11249-022-01630-2)

With spacer height 0.2184, a 0.035 mm bar and 0.0316 mm wire, the silicone gap above a cold crossing is about 0.152 mm. Relative to the uncompressed 0.254 mm gasket this is 40.2% local geometric compression, compared with 14.0% on flat land. A further 25 µm ridge would raise the local value to 50.1%. A loose cross-wire introduces another electrical interface and a movable line load comparable in height to the heater diameter. Retain the smooth bar in the production files. The true contact force, oxide penetration, thermal contact conductance and fatigue life remain unmeasured.

Use single-wire witness rows from the production carrier with the same compression stack. Drive low current through one adjacent bar pair and sense voltage separately on those same bars. Measure a sufficiently long sample of the same wire lot with four terminals to establish the resistance per millimetre. Record each clamped row's resistance, repeat without changing the sense points through dwell and thermal cycling, then inspect the wire for permanent flattening. Compare against the electrical model's allowed branch resistance and the temperature estimate's permissible drift. The absolute excess over bulk wire includes uncertain electrical pickup position and both contacts. The repeated measurement on the same geometry resolves drift more reliably. Check every final pixel separately. Consider a controlled, plated radius on a subsequent coupon only if flat-bar contact resistance exceeds its budget.

## Pressure seal and first-article checks

The cut-pattern and manufacturing-file inspection found nine distinct pneumatic cells with a minimum 0.325 mm gasket land to the exterior or to an interstitial pocket. The four 2.209 mm² interstitial pockets between rows and columns are separate voids outside the active cells. The gasket lands between horizontally and vertically adjacent cell apertures are 0.75 and 1.20 mm. The corresponding face-adhesive lands are 0.51 and 0.96 mm. The design relies on actual compression and adhesion along both interfaces of each land. The 48 wire/bar crossings, corners, burrs, embedded debris and incomplete adhesive wet-out merit inspection on every article.

For a four-wire blocked cell and the hot-gas pneumatic capacitance used in the model, a total ambient leak conductance no greater than 4.45 × 10⁻¹⁴ m³/(Pa·s) limits modeled pressure loss to 5% over 55 ms at 60 kPa. This is a proposed aggregate first-article threshold for leaks to ambient. A separate neighbour-pressure or displacement measurement tests intercell leakage. The nominal smaller port has a modeled acoustic frequency of about 16.56 kHz, compared with actuation pulse durations measured in milliseconds. Across the prescribed equal-power thermal traces, the predicted upper-chamber pressure deviates by approximately 0.002 kPa or less from the single-pressure chamber model at nominal port dimensions. Fixture dead volume and diaphragm compliance affect a measured decay constant.

The twelve carrier vias do not intersect a pneumatic opening. The minimum via-bore-edge clearance to the gasket opening is 0.266 mm and to a lower carrier window is 0.741 mm. Each via mouth on the underside falls behind the L04/L03/L02 bond. Three left-hand via rims have only 0.200 mm nominal coverage at the outer edge. Visually confirm that L04 continuously covers all twelve mouths, particularly at x = −6.95 mm on each row. Solder mask tenting does not establish a hermetic joint.



- Measure both free gasket thickness and installed spacer height. The accepted 0.244–0.264 and 0.215–0.235 mm ranges correspond to a 3.7–18.6% geometric flat compression range. Check seal retention through dwell and thermal cycling.
- Measure unsupported wire lengths on each installed lane. Rounded aperture corners and assembly offset yield a possible 2.659–3.100 mm range before acceptance. Select 2.70–3.10 mm spans for use with the documented thermal model.
- Measured nominal drawing areas are 58.75 mm² of compressed gasket and 58.13 mm² of spacer bond. At an *assumed* 0.20 MPa mean gasket reaction stress the normal reaction is 11.75 N. At a simultaneous design check of 60 kPa gauge per pixel, opening force is 0.703 N across each 11.72 mm² face opening and 6.33 N across nine. The combined 18.08 N load corresponds to 0.311 MPa average across 58.13 mm² of spacer bond. The all-nine static case sizes a joint load and makes no claim of simultaneous pulse power. Edge peel and wet-out are separate test quantities.
- The nominal undeformed gas volume is 13.889, 13.886 and 13.883 mm³ per pixel for two, three and four wires. Verify foil flatness, pressure decay, diaphragm displacement under load, hot-wire clearance, cold resistance and fault-free cycling. The proposed 450 and 750 °C limits refer to estimated wire temperatures. Measure the nearest polymer and skin-facing temperatures independently.
