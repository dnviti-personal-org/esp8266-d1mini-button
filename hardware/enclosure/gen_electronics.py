#!/usr/bin/env python3
"""rev C electronics generator: every lead in its layout.json hole, all wiring modelled.
Run from the staging dir (C:/Users/daniele/esp-button-cad/enclosure) with the layout.json path as argv[1]."""
import json, math, sys
L = json.load(open(sys.argv[1]))
M = "C:/Users/daniele/esp-button-cad/models/"
E = []; ALL = []; COL = {}
OFF = L["board"]["cavity_offset"]          # (2.46, 1.73)
PX0, PY0 = 2 + OFF[0], 2 + OFF[1]           # perfboard origin, world (4.46, 3.73)
PZ0 = 13.0; PT = 1.6; PTOP = PZ0 + PT       # underside / top, world

def P(n, e, c=None): E.append({"command": "parameters.add", "params": {"name": n, "expression": e, **({"comment": c} if c else {})}})
P("pcb_x0", f"{PX0} mm", "perfboard origin, world x (= wall 2 + cavity offset 2.46, layout.json)")
P("pcb_y0", f"{PY0} mm", "perfboard origin, world y (= wall 2 + cavity offset 1.73, layout.json)")
P("pcb_z0", "13 mm", "perfboard underside, world z (= floor 2 + standoff 11)")
P("pcb_t", "1.6 mm", "perfboard thickness")
P("pcb_top", "pcb_z0 + pcb_t", "perfboard top face, world z (cavity 12.6)")
P("hdr_h", "2.54 mm", "pin-header plastic = module standoff height")
P("wire_z", "pcb_z0 - 0.6 mm", "axis of the solder-side wires (cavity 10.4)")
def X(v): return f"pcb_x0 + {round(v, 3)} mm"
def Y(v): return f"pcb_y0 + {round(v, 3)} mm"
def Z(v=0): return f"pcb_top + {round(v, 3)} mm" if v else "pcb_top"
def reg(*names): ALL.extend(names)
def box(body, Lh, W, H, c, color=None, join=None, label=None):
    p = {"length": f"{Lh} mm", "width": f"{W} mm", "height": f"{H} mm", "corner": list(c), "name": label or body}
    if join: p.update({"operation": "join", "targets": [join]})
    else: p.update({"operation": "new", "body_name": body}); reg(body)
    E.append({"command": "solid.box", "params": p})
    if color: COL[body] = color
def cyl(body, d, h, b, axis="Z", color=None, join=None, label=None, cut=None):
    if isinstance(axis, list):
        n = math.sqrt(sum(v * v for v in axis)); axis = [round(v / n, 6) for v in axis]
    p = {"diameter": f"{d} mm", "height": f"{round(h, 3)} mm", "base": list(b), "axis": axis, "name": label or body}
    if cut: p.update({"operation": "cut", "targets": [cut]})
    elif join: p.update({"operation": "join", "targets": [join]})
    else: p.update({"operation": "new", "body_name": body}); reg(body)
    E.append({"command": "solid.cylinder", "params": p})
    if color: COL[body] = color
def ins(refdes, file, bodyname, newname, tr, axis=None, angle=None, steps=None, up=None, color=None):
    p = {"path": M + file, "name": refdes}
    if up: p["up"] = up
    E.append({"command": "file.insert_step", "params": p})
    E.append({"command": "body.rename", "params": {"body": bodyname, "name": newname}}); reg(newname)
    if steps:
        for ax, an in steps[:-1]: E.append({"command": "solid.move", "params": {"bodies": [newname], "axis": ax, "angle": an}})
        ax, an = steps[-1]; E.append({"command": "solid.move", "params": {"bodies": [newname], "axis": ax, "angle": an, "translate": list(tr)}})
    elif axis: E.append({"command": "solid.move", "params": {"bodies": [newname], "axis": axis, "angle": angle, "translate": list(tr)}})
    else: E.append({"command": "solid.move", "params": {"bodies": [newname], "translate": list(tr)}})
    if color: COL[newname] = color

parts = {p["ref"]: p for p in L["parts"]}
def H(ref, pin): return tuple(parts[ref]["holes"][pin]["xy"])
G = L["grid"]

