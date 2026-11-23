"""Recover enclosed volumes from the exported assembly by cutting solids out of a test box."""
from pathlib import Path
import json
import cadquery as cq
ROOT=Path(__file__).resolve().parents[2]
SITES=[(x,y) for y in (4.2,0.,-4.2) for x in (-4.2,0.,4.2)]

def compartments(path, sites=SITES):
    assembly=cq.Assembly.load(str(path))
    parts={key:node.obj.moved(node.loc) for key,node in assembly.objects.items() if node.obj is not None}
    shapes=[(solid,solid.BoundingBox()) for part in parts.values() for solid in part.Solids()]
    # Boundaries cross the middle of each inter-pixel web. Extend above and below the hardware.
    xyz=[s[1] for s in shapes];bottom=min(b.zmin for b in xyz)-.15;top=max(b.zmax for b in xyz)+.15
    found=[]
    for x,y in sites:
        pitch=4.2
        box=cq.Solid.makeBox(pitch,pitch,top-bottom,cq.Vector(x-pitch/2,y-pitch/2,bottom))
        relevant=[s for s,b in shapes if b.xmin < x+pitch/2 and b.xmax>x-pitch/2 and b.ymin<y+pitch/2 and b.ymax>y-pitch/2]
        cavity=box.cut(*relevant).Solids()
        selected=[c for c in cavity if c.isInside(cq.Vector(x,y,-.40))]
        assert len(selected)==1,(x,y,len(selected))
        c=selected[0];bb=c.BoundingBox()
        margins=[bb.xmin-(x-pitch/2),x+pitch/2-bb.xmax,bb.ymin-(y-pitch/2),y+pitch/2-bb.ymax,bb.zmin-bottom,top-bb.zmax]
        assert min(margins)>0.001,(x,y,margins)
        found.append(dict(site_xy_mm=[x,y],free_volume_mm3=c.Volume(),z_extent_mm=[bb.zmin,bb.zmax],
                          min_distance_to_cut_plane_mm=min(margins)))
    return found,parts

if __name__=="__main__":
    from fastener_check import run as fasteners
    assembly_dir=ROOT/"head/mechanics"
    rows,parts=compartments(assembly_dir/"TA-assembled.step")
    checks=fasteners(parts)
    data=dict(four_strand_cells=rows,fasteners_and_clearance=checks,center_other_strands={})
    for n in (2,3):
        data["center_other_strands"][n]=compartments(assembly_dir/f"TA-{n}-strands.step",[(0.,0.)])[0][0]
    print(json.dumps(data,indent=2))
