"""Render the cut-plane and the modeled pulse loss from the issued readbacks."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Circle
from shapely.plotting import plot_polygon
from geometry_check import cut, holes
OUT=Path(__file__).resolve().parent

def poly(ax,g,color,ec=None):
    for p in getattr(g,"geoms",[g]):
        plot_polygon(p,ax=ax,add_points=False,facecolor=color,edgecolor=ec or color,linewidth=.65)

def main():
    data=json.loads((OUT/"seal-results.json").read_text())
    g=data["geometry"]
    fig,ax=plt.subplots(figsize=(6.15,4.45),layout="constrained")
    gasket=cut("L05")
    for x,y in g["fastener_xy_mm"]:
        ax.add_patch(Circle((x,y),.70,facecolor="#d6dce1",edgecolor="#536578",lw=.8))
    poly(ax,gasket,"#61ad9c","#338273")
    poly(ax,cut("L06"),"#828b99","#606d7c")
    for cell in holes(cut("L02")):
        plot_polygon(cell,ax=ax,add_points=False,facecolor="#dae7f1",edgecolor="#6593af",linewidth=.8)
    for cell in holes(cut("L07")):
        plot_polygon(cell,ax=ax,add_points=False,facecolor="#1f526f",edgecolor="#1f526f",linewidth=.7)
    for p in g["gasket_enclosed_interstitial_pockets"]:
        ax.plot(*p["centroid_mm"],marker="+",mec="#6a4894",mew=1.6,ms=7)
    for v in g["via"]:
        ax.add_patch(Circle((v["x"],v["y"]),.15,facecolor="#f9d5a0",edgecolor="#a54a27",lw=.7))
    for y in (-4.2,0,4.2):
        for a in (-.626,-.294,.294,.626):
            ax.plot([-7.65,8.58],[y+a,y+a],c="#504434",lw=.35,alpha=.8)
    ax.set_aspect("equal",adjustable="box"); ax.set(xlim=(-8.0,8.7),ylim=(-7.9,7.9),xlabel="Face x (mm)",ylabel="Face y (mm)")
    ax.spines[["right","top"]].set_visible(False)
    legend=[Patch(facecolor="#828b99",label="Gap spacer"),Patch(facecolor="#61ad9c",label="Gasket land"),Patch(facecolor="#d6dce1",label="Screw bore"),
        Patch(facecolor="#dae7f1",edgecolor="#6593af",label="Heater window"),Patch(facecolor="#1f526f",label="Roof bore"),
        Line2D([],[],marker="o",mfc="#f9d5a0",mec="#a54a27",ls="",ms=5,label="Plated via"),
        Line2D([],[],marker="+",c="#6a4894",ls="",ms=7,label="Blind pocket"),
        Line2D([],[],c="#504434",lw=1,label="Heater wire")]
    ax.legend(handles=legend,loc="center left",bbox_to_anchor=(1.01,.5),frameon=False,fontsize=8)
    fig.savefig(OUT/"seal-map.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.05,3.35),layout="constrained")
    for typ,key,color,label in [
            ("four strands","ambient_loss_percent","#aa412d","Exterior loss · 16 flanks"),
            ("interpixel","equal_neighbor_fraction_percent","#227d78","Neighbor gain · 8 flanks")]:
        rs=[r for r in data["leak"]["gaps"] if r["path"].startswith(typ) and r["h_um"]<=10]
        h=[r["h_um"] for r in rs]
        base=[r["scenarios"][-1][key] for r in rs]
        slip=[r["scenarios"][-1][("ambient_loss_percent_slip" if typ=="four strands" else "equal_neighbor_percent_slip")] for r in rs]
        ax.fill_between(h,base,slip,color=color,alpha=.20)
        ax.plot(h,base,".-",c=color,label=label)
    ax.axhline(5,ls="--",color=".3",lw=.85,label="5% of initial pressure")
    ax.legend(frameon=False,fontsize=8)
    ax.set(xlabel="Equivalent slit height (µm)",ylabel="Fraction of initial 60 kPa (%)",xlim=(.8,10.2),ylim=(0,103))
    ax.spines[["top","right"]].set_visible(False); ax.grid(axis="y",alpha=.15)
    fig.savefig(OUT/"leak-sensitivity.png",dpi=180);plt.close(fig)
if __name__=="__main__":main()
