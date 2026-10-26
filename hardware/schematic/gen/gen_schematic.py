#!/usr/bin/env python3
"""Generates schematic.scr (CADCraft script) for the ESP8266 D1 mini MQTT button."""
import json, sys

out = ["; schematic.scr - ESP8266 D1 mini MQTT battery button, schematic (CADCraft script, mm).",
       "; Replay: cadcraft-cli run --metric --script-file schematic.scr --save schematic.dxf --export schematic.png",
       "; Circuit per hardware/DESIGN.md sections 1-3. Layers: frame, symbols, wires, text, nets, notes."]
def cmd(id_, **p): out.append(f"{id_} {json.dumps(p, ensure_ascii=False)}")
def layer(name): cmd("layer.current", name=name)
def line(*pts): cmd("line", points=[list(p) for p in pts])
def rect(x1, y1, x2, y2): cmd("rectang", p1=[x1, y1], p2=[x2, y2])
def circle(x, y, r): cmd("circle", center=[x, y], radius=r)
def arc(cx, cy, r, a0, a1): cmd("arc", center=[cx, cy], radius=r, start=a0, end=a1)
def dot(x, y): cmd("donut", center=[x, y], inside=0, outside=1.6)
def text(x, y, s, h=3.5, j="MC", rot=0):
    p = dict(at=[x, y], text=s, height=h, justify=j)
    if rot: p["rotation"] = rot
    cmd("text", **p)
def thick(*pts, w=0.8): cmd("pline", vertices=[list(p) for p in pts], width=w)

# ---------- layers ----------
cmd("lwdisplay", on=True)
cmd("layer.new", name="frame",   color=7, lineweight=0.5)
cmd("layer.new", name="symbols", color=7, lineweight=0.35)
cmd("layer.new", name="wires",   color="0,200,0", lineweight=0.25)
cmd("layer.new", name="text",    color="0,170,230")
cmd("layer.new", name="nets",    color="255,140,0")
cmd("layer.new", name="notes",   color="0,170,230")

# ---------- symbol helpers (all vertical unless noted) ----------
def battery(x, yc):
    layer("symbols")
    line((x-6, yc+2), (x+6, yc+2))          # long plate = +
    thick((x-3, yc-2), (x+3, yc-2))         # short thick plate = -
    text(x+8, yc+5, "+", 4)

def slide_switch_h(x1, x2, y):
    layer("symbols")
    line((x1, y), (x1+1.5, y)); line((x2-1.5, y), (x2, y))
    circle(x1+2.3, y, 0.8); circle(x2-2.3, y, 0.8)
    line((x1+3, y+0.4), (x2-2.8, y+5.2))     # blade (shown open = OFF)
    line((x1+5.5, y+7.5), (x1+8.5, y+7.5)); line((x1+7, y+7.5), (x1+7, y+6))  # actuator

def resistor_h(xc, y, L=16, H=5):
    layer("symbols"); rect(xc-L/2, y-H/2, xc+L/2, y+H/2)

def resistor_v(x, yc, L=16, H=5):
    layer("symbols"); rect(x-H/2, yc-L/2, x+H/2, yc+L/2)

def cap_polar_v(x, yc, hw=4.5):
    """straight plate (+) on top, curved plate (-) below; returns (y_top_plate, y_bottom_plate_top)"""
    layer("symbols")
    line((x-hw, yc+1.2), (x+hw, yc+1.2))
    r = 7.5; cy = yc-1.2-r
    arc(cy and x, cy, r, 55, 125)
    text(x-7, yc+4, "+", 4)
    return yc+1.2, yc-1.2

def cap_v(x, yc, hw=4):
    layer("symbols")
    line((x-hw, yc+1.2), (x+hw, yc+1.2)); line((x-hw, yc-1.2), (x+hw, yc-1.2))
    return yc+1.2, yc-1.2

def pushbutton_v(x, y_top, y_bot):
    layer("symbols")
    circle(x, y_top, 0.8); circle(x, y_bot, 0.8)
    line((x-5, y_top+1.5), (x-5, y_bot-1.5))           # bar (open)
    line((x-5, (y_top+y_bot)/2), (x-9, (y_top+y_bot)/2))  # actuator
    line((x-9, (y_top+y_bot)/2-2), (x-9, (y_top+y_bot)/2+2))

