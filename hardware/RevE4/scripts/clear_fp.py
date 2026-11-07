# remove copper (other nets, and same-net stubs) overlapping footprint pads + clearance
import sys, pcbnew
from shapely.geometry import LineString, Point, Polygon
SRC,DST,REFS=sys.argv[1],sys.argv[2],sys.argv[3].split(',')
MM=1e6; CL=0.12
b=pcbnew.LoadBoard(SRC)
def poly(s):
    o=s.Outline(0); return Polygon([(o.CPoint(j).x/MM,o.CPoint(j).y/MM) for j in range(o.PointCount())])
pads=[]
for r in REFS:
    for p in b.FindFootprintByReference(r).Pads():
        s=pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(s,pcbnew.F_Cu,0,2000); pads.append((poly(s),p.GetNetCode()))
for t in list(b.GetTracks()):
    if not t.IsOnLayer(pcbnew.F_Cu): continue
    s,e=t.GetStart(),t.GetEnd(); w=t.GetWidth()/MM/2
    g=(LineString([(s.x/MM,s.y/MM),(e.x/MM,e.y/MM)]) if s!=e else Point(s.x/MM,s.y/MM)).buffer(w)
    for pg,net in pads:
        if t.GetNetCode()!=net and g.distance(pg)<CL:
            print('rm',t.GetClass(),t.GetNetname(),round(s.x/MM,2),round(s.y/MM,2),round(e.x/MM,2),round(e.y/MM,2)); b.RemoveNative(t); break
b.Save(DST)