# ---------------- PCB1 perfboard 70 x 50 x 1.6, 5 x 5 notches, 4 x O2.2 mounting holes on grid holes, 24 x 18 grid ----------------
box("PCB1", 70, 50, 1.6, ("pcb_x0", "pcb_y0", "pcb_z0"), "#2e7d32", label="PCB1_board")
N = L["board"]["notch"]
for i, (nx, ny) in enumerate(((0, 0), (70 - N, 0), (0, 50 - N), (70 - N, 50 - N)), 1):
    E.append({"command": "solid.box", "params": {"length": f"{N} mm", "width": f"{N} mm", "height": "3 mm", "corner": [X(nx), Y(ny), "pcb_z0 - 0.5 mm"], "operation": "cut", "targets": ["PCB1"], "name": f"PCB1_notch{i}"}})
for i, m in enumerate(L["mount"], 1):
    cyl("PCB1", m["d"], 3, (X(m["xy"][0]), Y(m["xy"][1]), "pcb_z0 - 0.5 mm"), cut="PCB1", label=f"PCB1_mount_{m['name']}")
E += [{"command": "sketch.create", "params": {"plane": "XY", "offset": "pcb_z0", "name": "PCB1_grid"}},
      {"command": "sketch.circle.center", "params": {"center": [PX0 + G["x0"], PY0 + G["y0"]], "diameter": G["hole_d"]}},
      {"command": "sketch.pattern.rectangular", "params": {"entities": ["c1"], "count": len(G["cols"]), "spacing": G["pitch"], "count2": G["rows"], "spacing2": G["pitch"]}},
      {"command": "sketch.finish", "params": {}},
      {"command": "solid.extrude", "params": {"sketch": "PCB1_grid", "distance": "pcb_t", "operation": "cut", "targets": ["PCB1"], "profiles": "all", "name": "PCB1_holes"}}]

# ---------------- U1 D1 mini (Technariumas, Y-up) on two flipped 1x08 headers: pins A3..A10 / J3..J10 ----------------
hy = H("U1", "3V3")[1]                                   # row 3
for h, pin in (("U1_H1", "3V3"), ("U1_H2", "5V")):
    xx = H("U1", pin)[0]
    ins(h, "PinHeader_1x08_P2.54mm_Vertical.step", "PinHeader_1x08_P254mm_Vertical", h, (X(xx), Y(hy), Z(2.54)), axis=[1, 0, 0], angle="180 deg")
    E.append({"command": "solid.box", "params": {"length": "5 mm", "width": "25 mm", "height": "pcb_z0 - 1 mm", "corner": [X(xx - 2.5), Y(hy - 3.5), "0 mm"], "operation": "cut", "targets": [h], "name": h + "_trim"}})
E.append({"command": "file.insert_step", "params": {"path": M + "WEMOS_D1_mini_Technariumas.step", "name": "U1", "up": "y"}})
E.append({"command": "solid.remove", "params": {"bodies": ["USB Micro"]}})
for a, b in (("PCB", "U1"), ("Default (29)", "U1_shield"), ("Default (30)", "U1_esp_pcb"), ("Default (25)", "U1_CH340"), ("Default (28)", "U1_reset")):
    E.append({"command": "body.rename", "params": {"body": a, "name": b}})
u1_small = ["Default"] + [f"Default ({i})" for i in range(2, 31) if i not in (25, 28, 29, 30)]
u1_bodies = ["U1", "U1_shield", "U1_esp_pcb", "U1_CH340", "U1_reset"] + u1_small; reg(*u1_bodies)
# NOTE: numeric translation on purpose - on a Y-up import SolidCraft applies expression translations in the component frame.
# Module origin = perf (30.02, 0.28): header pin 1 lands on A3 / J3 (checked against the B.3 placement, +1.42 / +0.28 mm).
U1X, U1Y = H("U1", "5V")[0] + 1.37, hy - 8.21
E.append({"command": "solid.move", "params": {"bodies": u1_bodies, "translate": [round(PX0 + U1X, 3), round(PY0 + U1Y, 3), round(PTOP + 2.54, 3)]}})
COL["U1"] = "#15265f"
COL["U1_shield"] = {"color": "#b4b8bc", "pbr": {"metallic": 0.9, "roughness": 0.35, "dielectric_ior": 1.5}}
# real micro-B on the shield side (the STEP has it underneath), 1 mm proud of the module edge
ins("U1_USB", "USB_Micro-B_Molex_47346-0001.step", "USB_Micro-B_Molex_47346-0001", "U1_USB", (X(U1X - 13.25), Y(U1Y + 2.77), Z(2.54 + 1.5 + 0.24)))

