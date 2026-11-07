import pcbnew, re, sys, math
from collections import Counter
mm=pcbnew.ToMM; MM=pcbnew.FromMM
D='fin'
bd=pcbnew.LoadBoard(f'{D}/FC-EXPSYNTH.kicad_pcb')
GR=[]
def drc():
    for z in bd.Zones():
        if not z.GetIsRuleArea(): z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    bd.BuildConnectivity(); pcbnew.ZONE_FILLER(bd).Fill(bd.Zones()); bd.BuildConnectivity()
    pcbnew.WriteDRCReport(bd,f'{D}/drc.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)
    r=open(f'{D}/drc.rpt').read(); return r, Counter(re.findall(r'^\[(\w+)\]',r,re.M))
# 1. duplicated GND via at (46.675,48.442): move its tracks onto the first via and delete it
vias=[t for t in bd.GetTracks() if t.GetClass()=='PCB_VIA']
A=[v for v in vias if abs(mm(v.GetPosition().x)-46.675)<0.01 and abs(mm(v.GetPosition().y)-48.325)<0.01]
B=[v for v in vias if abs(mm(v.GetPosition().x)-46.675)<0.01 and abs(mm(v.GetPosition().y)-48.442)<0.01]
print('dup vias',len(A),len(B))
if A and B:
    pa=A[0].GetPosition(); pb=B[0].GetPosition()
    for t in bd.GetTracks():
        if t.GetClass()=='PCB_VIA': continue
        if t.GetStart()==pb: t.SetStart(pa)
        if t.GetEnd()==pb: t.SetEnd(pa)
    bd.RemoveNative(B[0]); GR.append(B[0])
r,c=drc(); print('after dup fix',dict(c))
# 2. stitch via for C12 GND fragment
best=None
base=pcbnew.ToMM
for (x,y) in [(44.4,21.35),(44.5,21.45),(44.3,21.25),(44.45,21.4),(44.55,21.5)]:
    v=pcbnew.PCB_VIA(bd); v.SetPosition(pcbnew.VECTOR2I(MM(x),MM(y))); v.SetWidth(MM(0.45)); v.SetDrill(MM(0.20))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNetCode(bd.GetNetcodeFromNetname('GND')); bd.Add(v)
    r,c=drc(); bad=c.get('clearance',0)+c.get('shorting_items',0)+c.get('hole_clearance',0)+c.get('hole_near_hole',0)
    print((x,y),'unconnected',c.get('unconnected_items',0),'bad',bad,flush=True)
    if c.get('unconnected_items',0)==0 and bad==0: best=(x,y); break
    bd.RemoveNative(v); GR.append(v)
print('best',best)
pcbnew.SaveBoard(f'{D}/out.kicad_pcb',bd)
r,c=drc(); print('FINAL',dict(c))
