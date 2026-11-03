import re, math, sys, os
import pcbnew
from pcbnew import FromMM as MM, ToMM, VECTOR2I, wxPoint

HERE = os.path.dirname(os.path.abspath(__file__))
NET = f'{HERE}/fc.net'
KFP = '/usr/share/kicad/footprints'
W, H, TL = 92.0, 60.0, 10.7
BODY_BOTTOM = H - TL

# ---------------- parse netlist
x = open(NET).read()
comps = {}
for m in re.finditer(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]*)"\)', x):
    comps[m.group(1)] = (m.group(2), m.group(3))
t = x[x.index('(nets'):]
nets = {}
for b in re.split(r'\n    \(net ', t)[1:]:
    name = re.match(r'\(code "\d+"\) \(name "([^"]*)"\)', b).group(1)
    nets[name] = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', b)
pin_net = {}
for n, nodes in nets.items():
    for r, p in nodes: pin_net[(r, p)] = n

# ---------------- board
bd = pcbnew.BOARD()
ds = bd.GetDesignSettings()
bd.SetCopperLayerCount(4)
try: ds.SetBoardThickness(MM(1.2))
except Exception as e: print('thickness', e)
ds.m_MinClearance = MM(0.15)
ds.m_TrackMinWidth = MM(0.15)
ds.m_ViasMinSize = MM(0.5)
ds.m_MinThroughDrill = MM(0.25)
ds.m_CopperEdgeClearance = MM(0.3)
ns = ds.m_NetSettings
dc = ns.m_DefaultNetClass
dc.SetClearance(MM(0.15)); dc.SetTrackWidth(MM(0.2)); dc.SetViaDiameter(MM(0.6)); dc.SetViaDrill(MM(0.3))
pc = pcbnew.NETCLASS('Power')
pc.SetClearance(MM(0.2)); pc.SetTrackWidth(MM(0.5)); pc.SetViaDiameter(MM(0.8)); pc.SetViaDrill(MM(0.4))
ns.m_NetClasses['Power'] = pc
for n in ('+5V', 'VSYS', '/VSYS', 'VBUS', '+3V3', '+1V1'):
    ns.m_NetClassPatternAssignments.append((pcbnew.NETCLASS_PATTERN if False else None, 'Power')) if False else None
netinfo = {}
for n in nets:
    ni = pcbnew.NETINFO_ITEM(bd, n)
    bd.Add(ni); netinfo[n] = ni
# netclass membership
for n in ('+5V', '/VSYS', 'VBUS', '+3V3', '+1V1'):
    if n in netinfo:
        try: netinfo[n].SetNetClass(pc)
        except Exception as e: print('netclass', e)

def load_fp(fpid):
    lib, name = fpid.split(':')
    path = f'{HERE}/{lib}.pretty' if os.path.isdir(f'{HERE}/{lib}.pretty') else f'{KFP}/{lib}.pretty'
    fp = pcbnew.FootprintLoad(path, name)
    assert fp, fpid
    return fp

F = {}
for ref, (val, fpid) in sorted(comps.items()):
    fp = load_fp(fpid)
    fp.SetReference(ref); fp.SetValue(val)
    for pad in fp.Pads():
        n = pin_net.get((ref, pad.GetNumber()))
        if n: pad.SetNet(netinfo[n])
    bd.Add(fp); F[ref] = fp

def at(ref, xm, ym, rot=0):
    fp = F[ref]
    fp.SetPosition(VECTOR2I(MM(xm), MM(ym)))
    fp.SetOrientationDegrees(rot)

def padpos(ref, num):
    for p in F[ref].Pads():
        if p.GetNumber() == num:
            pos = p.GetPosition(); return ToMM(pos.x), ToMM(pos.y)
    raise KeyError((ref, num))

def bbox(ref, margin=0.25):
    b = F[ref].GetBoundingBox(False, False)
    return (ToMM(b.GetX()) - margin, ToMM(b.GetY()) - margin, ToMM(b.GetRight()) + margin, ToMM(b.GetBottom()) + margin)
placed = set()
def overlaps(ref):
    a = bbox(ref)
    for o in placed:
        if o == ref: continue
        b = bbox(o)
        if a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]: return True
    return False
def inside(ref):
    a = bbox(ref, 0)
    return a[0] >= 1.0 and a[2] <= W - 1.0 and a[1] >= 4.8 and a[3] <= BODY_BOTTOM - 1.0
def fixed(ref, xm, ym, rot=0):
    at(ref, xm, ym, rot); placed.add(ref)
