#!/usr/bin/env python3
"""Generates schematic.scr (CADCraft script) for the ESP8266 D1 mini MQTT button, hardware rev B.1 (LiPo + I2S audio)."""
import json, sys

out = ["; schematic.scr - ESP8266 D1 mini MQTT battery button, schematic rev B.3 (CADCraft script, mm).",
       "; Replay: cadcraft-cli run --metric --script-file schematic.scr --save schematic.dxf --export schematic.png",
       "; Circuit per hardware/DESIGN.md sections 1-4. Layers: frame, symbols, wires, text, nets, notes."]
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

# ---------- symbol helpers ----------
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

def diode_h(x1, x2, y):
    """anode at x1, cathode (bar) at x2"""
    layer("symbols")
    xa, xk = x1+3, x2-3
    line((x1, y), (xa, y)); line((xk, y), (x2, y))
    cmd("pline", vertices=[[xa, y+3.5], [xk, y], [xa, y-3.5]], closed=True)
    thick((xk, y+3.5), (xk, y-3.5), w=0.6)

def resistor_v(x, yc, L=16, H=5):
    layer("symbols"); rect(x-H/2, yc-L/2, x+H/2, yc+L/2)

def cap_polar_v(x, yc, hw=4.5, plus_dx=-7):
    layer("symbols")
    line((x-hw, yc+1.2), (x+hw, yc+1.2))
    r = 7.5; arc(x, yc-1.2-r, r, 55, 125)
    text(x+plus_dx, yc+4, "+", 4)
    return yc+1.2, yc-1.2

def cap_v(x, yc, hw=4):
    layer("symbols")
    line((x-hw, yc+1.2), (x+hw, yc+1.2)); line((x-hw, yc-1.2), (x+hw, yc-1.2))
    return yc+1.2, yc-1.2

def pushbutton_v(x, y_top, y_bot):
    layer("symbols")
    circle(x, y_top, 0.8); circle(x, y_bot, 0.8)
    line((x-5, y_top+1.5), (x-5, y_bot-1.5))
    ym = (y_top+y_bot)/2
    line((x-5, ym), (x-9, ym)); line((x-9, ym-2), (x-9, ym+2))

def jumper_h(x1, x2, y):
    """JP1 solder bridge: two pads, bridged (battery mode)"""
    layer("symbols")
    rect(x1, y-3, x2, y+3)
    dot(x1+3.5, y); dot(x2-3.5, y)
    thick((x1+3.5, y), (x2-3.5, y), w=1.2)          # solder bridge closed

def connector_v(x, y_top, y_bot):
    """2-pin connector drawn on two horizontal wires"""
    layer("symbols")
    rect(x-4, y_bot-6, x+4, y_top+6)
    for y in (y_top, y_bot):
        circle(x, y, 1.3); line((x-4, y), (x-1.3, y)); line((x+1.3, y), (x+4, y))

def ground(x, y):
    layer("symbols")
    line((x, y), (x, y-6)); line((x-5, y-6), (x+5, y-6)); line((x-3, y-8), (x+3, y-8)); line((x-1.2, y-10), (x+1.2, y-10))

def mic_v(x, yc, r=5):
    """electret capsule: circle with the two internal plates; terminals top and bottom"""
    layer("symbols")
    circle(x, yc, r)
    line((x-3, yc+1.2), (x+3, yc+1.2)); line((x-3, yc-1.2), (x+3, yc-1.2))
    line((x, yc+r), (x, yc+1.2)); line((x, yc-1.2), (x, yc-r))

def nc_mark(x, y):
    layer("symbols"); line((x-1.3, y-1.3), (x+1.3, y+1.3)); line((x-1.3, y+1.3), (x+1.3, y-1.3))

