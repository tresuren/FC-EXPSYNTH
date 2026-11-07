import sys, pcbnew
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

SRC, DST = sys.argv[1], sys.argv[2]
NETS = sys.argv[3].split(',')
WIDTHS = [float(x) for x in sys.argv[4].split(',')]
CLR = 0.1 + 0.012      # copper clearance + margin
HCLR = 0.2 + 0.012     # hole clearance
ECLR = 0.3 + 0.012     # copper-edge clearance
MM = 1e6

b = pcbnew.LoadBoard(SRC)
cu = list(b.GetEnabledLayers().CuStack())

def sps_to_shapely(sps):
    polys = []
    for i in range(sps.OutlineCount()):
        o = sps.Outline(i)
        pts = [(o.CPoint(j).x / MM, o.CPoint(j).y / MM) for j in range(o.PointCount())]
        if len(pts) >= 3:
            polys.append(Polygon(pts).buffer(0))
    from shapely.ops import unary_union
    return unary_union(polys)

# obstacle items: (geom, halfwidth, net, layer)
items = []
tracks = []
holes = []   # (geom(point), radius, net)
for t in b.GetTracks():
    cls = t.GetClass()
    if cls == 'PCB_TRACK':
        s, e = t.GetStart(), t.GetEnd()
        g = LineString([(s.x / MM, s.y / MM), (e.x / MM, e.y / MM)]) if s != e else Point(s.x / MM, s.y / MM)
        idx = len(items)
        items.append([g, t.GetWidth() / MM / 2, t.GetNetCode(), t.GetLayer()])
        tracks.append((idx, t))
    elif cls == 'PCB_VIA':
        p = t.GetPosition()
        for L in cu:
            if t.IsOnLayer(L):
                items.append([Point(p.x / MM, p.y / MM), t.GetWidth() / MM / 2, t.GetNetCode(), L])
        holes.append((Point(p.x / MM, p.y / MM), t.GetDrillValue() / MM / 2, t.GetNetCode()))
    else:
        print('other track class', cls)
for fp in b.GetFootprints():
    for pad in fp.Pads():
        for L in cu:
            if pad.IsOnLayer(L) and pad.FlashLayer(L):
                sps = pcbnew.SHAPE_POLY_SET()
                pad.TransformShapeToPolygon(sps, L, 0, 2000)
                items.append([sps_to_shapely(sps), 0.0, pad.GetNetCode(), L])
        if pad.HasHole():
            p = pad.GetPosition()
            ds = pad.GetDrillSize()
            holes.append((Point(p.x / MM, p.y / MM), min(ds.x, ds.y) / MM / 2, pad.GetNetCode()
                          if pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH else -1))

# board outline
sps = pcbnew.SHAPE_POLY_SET()
b.GetBoardPolygonOutlines(sps)
outline = sps_to_shapely(sps)
edge = outline.boundary

# rule areas that forbid tracks
keep = []
for z in b.Zones():
    if z.GetIsRuleArea() and z.GetDoNotAllowTracks():
        g = sps_to_shapely(z.Outline())
        keep.append((g, [L for L in cu if z.IsOnLayer(L)]))

tree = STRtree([it[0] for it in items])
htree = STRtree([h[0] for h in holes])

netcodes = {b.GetNetcodeFromNetname(n): n for n in NETS}
cand = [(i, t) for i, t in tracks if t.GetNetCode() in netcodes]
cand.sort(key=lambda x: -x[1].GetLength())

def ok(i, t, hw):
    g = items[i][0]
    net, L = items[i][2], items[i][3]
    if g.distance(edge) < hw + ECLR:
        return False
    for kg, kls in keep:
        if L in kls and g.distance(kg) < hw:
            return False
    reach = hw + CLR + 0.5
    for j in tree.query(g.buffer(reach)):
        o = items[j]
        if j == i or o[3] != L or o[2] == net:
            continue
        if g.distance(o[0]) < hw + o[1] + CLR:
            return False
    for j in htree.query(g.buffer(hw + HCLR + 1.0)):
        hp, hr, hn = holes[j]
        if hn == net:
            continue
        if g.distance(hp) < hw + hr + HCLR:
            return False
    return True

stats = {}
for i, t in cand:
    old = items[i][1]
    for w in WIDTHS:
        if w / 2 <= old + 1e-9:
            break
        if ok(i, t, w / 2):
            items[i][1] = w / 2
            t.SetWidth(int(round(w * MM)))
            break
    n = netcodes[t.GetNetCode()]
    stats.setdefault(n, {}).setdefault(round(items[i][1] * 2, 3), 0)
    stats[n][round(items[i][1] * 2, 3)] += t.GetLength() / MM

for n in NETS:
    print(n, {k: round(v, 1) for k, v in sorted(stats.get(n, {}).items())})

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(DST)
