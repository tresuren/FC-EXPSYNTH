# Generates FC-EXPSYNTH.kicad_sch: Raspberry Pi RP2350B minimal design (official reference, headers removed)
# + Famicom bus interface (our additions). KiCad 7 format.
import re, uuid, math, os, shutil, sys
from kiutils.schematic import Schematic

REF = '/tmp/claude-0/-home-claude/502ee83b-d9db-56cb-98b9-8c40173c48e0/scratchpad/ref/a182/RP-006442-DD-2-RP2350B Minimal Board Kicad archive'
import os
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = 'FC-EXPSYNTH'
ROOT = '94683f5c-9cd9-448e-be96-9792537b5cb8'
SYM = '/usr/share/kicad/symbols'
uid = lambda: str(uuid.uuid4())

# ---------------------------------------------------------------- 1. trim the official design
s = Schematic.from_file(f'{REF}/RP2350_80QFN_minimal.kicad_sch')
drop_refs = {'J1', 'J2', 'J3', 'U2', 'C1', 'C5', 'H1', 'H2', 'H3', 'H4'}
def sref(sym): return [p.value for p in sym.properties if p.key == 'Reference'][0]
def in_box(x, y, b): return b[0] <= x <= b[2] and b[1] <= y <= b[3]
HDR = (320, 100, 425, 200)       # J2/J3 headers
PWR = (15, 30, 100, 72)          # USB-B + NCP1117 area
boxes = [HDR, PWR]
def inb(x, y): return any(in_box(x, y, b) for b in boxes)
keep_syms = []
for sym in s.schematicSymbols:
    r = sref(sym)
    if r in drop_refs: continue
    if r.startswith('#PWR') and inb(sym.position.X, sym.position.Y): continue
    keep_syms.append(sym)
s.schematicSymbols = keep_syms
s.graphicalItems = [g for g in s.graphicalItems if not (g.type == 'wire' and all(inb(p.X, p.Y) for p in g.points))]
s.labels = [l for l in s.labels if not inb(l.position.X, l.position.Y)]
s.junctions = [j for j in s.junctions if not inb(j.position.X, j.position.Y)]
s.noConnects = [n for n in s.noConnects if not inb(n.position.X, n.position.Y)]
s.texts = [t for t in s.texts if t.text not in ('IOs', 'Power')]
s.paper.paperSize = 'A1'
s.titleBlock.title = 'FC-EXPSYNTH: Famicom expansion-audio relay cartridge (RP2350B)'
s.titleBlock.company = 'Takara (RP2350B core: Raspberry Pi Ltd minimal design REV2)'
s.titleBlock.date = '2026-11-07'
s.titleBlock.revision = 'E5'
tmp = f'{OUT}/_base.kicad_sch'
s.to_file(tmp)
txt = open(tmp, encoding='utf-8').read().replace('"RP2350_80QFN_minimal"', f'"{PROJ}"', 1) if False else open(tmp, encoding='utf-8').read()
txt = txt.replace('(project "RP2350_80QFN_minimal"', f'(project "{PROJ}"')

# ---------------------------------------------------------------- 2. library helpers
def lib_block(fn, name):
    t = open(f'{SYM}/{fn}', encoding='utf-8').read()
    i = t.index(f'  (symbol "{name}"')
    d = 0; j = i
    while True:
        c = t[j]
        if c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: break
        j += 1
    return t[i:j + 1]

def rename_top(block, lib, name):
    return block.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)

def parse_pins(block):
    pins = {}
    for m in re.finditer(r'\(pin (\w+) (\w+)\s+\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s+\(length ([\d.]+)\)(?:\s+hide)?\s+\(name "((?:[^"\\]|\\.)*)".*?\(number "([^"]*)"', block, re.S):
        pins.setdefault(m.group(8), (float(m.group(3)), float(m.group(4)), int(m.group(5)), m.group(7), m.group(1)))
    return pins

