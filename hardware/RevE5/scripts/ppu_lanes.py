"""RevE5: pre-route the 27 PPU pass-through nets J10 <-> J11 as locked straight lanes on B.Cu.
F-side pins (17-29): F stub from the finger up to a via above the finger band, B lane at x-0.6, via below the J11 pads, F stub into the J11 pad.
B-side pins (47-60): B stub, jog to x+0.6, B lane, jog back into the J11 pad.
usage: ppu_lanes.py board.kicad_pcb  (in place)"""
import sys, pcbnew
from pcbnew import FromMM as MM, VECTOR2I
P = sys.argv[1]
b = pcbnew.LoadBoard(P)
W = 0.15                     # lane width
Y_VIA_BOT, Y_JOG_BOT = 68.3, 68.9   # vias stay above the NOVIA_FINGERS keep-out (y >= 68.8)
Y_VIA_TOP, Y_JOG_TOP = 5.6, 4.9     # and below NOVIA_TOP_PADS (y < 4.8)
Y_FINGER, Y_SLOT = 72.8, 2.6        # stub ends inside the finger / slot pads
j10 = b.FindFootprintByReference('J10'); j11 = b.FindFootprintByReference('J11')
def pad(fp, num): return [p for p in fp.Pads() if p.GetNumber() == str(num)][0]
def trk(pts, layer, net):
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(MM(x1), MM(y1))); t.SetEnd(VECTOR2I(MM(x2), MM(y2)))
        t.SetWidth(MM(W)); t.SetLayer(layer); t.SetNet(net); t.SetLocked(True); b.Add(t)
def via(x, y, net):
    v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(MM(x), MM(y))); v.SetWidth(MM(0.45)); v.SetDrill(MM(0.2))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net); v.SetLocked(True); b.Add(v)
n = 0
for num in list(range(17, 30)) + list(range(47, 61)):
    p10, p11 = pad(j10, num), pad(j11, num)
    net = p10.GetNet()
    assert net.GetNetname() == p11.GetNetname() and 'PPU' in net.GetNetname() or 'CIRAM' in net.GetNetname(), (num, net.GetNetname())
    x = p10.GetPosition().x / 1e6
    assert abs(x - p11.GetPosition().x / 1e6) < 0.01, num
    if num <= 30:      # F side
        xl = x - 0.6
        trk([(x, Y_FINGER), (x, Y_JOG_BOT), (xl, Y_VIA_BOT)], pcbnew.F_Cu, net)
        via(xl, Y_VIA_BOT, net)
        trk([(xl, Y_VIA_BOT), (xl, Y_VIA_TOP)], pcbnew.B_Cu, net)
        via(xl, Y_VIA_TOP, net)
        trk([(xl, Y_VIA_TOP), (x, Y_JOG_TOP), (x, Y_SLOT)], pcbnew.F_Cu, net)
    else:              # B side
        xr = x + 0.6
        mid = [(xr, Y_VIA_BOT), (xr, Y_VIA_TOP)]
        if num == 60:   # detour left of the USB-C shell tabs (J12 S1 at x~84.6, y 10.7 / 19.3)
            mid = [(xr, Y_VIA_BOT), (xr, 22.0), (82.1, 21.4), (82.1, 8.6), (xr, 8.0), (xr, Y_VIA_TOP)]
        trk([(x, Y_FINGER), (x, Y_JOG_BOT)] + mid + [(x, Y_JOG_TOP), (x, Y_SLOT)], pcbnew.B_Cu, net)
    n += 1
b.Save(P)
print('lanes', n)
