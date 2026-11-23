"""Read finished cut paths, Excellon bores and soldermask/copper layers in face coordinates (mm)."""
from pathlib import Path
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
    layers = {k:cut(k) for k in ("L01","L02","L03","L04","L06","L07","L08","L09","L10","L11","L13","L14","L15","L16","L17")}
    gasket = layers["L10"]
    cells = holes(gasket)
    window = routed()
    ports = dict((k,holes(layers[k])) for k in ("L02","L03","L04","L10","L11","L13","L14","L15","L16"))
    for k in ("L02","L03","L04"):
        assert max(a.symmetric_difference(b).area for a,b in zip(window,ports[k])) < .00001
    assert layers["L07"].equals(layers["L08"]) and layers["L08"].equals(layers["L09"])
    assert layers["L14"].equals(layers["L15"])
    assert all(layers["L01"].covers(p) and layers["L17"].covers(p) for p in cells)
    cap_join = unary_union(ports["L16"])
    floor_join = unary_union(window)
    cavity = unary_union(cells)
    other = [Polygon(r) for r in gasket.interiors if not any(Polygon(r).contains(Point(c)) for c in SITES)]
    islands = [p for p in other if p.area>1]
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
    lower = layers["L04"]
    via_metrics = [dict(x=p.centroid.x,y=p.centroid.y,cell_mm=p.distance(cavity),floor_mm=p.distance(floor_join),
                        front_mask_opening_mm=p.distance(mask_top),back_mask_opening_mm=p.distance(mask_bot),
                        bottom_bond_cover_mm=p.distance(lower.boundary)) for p in via]
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
            line=LineString([(-7.33,y+off),(8.33,y+off)])
            cuts=sorted(line.intersection(exposed).geoms,key=lambda p:p.centroid.x)
            assert len(cuts)==4 and all(abs(s.length-.35)<1e-5 for s in cuts)
            contacts.extend(cuts)
            flank_lengths.extend([s.length for s in line.intersection(gasket).geoms])
    all_ports = {k:ports[k][4].area for k in ports}
    return dict(cells=9,edgecut_windows=len(window),gasket_land_area_mm2=gasket.area,spacer_area_mm2=layers["L08"].area,
        lower_routed_gasket_aperture_min_margin_mm=min(p.boundary.distance(w.boundary) for p,w in zip(cells,window)),
        gasket_enclosed_interstitial_pockets=[dict(centroid_mm=[p.centroid.x,p.centroid.y],area_mm2=p.area,
               free_area_after_spacer_mm2=p.difference(layers["L08"]).area) for p in islands],
        gasket_datum_count=len(other)-len(islands),gasket_outer_land_min_mm=min(p.distance(exterior) for p in cells),
        gasket_adjacent_horizontal_mm=cells[3].distance(cells[4]),gasket_adjacent_vertical_mm=cells[1].distance(cells[4]),
        face_bond_adjacent_horizontal_mm=ports["L16"][3].distance(ports["L16"][4]),face_bond_adjacent_vertical_mm=ports["L16"][1].distance(ports["L16"][4]),
        floor_outer_land_min_mm=min(w.distance(lower.exterior) for w in window),face_bond_outer_land_min_mm=cap_join.distance(layers["L16"].exterior),
        wire_crossed_land_intervals_mm=sorted({round(v,4) for v in flank_lengths}),exposed_bar_intersections=len(contacts),
        via=via_metrics,cable_PTHs=sum(d==.65 for d,p in drill),cable_rim_to_cell_mm=min(p.distance(cavity) for d,p in drill if d==.65),
        datum_NPTHs=sum(d==.55 for d,p in drill),datum_rim_to_cell_mm=min(p.distance(cavity) for d,p in drill if d==.55),
        cut_area_by_layer_mm2=all_ports,
        negative_controls=["0.020 mm slit merges adjacent cavities","0.020 mm slit connects left cell to skirt"],
        plotted_upper_liner_to_foil_radial_lip_mm=ports["L11"][4].boundary.distance(ports["L13"][4].boundary))
if __name__=="__main__":
    print(json.dumps(run(),indent=2))