FONT = '(effects (font (size 1.27 1.27)))'
def box_symbol(lib, name, ref, left, right, top=(), bottom=(), w=15.24, pitch=2.54, plen=5.08, desc=''):
    """left/right: list of (num, name, type) top-to-bottom; top/bottom: lists left-to-right. Returns lib symbol text."""
    n = max(len(left), len(right), 1)
    h = pitch * (n + 1)
    h = math.ceil(h / 2.54) * 2.54
    if top or bottom: w = max(w, 2.54 * (max(len(top), len(bottom)) + 1))
    hw, hh = w / 2, h / 2
    pins = []
    def addp(num, nm, ty, x, y, ang):
        pins.append(f'      (pin {ty} line (at {x:.2f} {y:.2f} {ang}) (length {plen})\n        (name "{nm}" {FONT})\n        (number "{num}" {FONT}))')
    for i, (num, nm, ty) in enumerate(left):
        addp(num, nm, ty, -hw - plen, hh - pitch * (i + 1), 0)
    for i, (num, nm, ty) in enumerate(right):
        addp(num, nm, ty, hw + plen, hh - pitch * (i + 1), 180)
    for i, (num, nm, ty) in enumerate(top):
        addp(num, nm, ty, -w / 2 + 2.54 * (i + 1), hh + plen, 270)
    for i, (num, nm, ty) in enumerate(bottom):
        addp(num, nm, ty, -w / 2 + 2.54 * (i + 1), -hh - plen, 90)
    return f'''    (symbol "{lib}:{name}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
      (property "Reference" "{ref}" (at 0 {hh + plen + 2.54:.2f} 0) {FONT})
      (property "Value" "{name}" (at 0 {-hh - plen - 2.54:.2f} 0) {FONT})
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "ki_description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "{name}_0_1" (rectangle (start {-hw:.2f} {hh:.2f}) (end {hw:.2f} {-hh:.2f}) (stroke (width 0.254) (type default)) (fill (type background))))
      (symbol "{name}_1_1"
{chr(10).join(pins)}
      )
    )'''

# --- custom symbols
EDGE_NAMES = {1: 'GND', 14: 'R/W', 15: '/IRQ', 16: 'GND', 30: '+5V', 31: 'CART/5V', 32: 'M2', 44: '/ROMSEL', 45: 'AUDIO_FROM_2A03', 46: 'AUDIO_TO_RF'}
for k, nm in zip(range(2, 14), ['A11', 'A10', 'A9', 'A8', 'A7', 'A6', 'A5', 'A4', 'A3', 'A2', 'A1', 'A0']): EDGE_NAMES[k] = nm
for k, nm in zip(range(17, 30), ['PPU_/RD', 'CIRAM_A10', 'PPU_A6', 'PPU_A5', 'PPU_A4', 'PPU_A3', 'PPU_A2', 'PPU_A1', 'PPU_A0', 'PPU_D0', 'PPU_D1', 'PPU_D2', 'PPU_D3']): EDGE_NAMES[k] = nm
for k, nm in zip(range(33, 44), ['A12', 'A13', 'A14', 'D7', 'D6', 'D5', 'D4', 'D3', 'D2', 'D1', 'D0']): EDGE_NAMES[k] = nm
for k, nm in zip(range(47, 61), ['PPU_/WR', 'CIRAM_/CE', 'PPU_/A13', 'PPU_A7', 'PPU_A8', 'PPU_A9', 'PPU_A10', 'PPU_A11', 'PPU_A12', 'PPU_A13', 'PPU_D7', 'PPU_D6', 'PPU_D5', 'PPU_D4']): EDGE_NAMES[k] = nm
def edge_sym(name, ref):
    left = [(str(i), f'{i} {EDGE_NAMES[i]}', 'passive') for i in range(1, 31)]
    right = [(str(i), f'{i} {EDGE_NAMES[i]}', 'passive') for i in range(31, 61)]
    return box_symbol('FCSYNTH', name, ref, left, right, w=30.48)

SYMS = []   # custom lib symbol texts
SYMS.append(edge_sym('FC_Cart_Edge_60', 'J'))
SYMS.append(edge_sym('FC_Slot_60', 'J'))
LV = [('1', 'DIR', 'input'), ('19', '~{OE}', 'input')]
bus_b = [(str(18 - i), f'B{i+1}', 'bidirectional') for i in range(8)]
bus_a = [(str(2 + i), f'A{i+1}', 'bidirectional') for i in range(8)]
SYMS.append(box_symbol('FCSYNTH', '74x245', 'U', LV + bus_b, bus_a, top=[('20', 'VCC', 'power_in')], bottom=[('10', 'GND', 'power_in')],
                       w=15.24, desc='Octal bus transceiver 20-pin (74LVC245 / 74AHCT245)'))
