# Footprints for FC-EXPSYNTH (our own generator; geometry from NESdev "Famicom cartridge dimensions" numbers)
import uuid
u = lambda: str(uuid.uuid4())
PITCH = 2.54
def edge():
    TW, TL = 78.4, 10.7
    hw = TW / 2
    o = ['(footprint "FC_Cart_Edge_60"', '  (version 20221018)', '  (generator gen_fp)', '  (layer "F.Cu")',
         '  (descr "Famicom 60-pin cartridge edge fingers. F.Cu = pins 1-30 (console front), B.Cu = 31-60, pin 1/31 at -X (seen from F side). Origin = tongue root centre, insertion edge at y=+10.7. PCB 1.2mm, ENIG.")',
         '  (attr smd exclude_from_pos_files exclude_from_bom)',
         f'  (fp_text reference "J10" (at 0 -2 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))) (tstamp {u()}))',
         f'  (fp_text value "FC_Cart_Edge_60" (at 0 -4 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))) (tstamp {u()}))']
    # (no whole-tongue solder-mask opening: each finger pad has its own mask opening)
    o.append(f'  (fp_rect (start {-hw} 0) (end {hw} {TL}) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab") (tstamp {u()}))')
    o.append(f'  (fp_rect (start {-hw-0.25} -0.25) (end {hw+0.25} {TL+0.25}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd") (tstamp {u()}))')
    for k in range(30):
        x = -36.83 + PITCH * k
        for layer, num in (('F.Cu', k + 1), ('B.Cu', k + 31)):
            w, h, cy = 1.6, 5.7, 5.85
            xx = x
            if num in (1, 30, 31):
                w, h, cy = 2.6, 6.7, 6.35
                xx = x + 0.5 if x > 0 else x - 0.5
            if num == 16:
                h, cy = 6.7, 6.35
            lays = f'"{layer}"' + (' "F.Mask"' if layer == 'F.Cu' else ' "B.Mask"')
            o.append(f'  (pad "{num}" smd rect (at {xx:.2f} {cy}) (size {w} {h}) (layers {lays}) (tstamp {u()}))')
    o.append(')')
    open('FCSYNTH.pretty/FC_Cart_Edge_60.kicad_mod', 'w').write('\n'.join(o) + '\n')

def slot():
    # Straddle-mount pads at the TOP board edge: pins 1-30 on F.Cu, 31-60 on B.Cu (same X). Hand-soldered: the legs of a
    # through-hole 2x30 card-edge connector are bent flat onto these pads. Origin = board top edge centre, pads extend to +Y (inside board).
    o = ['(footprint "FC_Slot_60"', '  (version 20221018)', '  (generator gen_fp)', '  (layer "F.Cu")',
         '  (descr "60-pin card-edge connector straddle pads, 2.54mm pitch. F.Cu=1-30, B.Cu=31-60. PLACEHOLDER pad size: set from the real connector leg geometry. Hand-solder.")',
         '  (attr smd exclude_from_pos_files exclude_from_bom)',
         f'  (fp_text reference "J11" (at 0 -2 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))) (tstamp {u()}))',
         f'  (fp_text value "FC_Slot_60" (at 0 -4 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))) (tstamp {u()}))']
    hw = 29 * PITCH / 2
    o.append(f'  (fp_rect (start {-hw-1.5} 0) (end {hw+1.5} 3.2) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab") (tstamp {u()}))')
    o.append(f'  (fp_rect (start {-hw-1.5} -3) (end {hw+1.5} 3.4) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd") (tstamp {u()}))')
    for k in range(30):
        x = -hw + PITCH * k
        o.append(f'  (pad "{k+1}" smd rect (at {x:.2f} 1.9) (size 1.5 3.0) (layers "F.Cu" "F.Mask") (tstamp {u()}))')
        o.append(f'  (pad "{k+31}" smd rect (at {x:.2f} 1.9) (size 1.5 3.0) (layers "B.Cu" "B.Mask") (tstamp {u()}))')
    o.append(')')
    open('FCSYNTH.pretty/FC_Slot_60.kicad_mod', 'w').write('\n'.join(o) + '\n')
edge(); slot()
open('fp-lib-table', 'w').write('''(fp_lib_table
  (version 7)
  (lib (name "FCSYNTH")(type "KiCad")(uri "${KIPRJMOD}/FCSYNTH.pretty")(options "")(descr "FC-EXPSYNTH local"))
  (lib (name "RP2350_80QFN_minimal")(type "KiCad")(uri "${KIPRJMOD}/RP2350_80QFN_minimal.pretty")(options "")(descr "Raspberry Pi minimal design"))
)
''')
print('ok')
