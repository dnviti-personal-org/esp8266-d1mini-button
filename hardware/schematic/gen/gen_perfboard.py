#!/usr/bin/env python3
"""Generates perfboard-layout.scr (CADCraft script): 70x50 mm perfboard, top view, DESIGN.md section 5 (rev B.3)."""
import json, sys

out = ["; perfboard-layout.scr - 70 x 50 mm perfboard placement rev B.3, top view (CADCraft script, mm, origin = board bottom-left).",
       "; Replay: cadcraft-cli run --metric --script-file perfboard-layout.scr --save perfboard-layout.dxf --export perfboard-layout.png",
       "; Centres per hardware/DESIGN.md section 5. The hole grid is one circle (handle 100) replicated with arrayrect 24 x 18 @ 2.54 mm."]
def cmd(id_, **p): out.append(f"{id_} {json.dumps(p, ensure_ascii=False)}")
def layer(name): cmd("layer.current", name=name)
def line(*pts): cmd("line", points=[list(p) for p in pts])
def rect(x1, y1, x2, y2): cmd("rectang", p1=[x1, y1], p2=[x2, y2])
def circle(x, y, r): cmd("circle", center=[x, y], radius=r)
def text(x, y, s, h=2, j="MC", rot=0):
    p = dict(at=[x, y], text=s, height=h, justify=j)
    if rot: p["rotation"] = rot
    cmd("text", **p)
def pin(x, y, r=0.6): circle(x, y, r)
def dashed_rect(x1, y1, x2, y2, dash=2.5, gap=1.2):
    """closed dashed outline drawn as short lines (no linetype dependency)"""
    corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
    for (ax, ay), (bx, by) in zip(corners, corners[1:]):
        L = abs(bx-ax) + abs(by-ay); ux, uy = (bx-ax)/L, (by-ay)/L; s = 0.0
        while s < L:
            e = min(s+dash, L)
            line((round(ax+ux*s, 3), round(ay+uy*s, 3)), (round(ax+ux*e, 3), round(ay+uy*e, 3)))
            s += dash + gap

PITCH = 2.54; COLS, ROWS = 24, 18
X0 = (70 - (COLS-1)*PITCH)/2; Y0 = (50 - (ROWS-1)*PITCH)/2   # grid centred on the board

# --- hole grid first: the first entity gets handle 100, which the array references ---
cmd("layer.new", name="holes", color="128,128,128", current=True)
circle(round(X0, 3), round(Y0, 3), 0.5)
cmd("arrayrect", handles=["100"], rows=ROWS, cols=COLS, rowSpacing=PITCH, colSpacing=PITCH, associative=False)

cmd("lwdisplay", on=True)
cmd("layer.new", name="under", color="200,90,220")      # parts under the perfboard (LiPo)
cmd("layer.new", name="board", color=7, lineweight=0.5)
cmd("layer.new", name="components", color="0,170,230", lineweight=0.35)
cmd("layer.new", name="pins", color="255,140,0")
cmd("layer.new", name="refdes", color="255,140,0")
cmd("layer.new", name="dims", color="0,200,0")
cmd("layer.new", name="notes", color="0,170,230")

# --- BT1 LiPo 803040 under the board, 40 (X) x 30 (Y), centred (35, 26.5) = cavity (40, 28) minus the (5, 1.5) offset ---
layer("under"); dashed_rect(15, 11.5, 55, 41.5)
layer("refdes"); text(35, 18.2, "BT1 under", 1.2)

# --- board outline with 4 x 4 mm corner notches + mounting holes ---
layer("board")
N = 4
cmd("pline", vertices=[[N, 0], [70-N, 0], [70-N, N], [70, N], [70, 50-N], [70-N, 50-N], [70-N, 50], [N, 50], [N, 50-N], [0, 50-N], [0, N], [N, N]], closed=True)
for (x, y) in [(34, 3), (34, 47), (6, 40), (64, 21)]:
    circle(x, y, 1.1); line((x-1.4, y), (x+1.4, y)); line((x, y-1.4), (x, y+1.4))