SYMS.append(box_symbol('FCSYNTH', '74x32', 'U',
                       [('1', '1A', 'input'), ('2', '1B', 'input'), ('4', '2A', 'input'), ('5', '2B', 'input'), ('9', '3A', 'input'), ('10', '3B', 'input'), ('12', '4A', 'input'), ('13', '4B', 'input')],
                       [('3', '1Y', 'output'), ('6', '2Y', 'output'), ('8', '3Y', 'output'), ('11', '4Y', 'output')],
                       top=[('14', 'VCC', 'power_in')], bottom=[('7', 'GND', 'power_in')], desc='Quad 2-input OR 74HCT32'))
SYMS.append(box_symbol('FCSYNTH', '74x04', 'U',
                       [('1', '1A', 'input'), ('3', '2A', 'input'), ('5', '3A', 'input'), ('9', '4A', 'input'), ('11', '5A', 'input'), ('13', '6A', 'input')],
                       [('2', '1Y', 'output'), ('4', '2Y', 'output'), ('6', '3Y', 'output'), ('8', '4Y', 'output'), ('10', '5Y', 'output'), ('12', '6Y', 'output')],
                       top=[('14', 'VCC', 'power_in')], bottom=[('7', 'GND', 'power_in')], desc='Hex inverter 74HC04'))
SYMS.append(box_symbol('FCSYNTH', '74x1G02', 'U', [('1', 'A', 'input'), ('2', 'B', 'input')], [('4', 'Y', 'output')],
                       top=[('5', 'VCC', 'power_in')], bottom=[('3', 'GND', 'power_in')], w=10.16, desc='Single 2-input NOR SOT-23-5'))
SYMS.append(box_symbol('FCSYNTH', 'AP2112K-3.3', 'U', [('1', 'VIN', 'power_in'), ('3', 'EN', 'input')], [('5', 'VOUT', 'power_out'), ('4', 'NC', 'no_connect')],
                       bottom=[('2', 'GND', 'power_in')], w=12.7, desc='600mA LDO 3.3V SOT-23-5'))
SYMS.append(box_symbol('FCSYNTH', 'microSD', 'J',
                       [('1', 'DAT2', 'passive'), ('2', 'DAT3/CS', 'passive'), ('3', 'CMD/MOSI', 'passive'), ('4', 'VDD', 'passive'), ('5', 'CLK', 'passive'),
                        ('6', 'VSS', 'passive'), ('7', 'DAT0/MISO', 'passive'), ('8', 'DAT1', 'passive'), ('9', 'DET_B', 'passive'), ('10', 'DET_A', 'passive'), ('11', 'SHIELD', 'passive')],
                       [], w=15.24, desc='microSD socket (Hirose DM3AT-SF-PEJM5 pin numbering)'))
SYMS.append(box_symbol('FCSYNTH', 'USB_C_16P', 'J',
                       [('A1', 'GND', 'passive'), ('A12', 'GND', 'passive'), ('B1', 'GND', 'passive'), ('B12', 'GND', 'passive'), ('S1', 'SHIELD', 'passive'),
                        ('A4', 'VBUS', 'passive'), ('A9', 'VBUS', 'passive'), ('B4', 'VBUS', 'passive'), ('B9', 'VBUS', 'passive')],
                       [('A5', 'CC1', 'passive'), ('B5', 'CC2', 'passive'), ('A6', 'D+', 'passive'), ('B6', 'D+', 'passive'), ('A7', 'D-', 'passive'), ('B7', 'D-', 'passive'),
                        ('A8', 'SBU1', 'passive'), ('B8', 'SBU2', 'passive')], w=15.24, desc='USB-C receptacle 16P (HRO TYPE-C-31-M-12)'))
SYMS.append(box_symbol('FCSYNTH', 'Conn_2x08', 'J', [(str(i), f'{i}', 'passive') for i in range(1, 17, 2)], [(str(i), f'{i}', 'passive') for i in range(2, 17, 2)], w=10.16))
SYMS.append(box_symbol('FCSYNTH', 'Conn_2x04', 'J', [(str(i), f'{i}', 'passive') for i in range(1, 9, 2)], [(str(i), f'{i}', 'passive') for i in range(2, 9, 2)], w=10.16))
# stock symbols (no "extends")
STOCK = [('Device.kicad_sym', 'Device', 'LED'), ('Device.kicad_sym', 'Device', 'D_Schottky'), ('power.kicad_sym', 'power', '+5V'),
         ('power.kicad_sym', 'power', 'PWR_FLAG'), ('power.kicad_sym', 'power', 'VBUS'), ('Connector.kicad_sym', 'Connector', 'TestPoint')]
