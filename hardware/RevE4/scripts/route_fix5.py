#!/usr/bin/env python3
"""Rip-up & reroute fixer: grid A* on F.Cu/In2.Cu/B.Cu with through vias.
usage: route_fix2.py dir   (dir has FC-EXPSYNTH.kicad_pcb + .kicad_pro; writes dir/out.kicad_pcb)"""
import sys, os, re, math, heapq, numpy as np
import pcbnew
from PIL import Image, ImageDraw
mm = pcbnew.ToMM; MM = pcbnew.FromMM
D = sys.argv[1]
S = 20; CLR = 0.103; TW = 0.10; VD, VH = 0.45, 0.20
HARD = os.environ.get('HARD') == '1'
VIA_COST = 40; SOFT = 4
LAY = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]; LNAME = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
bd = pcbnew.LoadBoard(f'{D}/FC-EXPSYNTH.kicad_pcb')
bb = bd.GetBoardEdgesBoundingBox()
NX, NY = int(mm(bb.GetRight()) * S) + 2, int(mm(bb.GetBottom()) * S) + 2
BODY_BOTTOM = 49.3
GRAVE = []
locked = set()   # uuids of tracks/vias added by this script

def uid(t):
    if t.GetClass() == 'PCB_VIA':
        q = t.GetPosition(); return ('v', q.x, q.y)
    a, b = t.GetStart(), t.GetEnd(); return ('t', t.GetLayer(), a.x, a.y, b.x, b.y)

def seg(draw, p1, p2, half):
    (x1, y1), (x2, y2) = p1, p2
    dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy)
    if L > 1e-9:
        nx, ny = -dy / L * half, dx / L * half
        draw.polygon([((x1 + nx) * S, (y1 + ny) * S), ((x2 + nx) * S, (y2 + ny) * S), ((x2 - nx) * S, (y2 - ny) * S), ((x1 - nx) * S, (y1 - ny) * S)], fill=255)
    for (cx, cy) in ((x1, y1), (x2, y2)):
        draw.ellipse([(cx - half) * S, (cy - half) * S, (cx + half) * S, (cy + half) * S], fill=255)