# ---------- geometry ----------
XB = 45; YBP, YBN = 195, 160          # BT1 wires (+ top, - bottom)
XJ = 65                               # J1
M1X1, M1Y1, M1X2, M1Y2 = 85, 150, 145, 207
YOUT, YCHRG = 190, 170                # M1 right pins
XSW1, XSW2 = 160, 180                 # SW2
XD1, XD2 = 185, 199                   # D2
UX1, UY1, UX2, UY2 = 240, 100, 300, 212
P3V3, P5V, PD0, PD4, PG = 204, 190, 150, 125, 110                 # U1 left pins
PRST, PD1, PA0, PD2, PD7, PD5, PD6 = 200, 188, 172, 140, 128, 118, 108  # U1 right pins
YBUS = 225; XBUS = 215; XC4 = 205; XR3 = 195
XJP1, XJP2 = 318, 332; XJPD = 340
XR2, XC3, XSW = 350, 365, 385
XJ2 = 325; XGM = 312                                             # J2 mic header, mic ground
M2X1, M2Y1, M2X2, M2Y2 = 345, 80, 395, 145
YVDD, YSCK, YWS, YSD, YLR, YGNDM = PD2, PD7, PD5, PD6, 98, 88

# ---------- frame & title block ----------
layer("frame")
rect(10, 10, 430, 270)
rect(270, 10, 430, 40); line((270, 28), (430, 28)); line((360, 10), (360, 28)); line((400, 10), (400, 28))
layer("text")
text(350, 34, "ESP8266 D1 mini MQTT battery button", 4.5)
text(275, 21.5, "Rev B.3: LiPo, button, I2S mic", 3, "L")
text(275, 14, "Date: 2026-10-26", 3, "L")
text(380, 21.5, "Rev B.3", 3); text(380, 14, "CADCraft", 3)
text(415, 21.5, "Sheet", 3); text(415, 14, "1 / 1", 3)

# ---------- battery, connector, charger ----------
battery(XB, 177.5)
layer("text")
text(37, 183, "BT1", 3.5, "R"); text(37, 178, "LiPo 3.7 V", 3, "R"); text(37, 173.5, "1000 mAh", 3, "R"); text(37, 169, "803040", 2.6, "R")
connector_v(XJ, YBP, YBN)
layer("text"); text(XJ, 206, "J1", 3.5); text(XJ, 210.5, "JST-PH 2.0", 2.6)
layer("wires")
line((XB, YBP), (XB, 179.5)); line((XB, 175.5), (XB, YBN))
line((XB, YBP), (XJ-4, YBP)); line((XJ+4, YBP), (M1X1, YBP))
line((XB, YBN), (XJ-4, YBN)); line((XJ+4, YBN), (M1X1, YBN))
layer("nets"); text(78, 199, "VBAT", 3.5)

layer("symbols"); rect(M1X1, M1Y1, M1X2, M1Y2)
layer("text")
text(M1X1+3, YBP, "B+", 3, "ML"); text(M1X1+3, YBN, "B-", 3, "ML")
text(M1X2-3, YOUT, "OUT+", 3, "MR"); text(M1X2-3, YCHRG, "CHRG", 3, "MR")
text(103, 154, "OUT-", 2.6, "ML")
text(115, 186, "M1", 4.5); text(115, 179, "TP4056 + DW01", 3); text(115, 173.5, "LiPo charger 1 A", 2.6)
text(115, 166, "USB-C (charge only)", 2.4)
layer("wires")
line((M1X2, YOUT), (XSW1, YOUT))
line((100, M1Y1), (100, 140)); ground(100, 140)
layer("text"); text(100, 126, "GND", 2.5)

# ---------- switch, diode, 5V ----------
slide_switch_h(XSW1, XSW2, YOUT)
layer("text"); text(170, 205, "SW2", 3.5); text(170, 200.5, "POWER", 3)
diode_h(XD1, XD2, YOUT)
layer("text"); text(192, 200.5, "D2", 3.5); text(192, 196, "SS14", 2.8)
layer("wires"); line((XSW2, YOUT), (XD1, YOUT)); line((XD2, YOUT), (UX1, P5V))
layer("nets"); text(182.5, 184, "VSW", 3); text(222, 194, "5V", 3.5)

# ---------- 3V3 bus + C4 ----------
layer("wires")
line((UX1, P3V3), (XBUS, P3V3), (XBUS, YBUS)); line((XC4, YBUS), (XR2, YBUS)); dot(XBUS, YBUS)
t4, b4 = cap_polar_v(XC4, 213.5, plus_dx=6)
layer("wires"); line((XC4, YBUS), (XC4, t4)); line((XC4, b4), (XC4, 207)); ground(XC4, 207)
layer("text"); text(199, 218, "C4", 3.5, "R"); text(199, 213, "100 µF", 3, "R"); text(199, 209, "low ESR", 2.5, "R")
layer("nets"); text(280, 229, "3V3", 3.5)

