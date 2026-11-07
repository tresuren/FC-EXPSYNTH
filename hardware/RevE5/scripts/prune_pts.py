import sys, pcbnew
SRC,DST,NET=sys.argv[1:4]; pts=[tuple(map(float,a.split(','))) for a in sys.argv[4:]]
b=pcbnew.LoadBoard(SRC)
def key(p): return (round(p.x/1000),round(p.y/1000))
def pad_hit(p):
    return any(pad.GetNetname()==NET and pad.HitTest(p) for fp in b.GetFootprints() for pad in fp.Pads())
fr={(round(x*1000),round(y*1000)) for x,y in pts}; n=0
while fr:
    pt=fr.pop()
    for t in list(b.GetTracks()):
        if t.GetNetname()!=NET: continue
        if t.GetClass()=='PCB_VIA':
            if key(t.GetPosition())==pt: b.RemoveNative(t); n+=1
            continue
        ends=[key(t.GetStart()),key(t.GetEnd())]
        if pt in ends:
            o=t.GetEnd() if ends[0]==pt else t.GetStart(); b.RemoveNative(t); n+=1; ok=key(o)
            deg=sum(1 for u in b.GetTracks() if u.GetNetname()==NET and ((u.GetClass()=='PCB_VIA' and key(u.GetPosition())==ok) or (u.GetClass()!='PCB_VIA' and ok in (key(u.GetStart()),key(u.GetEnd())))))
            if deg<=1 and not pad_hit(o):
                # via at ok with only this? check via present
                fr.add(ok)
            print('rm',t.GetLayerName() if False else '',ok)
print('removed',n); b.Save(DST)