def build(net):
    """returns blk[l], soft[l], vblk, vsoft  (numpy bool [y,x])"""
    I = lambda: Image.new('L', (NX, NY), 0)
    hard = [I() for _ in LAY]; sft = [I() for _ in LAY]; vh = I(); vs = I()
    dh = [ImageDraw.Draw(i) for i in hard]; ds = [ImageDraw.Draw(i) for i in sft]; dvh = ImageDraw.Draw(vh); dvs = ImageDraw.Draw(vs)
    ti = TW / 2 + CLR; vi = VD / 2 + CLR
    for t in bd.GetTracks():
        if t.GetNetCode() == net: continue
        if t.GetClass() == 'PCB_VIA':
            q = t.GetPosition(); c = (mm(q.x), mm(q.y)); r = mm(t.GetWidth()) / 2
            for d in dh: seg(d, c, c, r + ti)
            seg(dvh, c, c, r + vi)
        else:
            if t.GetLayer() not in LAY: continue
            li = LAY.index(t.GetLayer())
            a = (mm(t.GetStart().x), mm(t.GetStart().y)); b = (mm(t.GetEnd().x), mm(t.GetEnd().y)); w = mm(t.GetWidth()) / 2
            if HARD or uid(t) in locked:
                seg(dh[li], a, b, w + ti); seg(dvh, a, b, w + vi)
            else:
                seg(ds[li], a, b, w + ti); seg(dvs, a, b, w + vi)
    for f in bd.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() == net: continue
            b = p.GetBoundingBox()
            x0, y0, x1, y1 = mm(b.GetLeft()), mm(b.GetTop()), mm(b.GetRight()), mm(b.GetBottom())
            for li, L in enumerate(LAY):
                if p.IsOnLayer(L) or p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    dh[li].rectangle([(x0 - ti) * S, (y0 - ti) * S, (x1 + ti) * S - 1, (y1 + ti) * S - 1], fill=255)
            dvh.rectangle([(x0 - vi) * S, (y0 - vi) * S, (x1 + vi) * S - 1, (y1 + vi) * S - 1], fill=255)
    for z in bd.Zones():
        if not z.GetIsRuleArea(): continue
        ol = z.Outline().COutline(0)
        pts = [(mm(ol.CPoint(k).x) * S, mm(ol.CPoint(k).y) * S) for k in range(ol.PointCount())]
        if z.GetDoNotAllowVias(): dvh.polygon(pts, fill=255)
        if z.GetDoNotAllowTracks():
            for li, L in enumerate(LAY):
                if z.GetLayerSet().Contains(L): dh[li].polygon(pts, fill=255)
    for f in bd.GetFootprints():
        for z in f.Zones():
            if not z.GetIsRuleArea(): continue
            ol = z.Outline().COutline(0)
            pts = [(mm(ol.CPoint(k).x) * S, mm(ol.CPoint(k).y) * S) for k in range(ol.PointCount())]
            if z.GetDoNotAllowVias(): dvh.polygon(pts, fill=255)
            if z.GetDoNotAllowTracks():
                for li, L in enumerate(LAY):
                    if z.GetLayerSet().Contains(L): dh[li].polygon(pts, fill=255)
    m = 0.45 * S
    for im in hard + [vh]:
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, NX, m], fill=255); d.rectangle([0, 0, m, NY], fill=255); d.rectangle([NX - m, 0, NX, NY], fill=255)
        d.rectangle([0, (BODY_BOTTOM - 0.4) * S, NX, NY], fill=255)
    blk = np.stack([np.array(i) != 0 for i in hard]); soft = np.stack([np.array(i) != 0 for i in sft]); soft &= ~blk
    # own pads / own tracks are free
    for f in bd.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() != net: continue
            b = p.GetBoundingBox()
            xa, xb = int(math.ceil((mm(b.GetLeft()) + TW / 2) * S)), int(math.floor((mm(b.GetRight()) - TW / 2) * S))
            ya, yb = int(math.ceil((mm(b.GetTop()) + TW / 2) * S)), int(math.floor((mm(b.GetBottom()) - TW / 2) * S))
            for li, L in enumerate(LAY):
                if p.IsOnLayer(L): blk[li, ya:yb + 1, xa:xb + 1] = False; soft[li, ya:yb + 1, xa:xb + 1] = False
    return blk, soft, np.array(vh) != 0, (np.array(vs) != 0)

def astar(blk, soft, vblk, vsoft, l0, s, l1, g, margin):
    sx, sy = int(math.floor(s[0] * S)), int(math.floor(s[1] * S)); gx, gy = int(math.floor(g[0] * S)), int(math.floor(g[1] * S))
    x0 = max(0, min(sx, gx) - int(margin * S)); x1 = min(NX - 1, max(sx, gx) + int(margin * S))
    y0 = max(0, min(sy, gy) - int(margin * S)); y1 = min(NY - 1, max(sy, gy) + int(margin * S))
    start = (l0, sx, sy); goal = (l1, gx, gy)
    h = lambda x, y: max(abs(x - gx), abs(y - gy)) + 0.414 * min(abs(x - gx), abs(y - gy))
    pq = [(h(sx, sy), 0.0, start)]; came = {start: None}; gs = {start: 0.0}
    N8 = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    while pq:
        f, g0, cur = heapq.heappop(pq)
        if g0 > gs.get(cur, 1e18) + 1e-9: continue
        if cur == goal:
            path = []
            while cur is not None: path.append(cur); cur = came[cur]
            return path[::-1]
        l, x, y = cur
        for dx, dy, c in N8:
            nx, ny = x + dx, y + dy
            if nx < x0 or nx > x1 or ny < y0 or ny > y1: continue
            if blk[l, ny, nx] and not ((nx, ny) == (gx, gy) and l == l1): continue
            ng = g0 + c + (SOFT * c if soft[l, ny, nx] else 0)
            nn = (l, nx, ny)
            if ng < gs.get(nn, 1e18): gs[nn] = ng; came[nn] = cur; heapq.heappush(pq, (ng + h(nx, ny), ng, nn))
        if not vblk[y, x]:
            for l2 in range(len(LAY)):
                if l2 == l or blk[l2, y, x]: continue
                ng = g0 + VIA_COST + (30 if vsoft[y, x] else 0)
                nn = (l2, x, y)
                if ng < gs.get(nn, 1e18): gs[nn] = ng; came[nn] = cur; heapq.heappush(pq, (ng + h(x, y), ng, nn))
    return None