layer("refdes"); text(8.2, 40, "4× Ø2.2", 1.3, "ML")

# --- U1 D1 mini: 25.6 (X) x 34.2 (Y) at (15.8, 17.1): PCB y 0 -> 34.2, USB on the y = 0 edge, antenna toward y = 50 ---
cx, cy = 15.8, 17.1
layer("components"); rect(cx-12.8, cy-17.1, cx+12.8, cy+17.1)
rect(cx-4, cy-17.1-1.0, cx+4, cy-17.1+5.0)                      # micro-USB receptacle, protrudes 1 mm past the edge
layer("refdes"); text(cx, cy-17.1+2.2, "USB", 1.6)
layer("components")
ax1, ay1, ax2, ay2 = cx-6, cy+17.1-5.5, cx+6, cy+17.1-0.8    # PCB antenna (meander) at the far edge
rect(ax1, ay1, ax2, ay2)
pts = []
for i in range(7):
    x = ax1 + 1 + i*(10/6)
    pts += [(x, ay1+0.8), (x, ay2-0.8)] if i % 2 == 0 else [(x, ay2-0.8), (x, ay1+0.8)]
line(*pts)
layer("refdes"); text(cx, ay1-1.8, "antenna", 1.4)
layer("pins")
for k in range(8):                                                # 2 x 8 pins, rows 22.86 mm apart
    y = cy + (k-3.5)*PITCH
    pin(cx-11.43, y); pin(cx+11.43, y)
layer("refdes")
text(cx, cy+2, "U1", 3); text(cx, cy-1.8, "D1 mini", 2); text(cx, cy-4.6, "ESP8266", 1.6)
text(cx-11.43, cy+9.5, "RST", 1.2, "L", 90); text(cx+11.43, cy+9.5, "TX", 1.2, "L", 90)
text(cx-11.43, cy-9.5, "3V3", 1.2, "R", 90); text(cx+11.43, cy-9.5, "5V", 1.2, "R", 90)

# --- SW1 tactile 12x12 at (35, 26.5): centre of the enclosure cavity ---
cx, cy = 35.0, 26.5
layer("components"); rect(cx-6, cy-6, cx+6, cy+6); circle(cx, cy, 3.65)   # body + 7.3 mm actuator
layer("pins")
for dx in (-3.25, 3.25):
    for dy in (-6.25, 6.25): pin(cx+dx, cy+dy)
layer("refdes"); text(cx, cy, "SW1", 2.2)

# --- M1 TP4056 charger module 26 (X) x 17.5 (Y) at (52.5, 9.5): x 39.5 -> 65.5, USB-C toward y = 0 (protrudes 1.5 mm), on header pins ---
cx, cy = 52.5, 9.5
layer("components"); rect(cx-13, cy-8.75, cx+13, cy+8.75)
rect(cx-4.5, cy-8.75-1.5, cx+4.5, cy-8.75+3.5)                  # USB-C receptacle
rect(cx-3.5, cy-2.5, cx-1.5, cy-1); rect(cx+1.5, cy-2.5, cx+3.5, cy-1)   # charge / full LEDs
layer("pins")
for (dx, dy) in ((-11.5, 7.0), (11.5, 7.0), (-11.5, 3.5), (11.5, 3.5), (-11.5, -6.5), (11.5, -6.5)):
    pin(cx+dx, cy+dy)
layer("refdes")
text(cx, cy+3.6, "M1", 2.6); text(cx, cy+0.6, "TP4056", 2); text(cx, cy-4.8, "LEDs", 1.2)
text(cx, cy-8.75+1.6, "USB-C", 1.4)
text(cx-10, cy+7, "B+", 1.2, "L"); text(cx+10, cy+7, "B-", 1.2, "R")
text(cx-10, cy+3.5, "OUT+", 1.2, "L"); text(cx+10, cy+3.5, "OUT-", 1.2, "R")
text(cx-10, cy-6.5, "IN+", 1.2, "L"); text(cx+10, cy-6.5, "IN-", 1.2, "R")
text(cx-10, cy+5.2, "CHRG pad", 1.0, "L")

