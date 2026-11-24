"""Measure the actual assembled STEP via intersections and spatial probes at each bearing."""
from math import pi
import cadquery as cq
from wire_clearance import screen

def member(parts,prefix):
    shapes=[v for k,v in parts.items() if k.startswith(prefix)]
    assert len(shapes)==1,prefix
    return shapes[0]

def run(parts):
    floor,board=member(parts,'L01'),member(parts,'L03_electrode')
    stop,liner=member(parts,'L06'),member(parts,'L07')
    cap,diaphragm,top=member(parts,'L09'),member(parts,'L10'),member(parts,'L11')
    wires=[p for k,p in parts.items() if k.startswith('L04_straight')]
    assert len(wires)==12
    for s in stop.Solids():
        b=s.BoundingBox()
        for x in (b.xmin+.02,b.xmax-.02):
            for y in (b.ymin+.02,b.ymax-.02):
                assert board.isInside(cq.Vector(x,y,b.zmin-.0005))
                assert liner.isInside(cq.Vector(x,y,b.zmax+.0005))
                assert s.isInside(cq.Vector(x,y,b.zmax-.0005))
    assert len(stop.Solids())==2
    def flat(shape,z):return [f for f in shape.Faces() if f.BoundingBox().zlen<.00001 and abs(f.Center().z-z)<.00001]
    floor_bottom=floor.BoundingBox().zmin; cap_top=top.BoundingBox().zmax
    assert abs(cap.Volume()-top.Volume())<.0000001
    profiles=flat(top,top.BoundingBox().zmin)
    hole=next(w for f in profiles for w in f.Wires() if abs(w.Center().x)<.01 and abs(w.Center().y)<.01)
    membrane_faces=flat(diaphragm,top.BoundingBox().zmin)
    area=sum(f.intersect(g).Area() for f in profiles for g in membrane_faces)
    records=[]
    for i in range(1,5):
        screw=parts[f'L12_button_screw_{i}']; nut=parts[f'L13_hex_nut_{i}']
        sb=screw.BoundingBox();nb=nut.BoundingBox();x,y=(sb.xmin+sb.xmax)/2,(sb.ymin+sb.ymax)/2
        for dx,dy in ((.80,0),(-.80,0),(0,.80),(0,-.80)):
            def pt(z):return cq.Vector(x+dx,y+dy,z)
            assert screw.isInside(pt(cap_top+.0005)) and top.isInside(pt(cap_top-.0005))
            assert floor.isInside(pt(floor_bottom+.0005)) and nut.isInside(pt(floor_bottom-.0005))
        for k,q in parts.items():
            if q is screw:continue
            b=q.BoundingBox()
            if b.xmin>sb.xmax or b.xmax<sb.xmin or b.ymin>sb.ymax or b.ymax<sb.ymin:continue
            assert sum(t.Volume() for t in screw.intersect(q).Solids())<.00000002,(i,k)
        records.append(dict(xy_mm=[x,y],underhead_z_mm=cap_top,underhead_length_mm=cap_top-sb.zmin,
            head_diameter_mm=sb.xlen,head_height_mm=sb.zmax-cap_top,thread_pitch_mm=25.4/90,
            nut_height_mm=nb.zlen,nut_af_mm=nb.ylen,engagement_pitches=nb.zlen/(25.4/90),
            screw_tip_beyond_nut_mm=nb.zmin-sb.zmin,plate_bearing_separation_mm=cap_top-floor_bottom))
    clearance=liner.BoundingBox().zmin-max(w.BoundingBox().zmax for w in wires)
    return dict(grid_opening_mm2=cq.Face.makeFromWires(hole).Area(),diaphragm_to_grid_contact_area_mm2=area,
        contacts=dict(spacer_count=2,spacer_bearing_area_mm2=sum(s.Volume()/s.BoundingBox().zlen for s in stop.Solids()),
                      clamped_material_mm=cap_top-floor_bottom),
        screw_records=records, cap_solids_volume_difference_mm3=abs(cap.Volume()-top.Volume()),
        cold_wire_crown_to_dielectric_mm=clearance,diaphragm_recess_at_active_field_mm=cap_top-diaphragm.BoundingBox().zmax,
        wire_thermal_screen=screen(4.20,.540,.040,.034,.050,clearance),wire_outer_pad_edge_sensitivity=screen(4.55,.540,.040,.034,.050,clearance))