# ---------------- SW1 tactile 12 mm (Wuerth STEP, actuator cut to the B3F-4000's 7.3 mm): pins K9 P9 K11 P11 ----------------
sx = (H("SW1", "1a")[0] + H("SW1", "1b")[0]) / 2; sy = (H("SW1", "1a")[1] + H("SW1", "2a")[1]) / 2   # (37.54, 26.27)
ins("SW1", "SW_PUSH-12mm_Wuerth-430476085716.step", "SW_PUSH-12mm_Wuerth-430476085716", "SW1", (X(sx - 6.25), Y(sy + 2.5), Z()))
E.append({"command": "solid.box", "params": {"length": "16 mm", "width": "16 mm", "height": "4 mm", "corner": [X(sx - 8), Y(sy - 8), Z(7.3)], "operation": "cut", "targets": ["SW1"], "name": "SW1_actuator_trim"}})

# ---------------- M1 TP4056 USB-C module glued flat: 1 mm foam + 1 mm PCB, no pins; USB-C centred x 55.04 ----------------
mb = parts["M1"]["body"]                                  # (46.29, -0.5, 63.79, 25.5)
box("M1_foam", mb[2] - mb[0], mb[3], 1.0, (X(mb[0]), Y(0), Z()), "#e8e8e8")
box("M1_PCB", mb[2] - mb[0], mb[3] - mb[1], 1.0, (X(mb[0]), Y(mb[1]), Z(1.0)), "#1e4fa3")
MT = 2.0                                                  # module top above the perfboard
padpos = dict(L["m1_pads"]); padpos.update({"IN+": (47.5, 5.0), "IN-": (62.5, 5.0)})
for k, (px, py) in padpos.items():
    cyl("M1_pad_" + k.replace("+", "p").replace("-", "m"), 1.5, 0.05, (X(px), Y(py), Z(MT)), color="#b87333")
E.append({"command": "file.insert_step", "params": {"path": M + "USB_C_Receptacle_GCT_USB4125-xx-x_6P_TopMnt_Horizontal.step", "name": "M1_USBC"}})
usbc = ["USB_C_Receptacle_GCT_USB4125-xx-x_6P_TopMnt_Horizontal"] + [f"USB_C_Receptacle_GCT_USB4125-xx-x_6P_TopMnt_Horizontal ({i})" for i in range(2, 17)]; reg(*usbc)
E.append({"command": "solid.move", "params": {"bodies": usbc, "translate": [X(55.04), Y(mb[1] + 2.4), Z(MT)]}})
ins("M1_U1", "SOIC-8_3.9x4.9mm_P1.27mm.step", "SOIC-8_3.9x4.9mm_P1.27mm", "M1_U1", (X(55.04), Y(12.5), Z(MT)))
ins("M1_U2", "SOT-23-6.step", "SOT-23-6", "M1_U2", (X(51.5), Y(19.75), Z(MT)))
ins("M1_U3", "TSSOP-8_4.4x3mm_P0.65mm.step", "TSSOP-8_4.4x3mm_P0.65mm", "M1_U3", (X(57.5), Y(19.75), Z(MT)))
# LEDs beside the USB-C, under the lid window (cavity x 57..67, y 3.25..5.75)
ins("M1_LED_red", "LED_0603_1608Metric.step", "LED_0603_1608Metric", "M1_LED_red", (X(60.8), Y(3.5), Z(MT)), color="#e53935")
ins("M1_LED_blue", "LED_0603_1608Metric.step", "LED_0603_1608Metric", "M1_LED_blue", (X(62.8), Y(3.5), Z(MT)), color="#1e88e5")
for i, (px, py) in enumerate(((60.8, 6.5), (62.8, 6.5), (49.0, 8.0)), 1):
    ins(f"M1_R{i}", "R_0603_1608Metric.step", "R_0603_1608Metric", f"M1_R{i}", (X(px), Y(py), Z(MT)))