# ---------- CHRG wire M1 -> D0 with R3 pull-up (3V3 flag) ----------
layer("wires"); line((M1X2, YCHRG), (165, YCHRG), (165, PD0), (UX1, PD0)); dot(XR3, PD0)
resistor_v(XR3, 166)
layer("wires"); line((XR3, PD0), (XR3, 158)); line((XR3, 174), (XR3, 180))
layer("symbols"); line((XR3-4, 180), (XR3+4, 180))
layer("nets"); text(XR3, 184, "3V3", 3); text(222, PD0+3.5, "CHRG", 3)
layer("text"); text(XR3+4, 169, "R3", 3, "L"); text(XR3+4, 164, "10 k", 3, "L"); text(215, PD0-3.5, "open drain, low = charging", 2.3)

# ---------- U1 ----------
layer("symbols"); rect(UX1, UY1, UX2, UY2)
layer("wires"); line((UX1, PG), (230, PG), (230, 100)); ground(230, 100)
layer("wires"); line((UX1, PD4), (UX1-10, PD4))
layer("text"); text(230, 86, "GND", 2.5)
layer("text")
text(UX1+3, P3V3, "3V3", 3, "ML"); text(UX1+3, P5V, "5V", 3, "ML"); text(UX1+3, PD0, "D0 GPIO16", 2.6, "ML")
text(UX1+3, PD4, "D4 GPIO2", 2.6, "ML"); text(UX1+3, PG, "G", 3, "ML")
text(UX2-3, PRST, "RST", 3, "MR"); text(UX2-3, PD1, "D1 GPIO5", 2.6, "MR"); text(UX2-3, PA0, "A0", 2.6, "MR")
text(UX2-3, PD2, "D2 GPIO4", 2.6, "MR"); text(UX2-3, PD7, "D7 GPIO13", 2.6, "MR")
text(UX2-3, PD5, "D5 GPIO14", 2.6, "MR"); text(UX2-3, PD6, "D6 GPIO12", 2.6, "MR")
text(270, 178, "U1", 4.5); text(270, 171, "D1 mini", 3.5); text(270, 165, "ESP8266 / CH340", 3)
text(270, 104, "micro-USB: programming, any time", 2.2)
text(UX1-12, PD4+1.8, "LED on board", 2.2, "MR"); text(UX1-12, PD4-2.2, "(active-low)", 2.2, "MR")
layer("nets"); text(UX1-12, PD4+5.6, "LED", 2.6, "MR")
layer("wires"); line((UX2, PA0), (UX2+10, PA0)); nc_mark(UX2+11.5, PA0)
layer("text"); text(UX2+14, PA0, "n.c.", 2.4, "ML")

# ---------- button node ----------
layer("wires")
line((UX2, PRST), (XJP1, PRST)); line((XJP2, PRST), (XJPD, PRST), (XJPD, PD1))
line((UX2, PD1), (XSW, PD1)); dot(XJPD, PD1)
jumper_h(XJP1, XJP2, PRST)
layer("text"); text(325, 207, "JP1", 3.5); text(325, 193.5, "solder bridge", 2.2)
layer("nets"); text(357, PD1+3.5, "BTN", 3.5)

resistor_v(XR2, 206.5)
layer("wires"); line((XR2, YBUS), (XR2, 214.5)); line((XR2, 198.5), (XR2, PD1)); dot(XR2, PD1); dot(XR2, YBUS)
layer("text"); text(XR2+4, 209, "R2", 3.5, "L"); text(XR2+4, 204, "10 k", 3.5, "L")

tc, bc = cap_v(XC3, 174.5)
layer("wires"); line((XC3, PD1), (XC3, tc)); line((XC3, bc), (XC3, 168)); ground(XC3, 168); dot(XC3, PD1)
layer("text"); text(XC3-6, 177.5, "C3", 3.5, "R"); text(XC3-6, 172.5, "100 nF", 3, "R")