def jumper_v(x, y1, y2):
    layer("symbols")
    rect(x-3, y1-3, x+3, y2+3)
    circle(x, y1, 1); circle(x, y2, 1)
    thick((x, y1+1), (x, y2-1), w=1.2)              # shunt fitted

def ground(x, y):
    layer("symbols")
    line((x, y), (x, y-7)); line((x-5, y-7), (x+5, y-7)); line((x-3, y-9), (x+3, y-9)); line((x-1.2, y-11), (x+1.2, y-11))

def nc_mark(x, y):
    layer("symbols"); line((x-1.3, y-1.3), (x+1.3, y+1.3)); line((x-1.3, y+1.3), (x+1.3, y-1.3))

# ---------- geometry ----------
YT, YG = 215, 105          # top (3V3) rail and GND rail
XB = 45                    # BT1
XC1 = 165; XC4 = 210; XBR = 220   # supercaps, C4, branch to U1
UX1, UY1, UX2, UY2 = 240, 115, 300, 200
P3V3, PG = 190, 125        # left pins
PRST, PA0, PD1, PD4 = 185, 170, 155, 140   # right pins
YB = PD1                   # BTN node line
XJP, XR2, XC3, XSW = 325, 350, 368, 388

# ---------- frame & title block ----------
layer("frame")
rect(10, 10, 410, 270)
rect(250, 10, 410, 40); line((250, 28), (410, 28)); line((340, 10), (340, 28)); line((380, 10), (380, 28))
layer("text")
text(330, 34, "ESP8266 D1 mini MQTT battery button", 4.5)
text(255, 21.5, "Schematic: power path + button", 3, "L")
text(255, 14, "Date: 2026-10-26", 3, "L")
text(360, 21.5, "Rev A", 3); text(360, 14, "CADCraft", 3)
text(395, 21.5, "Sheet", 3); text(395, 14, "1 / 1", 3)

# ---------- power path ----------
battery(XB, 160)
layer("text")
text(37, 164, "BT1", 3.5, "R"); text(37, 159, "CR2032", 3.5, "R"); text(37, 154, "3.0 V", 3, "R")

slide_switch_h(70, 90, YT)
layer("text"); text(80, 232, "SW2", 3.5); text(80, 227.5, "POWER", 3)

resistor_h(115, YT)
layer("text"); text(115, 226, "R1", 3.5); text(115, 221, "68 Ω", 3.5)

layer("wires")
line((XB, YT), (XB, 162)); line((XB, 158), (XB, YG))
line((XB, YT), (70, YT)); line((90, YT), (107, YT)); line((123, YT), (XR2, YT))
line((XB, YG), (XSW, YG))

layer("nets")
text(57, 219, "VBAT", 3.5); text(150, 219.5, "VCAP = 3V3", 3.5); text(300, 219.5, "3V3", 3.5)

# supercaps C1, C2 in series
t1, b1 = cap_polar_v(XC1, 190)
t2, b2 = cap_polar_v(XC1, 160)
layer("wires")
line((XC1, YT), (XC1, t1)); line((XC1, b1), (XC1, t2)); line((XC1, b2), (XC1, YG))
dot(XC1, YT); dot(XC1, YG)
layer("text")
text(173, 193, "C1", 3.5, "L"); text(173, 188, "3.3 F 2.7 V", 3, "L")
text(173, 163, "C2", 3.5, "L"); text(173, 158, "3.3 F 2.7 V", 3, "L")
text(173, 150, "EDLC, series", 2.5, "L"); text(173, 146, "= 1.65 F / 5.4 V", 2.5, "L")

# C4
t4, b4 = cap_polar_v(XC4, 160)
layer("wires"); line((XC4, YT), (XC4, t4)); line((XC4, b4), (XC4, YG)); dot(XC4, YT); dot(XC4, YG)
layer("text"); text(218, 163, "C4", 3.5, "L"); text(218, 158, "100 µF", 3, "L"); text(218, 154, "low ESR", 2.5, "L")

# ground symbol
ground(130, YG)
layer("nets"); text(130, 89, "GND", 3.5)