stock_txt = []
PIN = {}     # lib_id -> {num: (x,y,angle,name,type)}
for fn, lib, nm in STOCK:
    b = lib_block(fn, nm)
    assert 'extends' not in b, nm
    stock_txt.append(rename_top(b, lib, nm))
    PIN[f'{lib}:{nm}'] = parse_pins(b)
for lib, nm in [('Device', 'R'), ('Device', 'C'), ('power', 'GND'), ('power', '+3V3')]:
    PIN[f'{lib}:{nm}'] = parse_pins(lib_block('Device.kicad_sym' if lib == 'Device' else 'power.kicad_sym', nm))
for sym_txt in SYMS:
    name = re.match(r'\s*\(symbol "FCSYNTH:([^"]+)"', sym_txt).group(1)
    PIN[f'FCSYNTH:{name}'] = parse_pins(sym_txt)

# ---------------------------------------------------------------- 3. placement helpers
items = []     # schematic body texts
refcount = {'U': 9, 'J': 9, 'R': 29, 'C': 29, 'D': 9}
pwrn = [100]
def rot_pt(sx, sy, th):
    th %= 360
    if th == 0: return sx, sy
    if th == 90: return sy, -sx
    if th == 180: return -sx, -sy
    if th == 270: return -sy, sx
def tip(lib_id, num, ox, oy, th=0):
    px, py, ang, nm, ty = PIN[lib_id][num]
    rx, ry = rot_pt(px, -py, th)
    return round(ox + rx, 3), round(oy + ry, 3)
def outdir(lib_id, num, th=0):
    px, py, ang, nm, ty = PIN[lib_id][num]
    ox_, oy_ = -math.cos(math.radians(ang)), math.sin(math.radians(ang))   # screen coords before rotation (y down)
    rx, ry = rot_pt(ox_, oy_, th)
    return (round(rx), round(ry))
def label(name, x, y, d=(1, 0)):
    ang, just = {(1, 0): (0, 'left bottom'), (-1, 0): (180, 'right bottom'), (0, -1): (90, 'left bottom'), (0, 1): (270, 'right bottom')}[d]
    items.append(f'  (label "{name}" (at {x} {y} {ang}) (fields_autoplaced)\n    (effects (font (size 1.27 1.27)) (justify {just}))\n    (uuid {uid()})\n  )')
def noconn(x, y):
    items.append(f'  (no_connect (at {x} {y}) (uuid {uid()}))')
def text(x, y, s, size=2.0):
    items.append(f'  (text "{s}" (at {x} {y} 0)\n    (effects (font (size {size} {size})))\n    (uuid {uid()})\n  )')
def place(lib_id, refp, value, fp, ox, oy, th=0, nets=None, nc=(), unit=1, show_value=True, extra=None):
    """nets: {pin_num: netname}. 'GND','+3V3','+5V','VBUS' use power symbols. Pins in nc get no-connect."""
    refcount[refp] = refcount.get(refp, 0) + 1
    ref = refp if refp[-1].isdigit() else f'{refp}{refcount[refp]}'
    pr = f'''  (symbol (lib_id "{lib_id}") (at {ox} {oy} {th}) (unit {unit})
    (in_bom {'no' if refp.startswith('#') else 'yes'}) (on_board {'no' if refp.startswith('#') else 'yes'}) (dnp no)
    (uuid {uid()})
    (property "Reference" "{ref}" (at {ox + 2.54} {oy - 5.08} 0)
      (effects (font (size 1.27 1.27)) (justify left))
    )
    (property "Value" "{value}" (at {ox + 2.54} {oy - 2.54} 0)
      (effects (font (size 1.27 1.27)) (justify left){'' if show_value else ' hide'})
    )
    (property "Footprint" "{fp}" (at {ox} {oy} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "~" (at {ox} {oy} 0)
      (effects (font (size 1.27 1.27)) hide)
    )'''
    if extra:
        for k, v in extra.items():
            pr += f'\n    (property "{k}" "{v}" (at {ox} {oy} 0)\n      (effects (font (size 1.27 1.27)) hide)\n    )'
    for num in PIN[lib_id]:
        pr += f'\n    (pin "{num}" (uuid {uid()}))'
    pr += f'''
    (instances
      (project "{PROJ}"
        (path "/{ROOT}"
          (reference "{ref}") (unit {unit})
        )
      )
    )
  )'''
    items.append(pr)
    for num, net in (nets or {}).items():
        x, y = tip(lib_id, num, ox, oy, th)
        d = outdir(lib_id, num, th)
        connect(x, y, net, d)
    for num in nc:
        x, y = tip(lib_id, num, ox, oy, th)
        noconn(x, y)
    return ref
