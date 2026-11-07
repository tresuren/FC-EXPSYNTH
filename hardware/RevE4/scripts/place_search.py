import sys, pcbnew, math
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
SRC, REF = sys.argv[1], sys.argv[2]
TX, TY, R = map(float, sys.argv[3:6])
MM = 1e6
b = pcbnew.LoadBoard(SRC)
def poly(sps):
    ps = []
    for i in range(sps.OutlineCount()):
        o = sps.Outline(i); ps.append(Polygon([(o.CPoint(j).x / MM, o.CPoint(j).y / MM) for j in range(o.PointCount())]).buffer(0))
    return unary_union(ps)
fp = b.FindFootprintByReference(REF)
obs = []   # F.Cu copper of everything else
crt = []
for t in b.GetTracks():
    if t.IsOnLayer(pcbnew.F_Cu):
        s, e = t.GetStart(), t.GetEnd()
        w = t.GetWidth() / MM / 2
        obs.append(LineString([(s.x / MM, s.y / MM), (e.x / MM, e.y / MM)]).buffer(w) if s != e else Point(s.x / MM, s.y / MM).buffer(w))
for f in b.GetFootprints():
    if f.GetReference() == REF: continue
    for p in f.Pads():
        if p.IsOnLayer(pcbnew.F_Cu):
            s = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(s, pcbnew.F_Cu, 0, 2000); obs.append(poly(s))
    if f.GetLayer() == pcbnew.F_Cu:
        try: crt.append(poly(f.GetCourtyard(pcbnew.F_CrtYd)))
        except Exception: pass
O = unary_union(obs); C = unary_union(crt)
res = []
for rot in (0, 90, 180, 270):
    for ix in range(-int(R * 20), int(R * 20) + 1):
        for iy in range(-int(R * 20), int(R * 20) + 1):
            x, y = TX + ix * 0.05, TY + iy * 0.05
            if math.hypot(x - TX, y - TY) > R: continue
            fp.SetPosition(pcbnew.VECTOR2I(int(x * MM), int(y * MM))); fp.SetOrientationDegrees(rot)
            ok = True; pads = []
            for p in fp.Pads():
                s = pcbnew.SHAPE_POLY_SET(); p.TransformShapeToPolygon(s, pcbnew.F_Cu, 0, 2000); g = poly(s)
                if g.distance(O) < 0.15: ok = False; break
                pads.append((p.GetNetname(), p.GetPosition()))
            if not ok: continue
            cy = poly(fp.GetCourtyard(pcbnew.F_CrtYd))
            if cy.intersection(C).area > 0.01: continue
            res.append((math.hypot(x - TX, y - TY), x, y, rot, [(n, round(q.x / MM, 2), round(q.y / MM, 2)) for n, q in pads]))
res.sort()
for r in res[:15]: print(r)
print(len(res))
