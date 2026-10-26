#!/usr/bin/env python3
"""Generates perfboard-layout.scr (CADCraft script): 70x50 mm perfboard, top view, DESIGN.md section 4."""
import json, sys

out = ["; perfboard-layout.scr - 70 x 50 mm perfboard placement, top view (CADCraft script, mm, origin = board bottom-left).",
       "; Replay: cadcraft-cli run --metric --script-file perfboard-layout.scr --save perfboard-layout.dxf --export perfboard-layout.png",
       "; Centres per hardware/DESIGN.md section 4. The hole grid is one circle (handle 100) replicated with arrayrect 24 x 18 @ 2.54 mm."]
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

PITCH = 2.54; COLS, ROWS = 24, 18
X0 = (70 - (COLS-1)*PITCH)/2; Y0 = (50 - (ROWS-1)*PITCH)/2   # grid centred on the board

# --- hole grid first: the first entity gets handle 100, which the array references ---
cmd("layer.new", name="holes", color="128,128,128", current=True)
circle(round(X0, 3), round(Y0, 3), 0.5)
cmd("arrayrect", handles=["100"], rows=ROWS, cols=COLS, rowSpacing=PITCH, colSpacing=PITCH, associative=False)

cmd("lwdisplay", on=True)
cmd("layer.new", name="board", color=7, lineweight=0.5)
cmd("layer.new", name="components", color="0,170,230", lineweight=0.35)
cmd("layer.new", name="pins", color="255,140,0")
cmd("layer.new", name="refdes", color="255,140,0")
cmd("layer.new", name="dims", color="0,200,0")
cmd("layer.new", name="notes", color="0,170,230")

# --- board outline + mounting holes ---
layer("board"); rect(0, 0, 70, 50)
for (x, y) in [(3, 3), (67, 3), (3, 47), (67, 47)]:
    circle(x, y, 1.1); line((x-1.8, y), (x+1.8, y)); line((x, y-1.8), (x, y+1.8))
layer("refdes"); text(5, 2.2, "4× Ø2.2", 1.5, "L")

# --- U1 D1 mini: 25.6 (X) x 34.2 (Y) at (15.8, 25); USB toward y=0, antenna toward y=50 ---
cx, cy = 15.8, 25.0
layer("components"); rect(cx-12.8, cy-17.1, cx+12.8, cy+17.1)
rect(cx-4, cy-17.1-1.0, cx+4, cy-17.1+5.0)                      # micro-USB receptacle, protrudes 1 mm
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

# --- SW1 tactile 12x12 at (35, 25): exact centre of the enclosure ---
cx, cy = 35.0, 25.0
layer("components"); rect(cx-6, cy-6, cx+6, cy+6); circle(cx, cy, 3.65)   # body + 7.3 mm actuator
layer("pins")
for dx in (-3.25, 3.25):
    for dy in (-6.25, 6.25): pin(cx+dx, cy+dy)
layer("refdes"); text(cx, cy, "SW1", 2.2)

# --- BT1 CR2032 holder 24x24 at (53.5, 14): x 41.5 -> 65.5, y 2 -> 26; cell Ø20 ---
cx, cy = 53.5, 14.0
layer("components"); rect(cx-12, cy-12, cx+12, cy+12); circle(cx, cy, 10)
layer("pins"); pin(cx-10.2, cy, 0.8); pin(cx+10.2, cy, 0.8)
layer("refdes"); text(cx, cy+1.5, "BT1", 3); text(cx, cy-2, "CR2032", 2); text(cx-11.2, cy+2.2, "-", 2.5); text(cx+11.2, cy+2.2, "+", 2.5)

# --- C1, C2 supercaps Ø8x20 lying along X at (54,35) and (54,44): x 44 -> 64, leads at the x=44 end ---
for ref, cy in (("C1", 35.0), ("C2", 44.0)):
    cx = 54.0
    layer("components"); rect(cx-10, cy-4, cx+10, cy+4); line((cx-8, cy-4), (cx-8, cy+4))   # body + polarity band
    layer("pins"); pin(cx-11.3, cy-1.75); pin(cx-11.3, cy+1.75)
    layer("refdes"); text(cx+1.5, cy+1.2, ref + " 3.3 F", 2); text(cx+1.5, cy-1.6, "2.7 V EDLC", 1.5); text(cx-9, cy-2, "-", 1.8); text(cx-9, cy+2, "+", 1.8)