def pwr(netname, x, y):
    lib = {'GND': 'power:GND', '+3V3': 'power:+3V3', '+5V': 'power:+5V', 'VBUS': 'power:VBUS'}[netname]
    pwrn[0] += 1
    refcount['#PWR'] = 0
    items.append(f'''  (symbol (lib_id "{lib}") (at {x} {y} 0) (unit 1)
    (in_bom no) (on_board no) (dnp no)
    (uuid {uid()})
    (property "Reference" "#PWR0{pwrn[0]}" (at {x} {y + (3.81 if netname != 'GND' else -3.81)} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "{netname}" (at {x + 2.54} {y + (-2.54 if netname != 'GND' else 5.08)} 0)
      (effects (font (size 1.27 1.27)) (justify left))
    )
    (property "Footprint" "" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (pin "1" (uuid {uid()}))
    (instances
      (project "{PROJ}"
        (path "/{ROOT}"
          (reference "#PWR0{pwrn[0]}") (unit 1)
        )
      )
    )
  )''')
def flag(x, y):
    pwrn[0] += 1
    items.append(f'''  (symbol (lib_id "power:PWR_FLAG") (at {x} {y} 0) (unit 1)
    (in_bom no) (on_board no) (dnp no)
    (uuid {uid()})
    (property "Reference" "#FLG0{pwrn[0]}" (at {x} {y - 3.81} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Value" "PWR_FLAG" (at {x} {y - 5.08} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "~" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (pin "1" (uuid {uid()}))
    (instances
      (project "{PROJ}"
        (path "/{ROOT}"
          (reference "#FLG0{pwrn[0]}") (unit 1)
        )
      )
    )
  )''')
def connect(x, y, net, d):
    if net in ('GND', '+3V3', '+5V', 'VBUS'):
        pwr(net, x, y)
    elif net == 'NC':
        noconn(x, y)
    else:
        label(net, x, y, d)

R_FP, C_FP = 'Resistor_SMD:R_0402_1005Metric', 'Capacitor_SMD:C_0402_1005Metric'
C8 = 'Capacitor_SMD:C_0805_2012Metric'
def R(val, a, b, x, y, fp=R_FP, ref='R'):
    return place('Device:R', ref, val, fp, x, y, th=90, nets={'1': a, '2': b})
def Cv(val, a, b, x, y, fp=C_FP, ref='C'):
    return place('Device:C', ref, val, fp, x, y, th=90, nets={'1': a, '2': b})
def Cg(val, rail, x, y, fp=C_FP):      # decoupling cap rail->GND, vertical
    return place('Device:C', 'C', val, fp, x, y, th=0, nets={'1': rail, '2': 'GND'})

# ---------------------------------------------------------------- 4. our circuit
X0, Y0 = 470.0, 30.0
text(X0, Y0 - 6, '=== Famicom bus interface (FC-EXPSYNTH additions) ===', 3)
# J10 edge / J11 slot -------------------------------------------------
J1NET = {}
for i in range(1, 61):
    nm = EDGE_NAMES[i]
    if nm == 'GND': J1NET[i] = 'GND'
    elif i in (30, 31): J1NET[i] = '+5V'
    elif nm in ('R/W',): J1NET[i] = 'RW'
    elif nm == '/ROMSEL': J1NET[i] = 'ROMSEL_N'
    elif nm == 'M2': J1NET[i] = 'M2'
    elif nm == 'AUDIO_FROM_2A03': J1NET[i] = 'AUD_FROM_2A03'
    elif nm == 'AUDIO_TO_RF': J1NET[i] = 'AUD_TO_RF'
    elif re.fullmatch(r'[AD]\d+', nm): J1NET[i] = nm
    elif nm == '/IRQ': J1NET[i] = 'IRQ_N'
    elif nm.startswith(('PPU_', 'CIRAM_')):
        J1NET[i] = {'PPU_/RD': 'PPU_RD_N', 'PPU_/WR': 'PPU_WR_N', 'CIRAM_/CE': 'CIRAM_CE_N', 'PPU_/A13': 'PPU_A13_N'}.get(nm, nm)
    else: J1NET[i] = 'NC'
