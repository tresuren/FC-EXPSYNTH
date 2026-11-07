"""Move L1 next to U1 pin 63 and strip the tracks that need re-routing."""
import sys, pcbnew
from collections import defaultdict
SRC, DST = sys.argv[1], sys.argv[2]
LX, LY, ROT = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
C11 = sys.argv[6] if len(sys.argv) > 6 else None   # "x,y,rot"
MM = 1e6; mm = lambda v: v / MM
b = pcbnew.LoadBoard(SRC)

def key(p): return (round(p.x / 1000), round(p.y / 1000))   # um

def pad_hit(net, p):
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == net and pad.HitTest(p):
                return True
    return False

def prune(net, seeds):
    """remove tracks of net that start from seed points, walking along until a junction/pad."""
    removed = 0
    frontier = set(seeds)
    while frontier:
        pt = frontier.pop()
        for t in list(b.GetTracks()):
            if t.GetNetname() != net: continue
            if t.GetClass() == 'PCB_VIA':
                if key(t.GetPosition()) == pt:
                    b.RemoveNative(t); removed += 1
                    frontier.add(pt)
                continue
            ends = [key(t.GetStart()), key(t.GetEnd())]
            if pt in ends:
                other = t.GetEnd() if ends[0] == pt else t.GetStart()
                b.RemoveNative(t); removed += 1
                # continue if the other end is now a dead end (degree 0, not on a pad)
                ok = key(other)
                deg = 0
                for u in b.GetTracks():
                    if u.GetNetname() != net: continue
                    if u.GetClass() == 'PCB_VIA':
                        if key(u.GetPosition()) == ok: deg += 1
                    elif ok in (key(u.GetStart()), key(u.GetEnd())): deg += 1
                if deg <= 1 and not pad_hit(net, other):
                    frontier.add(ok)
    return removed

l1 = b.FindFootprintByReference('L1')
old1 = [p.GetPosition() for p in l1.Pads() if p.GetNumber() == '1'][0]
# 1. all VREG_LX copper
n = 0
for t in list(b.GetTracks()):
    if t.GetNetname() == '/VREG_LX':
        b.RemoveNative(t); n += 1
print('removed LX', n)
# 2. +1V1 chain from old L1 pad 1
print('removed +1V1 chain', prune('+1V1', {key(old1)}))
# 3. tracks touching C11 pads and VREG_AVDD between pin 61 and R3 (re-route)
c11 = b.FindFootprintByReference('C11')
for p in c11.Pads():
    print('C11 pad', p.GetNumber(), p.GetNetname(), prune(p.GetNetname(), {key(p.GetPosition())}) if p.GetNetname() != 'GND' else 'gnd-skip')
u1 = b.FindFootprintByReference('U1')
p61 = [p for p in u1.Pads() if p.GetNumber() == '61'][0]
print('AVDD', prune('/VREG_AVDD', {key(p61.GetPosition())}))
# GND tracks/vias on C11 GND pad
for p in c11.Pads():
    if p.GetNetname() == 'GND':
        for t in list(b.GetTracks()):
            if t.GetNetname() != 'GND': continue
            if t.GetClass() == 'PCB_VIA':
                if p.HitTest(t.GetPosition()) or (t.GetPosition() - p.GetPosition()).EuclideanNorm() < 600000: b.RemoveNative(t)
            elif p.HitTest(t.GetStart()) or p.HitTest(t.GetEnd()):
                b.RemoveNative(t)
# 4. move parts
l1.SetPosition(pcbnew.VECTOR2I(int(LX * MM), int(LY * MM)))
l1.SetOrientationDegrees(ROT)
if C11:
    x, y, r = map(float, C11.split(','))
    c11.SetPosition(pcbnew.VECTOR2I(int(x * MM), int(y * MM)))
    c11.SetOrientationDegrees(r)
for p in l1.Pads():
    print('L1 pad', p.GetNumber(), p.GetNetname(), mm(p.GetPosition().x), mm(p.GetPosition().y))
for p in c11.Pads():
    print('C11 pad', p.GetNumber(), p.GetNetname(), mm(p.GetPosition().x), mm(p.GetPosition().y))
b.Save(DST)