# ---------- U1 ----------
layer("symbols"); rect(UX1, UY1, UX2, UY2)
layer("wires")
line((XBR, YT), (XBR, P3V3), (UX1, P3V3)); dot(XBR, YT)
line((XBR, YG), (XBR, PG), (UX1, PG)); dot(XBR, YG)
line((UX2, PRST), (XJP, PRST), (XJP, PRST-5))
line((UX2, PA0), (UX2+8, PA0))
line((UX2, PD1), (XSW, PD1))
line((UX2, PD4), (UX2+8, PD4))
nc_mark(UX2+9.5, PA0)
layer("text")
text(UX1+3, P3V3, "3V3", 3, "ML"); text(UX1+3, PG, "G", 3, "ML")
text(UX2-3, PRST, "RST", 3, "MR"); text(UX2-3, PA0, "A0", 3, "MR")
text(UX2-3, PD1, "D1", 3, "MR"); text(UX2-3, PD4, "D4", 3, "MR")
text(270, 172, "U1", 4.5); text(270, 165, "D1 mini", 3.5); text(270, 159, "ESP8266 / CH340", 3)
text(270, 119, "USB: programming only, SW2 OFF", 2.3)
text(UX2+12, PA0, "n.c.", 2.5, "ML")
text(UX2+12, PD4+0.5, "GPIO2: LED on board", 2.5, "ML"); text(UX2+12, PD4-3.5, "(active-low)", 2.3, "ML")
text(UX2+11, PD1+3.5, "GPIO5", 2.5, "L")
layer("nets"); text(338, PD1+3.5, "BTN", 3.5)

# ---------- button node ----------
jumper_v(XJP, PD1+12, PD1+20)   # 167 .. 175
layer("wires"); line((XJP, PRST-5), (XJP, PD1+23)); line((XJP, PD1+9), (XJP, PD1)); dot(XJP, PD1)
layer("text"); text(XJP+5, 171, "JP1", 3.5, "L"); text(XJP+5, 167, "RST", 2.5, "L")

resistor_v(XR2, 180)
layer("wires"); line((XR2, YT), (XR2, 188)); line((XR2, 172), (XR2, PD1)); dot(XR2, PD1)
layer("text"); text(XR2+4.5, 183, "R2", 3.5, "L"); text(XR2+4.5, 178, "10 k", 3.5, "L")

tc, bc = cap_v(XC3, 128)
layer("wires"); line((XC3, PD1), (XC3, tc)); line((XC3, bc), (XC3, YG)); dot(XC3, PD1); dot(XC3, YG)
layer("text"); text(XC3-6, 131, "C3", 3.5, "R"); text(XC3-6, 126, "100 nF", 3, "R")

pushbutton_v(XSW, 135, 118)
layer("wires"); line((XSW, PD1), (XSW, 135.8)); line((XSW, 117.2), (XSW, YG))
layer("text"); text(XSW+4, 131, "SW1", 3.5, "L"); text(XSW+4, 126.5, "tactile", 2.8, "L"); text(XSW+4, 122.5, "100 gf", 2.8, "L")

# ---------- notes ----------
layer("notes")
notes = ("NOTES\\P"
 "1. SW2 OFF before connecting USB: the on-board USB LDO (3.3 V) would push current back into the cell.\\P"
 "2. A0 must stay unconnected (ADC_VCC): the firmware reads VCC with ADC_MODE(ADC_VCC).\\P"
 "3. C1 + C2 in series = 1.65 F / 5.4 V. R1 limits the cell current (<= 45 mA at insertion, then < 5 mA), tau = 112 s.\\P"
 "4. JP1 closed = battery mode: a press pulls RST low and wakes U1 from deep sleep. JP1 open = always_on (USB).\\P"
 "5. U1 is fed directly on its 3V3 pin (on-board LDO bypassed). Standby 0.2-0.3 mA => about 4-6 weeks per CR2032.\\P"
 "6. GPIO2 drives the LED already on the D1 mini (active-low): one blink per publish. SW1 pressed = GPIO5 LOW.")
cmd("mtext", at=[15, 70], text=notes, height=2.5, width=232, attach=1, lineSpacing=1.15)

cmd("zoom", mode="extents")
sys.stdout.write("\n".join(out) + "\n")