J2NET = dict(J1NET); J2NET[44] = 'ROMSEL_EXP'   # RevE5: PPU bus (27) + /IRQ passed straight through J10 <-> J11
place('FCSYNTH:FC_Cart_Edge_60', 'J', 'FC_Cart_Edge_60', 'FCSYNTH:FC_Cart_Edge_60', X0 + 45, Y0 + 60,
      nets={str(i): n for i, n in J1NET.items()}, show_value=True)
place('FCSYNTH:FC_Slot_60', 'J', 'FC_Slot_60 (expansion cart)', 'FCSYNTH:FC_Slot_60', X0 + 215, Y0 + 60,
      nets={str(i): n for i, n in J2NET.items()}, show_value=True)
text(X0 + 20, Y0 - 1, 'J10: console-side gold fingers (1-30 front / 31-60 back)', 2)
text(X0 + 190, Y0 - 1, 'J11: 60-pin slot (pin n -> pin n incl. PPU bus and /IRQ; /ROMSEL gated in synth mode)', 2)
# 74LVC245 x3 --------------------------------------------------------
LVC_FP = 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm'
YB = Y0 + 175
def lvc(x, bnets, anets, val='74LVC245'):
    nets = {'1': 'GND', '19': 'GND', '20': '+3V3', '10': 'GND'}
    nc = []
    for i in range(8):
        b = bnets[i]; a = anets[i]
        nets[str(18 - i)] = b
        if a == 'NC': nc.append(str(2 + i))
        else: nets[str(2 + i)] = a
    place('FCSYNTH:74x245', 'U', val, LVC_FP, x, YB, nets=nets, nc=nc)
    Cg('100n', '+3V3', x + 14, YB - 18)
text(X0, YB - 22, 'U10-U12: 5V bus -> 3.3V (74LVC245, VCC=3V3, DIR=GND: B->A, /OE=GND)', 2)
lvc(X0 + 25, [f'A{i}' for i in range(8)], [f'GPIO{1+i}' for i in range(8)])
lvc(X0 + 95, [f'A{i}' for i in range(8, 15)] + ['GND'], [f'GPIO{9+i}' for i in range(7)] + ['NC'])
lvc(X0 + 165, ['M2', 'RW', 'ROMSEL_N'] + ['GND'] * 5, ['GPIO16', 'GPIO17', 'GPIO18'] + ['NC'] * 5)
# data output AHCT245 + 330R -------------------------------------------
XD = X0 + 260
nets = {'1': 'RW', '19': 'OE_N', '20': '+3V3', '10': 'GND'}
for i in range(8):
    nets[str(2 + i)] = f'ED{i}'
    nets[str(18 - i)] = f'D{i}'
place('FCSYNTH:74x245', 'U', '74LVC245', LVC_FP, XD + 55, YB, th=0, nets=nets)
Cg('100n', '+3V3', XD + 69, YB - 18)
text(XD, YB - 22, 'U13: D0-D7 bidirectional (74LVC245 at 3V3, 5V-tolerant B side; DIR=R/W: read A->B, write B->A for capture)', 2)
for i in range(8):
    R('330', f'GPIO{19+i}', f'ED{i}', XD + 15, YB - 12 + 2.54 * 2 * i * 1.0 + 0)
# gates ------------------------------------------------------------------
YG = Y0 + 290
text(X0, YG - 22, 'U14/U15: /ROMSEL gating and U13 output enable', 2)
place('FCSYNTH:74x32', 'U', '74HCT32', 'Package_SO:TSSOP-14_4.4x5mm_P0.65mm', X0 + 30, YG,
      nets={'1': 'ROMSEL_N', '2': 'RW_SYN', '3': 'ROMSEL_EXP', '4': 'ROMSEL_N', '5': 'RW_N', '6': 'RDSEL_N', '9': 'RDSEL_N', '10': 'EN_N', '8': 'OE1_N',
            '12': 'RW_N', '13': 'GAME', '11': 'WRS_N', '14': '+5V', '7': 'GND'})
