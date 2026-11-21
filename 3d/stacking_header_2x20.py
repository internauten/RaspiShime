"""3D-Modell Stacking-Header (Buchsenleiste mit langen Stiften) 2x20, Raster 2.54 mm.

Erzeugt stacking_header_2x20.step (mit Farben) fuer J2.

Aufruf:  python stacking_header_2x20.py [Pinlaenge_ueber_Platine_mm]

Koordinaten (wie bei den KiCad-Modellen, Footprint auf B.Cu):
- Einheit mm, Ursprung = Mitte von Pin 1, Z = 0 ist die Platinenflaeche auf der Bestueckungsseite
- Pin 2 liegt bei X = -2.54 (wie PinSocket_2x20_P2.54mm_Vertical), Pin 3 bei Y = -2.54
- Der Buchsenkoerper liegt bei Z = 0 ... BODY_H (KiCad spiegelt das bei B.Cu nach unten)
- Die Stifte ragen durch die Platine (Z negativ) und enden PIN_ABOVE ueber der Platinenoberseite

Copyright (c) 2026 die.internauten.ch GmbH

"""
import sys
import cadquery as cq

PITCH = 2.54
COLS, ROWS = 2, 20
BODY_H = 8.5          # Hoehe Buchsenkoerper
BODY_W = 5.08         # Breite (2 x Raster)
BOARD_T = 1.6         # Platinendicke
PIN_W = 0.64          # Stift quadratisch
PIN_ABOVE = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0   # Stiftlaenge ueber Platinenoberseite
PIN_BOTTOM = 2.0      # Stiftende im Koerper (Z, ueber Platinenflaeche)
CHAMFER = 0.15

# Koerper: Aussenmasse, Loecher fuer die Stifte werden nicht modelliert
body_len = ROWS * PITCH
body = (cq.Workplane('XY')
        .box(BODY_W, body_len, BODY_H, centered=False)
        .translate((-PITCH - (BODY_W - PITCH) / 2, -(ROWS - 1) * PITCH - PITCH / 2, 0))
        .edges('|Z').chamfer(0.2))

# Stifte: von PIN_BOTTOM (im Koerper) bis durch die Platine und PIN_ABOVE darueber
z_top = -(BOARD_T + PIN_ABOVE)
pin_len = PIN_BOTTOM - z_top
pins = None
for c in range(COLS):
    for r in range(ROWS):
        p = (cq.Workplane('XY')
             .box(PIN_W, PIN_W, pin_len, centered=(True, True, False))
             .translate((-c * PITCH, -r * PITCH, z_top))
             .faces('<Z').chamfer(CHAMFER))
        pins = p if pins is None else pins.union(p)

asm = cq.Assembly(name='StackingHeader_2x20')
asm.add(body, name='koerper', color=cq.Color(0.08, 0.08, 0.08, 1))
asm.add(pins, name='stifte', color=cq.Color(0.85, 0.7, 0.3, 1))
out = 'stacking_header_2x20.step'
asm.export(out)
print('geschrieben:', out, '- Stifte ueber Platine:', PIN_ABOVE, 'mm, Gesamtlaenge:', round(pin_len, 2), 'mm')