pushbutton_v(XSW, 178, 162)
layer("wires"); line((XSW, PD1), (XSW, 178.8)); line((XSW, 161.2), (XSW, 158)); ground(XSW, 158)
layer("text"); text(XSW+4, 174, "SW1", 3.5, "L"); text(XSW+4, 169.5, "tactile", 2.8, "L"); text(XSW+4, 165.5, "100 gf", 2.8, "L")

# ---------- audio: J2 header + M2 INMP441 (in the lid) ----------
layer("symbols"); rect(XJ2-4, YGNDM-6, XJ2+4, YVDD+6)
for y in (YVDD, YSCK, YWS, YSD, YLR, YGNDM):
    circle(XJ2, y, 1.3)
layer("wires")
for py, my in ((PD2, YVDD), (PD7, YSCK), (PD5, YWS), (PD6, YSD)):
    line((UX2, py), (XJ2-1.3, my)); line((XJ2+1.3, my), (M2X1, my))
line((XJ2-1.3, YLR), (XGM, YLR), (XGM, 78)); line((XJ2-1.3, YGNDM), (XGM, YGNDM)); dot(XGM, YGNDM); ground(XGM, 78)
line((XJ2+1.3, YLR), (M2X1, YLR)); line((XJ2+1.3, YGNDM), (M2X1, YGNDM))
layer("symbols"); rect(M2X1, M2Y1, M2X2, M2Y2)
layer("nets")
text(337, YVDD+2.6, "MICPWR", 2.2); text(337, YSCK+2.6, "I2S_SCK", 2.2); text(337, YWS+2.6, "I2S_WS", 2.2); text(337, YSD+2.6, "I2S_SD", 2.2)
layer("text")
text(XJ2, 151, "J2", 3); text(XJ2, 155.5, "6-pin header", 2.2)
text(XGM, 64, "GND", 2.5)
text(M2X1+3, YVDD, "VDD", 2.6, "ML"); text(M2X1+3, YSCK, "SCK", 2.6, "ML"); text(M2X1+3, YWS, "WS", 2.6, "ML")
text(M2X1+3, YSD, "SD", 2.6, "ML"); text(M2X1+3, YLR, "L/R", 2.6, "ML"); text(M2X1+3, YGNDM, "GND", 2.6, "ML")
text(376, 131, "M2", 4); text(376, 124, "INMP441", 3); text(376, 118.5, "I2S MEMS mic", 2.3); text(376, 113.5, "11 × 14 mm breakout", 2.2)
text(376, 108.5, "under the lid,", 2.2); text(376, 104, "6 wires to J2", 2.2); text(376, 96, "L/R = GND: left ch.", 2.1)

# ---------- notes ----------
layer("notes")
notes = ("NOTES\\P"
 "1. Rev B: LiPo 1000 mAh replaces the CR2032 of rev A (audio recording needs about 75 mA for minutes).\\P"
 "2. Charge only via M1's USB-C port (TP4056, 1 A default; R_PROG 2.4 k for 0.5 A). DW01 protects the cell.\\P"
 "3. D2 blocks USB back-feed into the LiPo: USB programming is allowed at any time, with SW2 in any position.\\P"
 "4. A0 n.c.; I2S mic on GPIO12/13/14 (the ESP8266's fixed I2S RX pins): SCK = D7, WS = D5, SD = D6, L/R to GND (left channel).\\P"
 "5. M2 VDD power-gated by D2/GPIO4 (1.4 mA). M1 CHRG (open drain, low = charging) -> D0/GPIO16, R3 10 k pull-up to 3V3.\\P"
 "6. JP1 (solder bridge) closed = battery mode: a press pulls RST low and wakes U1 from deep sleep. Open = always_on (USB).\\P"
 "7. GPIO2 drives the LED already on the D1 mini (active-low): on while recording. SW1 pressed = GPIO5 LOW.\\P"
 "8. Rev B.1: M2 INMP441 (11 x 14 mm) sits in a pocket under the lid, sound port over a 2 mm hole; 6 wires to header J2.")
cmd("mtext", at=[15, 76], text=notes, height=2.5, width=250, attach=1, lineSpacing=1.15)

cmd("zoom", mode="extents")
sys.stdout.write("\n".join(out) + "\n")