Cg('100n', '+5V', X0 + 46, YG - 14)
place('FCSYNTH:74x04', 'U', '74HC04', 'Package_SO:TSSOP-14_4.4x5mm_P0.65mm', X0 + 100, YG,
      nets={'1': 'RW', '2': 'RW_N', '3': 'WRS_N', '4': 'RW_SYN', '5': 'OE1_N', '6': 'OE1', '9': 'GND', '11': 'GND', '13': 'GND', '14': '+5V', '7': 'GND'}, nc=['8', '10', '12'])
Cg('100n', '+5V', X0 + 116, YG - 14)
place('FCSYNTH:74x1G02', 'U17', '74LVC1G02', 'Package_TO_SOT_SMD:SOT-23-5', X0 + 130, YG + 40,
      nets={'1': 'RW_N', '2': 'OE1', '4': 'OE_N', '5': '+5V', '3': 'GND'})
place('Device:C', 'C42', '100n', C_FP, X0 + 146, YG + 30, th=0, nets={'1': '+5V', '2': 'GND'})
R('1k', 'GPIO30', 'GAME', X0 + 220, YG + 10, ref='R51')
R('10k', '+3V3', 'GAME', X0 + 250, YG + 10, ref='R52')
text(X0 + 205, YG + 20, 'GAME: high (default, 10k pull-up) = game mode, top cart gets every /ROMSEL cycle. GPIO30 low = synth mode (top cart sees writes only).', 1.8)
text(X0 + 150, YG - 16, 'RW_SYN     = R/W AND NOT GAME  (= NOT(RW_N OR GAME))', 1.8)
text(X0 + 150, YG - 12, 'ROMSEL_EXP = ROMSEL_N OR RW_SYN   (J11 pin44; game mode: = ROMSEL_N)', 1.8)
text(X0 + 150, YG - 8, 'RDSEL_N    = ROMSEL_N OR NOT R/W ;  OE1_N = RDSEL_N OR EN_N', 1.8)
text(X0 + 150, YG - 4, 'OE_N       = NOT(RW_N OR OE1)  (U17: U13 on for every CPU write, and for $8000+ reads when EN)', 1.8)
# EN control
R('1k', 'GPIO27', 'EN_N', X0 + 160, YG + 10)
R('10k', '+3V3', 'EN_N', X0 + 190, YG + 10)
text(X0 + 150, YG + 20, 'EN_N: GPIO27 low = U13 enabled. 10k pull-up keeps it disabled at reset.', 1.8)
# test points
for k, nm in enumerate(['M2', 'RW', 'ROMSEL_N', 'ROMSEL_EXP', 'OE_N', 'EN_N', 'GAME', 'IRQ_N']):
    place('Connector:TestPoint', 'TP', nm, 'TestPoint:TestPoint_Pad_D1.0mm', X0 + 160 + 12 * k, YG + 40, nets={'1': nm}, show_value=True)
# power block ----------------------------------------------------------------
YP = Y0 + 355
text(X0, YP - 14, 'Power: console +5V and USB VBUS -> Schottky OR -> VSYS -> 3.3V LDO (IOVDD is up whenever console 5V is present)', 2)
place('FCSYNTH:USB_C_16P', 'J', 'USB-C (HRO TYPE-C-31-M-12)', 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', X0 + 25, YP + 20,
      nets={'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'S1': 'GND', 'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS',
            'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_D+', 'B6': 'USB_D+', 'A7': 'USB_D-', 'B7': 'USB_D-', 'A8': 'NC', 'B8': 'NC'})
R('5.1k', 'CC1', 'GND', X0 + 60, YP + 6)
R('5.1k', 'CC2', 'GND', X0 + 60, YP + 14)
place('Device:D_Schottky', 'D', 'SS14', 'Diode_SMD:D_SMA', X0 + 100, YP, th=0, nets={'2': '+5V', '1': 'VSYS'})
place('Device:D_Schottky', 'D', 'SS14', 'Diode_SMD:D_SMA', X0 + 100, YP + 14, th=0, nets={'2': 'VBUS', '1': 'VSYS'})
text(X0 + 90, YP - 6, 'D10: console +5V -> VSYS   D11: VBUS -> VSYS (blocks back-feed)', 1.8)
place('FCSYNTH:AP2112K-3.3', 'U', 'AP2112K-3.3', 'Package_TO_SOT_SMD:SOT-23-5', X0 + 150, YP + 8,
      nets={'1': 'VSYS', '3': 'VSYS', '5': '+3V3', '2': 'GND'}, nc=['4'])
