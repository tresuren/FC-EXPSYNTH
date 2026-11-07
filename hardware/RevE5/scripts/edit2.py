import sys, pcbnew
from shapely.geometry import LineString, Point, Polygon
SRC, DST = sys.argv[1], sys.argv[2]
MM = 1e6
b = pcbnew.LoadBoard(SRC)
V = lambda x, y: pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
def key(p): return (round(p.x / 1000), round(p.y / 1000))
def pad_hit(net, p):
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == net and pad.HitTest(p): return True
    return False
def prune(net, seeds):
    n = 0; fr = set(seeds)
    while fr:
        pt = fr.pop()
        for t in list(b.GetTracks()):
            if t.GetNetname() != net: continue
            if t.GetClass() == 'PCB_VIA':
                if key(t.GetPosition()) == pt: b.RemoveNative(t); n += 1
                continue
            ends = [key(t.GetStart()), key(t.GetEnd())]
            if pt in ends:
                other = t.GetEnd() if ends[0] == pt else t.GetStart()
                b.RemoveNative(t); n += 1
                ok = key(other); deg = 0
                for u in b.GetTracks():
                    if u.GetNetname() != net: continue
                    if u.GetClass() == 'PCB_VIA':
                        if key(u.GetPosition()) == ok: deg += 1
                    elif ok in (key(u.GetStart()), key(u.GetEnd())): deg += 1
                if deg <= 1 and not pad_hit(net, other): fr.add(ok)
    return n
def strip_fp(ref):
    fp = b.FindFootprintByReference(ref)
    for p in fp.Pads():
        net = p.GetNetname()
        # tracks whose end lies on this pad
        seeds = set()
        for t in list(b.GetTracks()):
            if t.GetNetname() != net: continue
            if t.GetClass() == 'PCB_VIA':
                if p.HitTest(t.GetPosition()) or (t.GetPosition() - p.GetPosition()).EuclideanNorm() < 500000:
                    seeds.add(key(t.GetPosition()))
            else:
                for q in (t.GetStart(), t.GetEnd()):
                    if p.HitTest(q): seeds.add(key(q))
        if net == 'GND':
            for t in list(b.GetTracks()):
                if t.GetNetname() != 'GND': continue
                if t.GetClass() == 'PCB_VIA':
                    if key(t.GetPosition()) in seeds: b.RemoveNative(t)
                elif key(t.GetStart()) in seeds or key(t.GetEnd()) in seeds: b.RemoveNative(t)
            print(ref, p.GetNumber(), 'GND local strip')
        else:
            print(ref, p.GetNumber(), net, prune(net, seeds))
for r in ('R3', 'C9'):
    strip_fp(r)
def mv(ref, x, y, rot):
    f = b.FindFootprintByReference(ref); f.SetPosition(V(x, y)); f.SetOrientationDegrees(rot)
    print(ref, [(p.GetNumber(), p.GetNetname(), round(p.GetPosition().x / MM, 2), round(p.GetPosition().y / MM, 2)) for p in f.Pads()])
mv('C9', float(sys.argv[3]), float(sys.argv[4]), 90)
mv('R3', float(sys.argv[5]), float(sys.argv[6]), 90)
mv('C11', 48.8, 17.6, 270)
nets = {n: b.GetNetcodeFromNetname(n) for n in ('+1V1', '/VREG_LX', 'GND')}
def trk(pts, w, net, layer=pcbnew.F_Cu):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(V(*a)); t.SetEnd(V(*c)); t.SetWidth(int(w * MM)); t.SetLayer(layer)
        t.SetNetCode(nets[net]); b.Add(t)
def via(x, y, net):
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y)); v.SetWidth(int(0.45 * MM)); v.SetDrill(int(0.2 * MM))
    v.SetNetCode(nets[net]); b.Add(v)
# LX: L1 pad2 (47.25,18.0) -> U1 pin63 (47.0,20.1)
trk([(47.25, 18.2), (46.95, 18.6), (46.95, 19.45), (47.0, 19.7), (47.0, 20.1)], 0.2, '/VREG_LX')
# +1V1: L1 pad1 (47.25,16.6) -> C11 pad1 (top)
trk([(47.25, 16.8), (48.45, 16.8), (48.8, 17.12)], 0.3, '+1V1')
# C11 GND pad (bottom) -> via
trk([(48.8, 18.08), (48.8, 18.65)], 0.3, 'GND')
via(48.8, 18.65, 'GND')
b.Save(DST)
