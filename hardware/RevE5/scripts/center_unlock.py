"""Final step: move the whole board to the sheet centre (same place as RevE4 in KiCad: offset 100.9843, 67.5157 mm)
and unlock every track/via/footprint so the board can be moved by hand.
All other scripts work in the origin-based coordinates, so run this LAST.
usage: center_unlock.py in.kicad_pcb out.kicad_pcb"""
import sys, pcbnew
from pcbnew import FromMM as MM, VECTOR2I
SRC, DST = sys.argv[1], sys.argv[2]
DX, DY = 100.9843, 67.5157
b = pcbnew.LoadBoard(SRC)
d = VECTOR2I(MM(DX), MM(DY))
n = 0
for t in b.GetTracks():
    t.SetLocked(False); t.Move(d); n += 1
for f in b.GetFootprints():
    f.SetLocked(False); f.Move(d); n += 1
for z in b.Zones():
    z.SetLocked(False); z.Move(d); n += 1
for g in b.GetDrawings():
    g.Move(d); n += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(DST)
print('moved', n, 'items by', DX, DY)
