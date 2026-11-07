"""BOM.csv from the board (group by value + footprint). usage: make_bom.py (run in the RevE5 folder)"""
import pcbnew, re, csv, collections
b = pcbnew.LoadBoard('FC-EXPSYNTH.kicad_pcb')
g = collections.defaultdict(list)
for f in b.GetFootprints():
    g[(f.GetValue(), f.GetFPID().GetLibItemName().wx_str())].append(f.GetReference())
key = lambda r: (re.sub(r'\d', '', r), int(re.sub(r'\D', '', r) or 0))
rows = sorted(g.items(), key=lambda kv: key(sorted(kv[1], key=key)[0]))
with open('BOM.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['Designators', 'Qty', 'Value', 'Footprint', 'MPN/LCSC (UNVERIFIED - choose yourself)'])
    for (val, fp), refs in rows:
        refs = sorted(refs, key=key)
        note = 'not assembled (pads only)' if refs[0].startswith('TP') else ('hand-solder' if refs[0] in ('J11',) else '')
        w.writerow([' '.join(refs), len(refs), val, fp, note])
print(len(rows), 'lines', sum(len(r) for r in g.values()), 'parts')