Cg('10u', 'VSYS', X0 + 130, YP + 14, C8)
Cg('10u', '+3V3', X0 + 172, YP + 14, C8)
Cg('22u', '+5V', X0 + 118, YP + 34, C8)
Cg('100n', 'VBUS', X0 + 128, YP + 34)
flag(X0 + 196, YP); pwr('+5V', X0 + 196, YP)
flag(X0 + 196, YP + 10); label('VSYS', X0 + 196, YP + 10, (1, 0))
flag(X0 + 196, YP + 20); pwr('VBUS', X0 + 196, YP + 20)
flag(X0 + 196, YP + 30); pwr('GND', X0 + 196, YP + 30)
# 5V sense divider (ADC0 / GPIO40 is NOT 5V tolerant: divided to 3.0V)
text(X0 + 205, YP - 6, '+5V sense (GPIO40/ADC0)', 1.8)
R('10k', '+5V', 'GPIO40_ADC0', X0 + 210, YP + 2)
R('15k', 'GPIO40_ADC0', 'GND', X0 + 210, YP + 12)
# USB data (official R7/R8 27R sit on USB_D+/USB_D- already) ---------------------
# status LED, SD card, spare header -------------------------------------------
YS = Y0 + 440
text(X0, YS - 14, 'Status LED, microSD (SPI0: GPIO32-35, CD=GPIO36), spare header', 2)
R('1k', 'GPIO37', 'LEDA', X0 + 20, YS)
place('Device:LED', 'D', 'green', 'LED_SMD:LED_0603_1608Metric', X0 + 40, YS, th=0, nets={'2': 'LEDA', '1': 'GND'})
sdnets = {'1': 'SD_DAT2', '2': 'GPIO33', '3': 'GPIO35', '4': '+3V3', '5': 'GPIO34', '6': 'GND', '7': 'GPIO32', '8': 'SD_DAT1', '9': 'GND', '10': 'GPIO36', '11': 'GND'}
place('FCSYNTH:microSD', 'J', 'microSD (SPI)', 'Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5', X0 + 100, YS + 15, nets=sdnets)
for k, (a, nm) in enumerate([('+3V3', 'SD_DAT1'), ('+3V3', 'SD_DAT2'), ('+3V3', 'GPIO33'), ('+3V3', 'GPIO32'), ('+3V3', 'GPIO35'), ('+3V3', 'GPIO36')]):
    R('10k', a, nm, X0 + 150 + 14 * k, YS + 4)
Cg('10u', '+3V3', X0 + 150, YS + 30, C8)
Cg('100n', '+3V3', X0 + 162, YS + 30)
hdr = ['GPIO38', 'GPIO39', 'GPIO41_ADC1', 'GPIO42_ADC2', 'GPIO28', 'GPIO29', '+3V3', 'GND']
place('FCSYNTH:Conn_2x04', 'J', 'Spare GPIO', 'Connector_PinHeader_2.54mm:PinHeader_2x04_P2.54mm_Vertical', X0 + 230, YS + 12,
      nets={str(i + 1): hdr[i] for i in range(8)})
text(X0 + 215, YS - 6, 'J14: 6 spare GPIO (GPIO31/43-47 left unrouted; GPIO30 = GAME mode select); GPIO0 is left free (PSRAM CS option via R11)', 1.8)

# ---------------------------------------------------------------- 5. assemble
lib_add = '\n'.join(SYMS + stock_txt)
i = txt.index('(lib_symbols')
# insert before the closing paren of lib_symbols: find matching paren
d = 0; j = i
while True:
    c = txt[j]
    if c == '(': d += 1
    elif c == ')':
        d -= 1
        if d == 0: break
    j += 1
txt = txt[:j] + '\n' + lib_add + '\n  ' + txt[j:]
k = txt.index('(sheet_instances')
txt = txt[:k] + '\n'.join(items) + '\n\n  ' + txt[k:]
import re as _re
BACK = ()   # RevE5: all capacitors on the front (machine assembled)
if BACK: txt = _re.sub(r'(\(property "Reference" "(?:%s)"(?:(?!\(symbol \(lib_id).)*?\(property "Footprint" ")([^"]*)(")' % '|'.join(BACK),
              r'\1Capacitor_SMD:C_0603_1608Metric\3', txt, flags=_re.S)
open(f'{OUT}/{PROJ}.kicad_sch', 'w', encoding='utf-8').write(txt)
print('written', len(items), 'items')
