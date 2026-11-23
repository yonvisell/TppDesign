"""Read finished cut paths, Excellon bores and soldermask/copper layers in face coordinates (mm)."""
from pathlib import Path
import math
import warnings
import json
import gerbonara
from shapely.affinity import translate
from shapely.geometry import Point, Polygon, LineString, box
from shapely.ops import polygonize, unary_union
import ezdxf

ROOT = Path(__file__).resolve().parents[2]
CUTS = ROOT / "head/cuts"
CAM = ROOT / "head/carrier/CAM"
SITES = [(x, y) for y in (4.2, 0., -4.2) for x in (-4.2, 0., 4.2)]


def cut(layer):
    doc = ezdxf.readfile(next(CUTS.rglob(layer + "-*.dxf")))
    assert doc.units == 4
    shape = Polygon()
    for e in doc.modelspace():
        if e.dxftype() == "CIRCLE":
            contour = Point(e.dxf.center.x, e.dxf.center.y).buffer(e.dxf.radius, quad_segs=90)
        else:
            assert e.dxftype() == "LWPOLYLINE" and e.closed
            contour = Polygon(e.get_points("xy"))
        shape = shape.symmetric_difference(contour)
    return shape


def mask(ext):
    shapes = []
    for obj in gerbonara.GerberFile.open(next(CAM.glob("*." + ext))).objects:
        for s in obj.to_primitives():
            assert s.polarity_dark
            xy = s.to_arc_poly().approximate_arcs(.00005).outline
            if len(xy) > 2:
                shapes.append(Polygon(xy))
    return translate(unary_union(shapes), xoff=-20, yoff=20)


def routed():
    edges = gerbonara.GerberFile.open(next(CAM.glob("*.gm1"))).objects
    lines = [LineString([(s.x1-20,s.y1+20),(s.x2-20,s.y2+20)]) for s in edges]
    contours = list(polygonize(lines))
    assert len(contours) == 10
    return [min((p for p in contours if p.contains(Point(x,y))), key=lambda p:p.area) for x,y in SITES]


def holes(shape):
    rings = [Polygon(r) for r in shape.interiors]
    return [next(p for p in rings if p.contains(Point(x, y))) for x, y in SITES]