ins("M1_C1", "C_0603_1608Metric.step", "C_0603_1608Metric", "M1_C1", (X(49.0), Y(10.0), Z(MT)))
ins("M1_C2", "C_0805_2012Metric.step", "C_0805_2012Metric", "M1_C2", (X(52.5), Y(16.0), Z(MT)))
ins("M1_C3", "C_0805_2012Metric.step", "C_0805_2012Metric", "M1_C3", (X(57.5), Y(16.0), Z(MT)))

# ---------------- J2 right-angle 1x06: THT pins Q17..V17, bent pins toward row 18, trimmed at the board edge ----------------
j2 = H("J2", "SCK")
ins("J2", "PinHeader_1x06_P2.54mm_Horizontal.step", "PinHeader_1x06_P254mm_Horizontal", "J2", (X(j2[0]), Y(j2[1]), Z()), axis=[0, 0, 1], angle="90 deg")
E.append({"command": "solid.box", "params": {"length": "25 mm", "width": "10 mm", "height": "10 mm", "corner": [X(40), Y(49.5), Z(-4)], "operation": "cut", "targets": ["J2"], "name": "J2_trim"}})
# ---------------- J1 JST-PH S2B-PH-K: pins X14/X15 (2.0 mm pins centred between the 2.54 mm holes), mouth toward +x ----------------
j1a, j1b = H("J1", "1 (+)"), H("J1", "2 (−)")
J1Y = (j1a[1] + j1b[1]) / 2 - 1.0
ins("J1", "JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal.step", "JST_S2B_PH_K", "J1", (X(j1a[0]), Y(J1Y), Z()), axis=[0, 0, 1], angle="90 deg")
# ---------------- SW2 slide switch (C&K OS102011MS2Q STEP as stand-in for SS12D00G4) on its side at the left board edge ----------------
# native: body x -2.3..6.3 (8.6), y +-2.15 (4.3), z 0..4.7 body / -2.8..0 pins / 4.7..8.7 lever.  Mapping: native z -> world -x
# (lever toward the x = 0 wall), native x -> +y, native y -> -z.  Pin-exit face (native z = 0) at perf x 4.8, body resting on the board.
E.append({"command": "file.insert_step", "params": {"path": M + "SW_Slide_SPDT_Straight_CK_OS102011MS2Q.step", "name": "SW2"}})
sw2n = "SW_Slide_SPDT_Straight_CK_OS102011MS2Q"
E.append({"command": "solid.remove", "params": {"bodies": [f"{sw2n} ({i})" for i in (3, 4, 5)]}})   # straight pins -> replaced by bent ones
for a, b in ((sw2n, "SW2"), (f"{sw2n} (2)", "SW2_frame"), (f"{sw2n} (6)", "SW2_knob")):
    E.append({"command": "body.rename", "params": {"body": a, "name": b}})
sw2 = ["SW2", "SW2_frame", "SW2_knob"]; reg(*sw2)
sb = parts["SW2"]["body"]                                 # (1.1, 37.21, 4.8, 45.81)
SW2_FACE = sb[2]; SW2_YC = (sb[1] + sb[3]) / 2; SW2_ZC = 2.15      # knob/pin centre above the board top
E.append({"command": "solid.move", "params": {"bodies": sw2, "axis": [0, 0, 1], "angle": "90 deg"}})
E.append({"command": "solid.move", "params": {"bodies": sw2, "axis": [0, 1, 0], "angle": "-90 deg", "translate": [X(SW2_FACE), Y(SW2_YC - 2.0), Z(SW2_ZC)]}})
E.append({"command": "solid.box", "params": {"length": "4 mm", "width": "12 mm", "height": "8 mm", "corner": [X(SW2_FACE), Y(SW2_YC - 6), Z(-2)], "operation": "cut", "targets": ["SW2"], "name": "SW2_tails_trim"}})
COL["SW2"] = "#2b2b2b"; COL["SW2_knob"] = "#111111"; COL["SW2_frame"] = "#9e9e9e"
for i, (pin, yexit) in enumerate((("ON", SW2_YC - 2.0), ("COM", SW2_YC), ("NC", SW2_YC + 2.0)), 1):
    hx, hyy = H("SW2", pin)
    dx, dy = hx - SW2_FACE, hyy - yexit
    cyl(f"SW2_pin{i}", 0.6, math.hypot(dx, dy), (X(SW2_FACE), Y(yexit), Z(SW2_ZC)), axis=[round(dx, 3), round(dy, 3), 0], color="#c0c0c0")
    cyl(f"SW2_pin{i}", 0.64, 1 + PT + SW2_ZC + 0.35, (X(hx), Y(hyy), "pcb_z0 - 1 mm"), join=f"SW2_pin{i}", label=f"SW2_pin{i}_down")

