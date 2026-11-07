import sys, pcbnew, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Circle
src,out,x0,x1,y0,y1=sys.argv[1],sys.argv[2],*map(float,sys.argv[3:7])
hl=set(sys.argv[7].split(',')) if len(sys.argv)>7 else set()
b=pcbnew.LoadBoard(src)
col={pcbnew.F_Cu:'red',pcbnew.In1_Cu:'orange',pcbnew.In2_Cu:'magenta',pcbnew.B_Cu:'blue'}
fig,ax=plt.subplots(figsize=(16,16*(y1-y0)/(x1-x0)))
for t in b.GetTracks():
    s,e=t.GetStart(),t.GetEnd()
    if t.GetClass()=='PCB_VIA':
        ax.add_patch(Circle((s.x/1e6,s.y/1e6),t.GetWidth()/2e6,color='green',alpha=.6))
    else:
        lw=t.GetWidth()/1e6*72*16/(x1-x0)
        a=1 if t.GetNetname() in hl else .45
        ax.plot([s.x/1e6,e.x/1e6],[s.y/1e6,e.y/1e6],color=col.get(t.GetLayer(),'k'),lw=lw,alpha=a,solid_capstyle='round')
for fp in b.GetFootprints():
    for p in fp.Pads():
        L=pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        sps=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(sps,L,0,2000)
        o=sps.Outline(0); pts=[(o.CPoint(j).x/1e6,o.CPoint(j).y/1e6) for j in range(o.PointCount())]
        c='gold' if p.GetNetname() in hl else ('salmon' if L==pcbnew.F_Cu else 'lightblue')
        ax.add_patch(MP(pts,color=c,alpha=.7))
        x,y=p.GetPosition().x/1e6,p.GetPosition().y/1e6
        if x0<x<x1 and y0<y<y1: ax.text(x,y,p.GetNetname().replace('/','')[:7],fontsize=5,ha='center')
    x,y=fp.GetPosition().x/1e6,fp.GetPosition().y/1e6
    if x0<x<x1 and y0<y<y1: ax.text(x,y-0.6,fp.GetReference(),fontsize=8,color='k',weight='bold')
ax.set_xlim(x0,x1);ax.set_ylim(y1,y0);ax.set_aspect('equal');ax.grid(alpha=.3)
ax.set_xticks([x0+i for i in range(int(x1-x0)+1)]);ax.set_yticks([y0+i for i in range(int(y1-y0)+1)])
plt.savefig(out,dpi=110,bbox_inches='tight')