def dist_pt_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy or 1e-12
    u = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2)); return math.hypot(px - ax - u * dx, py - ay - u * dy)

def rip(net, segs, vias):
    """delete other-net unlocked tracks that violate clearance with new geometry"""
    kill = []
    for t in list(bd.GetTracks()):
        if t.GetNetCode() == net or uid(t) in locked: continue
        if t.GetClass() == 'PCB_VIA': continue
        if t.GetLayer() not in LAY: continue
        li = LAY.index(t.GetLayer()); w = mm(t.GetWidth()) / 2
        a = (mm(t.GetStart().x), mm(t.GetStart().y)); b = (mm(t.GetEnd().x), mm(t.GetEnd().y))
        hit = False
        for (sl, p, q) in segs:
            if sl != li: continue
            n = max(2, int(math.hypot(q[0] - p[0], q[1] - p[1]) / 0.05))
            for k in range(n + 1):
                x = p[0] + (q[0] - p[0]) * k / n; y = p[1] + (q[1] - p[1]) * k / n
                if dist_pt_seg(x, y, a[0], a[1], b[0], b[1]) < w + TW / 2 + CLR - 0.01: hit = True; break
            if hit: break
        if not hit:
            for (vx, vy) in vias:
                if dist_pt_seg(vx, vy, a[0], a[1], b[0], b[1]) < w + VD / 2 + CLR - 0.01: hit = True; break
        if hit: kill.append(t)
    for t in kill:
        bd.RemoveNative(t); GRAVE.append(t)
    return len(kill)

def commit(net, path, s, g):
    pts = [(l, (x + .5) / S, (y + .5) / S) for (l, x, y) in path]
    out = []; cur_l, cx, cy = pts[0]; sg = [tuple(s), (cx, cy)]
    for (l, x, y) in pts[1:]:
        if l != cur_l: out.append(('t', cur_l, sg)); out.append(('v', (cx, cy))); sg = [(cx, cy)]; cur_l = l
        sg.append((x, y)); cx, cy = x, y
    sg.append(tuple(g)); out.append(('t', cur_l, sg))
    segs, vias, news = [], [], []
    for it in out:
        if it[0] == 'v': vias.append(it[1])
        else:
            q = [it[2][0]]
            for i in range(1, len(it[2]) - 1):
                a, b, c = q[-1], it[2][i], it[2][i + 1]
                if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9: q.append(b)
            q.append(it[2][-1])
            for a, b in zip(q, q[1:]):
                if abs(a[0] - b[0]) + abs(a[1] - b[1]) > 1e-9: segs.append((it[1], a, b))
    nk = rip(net, segs, vias)
    for (x, y) in vias:
        v = pcbnew.PCB_VIA(bd); v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); v.SetWidth(MM(VD)); v.SetDrill(MM(VH))
        v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNetCode(net); bd.Add(v); locked.add(('v', MM(x), MM(y)))
    for (li, a, b) in segs:
        t = pcbnew.PCB_TRACK(bd); t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
        t.SetWidth(MM(TW)); t.SetLayer(LAY[li]); t.SetNetCode(net); bd.Add(t); locked.add(('t', LAY[li], MM(a[0]), MM(a[1]), MM(b[0]), MM(b[1])))
    return len(segs), len(vias), nk

