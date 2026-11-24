# R2L tactile-array fabrication dimensions

Dimensions are in millimeters. The origin is the center pixel P22 viewed from the active face. The +x direction points away from the cable. Pixel centers occupy x and y = −4.20, 0, +4.20. All cut stock is bare and unbacked. The four common registration holes are Ø1.400 at the combinations of x = −6.30, +7.28 and y = ±6.65.

|Callout|Stock and finished feature|
|---|---|
|L01 copper floor and cooling plate|C110 dead-soft 0.032 in (0.8128), nominal 0.8. Rounded rectangle 16.15 × 15.90 R0.25, four through holes. Both major faces plain. Rear face exposed inside the perimeter nuts.|
|L02 floor gasket|Plain 35A silicone, 0.254 free, 0.218 target installed. Nine 2.90 × 2.00 R0.40 through windows. Covers all twelve rear via mouths.|
|L03 electrode board|0.800 FR-4, four copper layers, ENIG. Body 17.80 × 15.50. Nine routed windows match L02. Twelve 0.35 × 1.65 contact bars and ten Ø0.65 finished plated terminations.|
|L04 straight Ni80Cr20 wires|Bare AWG 48, nominal Ø0.0316. Twelve 55 mm pieces for the four-wire assembly, trimmed to x = −7.65 … +8.58 after closure. Row centers y = +4.20, 0, −4.20. Offsets ±0.6258 and ±0.2942. Two-wire builds use the outer lanes, three-wire builds also use −0.2942.|
|L05 contact gasket|Plain 0.600 silicone, 0.550 fitted. Nine 3.45 × 3.00 R0.40 openings, six cross-row bridges, four integral screw ears and two 11.46 × 1.40 strip pockets. Minimum 0.325 nominal seal band.|
|L06 gap strips|Two 11.26 × 1.20 × 0.550 rectangular steel feeler strips centered at x = +0.49, y = ±6.90. Slip clearance nominally 0.10 per edge in L05. Steel bears directly on the masked PCB and against the underside of the dry PI.|
|L07 upper dielectric|Plain 0.0254 polyimide film, nine Ø0.425 ±0.010 ports. The rectangular tongue covers the root of the upper copper tab for 0.60 beyond x = 8.55.|
|L08 upper copper roof|Annealed 0.127 C110, nine Ø0.600 ±0.010 ports. Flat 10.00 mm wide tab at y = ±5.00, extending 3.00 from x = +8.55 to +11.55. The floor plate ends at +8.55.|
|L09 lower aperture cap|0.400 mm all-copper-etched FR-4 with nine 3.45 × 3.00 R0.50 windows. Four clearance holes. Routed outline matches the floor.|
|L10 diaphragm|Plain 0.254 silicone, relaxed over each aperture, 0.225 nominal on lands. Four screw holes, otherwise continuous.|
|L11 upper aperture cap|Second piece of the identical L09 manufactured part. The relaxed diaphragm sits 0.371 below its top surface at nominal compression.|
|L12 through screws|Four McMaster 90910A634, 18-8 stainless, 00-90 × ¼ in, Torx Plus IP2. Head envelope Ø2.261 × 0.635, flat underside. Through length 6.350.|
|L13 rear nuts|Four McMaster 90001A403, stainless, 00-90, 1.984 across flats (5/64 in), 1.191 high. The nut bears directly on the L01 cooling plate.|

## Stock and cutting

Use the [profiles](cuts) and [full-scale patterns](Lab-templates-1to1.pdf). Verify the print scale in both directions. Use a spare cap or carrier as a four-hole stencil and a close-fit pair of temporary diagonal pins for matching the precision roof sheets. Clamp metal stock between sacrificial flat faces before drilling. Protect the spacer contact area and film from chips.