# --- C4 100 µF Ø5x11 lying along X at (36, 42) ---
cx, cy = 36.0, 42.0
layer("components"); rect(cx-5.5, cy-2.5, cx+5.5, cy+2.5); line((cx-4, cy-2.5), (cx-4, cy+2.5))
layer("pins"); pin(cx-6.6, cy-1); pin(cx-6.6, cy+1)
layer("refdes"); text(cx+1.2, cy, "C4 100µF", 1.25)

# --- C3 100 nF at (36, 35), 2.54 pitch ---
cx, cy = 36.0, 35.0
layer("components"); rect(cx-2.2, cy-1.5, cx+2.2, cy+1.5)
layer("pins"); pin(cx-1.27, cy, 0.5); pin(cx+1.27, cy, 0.5)
layer("refdes"); text(cx, cy+3.2, "C3 100nF", 1.5)

# --- R1 68 Ω at (36, 7) and R2 10 k at (36, 13): axial, 10 mm along X ---
for ref, val, cy in (("R1", "68 Ω", 7.0), ("R2", "10 k", 13.0)):
    cx = 36.0
    layer("components"); rect(cx-3, cy-1.2, cx+3, cy+1.2); line((cx-5, cy), (cx-3, cy)); line((cx+3, cy), (cx+5, cy))
    layer("pins"); pin(cx-5, cy, 0.5); pin(cx+5, cy, 0.5)
    layer("refdes"); text(cx, cy-3.0 if ref == "R1" else cy-2.9, f"{ref} {val}", 1.6)

# --- JP1 2-pin header at (34, 47.5), pins along X ---
cx, cy = 34.0, 47.5
layer("components"); rect(cx-2.54, cy-1.27, cx+2.54, cy+1.27)
layer("pins"); pin(cx-1.27, cy, 0.5); pin(cx+1.27, cy, 0.5)
layer("refdes"); text(cx-3.5, cy, "JP1", 1.6, "R")

# --- SW2 slide switch SS12D00 at (67, 36): body x 65.2 -> 68.8, y 31.7 -> 40.3, actuator toward x = 70 ---
cx, cy = 67.0, 36.0
layer("components"); rect(cx-1.8, cy-4.3, cx+1.8, cy+4.3); rect(cx+1.8, cy-1, cx+1.8+2.2, cy+1)   # body + actuator
layer("pins")
for dy in (-3, 0, 3): pin(cx, cy+dy, 0.5)
layer("refdes"); text(cx+0.6, cy-6.0, "SW2", 1.6)

# --- dimensions, axes, scale bar, title ---
layer("dims")
cmd("dimstyle", name="PCB", current=True, DIMTXT=2.2, DIMASZ=1.8, DIMEXO=1, DIMEXE=1.2, DIMDEC=1, DIMPOST="<> mm", DIMGAP=0.6)
cmd("dimlinear", p1=[0, 0], p2=[70, 0], at=[35, -7])
cmd("dimlinear", p1=[0, 0], p2=[0, 50], at=[-7, 25])
xp = X0 + 23*PITCH; yp = Y0 + 9*PITCH   # hole pitch callout on the right edge (manual, keeps the text horizontal)
line((xp+0.8, yp), (72.5, yp)); line((xp+0.8, yp+PITCH), (72.5, yp+PITCH)); line((72, yp), (72, yp+PITCH))
line((71.6, yp+0.6), (72.4, yp-0.6)); line((71.6, yp+PITCH+0.6), (72.4, yp+PITCH-0.6))
text(73, yp+PITCH/2, "pitch 2.54", 1.4, "ML")
line((0, -14), (10, -14)); line((0, -15), (0, -13)); line((5, -15), (5, -13)); line((10, -15), (10, -13))
text(12, -14, "10 mm", 2, "ML")
text(0, -3, "origin (0,0)", 1.5, "R"); line((0, 0), (-3, -2.2))
layer("notes")
text(35, 60, "Perfboard 70 × 50 mm, top view (component side)", 2.5); text(35, 56.5, "2.54 mm grid, 24 × 18 holes Ø1.0; SW2 actuator points to the x = 70 edge", 1.8)
text(15.8, -3, "micro-USB edge (y = 0)", 1.6); text(15.8, 51.5, "antenna edge (y = 50)", 1.6)
text(72.5, 36, "actuator", 1.3, "ML")
cmd("zoom", mode="extents")
sys.stdout.write("\n".join(out) + "\n")
