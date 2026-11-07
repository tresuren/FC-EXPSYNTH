import pcbnew, math, sys, re
from collections import Counter
from shapely.geometry import LineString, Polygon, Point, box
from shapely.ops import unary_union
from shapely.prepared import prep
mm=pcbnew.ToMM; MM=pcbnew.FromMM; V=pcbnew.VECTOR2I
bd=pcbnew.LoadBoard('orig.kicad_pcb')
# 1. move
for r,dx in (('J13',-2.5),('J12',0.65)):
    f=bd.FindFootprintByReference(r); p=f.GetPosition(); f.SetPosition(V(p.x+MM(dx),p.y))
# 2. strip tracks touching moved pads / inside moved keepouts
CL=0.13
MOVED=['J13','J12']
def padbox(p):
    b=p.GetBoundingBox(); return box(mm(b.GetLeft()),mm(b.GetTop()),mm(b.GetRight()),mm(b.GetBottom()))
def tgeom(t):
    if t.GetClass()=='PCB_VIA':
        q=t.GetPosition(); return Point(mm(q.x),mm(q.y)).buffer(mm(t.GetWidth())/2)
    return LineString([(mm(t.GetStart().x),mm(t.GetStart().y)),(mm(t.GetEnd().x),mm(t.GetEnd().y))]).buffer(mm(t.GetWidth())/2)
pads=[(r,p) for r in MOVED for p in bd.FindFootprintByReference(r).Pads()]
kz=[]
for r in MOVED:
    for z in bd.FindFootprintByReference(r).Zones():
        if z.GetIsRuleArea():
            ol=z.Outline().COutline(0); kz.append((Polygon([(mm(ol.CPoint(k).x),mm(ol.CPoint(k).y)) for k in range(ol.PointCount())]),z.GetLayerSet()))
kill=[]; nets=set()
for t in bd.GetTracks():
    g=tgeom(t); hit=False
    for r,p in pads:
        if not g.intersects(padbox(p).buffer(CL)): continue
        if t.GetClass()!='PCB_VIA' and not (p.IsOnLayer(t.GetLayer()) or p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH): continue
        hit=True; break
    if not hit and t.GetClass()!='PCB_VIA':
        hit=any(g.intersects(pl) and ls.Contains(t.GetLayer()) for pl,ls in kz)
    if not hit and t.GetClass()=='PCB_VIA':
        hit=any(g.intersects(pl) for pl,ls in kz)
    if hit: kill.append(t); nets.add(t.GetNetname())
print('killed',len(kill),sorted(nets))
for t in kill: bd.RemoveNative(t)
# dangling cleanup on affected nets (not GND)
def ends(t): return [(t.GetStart().x,t.GetStart().y),(t.GetEnd().x,t.GetEnd().y)]
changed=True; tot=0
cn=nets-{'GND'}
while changed:
    changed=False; tr=list(bd.GetTracks())
    for t in tr:
        if t.GetClass()=='PCB_VIA' or t.GetNetname() not in cn: continue
        for e in ends(t):
            touch=False
            for f in bd.GetFootprints():
                for p in f.Pads():
                    if p.GetNetCode()==t.GetNetCode() and p.IsOnLayer(t.GetLayer()) and padbox(p).buffer(0.01).contains(Point(mm(e[0]),mm(e[1]))): touch=True
            if not touch:
                for u in tr:
                    if u is t or u.GetNetCode()!=t.GetNetCode(): continue
                    if any(abs(e[0]-x)<5 and abs(e[1]-y)<5 for x,y in ends(u)) and (u.GetClass()=='PCB_VIA' or u.GetLayer()==t.GetLayer()): touch=True;break
                if not touch:
                    for u in tr:
                        if u.GetClass()=='PCB_VIA' and u.GetNetCode()==t.GetNetCode() and abs(u.GetPosition().x-e[0])<5 and abs(u.GetPosition().y-e[1])<5: touch=True;break
            if not touch: bd.RemoveNative(t); tot+=1; changed=True; break
print('dangling removed',tot)
# 3. GND wipe in microSD region + via per GND pad (same as before)
def inreg(x,y): return x<24 and 7<y<28
gnd=bd.GetNetcodeFromNetname('GND'); rm=0
for t in list(bd.GetTracks()):
    if t.GetNetCode()!=gnd: continue
    if t.GetClass()=='PCB_VIA':
        if inreg(mm(t.GetPosition().x),mm(t.GetPosition().y)): bd.RemoveNative(t); rm+=1
    elif all(inreg(mm(p.x),mm(p.y)) for p in (t.GetStart(),t.GetEnd())): bd.RemoveNative(t); rm+=1
print('GND wiped',rm)
def obst(net):
    gs=[]
    for t in bd.GetTracks():
        if t.GetNetCode()!=net: gs.append(tgeom(t))
    for f in bd.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode()!=net: gs.append(padbox(p))
    return unary_union(gs)
keeps=[]
for f in bd.GetFootprints():
    for z in f.Zones():
        if z.GetIsRuleArea():
            ol=z.Outline().COutline(0); keeps.append(Polygon([(mm(ol.CPoint(k).x),mm(ol.CPoint(k).y)) for k in range(ol.PointCount())]))
for z in bd.Zones():
    if z.GetIsRuleArea():
        ol=z.Outline().COutline(0); keeps.append(Polygon([(mm(ol.CPoint(k).x),mm(ol.CPoint(k).y)) for k in range(ol.PointCount())]))
KEEP=unary_union(keeps); KEEPB=prep(KEEP.buffer(0.05)); KEEPP=prep(KEEP)
for ref in ('J13','J12'):
    for p in bd.FindFootprintByReference(ref).Pads():
        if p.GetNetCode()!=gnd: continue
        pb=padbox(p); O=obst(gnd).buffer(0.14); OP=prep(O); cx,cy=pb.centroid.x,pb.centroid.y
        best=None
        for ix in range(-40,41):
            for iy in range(-40,41):
                x=round(cx+ix*0.05,3); y=round(cy+iy*0.05,3)
                if not (0.9<x<91.1 and 0.9<y<47.5): continue
                via=Point(x,y).buffer(0.225)
                if OP.intersects(via) or KEEPB.intersects(via): continue
                d=pb.distance(Point(x,y))
                if d>1.0: continue
                if d<0.2: tr=None
                else:
                    nearest=pb.exterior.interpolate(pb.exterior.project(Point(x,y)))
                    ex,ey=(nearest.x+(cx-nearest.x)*0.3, nearest.y+(cy-nearest.y)*0.3)
                    tr=LineString([(x,y),(ex,ey)]); trb=tr.buffer(0.05)
                    if OP.intersects(trb) or KEEPP.intersects(trb): continue
                if best is None or d<best[0]: best=(d,x,y,tr)
        if not best: print('NO GND via spot',ref,p.GetNumber()); continue
        d,x,y,tr=best
        v=pcbnew.PCB_VIA(bd); v.SetPosition(V(MM(x),MM(y))); v.SetWidth(MM(0.45)); v.SetDrill(MM(0.2)); v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNetCode(gnd); bd.Add(v)
        if tr is not None:
            c=list(tr.coords); t=pcbnew.PCB_TRACK(bd); t.SetStart(V(MM(c[0][0]),MM(c[0][1]))); t.SetEnd(V(MM(c[1][0]),MM(c[1][1]))); t.SetWidth(MM(0.15)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(gnd); bd.Add(t)
        print('GND via',ref,p.GetNumber(),'(%.2f,%.2f)'%(x,y))
pcbnew.SaveBoard('stage_a.kicad_pcb',bd)
