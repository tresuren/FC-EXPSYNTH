#!/bin/bash
# RevE5 board build: placement -> project rules -> PPU lanes   (run from the RevE5 folder)
set -e
cp FC-EXPSYNTH.kicad_pro /tmp/_pro_keep.json
python3 scripts/build_pcb.py | grep -v leak | tail -1
cp /tmp/_pro_keep.json FC-EXPSYNTH.kicad_pro     # SaveBoard rewrites the .kicad_pro: keep our rules/netclasses
python3 scripts/ppu_lanes.py FC-EXPSYNTH.kicad_pcb | grep -v leak
[ "${XTAL_LANES:-0}" = 1 ] && python3 scripts/xtal_lanes.py FC-EXPSYNTH.kicad_pcb | grep -v leak | tail -1 || true