# ---------------- axial / radial passives, pin 1 in its hole ----------------
ins("D2", "D_DO-41_SOD81_P10.16mm_Horizontal.step", "D_DO-41_SOD81_P10.16mm_Horizontal", "D2", (X(H("D2", "K")[0]), Y(H("D2", "K")[1]), Z()))
ins("R2", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal.step", "R_Axial_DIN0207_L63mm_D25mm_P1016mm_Horizontal", "R2", (X(H("R2", "1")[0]), Y(H("R2", "1")[1]), Z()))
ins("R3", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal.step", "R_Axial_DIN0207_L63mm_D25mm_P1016mm_Horizontal", "R3", (X(H("R3", "1")[0]), Y(H("R3", "1")[1]), Z()))
# C3 100 nF disc, 2.54 mm pitch (built: O5 x 2.5 disc 1.5 mm above the board, leads along y)
c3a, c3b = H("C3", "1"), H("C3", "2")
cyl("C3", 5.0, 2.5, (X(c3a[0] - 1.25), Y((c3a[1] + c3b[1]) / 2), Z(4.0)), axis="X", color="#d9a066")
for i, (hx, hyy) in enumerate((c3a, c3b), 1):
    cyl(f"C3_lead{i}", 0.5, 1 + PT + 4.0, (X(hx), Y(hyy), "pcb_z0 - 1 mm"), color="#c0c0c0")
# C4 100 uF O5 x 11 lying flat toward +x, axis 3 mm above the board, leads bent 90 deg into Q14 / Q15
c4m, c4p = H("C4", "-"), H("C4", "+")
cb = parts["C4"]["body"]                                   # (47.0, 35.2, 58.5, 40.2)
cyl("C4", 5.0, 11.0, (X(cb[0]), Y((cb[1] + cb[3]) / 2), Z(3.0)), axis="X", color="#1a237e")
cyl("C4_stripe", 5.06, 1.2, (X(cb[0] + 0.6), Y((cb[1] + cb[3]) / 2), Z(3.0)), axis="X", color="#eceff1")
for i, (hx, hyy) in enumerate((c4m, c4p), 1):
    cyl(f"C4_lead{i}", 0.54, 1 + PT + 3.0 + 0.3, (X(hx), Y(hyy), "pcb_z0 - 1 mm"), color="#c0c0c0")
    cyl(f"C4_lead{i}", 0.5, cb[0] - hx + 0.8, (X(hx), Y(hyy), Z(3.0)), axis="X", join=f"C4_lead{i}", label=f"C4_lead{i}_h")

# ---------------- solder-side wiring from layout.json: W<n>_<net> ----------------
WCOL = {"white": "#f5f5f5", "black": "#212121", "red": "#d32f2f", "violet": "#8A2BE2", "yellow": "#fdd835", "brown": "#6d4c41",
        "grey": "#9e9e9e", "green": "#43a047", "blue": "#1e88e5", "pink": "#FF69B4", "turquoise": "#30D5C8", "orange": "#fb8c00", "bare": "#c0c0c0"}
def stub(body, xy):
    cyl(body, 0.64, 2.7, (X(xy[0]), Y(xy[1]), "wire_z - 0.7 mm"), join=body, label=body + "_stub")   # pierces the wire (no equal-radius tangency)
    cyl(body, 1.8, 0.6, (X(xy[0]), Y(xy[1]), "pcb_z0 - 0.6 mm"), join=body, label=body + "_solder")
for w in L["wires"]:
    name = f"W{w['n']}_{w['net'].replace('-', 'm').replace('/', '')}"
    a, b = tuple(w["a"]), tuple(w["b"])
    if w["kind"] == "bridge":
        box(name, 1.6, abs(b[1] - a[1]) + 1.6, 0.6, (X(a[0] - 0.8), Y(min(a[1], b[1]) - 0.8), "pcb_z0 - 0.6 mm"), WCOL["bare"]); continue
    d = 1.1 if w["kind"] == "wire" else 0.6
    dx, dy = b[0] - a[0], b[1] - a[1]
    cyl(name, d, math.hypot(dx, dy), (X(a[0]), Y(a[1]), "wire_z"), axis=[round(dx, 3), round(dy, 3), 0], color=WCOL[w["colour"]])
    for end, xy in (("frm", a), ("to", b)):
        if w[end].startswith("M1:"):   # vertical run from the module pad down to the underside level (through module + board, as specified)
            cyl(name, d + 0.04, PT + MT + 0.6 + 0.3 + 0.7, (X(xy[0]), Y(xy[1]), "wire_z - 0.7 mm"), join=name, label=name + "_up")
        else:
            stub(name, xy)

# ---------------- BT1 LiPo 803040 on the floor under the board centre, kapton band, leads, PHR-2 plug in J1 ----------------
E.append({"command": "solid.box", "params": {"length": "40 mm", "width": "30 mm", "height": "8 mm", "corner": ["22 mm", "15 mm", "2 mm"], "operation": "new", "body_name": "BT1", "name": "BT1"}}); reg("BT1"); COL["BT1"] = "#9aa5ad"
E.append({"command": "solid.fillet", "params": {"body": "BT1", "edges": [[22, 15, 6], [62, 15, 6], [62, 45, 6], [22, 45, 6], [42, 15, 10], [62, 30, 10], [42, 45, 10], [22, 30, 10], [42, 15, 2], [62, 30, 2], [42, 45, 2], [22, 30, 2]], "radius": "1 mm", "name": "BT1_fillet"}})
E.append({"command": "solid.box", "params": {"length": "6 mm", "width": "30.4 mm", "height": "8.2 mm", "corner": ["56 mm", "14.8 mm", "2 mm"], "operation": "new", "body_name": "BT1_tape", "name": "BT1_tape"}}); reg("BT1_tape"); COL["BT1_tape"] = "#e6b800"
E.append({"command": "solid.combine", "params": {"target": "BT1_tape", "tools": ["BT1"], "operation": "cut", "keep_tools": True, "name": "BT1_tape_cut"}})
MOUTH = j1a[0] + 6.25                                      # J1 mouth, perf x (70.46)
PLUG_X0 = MOUTH - 3.5; PLUG_YC = J1Y + 1.0
LEAD_X = PX0 + MOUTH + 2.5 + 1.6                           # vertical lead run, world x (79.0)
for name, yw, col in (("BT1_wire_red", PY0 + J1Y, "#d32f2f"), ("BT1_wire_black", PY0 + J1Y + 2.0, "#212121")):
    yw = round(yw, 3)
    E.append({"command": "solid.cylinder", "params": {"diameter": "1.2 mm", "height": f"{round(LEAD_X - 62, 3)} mm", "base": [62, yw, 6], "axis": "X", "operation": "new", "body_name": name, "name": name}}); reg(name); COL[name] = col
    E.append({"command": "solid.cylinder", "params": {"diameter": "1.2 mm", "height": "11.1 mm", "base": [round(LEAD_X, 3), yw, 6], "axis": "Z", "operation": "join", "targets": [name], "name": name + "_up"}})
    E.append({"command": "solid.cylinder", "params": {"diameter": "1.2 mm", "height": "2.5 mm", "base": [round(LEAD_X, 3), yw, 17.1], "axis": [-1, 0, 0], "operation": "join", "targets": [name], "name": name + "_in"}})
E.append({"command": "solid.box", "params": {"length": "6 mm", "width": "4.75 mm", "height": "4 mm", "corner": [X(PLUG_X0), Y(PLUG_YC - 2.375), Z(0.5)], "operation": "new", "body_name": "BT1_plug", "name": "BT1_plug"}}); reg("BT1_plug"); COL["BT1_plug"] = "#f5f5f5"
E.append({"command": "solid.combine", "params": {"target": "BT1_plug", "tools": ["J1"], "operation": "cut", "keep_tools": True, "name": "BT1_plug_cut"}})

# ---------------- M2 INMP441 breakout in the lid pocket (unchanged from B.3) ----------------
E.append({"command": "solid.box", "params": {"length": "11 mm", "width": "14 mm", "height": "1 mm", "corner": ["70.5 mm", "23 mm", "26.2 mm"], "operation": "new", "body_name": "M2", "name": "M2"}}); reg("M2"); COL["M2"] = "#4a148c"
E.append({"command": "solid.cylinder", "params": {"diameter": "1 mm", "height": "3 mm", "base": [76, 30, 25.5], "operation": "cut", "targets": ["M2"], "name": "M2_port"}})
E.append({"command": "solid.box", "params": {"length": "4.72 mm", "width": "3.76 mm", "height": "1 mm", "corner": ["73.64 mm", "28.12 mm", "25.2 mm"], "operation": "new", "body_name": "M2_mic", "name": "M2_mic"}}); reg("M2_mic"); COL["M2_mic"] = "#b0bec5"
for i in range(6):
    n = f"M2_pad{i+1}"; E.append({"command": "solid.cylinder", "params": {"diameter": "1 mm", "height": "0.05 mm", "base": [71.5, 30 - 6.35 + 2.54 * i, 26.15], "operation": "new", "body_name": n, "name": n}}); reg(n); COL[n] = "#b87333"
ins("M2_C1", "C_0603_1608Metric.step", "C_0603_1608Metric", "M2_C1", (76, 33.5, 26.2), axis=[1, 0, 0], angle="180 deg")
M2_BODIES = ["M2", "M2_mic"] + [f"M2_pad{i}" for i in range(1, 7)] + ["M2_C1"]
for b, c in COL.items(): E.append({"command": "appearance.assign", "params": {"bodies": [b], **(c if isinstance(c, dict) else {"color": c})}})
json.dump({"commands": E}, open("electronics.script.json", "w"), indent=1)

# ---------------- full assembly variants ----------------
STRADDLE = ["PCB1", "BT1", "BT1_tape", "SW1", "U1", "U1_shield", "U1_esp_pcb", "M1_PCB", "M1_foam", "M2"]
def full(explode, variant=None):
    names = set(); cmds = []
    def add(c):
        if c["command"] == "parameters.add":
            if c["params"]["name"] in names: return
            names.add(c["params"]["name"])
        cmds.append(c)
    add({"command": "parameters.add", "params": {"name": "explode", "expression": f"{explode} mm", "comment": "exploded-view spacing (0 = assembled)"}})
    for c in json.load(open("lid.script.json"))["commands"]: add(c)
    for c in json.load(open("base.script.json"))["commands"]:
        if c["command"] == "parameters.add": add(c)
    add({"command": "solid.move", "params": {"bodies": ["Lid"], "translate": ["0 mm", "0 mm", "floor_t + cav_z + explode"]}})
    for c in json.load(open("plunger.script.json"))["commands"]: add(c)
    add({"command": "solid.move", "params": {"bodies": ["KeyCap"], "translate": ["wall + cap_x", "wall + cap_y", "floor_t + cav_z - 1.5 mm + 2*explode"]}})
    for c in json.load(open("base.script.json"))["commands"]: add(c)
    for c in E: add(c)
    add({"command": "solid.move", "params": {"bodies": M2_BODIES, "translate": ["0 mm", "0 mm", "explode"]}})
    if variant == "nolid": add({"command": "solid.remove", "params": {"bodies": ["Lid", "KeyCap"] + M2_BODIES}})
    if variant == "section":
        add({"command": "solid.remove", "params": {"bodies": [b for b in ALL if b not in STRADDLE]}})
        for b in ["Lid", "KeyCap", "Base"] + STRADDLE:
            add({"command": "solid.box", "params": {"length": "100 mm", "width": "34 mm", "height": "60 mm", "corner": ["-5 mm", "-5 mm", "-5 mm"], "operation": "cut", "targets": [b], "name": "Section_" + b}})
    if variant == "check": add({"command": "inspect.interference", "params": {}})
    return {"commands": cmds}
json.dump(full(0), open("full-assembly.script.json", "w"), indent=1)
json.dump(full(14), open("full-assembly-exploded.script.json", "w"), indent=1)
json.dump(full(0, "nolid"), open("full-assembly-nolid.script.json", "w"), indent=1)
json.dump(full(0, "section"), open("full-assembly-section.script.json", "w"), indent=1)
json.dump(full(0, "check"), open("full-assembly-check.script.json", "w"), indent=1)
json.dump(ALL, open("electronics-bodies.json", "w"))
print(len(E), "electronics commands;", len(ALL), "registered bodies")
