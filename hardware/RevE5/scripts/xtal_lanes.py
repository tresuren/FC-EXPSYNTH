"""RevE5 (pre-route, locked): compact crystal block right under U1 XIN/XOUT (pins 30/31) and hand-route it.
Removes the autorouted crystal nets, moves Y1/C3/C4/R2, adds short tracks + GND vias, rips other-net F.Cu copper that
collides with the new copper (route_fix6.py reconnects those afterwards).
usage: xtal_fix.py in.kicad_pcb out.kicad_pcb"""
import sys, pcbnew
from pcbnew import FromMM as MM, VECTOR2I
from shapely.geometry import LineString, Point, Polygon
SRC = DST = sys.argv[1]
b = pcbnew.LoadBoard(SRC)
CL = 0.11
XN = ('/XIN', '/XOUT', 'Net-(C4-Pad1)')
def mv(ref, x, y, rot):
    f = b.FindFootprintByReference(ref); f.SetPosition(VECTOR2I(MM(x), MM(y))); f.SetOrientationDegrees(rot); return f
parts = [mv('Y1', 44.0, 33.8, 270), mv('C3', 41.6, 32.9, 270), mv('R2', 46.25, 32.1, 270), mv('C4', 46.25, 35.7, 270)]
for f in parts:
    print(f.GetReference(), [(p.GetNumber(), p.GetNetname(), round(p.GetPosition().x / 1e6, 2), round(p.GetPosition().y / 1e6, 2)) for p in f.Pads()])
net = lambda n: b.GetNetcodeFromNetname(n)
new = []   # (shapely geom, layerset, netcode)
def trk(pts, w, n, layer=pcbnew.F_Cu):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(MM(x1), MM(y1))); t.SetEnd(VECTOR2I(MM(x2), MM(y2)))
        t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNetCode(net(n)); t.SetLocked(True); b.Add(t)
        new.append((LineString([(x1, y1), (x2, y2)]).buffer(w / 2), {layer}, net(n)))
def via(x, y, n):
    v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(MM(x), MM(y))); v.SetWidth(MM(0.45)); v.SetDrill(MM(0.2))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(net(n)); v.SetLocked(True); b.Add(v)
    new.append((Point(x, y).buffer(0.225), {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}, net(n)))
# XIN: pin30 -> Y1 pad1 (43.15,32.7) -> C3 pad1 (41.6,32.42)
trk([(43.8, 30.1), (43.8, 31.3), (43.4, 31.7), (43.4, 32.2)], 0.15, '/XIN')
trk([(42.7, 32.42), (41.6, 32.42)], 0.15, '/XIN')
# XOUT: pin31 -> R2 pad1 (46.25,31.62)
trk([(44.2, 30.1), (44.2, 30.6), (44.6, 31.0), (45.95, 31.0), (46.25, 31.3), (46.25, 31.62)], 0.15, '/XOUT')
# R2 pad2 (46.0,32.58) -> C4 pad1 (46.0,35.22), branch to Y1 pad3 (44.85,34.9)
trk([(46.25, 32.58), (46.25, 35.22)], 0.15, 'Net-(C4-Pad1)')
trk([(46.25, 34.6), (45.95, 34.9), (45.2, 34.9)], 0.15, 'Net-(C4-Pad1)')
# GND: Y1 pad2 (43.15,34.9) and pad4 (44.85,32.7), C3 pad2 (41.6,33.38), C4 pad2 (46.0,36.18)
trk([(43.15, 35.4), (43.15, 36.05)], 0.25, 'GND'); via(43.15, 36.05, 'GND')
trk([(44.85, 32.1), (44.85, 31.6)], 0.25, 'GND'); via(44.85, 31.6, 'GND')
trk([(41.6, 33.6), (41.6, 34.1)], 0.25, 'GND'); via(41.6, 34.1, 'GND')
trk([(46.25, 36.4), (46.25, 36.85)], 0.25, 'GND'); via(46.25, 36.85, 'GND')
b.Save(DST)