# --- J2 microphone header: right-angle 1x6 at (54, 40), body 15.24 (X) x 2.54 (Y), bent pins 6 mm toward y = 50 ---
cx, cy = 54.0, 40.0
layer("components"); rect(cx-3*PITCH, cy-PITCH/2, cx+3*PITCH, cy+PITCH/2)
j2 = ["SCK", "WS", "SD", "L/R", "VDD", "GND"]
for k, nm in enumerate(j2):
    x = round(cx + (k-2.5)*PITCH, 3)
    layer("pins"); pin(x, cy, 0.5)
    layer("components"); line((x, cy+PITCH/2), (x, cy+PITCH/2+6))     # bent pin, wires plug in from y = 50
    layer("refdes"); text(x+0.9, cy+PITCH/2+0.6, nm, 0.8, "L", 90)
layer("refdes"); text(cx, cy-2.7, "J2 mic (right-angle)", 1.3)

# --- R3 10 k (CHRG pull-up) at (40.5, 47.5): axial, 10 mm along X, pads at x 35.5 and 45.5 ---
cx, cy = 40.5, 47.5
layer("components"); rect(cx-3, cy-1.2, cx+3, cy+1.2); line((cx-5, cy), (cx-3, cy)); line((cx+3, cy), (cx+5, cy))
layer("pins"); pin(cx-5, cy, 0.5); pin(cx+5, cy, 0.5)
layer("refdes"); text(cx, cy-2.0, "R3 10 k", 1.1)

# --- J1 JST-PH 2-pin right-angle header 6 (X) x 5 (Y) at (66, 27), wires leave toward x = 70 ---
cx, cy = 66.0, 27.0
layer("components"); rect(cx-3, cy-2.5, cx+3, cy+2.5); line((cx+3, cy-1.8), (cx+5, cy-1.8)); line((cx+3, cy+1.8), (cx+5, cy+1.8))
layer("pins"); pin(cx-1.0, cy, 0.5); pin(cx+1.0, cy, 0.5)
layer("refdes"); text(cx, cy+3.6, "J1 BAT", 1.2)

# --- D2 Schottky SS14 / 1N5819 at (34, 7): axial, 10 mm along X, cathode band toward U1 (-x) ---
cx, cy = 34.0, 7.0
layer("components"); rect(cx-3, cy-1.3, cx+3, cy+1.3); line((cx-2.2, cy-1.3), (cx-2.2, cy+1.3)); line((cx-5, cy), (cx-3, cy)); line((cx+3, cy), (cx+5, cy))
layer("pins"); pin(cx-5, cy, 0.5); pin(cx+5, cy, 0.5)
layer("refdes"); text(cx, cy+2.9, "D2 SS14", 1.4)

# --- R2 10 k at (34, 13): axial, 10 mm along X ---
cx, cy = 34.0, 13.0
layer("components"); rect(cx-3, cy-1.2, cx+3, cy+1.2); line((cx-5, cy), (cx-3, cy)); line((cx+3, cy), (cx+5, cy))
layer("pins"); pin(cx-5, cy, 0.5); pin(cx+5, cy, 0.5)
layer("refdes"); text(cx, cy+2.9, "R2 10 k", 1.6)

# --- C3 100 nF at (36, 35), 2.54 pitch ---
cx, cy = 36.0, 35.0
layer("components"); rect(cx-2.2, cy-1.5, cx+2.2, cy+1.5)
layer("pins"); pin(cx-1.27, cy, 0.5); pin(cx+1.27, cy, 0.5)
layer("refdes"); text(cx, cy+3.2, "C3 100nF", 1.5)