# ---------- DRC -> unconnected pairs
def drc():
    for z in bd.Zones():
        if not z.GetIsRuleArea():
            try: z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
            except Exception as e: pass
    bd.BuildConnectivity()
    pcbnew.ZONE_FILLER(bd).Fill(bd.Zones())
    bd.BuildConnectivity()
    rpt = f'{D}/drc.rpt'
    pcbnew.WriteDRCReport(bd, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
    return open(rpt).read()

def cands(x, y, desc):
    m = re.match(r'(PTH )?Pad (\S+) \[([^\]]+)\] of (\S+)', desc)
    if m:
        f = bd.FindFootprintByReference(m.group(4))
        for p in f.Pads():
            if p.GetNumber() == m.group(2):
                q = p.GetPosition(); li = 0 if p.IsOnLayer(pcbnew.F_Cu) else len(LAY) - 1
                if m.group(4) == 'J10' and p.GetNumber().isdigit():
                    return m.group(3), [(0 if int(p.GetNumber()) <= 30 else len(LAY) - 1, (mm(q.x), 48.35))]
                return m.group(3), [(li, (mm(q.x), mm(q.y)))]
    best = None
    for t in bd.GetTracks():
        if t.GetNetname() not in desc: continue
        if t.GetClass() != 'PCB_VIA' and ('on ' + t.GetLayerName()) not in desc: continue
        if t.GetClass() == 'PCB_VIA':
            q = t.GetPosition(); c = [(0, (mm(q.x), mm(q.y)))]
        else:
            li = LAY.index(t.GetLayer()) if t.GetLayer() in LAY else 0
            c = [(li, (mm(t.GetStart().x), mm(t.GetStart().y))), (li, (mm(t.GetEnd().x), mm(t.GetEnd().y)))]
        d = min(math.hypot(p[0] - x, p[1] - y) for _, p in c)
        if best is None or d < best[0]: best = (d, c, t.GetNetname())
    return best[2], best[1]

def pairs(rpt):
    res = []
    for m in re.finditer(r'\[unconnected_items\][^\n]*\n[^\n]*\n\s*@\(([\d.]+) mm, ([\d.]+) mm\): ([^\n]+)\n\s*@\(([\d.]+) mm, ([\d.]+) mm\): ([^\n]+)', rpt):
        x1, y1, d1, x2, y2, d2 = m.groups()
        n, c1 = cands(float(x1), float(y1), d1); _, c2 = cands(float(x2), float(y2), d2)
        a, b = min(((a, b) for a in c1 for b in c2), key=lambda ab: math.hypot(ab[0][1][0] - ab[1][1][0], ab[0][1][1] - ab[1][1][1]))
        res.append((n, a[0], a[1], b[0], b[1], math.hypot(a[1][0] - b[1][0], a[1][1] - b[1][1])))
    return sorted(res, key=lambda r: r[5])

def summary(rpt):
    from collections import Counter
    return Counter(re.findall(r'^\[(\w+)\]', rpt, re.M))

failed = set()
for it in range(int(sys.argv[2]) if len(sys.argv) > 2 else 8):
    rpt = drc(); sm = summary(rpt)
    print(f'--- iter {it}: unconnected={sm.get("unconnected_items",0)} clearance={sm.get("clearance",0)} short={sm.get("shorting_items",0)} dangling={sm.get("track_dangling",0)}', flush=True)
    pr = [p for p in pairs(rpt)]
    if not pr: break
    for (n, l0, s, l1, g, dist) in pr:
        net = bd.GetNetcodeFromNetname(n)
        blk, soft, vblk, vsoft = build(net)
        path = None
        for mg in (6.0, 14.0, 40.0):
            path = astar(blk, soft, vblk, vsoft, l0, s, l1, g, mg)
            if path: break
        if not path: print(f'  {n} {s}->{g}: NO PATH', flush=True); continue
        ns, nv, nk = commit(net, path, s, g)
        print(f'  {n} ({s[0]:.2f},{s[1]:.2f})->({g[0]:.2f},{g[1]:.2f}): {ns} segs {nv} vias, ripped {nk}', flush=True)
rpt = drc(); sm = summary(rpt)
print('FINAL', dict(sm))
pcbnew.SaveBoard(f'{D}/out.kicad_pcb', bd)