- Saw or shear the 0.8128 copper plate from a flat 20 × 20 blank, file its edges to outline and support it during drilling. Remove raised lips from both sides without thinning the bearing areas. Check it against a ground surface. The flat central rear window between nuts can bear against a cooling block that clears the four projecting tips.
- Cut the two steel strips transverse to the 12.7 mm width of the feeler leaf. A fine abrasive cutoff or suitable hardened-stock snips can cut the steel. Deburr the short and long edges, clean and inspect each flat face. Measure the pair against a micrometer anvil. Select strips that give 0.540–0.560 at all nine sites in the seated assembly. Discard twisted or crowned pieces.
- Cut unreinforced silicone on a sacrificial flat support with a sharp blade, punch or material-approved bench laser. Trial the kerf on stock, preserve the 0.325 nominal minimum divider and clear each pocket. Check flatness, durometer and compression on a strip of the delivered sheet.
- Clamp thin copper between sacrificial plates on a microscope XY stage. Drill the Ø0.600 ports to the common array datum. Back the PI on a clean sacrificial support and individually pierce its Ø0.425 ports with a sharp hollow punch or controlled cutting process. Inspect hole diameters, burrs, complete slugs and position. A spare carrier can register the diagonal screw patterns. Its large pixel windows locate the grid approximately. Optical coordinates and direct lip measurement control the small ports.
- Finish two diagonal registration holes in the PI and roof as a matched pair, fit smooth pins with measured diametral clearance ≤0.020, and measure all nine port pairs off-device. An actual center offset ≤0.025 combined with the specified bore limits gives ≥0.0525 radial PI lip. Require ≥0.050 continuous actual lip. The nominal 0.206 diametral screw clearance allows independent sheet movement, so record two separated exterior alignment marks and retain the verified pair with clips during transfer.

## Mechanical envelope and electrical spacing

The body extends x = −9.25 … +8.55 and y = ±7.95. It is 17.80 × 15.90 excluding the single upper tab, or 20.80 × 15.90 with the tab flat. At nominal gasket squeeze the bearing-to-bearing grip is 3.5582. The screw head projects 0.635 above the upper cap. The nut uses 1.1906 of axial thread envelope (4.22 pitches), leaving 1.6012 beyond the nut and 2.7918 below the plate. The full tip-to-head axial envelope is 6.985. A 3/16 in screw would leave only 0.0137 nominal beyond the nut, readily consumed by cap/PCB stock tolerances. Inspect the actual four assemblies for full nut engagement. Keep protruding tips clear of the heat sink and cable fixtures. Side access to the nuts uses a 5/64 in tool.

The plate edge is 0.410 from the nominal Ø0.98 terminal lands on the −x cable terrace. Keep solder and conductor strands clear. Across all four copper layers the drilled screw-hole rim has 0.287 minimum copper clearance. The free steel strips are 0.470 from top copper at nominal position, or ≥0.25 after allowing 0.10 pocket float, 0.08 registration and 0.04 cut error. Verify these relationships against actual parts. The two main caps and floor plate carry the clamp load with the four screw heads and four nuts. Only the heater gap has rigid spacers. The 0.218 floor and 0.225 diaphragm compression targets must be established together on the actual stock. Torque alone cannot establish either local displacement.

The straight cold wire crown is 0.4834 below the supported liner. The bar-center chord is 4.20. At 750 °C the remaining clearance is ≥0.052 only if cold trapped excess length is ≤0.010 per span, the wire cannot feed through the contacts, hot expansion follows the stated model, contact height ≤0.040, wire diameter ≤0.034 and the combined inward roof/liner motion is ≤0.050. An adverse 4.55 chord leaves 0.024. The 2.70–3.10 free lower route span is measured independently. Four straight wires displace 0.01082 mm³ from the 15.46814 mm³ gross gas volume at each site. [Independent geometry and pressure analysis](../analysis/seal/Seal-validation.md)

[Owner assembly sequence](Owner-assembly.md) · [Carrier routing and fabrication tolerances](carrier/routing-tolerance.json) · [Carrier, cap and stock purchasing lines](BOM.csv)