# --- C4 100 µF Ø5x11 lying along X at (36, 42) ---
cx, cy = 36.0, 42.0
layer("components"); rect(cx-5.5, cy-2.5, cx+5.5, cy+2.5); line((cx-4, cy-2.5), (cx-4, cy+2.5))
layer("pins"); pin(cx-6.6, cy-1); pin(cx-6.6, cy+1)
layer("refdes"); text(cx+1.2, cy, "C4 100µF", 1.25)

# --- JP1: two solder-bridge pads at (30, 47.5), 2.54 apart along X (bridged = battery mode) ---
cx, cy = 30.0, 47.5
layer("pins"); pin(cx-1.27, cy, 0.7); pin(cx+1.27, cy, 0.7)
layer("components"); cmd("pline", vertices=[[cx-0.6, cy], [cx+0.6, cy]], width=0.9)
layer("refdes"); text(cx-2.6, cy, "JP1 bridge", 1.2, "MR")

# --- SW2 slide switch SS12D00 at (67, 36): body x 65.2 -> 68.8, y 31.7 -> 40.3, actuator toward x = 70 ---
cx, cy = 67.0, 36.0
layer("components"); rect(cx-1.8, cy-4.3, cx+1.8, cy+4.3); rect(cx+1.8, cy-1, cx+1.8+2.2, cy+1)   # body + actuator
layer("pins")
for dy in (-3, 0, 3): pin(cx, cy+dy, 0.5)
layer("refdes"); text(cx, cy+6.0, "SW2", 1.6)

# --- dimensions, axes, scale bar, title, legend ---
layer("dims")
cmd("dimstyle", name="PCB", current=True, DIMTXT=2.2, DIMASZ=1.8, DIMEXO=1, DIMEXE=1.2, DIMDEC=1, DIMPOST="<> mm", DIMGAP=0.6)
cmd("dimlinear", p1=[0, 0], p2=[70, 0], at=[35, -7])
cmd("dimlinear", p1=[0, 0], p2=[0, 50], at=[-7, 25])
xa = X0 + 21*PITCH; xb = X0 + 22*PITCH; yt = Y0 + 17*PITCH   # hole pitch callout on the top row (manual, text horizontal)
line((xa, yt+0.8), (xa, 52.5)); line((xb, yt+0.8), (xb, 52.5)); line((xa, 52), (xb, 52))
line((xa-0.6, 51.6), (xa+0.6, 52.4)); line((xb-0.6, 51.6), (xb+0.6, 52.4))
text((xa+xb)/2, 53.6, "pitch 2.54", 1.4)
line((0, -14), (10, -14)); line((0, -15), (0, -13)); line((5, -15), (5, -13)); line((10, -15), (10, -13))
text(12, -14, "10 mm", 2, "ML")
text(0, -3, "origin (0,0)", 1.5, "R"); line((0, 0), (-3, -2.2))
layer("notes")
text(35, 60, "Perfboard 70 × 50 mm, top view (component side), rev B.3", 2.5)
text(35, 56.5, "2.54 mm grid, 24 × 18 holes Ø1.0; 4 × 4 mm corner notches; SW2 actuator points to the x = 70 edge", 1.8)
text(15.8, -3, "micro-USB edge (y = 0)", 1.6); text(52.5, -3.2, "USB-C (charge)", 1.6); text(15.8, 51.5, "antenna edge (y = 50)", 1.6)
text(72.5, 36, "actuator", 1.3, "ML")
layer("under"); line((0, -10.5), (2.5, -10.5)); line((3.7, -10.5), (6.2, -10.5))
layer("notes"); text(8, -10.5, "BT1 LiPo 803040 (40 × 30 × 8) taped to the floor under the perfboard, centred (35, 26.5)", 1.4, "ML")
text(24, -14, "M2 INMP441 I2S mic under the lid, 6 wires into J2 from y = 50", 1.4, "ML")
text(24, -17.5, "D2 band (cathode) toward U1; JP1 = solder bridge (closed = battery mode)", 1.4, "ML")
cmd("zoom", mode="extents")
sys.stdout.write("\n".join(out) + "\n")
