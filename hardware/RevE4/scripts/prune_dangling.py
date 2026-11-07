import pcbnew, re, math, sys
from collections import Counter
mm=pcbnew.ToMM
SRC,DST,D=sys.argv[1:4]
bd=pcbnew.LoadBoard(SRC)
SAVE=DST
rpt=open(f'{D}/drc.rpt').read()
items=[]
for m in re.finditer(r'\[(track_dangling|via_dangling)\][^\n]*\n(?:[^\n@]*\n)?\s*@\(([\d.]+) mm, ([\d.]+) mm\): (Track|Via) \[([^\]]*)\] on ([\w.]+)(?:, length ([\d.]+) mm)?',rpt):
    items.append(m.groups())
print('dangling items',len(items))
rm=0
for kind,x,y,typ,net,lay,L in items:
    x,y=float(x),float(y)
    for t in list(bd.GetTracks()):
        if t.GetNetname()!=net: continue
        if typ=='Via':
            if t.GetClass()=='PCB_VIA' and abs(mm(t.GetPosition().x)-x)<0.02 and abs(mm(t.GetPosition().y)-y)<0.02: bd.RemoveNative(t); rm+=1; break
        else:
            if t.GetClass()=='PCB_VIA' or t.GetLayerName()!=lay: continue
            if (abs(mm(t.GetStart().x)-x)<0.02 and abs(mm(t.GetStart().y)-y)<0.02) or (abs(mm(t.GetEnd().x)-x)<0.02 and abs(mm(t.GetEnd().y)-y)<0.02):
                bd.RemoveNative(t); rm+=1; break
print('removed',rm)
pcbnew.SaveBoard(DST,bd)
for z in bd.Zones():
    if not z.GetIsRuleArea(): z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
bd.BuildConnectivity(); pcbnew.ZONE_FILLER(bd).Fill(bd.Zones()); bd.BuildConnectivity()
pcbnew.WriteDRCReport(bd,f'{D}/drc.rpt',pcbnew.EDA_UNITS_MILLIMETRES,True)
r=open(f'{D}/drc.rpt').read(); print(dict(Counter(re.findall(r'^\[(\w+)\]',r,re.M))))