def near(ref, anchor, rot=0, pref=(0, 1), rmax=30):
    ax, ay = anchor
    for rr in [i * 0.5 for i in range(0, int(rmax * 2))]:
        for k in range(0, 24):
            ang = math.atan2(pref[1], pref[0]) + (k // 2 + 1) * (math.pi / 12) * (1 if k % 2 == 0 else -1) if k else math.atan2(pref[1], pref[0])
            at(ref, ax + rr * math.cos(ang), ay + rr * math.sin(ang), rot)
            if inside(ref) and not overlaps(ref):
                placed.add(ref); return
    print('FAILED to place', ref); placed.add(ref)

# ---------------- fixed placement
fixed('J10', W / 2, BODY_BOTTOM, 0)
fixed('J11', W / 2, 0.0, 0)
fixed('U1', 44, 25)
fixed('U3', 68, 12)
fixed('U4', 68, 26)
fixed('J13', 14.5, 17, 270)      # microSD, opening toward left edge
fixed('J12', W - 4.3, 15, 90)    # USB-C, opening toward right edge
fixed('J14', 86.5, 27, 0)
fixed('J4', 7, 46, 0)
fixed('SW1', 6, 31, 0)
fixed('SW2', 6, 38, 0)
fixed('Y1', 26, 30, 0)
fixed('L1', 26, 21, 0)
fixed('U10', 18, 42); fixed('U11', 31, 42); fixed('U12', 44, 42); fixed('U13', 57, 42)
fixed('U14', 70, 42); fixed('U15', 80, 42)
fixed('U16', 76, 20)
fixed('D10', 62, 33); fixed('D11', 78, 7)
for r in placed: 
    b = bbox(r, 0); print(r, [round(v,1) for v in b])

# ---------------- passives near anchors
def anchor_of(ref):
    """anchor = pad of the IC (or connector) this passive talks to"""
    return None
ANCH = {
    'C30': ('U10', '20'), 'C31': ('U11', '20'), 'C32': ('U12', '20'), 'C33': ('U13', '20'), 'C34': ('U14', '14'), 'C35': ('U15', '14'),
    'C36': ('U16', '1'), 'C37': ('U16', '5'), 'C38': ('D10', '2'), 'C39': ('D11', '2'), 'C40': ('J13', '4'), 'C41': ('J13', '4'),
    'R40': ('J12', 'A5'), 'R41': ('J12', 'B5'), 'R38': ('U14', '10'), 'R39': ('U14', '10'),
    'R42': ('U1', '49'), 'R43': ('U1', '49'), 'R44': ('U1', '46'), 'D12': ('U1', '46'),
    'R45': ('J13', '2'), 'R46': ('J13', '2'), 'R47': ('J13', '2'), 'R48': ('J13', '7'), 'R49': ('J13', '3'), 'R50': ('J13', '10'),
}
for i in range(8): ANCH[f'R{30+i}'] = ('U13', str(2 + i))
for i, tp in enumerate(['TP1', 'TP2', 'TP3', 'TP4', 'TP5', 'TP6', 'TP7', 'TP8']):
    ANCH[tp] = ('U14', '8')
# official passives: attach to U1 pad (signal net) or U3 pad
upad_by_net = {}
for (r, p), n in pin_net.items():
    if r == 'U1': upad_by_net.setdefault(n, []).append(p)
pwr_nets = {'GND', '+3V3', '+5V', '+1V1', 'VBUS', '/VSYS'}
auto = [r for r in comps if r not in placed and r not in ANCH and r[0] in 'RCLYD']
ring = {'+3V3': [p for p in upad_by_net.get('+3V3', [])], '+1V1': upad_by_net.get('+1V1', [])}
ci = {'+3V3': 0, '+1V1': 0}
for r in sorted(auto, key=lambda s: (s[0], int(re.sub(r'\D', '', s) or 0))):
    nlist = [pin_net.get((r, '1')), pin_net.get((r, '2'))]
    ref_ic = None; pad = None
    for n in nlist:
        if n and n not in pwr_nets:
            for (rr, pp), nn in pin_net.items():
                if nn == n and rr in ('U1', 'U3', 'U4') and rr != r:
                    ref_ic, pad = rr, pp
            if ref_ic: break
    if not ref_ic:
        for n in nlist:
            if n in ring and ring[n]:
                pad = ring[n][ci[n] % len(ring[n])]; ci[n] += 1; ref_ic = 'U1'; break
    if not ref_ic:
        ref_ic, pad = 'U1', ring['+3V3'][0]
    ANCH[r] = (ref_ic, pad)
order = sorted(ANCH, key=lambda s: (s[0] != 'C', s))
for r in sorted(ANCH, key=lambda s: (0 if s.startswith(('C3', 'C4', 'R3', 'R4', 'TP')) else 1, s)):
    ic, pad = ANCH[r]
    ax_, ay_ = padpos(ic, pad)
    cx, cy = ToMM(F[ic].GetPosition().x), ToMM(F[ic].GetPosition().y)
    d = (ax_ - cx, ay_ - cy); L = math.hypot(*d) or 1
    near(r, (ax_, ay_), 90 if r[0] in 'RC' else 0, pref=(d[0] / L, d[1] / L))

# ---------------- outline
def line(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(bd); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(VECTOR2I(MM(x1), MM(y1))); s.SetEnd(VECTOR2I(MM(x2), MM(y2)))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); bd.Add(s)
tx0, tx1 = W / 2 - 39.2, W / 2 + 39.2
pts = [(0, 0), (W, 0), (W, BODY_BOTTOM), (tx1, BODY_BOTTOM), (tx1, H), (tx0, H), (tx0, BODY_BOTTOM), (0, BODY_BOTTOM)]
for i in range(len(pts)):
    a, b = pts[i], pts[(i + 1) % len(pts)]
    line(a[0], a[1], b[0], b[1])

# ---------------- zones: GND on In1, +3V3 on In2 ; GND on F/B fills
def zone(layer, net, poly):
    z = pcbnew.ZONE(bd); z.SetLayer(layer); z.SetNet(netinfo[net])
    z.SetMinThickness(MM(0.2)); z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.3))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetLocalClearance(MM(0.2))
    ol = z.Outline(); ol.NewOutline()
    for (px, py) in poly: ol.Append(MM(px), MM(py))
    bd.Add(z); return z
poly = [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, BODY_BOTTOM - 0.3), (0.3, BODY_BOTTOM - 0.3)]
zone(pcbnew.In1_Cu, 'GND', poly)
zone(pcbnew.In2_Cu, '+3V3', poly)
zone(pcbnew.B_Cu, 'GND', poly)

pcbnew.SaveBoard(f'{HERE}/FC-EXPSYNTH.kicad_pcb', bd)
print('saved; footprints', len(F))