def run():
    layers={k:cut(k) for k in ("L02","L03","L06","L07","L08","L09","L10")}
    gasket = layers["L06"]
    cells = holes(gasket)
    window = routed()
    ports={k:holes(layers[k]) for k in ("L03","L06","L07","L08","L09")}
    assert max(a.symmetric_difference(b).area for a,b in zip(window,ports["L03"])) < .00001
    assert all(layers["L02"].covers(p) and layers["L10"].covers(p) for p in cells)
    floor_join = unary_union(window)
    cavity = unary_union(cells)
    other = [Polygon(r) for r in gasket.interiors if not any(Polygon(r).contains(Point(c)) for c in SITES)]
    reg_xy=[(-6.30,6.65),(7.28,-6.65),(7.28,6.65),(-6.30,-6.65)]
    # Distinguish registration bores from unvented interstitial voids by their actual coordinates.
    islands=[p for p in other if not any(p.covers(Point(c)) for c in reg_xy)]
    exterior = unary_union([gasket.exterior,*[p.boundary for p in other]])
    exposed = mask("gtl").intersection(mask("gts"))
    mask_top, mask_bot = mask("gts"), mask("gbs")
    drill = []
    for kind in ("PTH","NPTH"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for o in gerbonara.ExcellonFile.open(next(CAM.glob("*-"+kind+".drl"))).objects:
                p = Point(o.x-20,o.y+20).buffer(o.tool.diameter/2, quad_segs=90)
                drill.append((round(o.tool.diameter,2),p))
    via = [p for d,p in drill if d==.30]
    assert len(via)==12
    lower = layers["L03"]
    via_metrics = [dict(x=p.centroid.x,y=p.centroid.y,cell_mm=p.distance(cavity),floor_mm=p.distance(floor_join),
                        front_mask_opening_mm=p.distance(mask_top),back_mask_opening_mm=p.distance(mask_bot),
                        lower_gasket_coverage_mm=p.distance(lower.boundary)) for p in via]
    assert all(lower.covers(p) for p in via)
    pos = [Point(c) for c in SITES]
    def void_count(solid):
        obj = box(-10,-9,12,9).difference(solid)
        parts = list(obj.geoms) if obj.geom_type=="MultiPolygon" else [obj]
        return [(sum(p.contains(q) for q in pos),p.contains(Point(-9,-8))) for p in parts]
    neg_neighbor = gasket.difference(LineString([SITES[0],SITES[1]]).buffer(.01))
    neg_ambient = gasket.difference(LineString([SITES[0],(-9,4.2)]).buffer(.01))
    assert sum(n==1 and not outside for n,outside in void_count(gasket))==9
    assert (2,False) in void_count(neg_neighbor) and (1,True) in void_count(neg_ambient)
    lanes=(-.625795425,-.294204575,.294204575,.625795425)
    contacts=[]
    flank_lengths=[]
    for y in (4.2,0.,-4.2):
        for off in lanes:
            line=LineString([(-7.33,y+off),(8.48,y+off)])
            cuts=sorted(line.intersection(exposed).geoms,key=lambda p:p.centroid.x)
            assert len(cuts)==4 and all(abs(s.length-.35)<1e-5 for s in cuts)
            contacts.extend(cuts)
            flank_lengths.extend([s.length for s in line.intersection(gasket).geoms])
    all_ports = {k:ports[k][4].area for k in ports}
    fasteners=[p for d,p in drill if d==1.40]
    assert len(fasteners)==4 and all(any(p.covers(Point(c)) for p in fasteners) for c in reg_xy)
    for layer in layers.values():
        assert all(layer.distance(Point(c))>.699 for c in reg_xy)
    a=all_ports
    # Nominal z increments from the fabrication drawings. The independent 3-D void readback tests this sum.
    lower_air=(.800+.218)*a["L03"]+.550*a["L06"]
    neck=.0254*a["L07"]+.127*a["L08"]
    cap=.400*a["L09"]
    gross=lower_air+neck+cap
    wire_volume=math.pi*(.0315908500818/2)**2*3.45
    return dict(cells=9,edgecut_windows=len(window),gasket_land_area_mm2=gasket.area,
        floor_gasket_area_mm2=layers["L03"].area,
        lower_routed_gasket_aperture_min_margin_mm=min(p.boundary.distance(w.boundary) for p,w in zip(cells,window)),
        gasket_enclosed_interstitial_pockets=[dict(centroid_mm=[p.centroid.x,p.centroid.y],area_mm2=p.area) for p in islands],
        gasket_screw_count=len(other)-len(islands),gasket_outer_land_min_mm=min(p.distance(exterior) for p in cells),
        gasket_adjacent_horizontal_mm=cells[3].distance(cells[4]),gasket_adjacent_vertical_mm=cells[1].distance(cells[4]),
        cap_horizontal_web_mm=ports["L09"][3].distance(ports["L09"][4]),cap_vertical_web_mm=ports["L09"][1].distance(ports["L09"][4]),
        floor_outer_land_min_mm=min(w.distance(lower.exterior) for w in window),
        wire_crossed_land_intervals_mm=sorted({round(v,4) for v in flank_lengths}),exposed_bar_intersections=len(contacts),
        via=via_metrics,cable_PTHs=sum(d==.65 for d,p in drill),cable_rim_to_cell_mm=min(p.distance(cavity) for d,p in drill if d==.65),
        fastener_count=len(fasteners),fastener_xy_mm=reg_xy,fastener_rim_to_contact_cell_mm=min(p.distance(cavity) for p in fasteners),
        cut_area_by_layer_mm2=all_ports, floor_opening_mm2=a["L03"],gasket_opening_mm2=a["L06"],cap_area_mm2=a["L09"],
        diaphragm_pressure_area_mm2=a["L09"],liner_thickness_mm=.0254,roof_thickness_mm=.127,gross_volume_mm3=gross,
        net_volume_mm3={str(n):gross-n*wire_volume for n in (2,3,4)},lower_volume_4w_mm3=lower_air-4*wire_volume+neck/2,
        negative_controls=["0.020 mm slit merges adjacent cavities","0.020 mm slit connects left cell to skirt"],
        plotted_upper_liner_to_foil_radial_lip_mm=ports["L07"][4].boundary.distance(ports["L08"][4].boundary))
if __name__=="__main__":
    print(json.dumps(run(),indent=2))
