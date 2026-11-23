"""Check contact planes, screw engagement and free-field recess in the reopened four-wire STEP."""
from math import pi
import cadquery as cq
from wire_clearance import screen

def named(parts,prefix):
    hits=[s for k,s in parts.items() if k.startswith(prefix)]
    assert len(hits)==1,(prefix,len(hits))
    return hits[0]

def flat_faces(shape,z):
    return [f for f in shape.Faces() if f.BoundingBox().zlen<.00001 and abs(f.Center().z-z)<.00001]

def run(parts):
    backing=named(parts,"L01");board=named(parts,"L04_electrode")
    floor=named(parts,"L02");liner=named(parts,"L07");cap=named(parts,"L09")
    membrane=named(parts,"L10");grid=named(parts,"L11")
    wires=[p for k,p in parts.items() if k.startswith("L05_straight")]
    assert len(wires)==12
    contacts={}
    for name,part,x,y,halfx,halfy in (("board",board,3.65,7.26,.60,.325),("cap",cap,4.55,8.15,.625,.30),("grid",grid,2.85,8.15,.625,.30)):
        z=part.BoundingBox().zmin
        areas=[]
        for sx in (-1,1):
            for sy in (-1,1):
                tests=[(sx*x+i*.96*halfx,sy*y+j*.96*halfy) for i,j in ((0,0),(-1,-1),(-1,1),(1,-1),(1,1))]
                for tx,ty in tests:
                    assert backing.isInside(cq.Vector(tx,ty,z-.0005)),(name,tx,ty,z)
                    assert part.isInside(cq.Vector(tx,ty,z+.0005)) and not part.isInside(cq.Vector(tx,ty,z-.0005))
                    assert not backing.isInside(cq.Vector(tx,ty,z+.0005))
                areas.append(4*halfx*halfy)
        contacts[name]=dict(z_mm=z,nominal_four_pad_area_mm2=sum(areas),interior_witnesses=20)
    backing_surface=floor.BoundingBox().zmin
    screw_records=[]
    for name,screw in parts.items():
        if not name.startswith("L12"):continue
        b=screw.BoundingBox();x=(b.xmin+b.xmax)/2;y=(b.ymin+b.ymax)/2
        # Underhead radial slice at 0.80 mm lies on the seating annulus, outside the shank.
        seat=[f.Center().z for f in screw.Faces() if f.BoundingBox().zlen<1e-5 and f.Area()>1 and b.zmin+.1<f.Center().z<b.zmax-.1]
        assert len(seat)==1,(name,seat)
        z=seat[0]
        for sx,sy in ((1,0),(-1,0),(0,1),(0,-1)):
            tx=x+.80*sx;ty=y+.80*sy
            assert grid.isInside(cq.Vector(tx,ty,z-.0005))
            assert screw.isInside(cq.Vector(tx,ty,z+.0005))
        other_parts=[s for k,s in parts.items() if k!=name and (k.startswith("L0") or k.startswith("L1"))]
        collisions=[]
        for q in other_parts:
            c=q.BoundingBox()
            if c.xmax<b.xmin or b.xmax<c.xmin or c.ymax<b.ymin or b.ymax<c.ymin:continue
            if min(c.zmax,b.zmax)-max(c.zmin,b.zmin)<1e-7:continue
            hit=sum(h.Volume() for h in screw.intersect(q).Solids())
            if hit>1e-8:collisions.append(hit)
        assert not collisions,(name,collisions)
        screw_records.append(dict(xy_mm=[x,y],underhead_z_mm=z,underhead_length_mm=z-b.zmin,head_diameter_mm=b.xlen,
            pitch_mm=.25,head_height_mm=b.zmax-z,thread_engagement_envelope_mm=backing_surface-b.zmin,
            engagement_pitches=(backing_surface-b.zmin)/.25,tip_to_back_mm=b.zmin-backing.BoundingBox().zmin,
            head_recess_from_island_top_mm=grid.BoundingBox().zmax-b.zmax))
    assert len(screw_records)==4
    for x in (-4.2,0,4.2):
        for y in (-4.2,0,4.2):
            z=floor.BoundingBox().zmin
            assert not backing.isInside(cq.Vector(x,y,z-.15)) and floor.isInside(cq.Vector(x,y,z+.03))
    roof_z=liner.BoundingBox().zmin
    clearance=roof_z-max(w.BoundingBox().zmax for w in wires)
    # Field grid top is lower than the four raised screw islands. Select its largest free planar face above the diaphragm.
    topfield=max((f for f in grid.Faces() if f.BoundingBox().zlen<1e-5 and f.Center().z>grid.BoundingBox().zmin+.30),key=lambda f:f.Area()).Center().z
    grid_faces=flat_faces(grid,grid.BoundingBox().zmin)
    diaphragm_faces=flat_faces(membrane,grid.BoundingBox().zmin)
    compressed_face_area=sum(f.intersect(g).Area() for f in grid_faces for g in diaphragm_faces)
    center_opening=next(w for f in grid_faces for w in f.Wires() if abs(w.Center().x)<.01 and abs(w.Center().y)<.01)
    return dict(grid_opening_mm2=cq.Face.makeFromWires(center_opening).Area(),
        diaphragm_to_grid_contact_area_mm2=compressed_face_area,contacts=contacts,screw_records=screw_records,gas_floor_continuous_over_backing_windows=9,
        cold_wire_crown_to_dielectric_mm=clearance,diaphragm_recess_at_active_field_mm=topfield-membrane.BoundingBox().zmax,
        wire_thermal_screen=screen(4.20,.540,.040,.034,.050,clearance),
        wire_outer_pad_edge_sensitivity=screen(4.55,.540,.040,.034,.050,clearance))
