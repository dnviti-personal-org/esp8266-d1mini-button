#!/usr/bin/env python3
"""Perfboard layout generator (rev C).

Single source of truth for WHERE every lead goes on the 70 x 50 mm perfboard
and HOW every net is wired.  Produces:

  layout.json   - parts, pin holes, wires, mounting holes (mm + grid names);
                  consumed by the SolidCraft (3D) and CADCraft (2D) generators
  ../BUILD.md   - step-by-step assembly guide (English)
  ../BUILD.it.md- the same guide in Italian

Grid: 24 columns A..X along X (70 mm side), 18 rows 1..18 along Y (50 mm side),
2.54 mm pitch, hole A1 at (5.79, 3.41) mm from the board's bottom-left corner
seen from the COMPONENT side with the USB edge (y = 0) toward you.
Column X = x 64.21, row 18 = y 46.59.  All holes are drilled Ø1.0.

Run:  python3 gen_layout.py      (writes the three files next to it / above)
"""
import json
import math
import os
from collections import defaultdict

PITCH = 2.54
X0, Y0 = 5.79, 3.41
COLS = "ABCDEFGHIJKLMNOPQRSTUVWX"
NROWS = 18
BOARD = (70.0, 50.0, 1.6)
CAVITY_OFFSET = (2.46, 1.73)        # perfboard origin inside the enclosure cavity
NOTCH = 5.0                          # corner notches (clear the Ø6 lid bosses)
MOUNT_HOLE_D = 2.2                   # grid holes drilled out for M2 screws
STANDOFF_D = 5.0


def hole(name):
    """'K9' -> (x, y) mm (board origin, component side view)."""
    col = COLS.index(name[0])
    row = int(name[1:])
    assert 1 <= row <= NROWS, name
    return (round(X0 + PITCH * col, 2), round(Y0 + PITCH * (row - 1), 2))


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ---------------------------------------------------------------- parts
# Every through-hole lead is named by its grid hole.  "pins" maps the
# part's pin name to a hole.  Bodies are axis-aligned boxes (mm, board
# origin) used only for the overlap check and the 2D/3D generators.
PARTS = [
    dict(ref="U1", value="WEMOS D1 mini", kind="module",
         pins={"3V3": "A3", "D8": "A4", "D7": "A5", "D6": "A6", "D5": "A7",
               "D0": "A8", "A0": "A9", "RST": "A10",
               "5V": "J3", "GND": "J4", "D4": "J5", "D3": "J6", "D2": "J7",
               "D1": "J8", "RX": "J9", "TX": "J10"},
         body=(4.42, 0.28, 30.02, 34.48),   # PCB outline x0,y0,x1,y1
         note="micro-USB on the y = 0 edge, antenna toward row 18; "
              "header pins: LONG side down through the perfboard, trim flush after soldering"),
    dict(ref="SW1", value="tactile 12x12, 7.3 mm actuator (B3F-4000)", kind="tht",
         pins={"1a": "K9", "1b": "P9", "2a": "K11", "2b": "P11"},
         body=(31.54, 20.27, 43.54, 32.27),
         note="pins 12.5 mm apart go into holes 12.7 mm apart: spread them 0.1 mm each; "
              "pins on the same row are joined inside the switch"),
    dict(ref="D2", value="1N5819 Schottky, DO-41", kind="tht",
         pins={"A": "O3", "K": "K3"},
         body=(33.0, 7.24, 40.0, 9.74),
         note="band (cathode) toward column K, next to U1's 5V pin"),
    dict(ref="R2", value="10 kΩ 1/4 W", kind="tht",
         pins={"1": "K5", "2": "O5"},
         body=(33.0, 12.32, 40.0, 14.82), note="BTN pull-up"),
    dict(ref="R3", value="10 kΩ 1/4 W", kind="tht",
         pins={"1": "K7", "2": "O7"},
         body=(33.0, 17.40, 40.0, 19.90), note="CHRG pull-up"),
    dict(ref="C3", value="100 nF ceramic disc, 2.54 mm", kind="tht",
         pins={"1": "Q11", "2": "Q12"},
         body=(45.18, 27.54, 47.68, 32.62), note="any orientation"),
    dict(ref="C4", value="100 µF 10 V electrolytic Ø5x11", kind="tht",
         pins={"-": "Q14", "+": "Q15"},
         body=(47.0, 35.20, 58.5, 40.20),
         note="leads bent 90°, body lying flat toward column X; stripe (−) toward row 14"),
    dict(ref="J2", value="1x6 right-angle male header", kind="tht",
         pins={"SCK": "Q17", "WS": "R17", "SD": "S17", "VDD": "T17", "L/R": "U17", "GND": "V17"},
         body=(45.16, 42.78, 60.40, 45.32),
         note="bent pins point toward row 18 (board edge), plastic body on rows 17"),
    dict(ref="J1", value="JST-PH 2-pin right-angle (S2B-PH-K-S)", kind="tht",
         pins={"1 (+)": "X14", "2 (−)": "X15"},
         body=(62.7, 33.7, 70.0, 41.6),
         note="opening toward the board edge (column X side); 2.0 mm pins spread to 2.54 mm"),
    dict(ref="SW2", value="SS12D00G4 slide switch (4 mm lever)", kind="tht",
         pins={"ON": "A15", "COM": "A16", "NC": "A17"},
         body=(1.10, 37.21, 4.80, 45.81),
         note="laid on its side at the board edge, lever toward the edge; "
              "the three pins (3 mm pitch) are bent 90° down into column A"),
    dict(ref="M1", value="TP4056 USB-C charger module 03962A", kind="module",
         pins={},   # glued; wired from its pads, see WIRES
         body=(46.29, -0.5, 63.79, 25.5),
         note="stuck flat on the perfboard with 1 mm double-sided foam tape, "
              "USB-C over the board edge; covers columns R..X rows 1..9"),
    dict(ref="JP1", value="solder bridge", kind="bridge",
         pins={"RST": "A10", "BTN": "A11"},
         body=None, note="bridge the two pads on the solder side = battery mode"),
]

# Mounting holes (grid holes drilled out to Ø2.2) and the cavity standoffs under them
MOUNT = ["L1", "L18", "C17", "X11"]

# ---------------------------------------------------------------- wires
# Solder-side wiring.  kind: "link" = bare tinned wire between adjacent
# holes (or a solder bridge), "wire" = insulated 26 AWG hook-up wire.
# Endpoints are grid holes, or "M1:<pad>" for the charger module pads.
NET_COLOUR = {
    "GND": "black", "3V3": "red", "5V": "orange", "VSW": "yellow", "VBAT": "brown",
    "BAT-": "grey", "BTN": "white", "RST": "bare", "CHRG": "violet",
    "MICPWR": "green", "I2S_SCK": "blue", "I2S_WS": "pink", "I2S_SD": "turquoise",
}
WIRES = [
    # net, from, to, kind
    ("5V", "K3", "J3", "link"),
    ("RST", "A10", "A11", "bridge"),
    ("BTN", "K5", "K9", "wire"),
    ("BTN", "J8", "K9", "wire"),
    ("BTN", "Q11", "P9", "wire"),
    ("BTN", "A11", "P9", "wire"),
    ("GND", "J4", "K11", "wire"),
    ("GND", "P11", "Q12", "wire"),
    ("GND", "Q12", "Q14", "wire"),
    ("GND", "Q14", "V17", "wire"),
    ("GND", "U17", "V17", "link"),
    ("GND", "M1:OUT-", "P11", "wire"),
    ("3V3", "A3", "O5", "wire"),
    ("3V3", "O5", "O7", "wire"),
    ("3V3", "O7", "Q15", "wire"),
    ("CHRG", "A8", "K7", "wire"),
    ("CHRG", "K7", "M1:CHRG", "wire"),
    ("VSW", "O3", "A15", "wire"),
    ("VSW", "M1:OUT+", "A16", "wire"),
    ("VBAT", "M1:B+", "X14", "wire"),
    ("BAT-", "M1:B-", "X15", "wire"),
    ("MICPWR", "J7", "T17", "wire"),
    ("I2S_SCK", "A5", "Q17", "wire"),
    ("I2S_WS", "A7", "R17", "wire"),
    ("I2S_SD", "A6", "S17", "wire"),
]
# Pad positions on the glued TP4056 module (board origin, approximate: the
# pads sit along the module edges; measure your module before cutting wires)
M1_PADS = {"B+": (49.0, 24.0), "B-": (61.0, 24.0), "OUT+": (47.5, 19.0),
           "OUT-": (62.5, 19.0), "CHRG": (50.0, 6.0)}


def endpoint(name):
    if name.startswith("M1:"):
        return M1_PADS[name[3:]]
    return hole(name)


# ---------------------------------------------------------------- checks
def check():
    errors = []
    used = {}
    for p in PARTS:
        for pin, h in p["pins"].items():
            if p["ref"] == "JP1":
                continue
            if h in used:
                errors.append(f"hole {h} used by {used[h]} and {p['ref']}.{pin}")
            used[h] = f"{p['ref']}.{pin}"
    for m in MOUNT:
        if m in used:
            errors.append(f"mounting hole {m} is also {used[m]}")
        mx, my = hole(m)
        for h, who in used.items():
            d = dist(hole(h), (mx, my))
            if d < STANDOFF_D / 2 + 0.5:
                errors.append(f"{who} at {h} is {d:.2f} mm from standoff {m}")
    # wires per hole
    count = defaultdict(int)
    for net, a, b, kind in WIRES:
        for e in (a, b):
            if not e.startswith("M1:"):
                count[e] += 1
                if e not in used and kind != "bridge":
                    pass  # a wire may land on a free hole (e.g. A11)
    for h, n in count.items():
        if n > 2:
            errors.append(f"hole {h} has {n} wire ends (max 2)")
    # body overlaps (boxes)
    boxes = [(p["ref"], p["body"]) for p in PARTS if p["body"]]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (ra, a), (rb, b) = boxes[i], boxes[j]
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                errors.append(f"bodies overlap: {ra} {a} / {rb} {b}")
    # standoffs vs bodies
    for m in MOUNT:
        mx, my = hole(m)
        for ref, b in boxes:
            if b[0] - 2.5 < mx < b[2] + 2.5 and b[1] - 2.5 < my < b[3] + 2.5:
                errors.append(f"standoff {m} under {ref}")
    # net consistency: every pin of a net reachable
    return errors


# ---------------------------------------------------------------- output
def wire_rows():
    rows = []
    for i, (net, a, b, kind) in enumerate(WIRES, 1):
        pa, pb = endpoint(a), endpoint(b)
        length = dist(pa, pb)
        total = round(length + 8, 0) if kind == "wire" else round(length, 1)
        rows.append(dict(n=i, net=net, frm=a, to=b, kind=kind,
                         colour=NET_COLOUR[net] if kind == "wire" else "bare",
                         a=pa, b=pb, mm=round(length, 1), cut_mm=total))
    return rows


def build_json():
    parts = []
    for p in PARTS:
        q = dict(p)
        q["holes"] = {pin: dict(name=h, xy=hole(h)) for pin, h in p["pins"].items()}
        parts.append(q)
    off = CAVITY_OFFSET
    data = dict(
        rev="C",
        grid=dict(pitch=PITCH, x0=X0, y0=Y0, cols=COLS, rows=NROWS, hole_d=1.0),
        board=dict(size=BOARD, notch=NOTCH, cavity_offset=off),
        mount=[dict(name=m, xy=hole(m), d=MOUNT_HOLE_D,
                    cavity=(round(hole(m)[0] + off[0], 2), round(hole(m)[1] + off[1], 2)))
               for m in MOUNT],
        parts=parts,
        m1_pads=M1_PADS,
        wires=wire_rows(),
        enclosure=dict(
            usb_micro_slot_x=round(17.22 + off[0], 2),
            usb_c_slot_x=round(55.04 + off[0], 2),
            sw2_wall="x = 0",
            sw2_slot_y=round(hole("A16")[1] + off[1], 2),
            keycap_centre=(round(37.54 + off[0], 2), round(26.27 + off[1], 2)),
        ),
    )
    return data


GUIDE = {
    "en": dict(
        title="# Build guide — perfboard assembly (rev C)",
        intro="""Everything in this guide is derived from `layout/layout.json`
(generated by `layout/gen_layout.py`); the drawings in `schematic/` and the 3D
model in `enclosure/` use the same hole names, so you only have to follow the
tables. **Hole names**: hold the perfboard with the **component side up** and
the edge that will carry the USB connectors **toward you**; columns run
**A → X from left to right**, rows **1 → 18 from near to far**. Mark A1 with a
pen before you start. When you turn the board over to solder, left and right
swap: the `perfboard-solder-side.svg` drawing is already mirrored for you.

Only through-hole parts are soldered; the three modules (D1 mini, TP4056
charger, INMP441 microphone) come pre-assembled.""",
        tools="""## Tools and consumables

- Soldering iron (≤ 350 °C), 0.5–0.8 mm leaded or SAC solder, flux, cutters.
- Bare tinned wire 0.6 mm for the short links; insulated 26 AWG stranded
  hook-up wire in the colours of the table (any colours work, but keep one
  colour per net and write your substitutions in the table).
- 1 mm double-sided foam tape (for the charger module), kapton or PVC tape.
- Drill 2.2 mm (4 mounting holes), small file or cutters for the corner notches.
- Multimeter.""",
        prep="""## 1. Prepare the board

1. Cut the four corners of the perfboard **5 × 5 mm** (they clear the lid screw bosses).
2. Drill the four **mounting holes** to Ø2.2 mm at the grid holes **{mount}**.
   Nothing may be soldered on the 8 holes around each of them (the Ø5 mm
   standoff sits there).
3. With the USB edge toward you, mark **A1** (near-left) and **X18** (far-right).""",
        parts_h="## 2. Solder the components (component side), lowest first",
        parts_cols=("Step", "Ref", "Part", "Leads in holes", "Notes"),
        links_h="## 3. Bare links and solder bridge (solder side)",
        wires_h="## 4. Insulated wires (solder side)",
        wires_intro="""Cut each wire to the **Cut** length (= straight distance + 8 mm), strip 3 mm
at both ends, tin, then solder each end into its hole **together with the lead
already there** (or alone where the hole is empty). Wires lie flat against the
solder side; they may cross each other and pass over other joints — they are
insulated. Do them in this order.""",
        wires_cols=("#", "Net", "Colour", "From", "To", "Length", "Cut"),
        m1_h="## 5. Charger module M1",
        m1="""1. Stick 1 mm foam tape on the perfboard over columns **R..X, rows 1..9**
   (x 46.3–63.8 mm, y −0.5–25.5 mm from the A1 corner: the module overhangs
   the USB edge by 0.5 mm so its USB-C reaches the enclosure wall).
2. Press the TP4056 module on it, **USB-C toward the USB edge**, centred at
   **x = 55.0 mm** (= 1.1 mm right of column T).
3. Solder the five wires of table 4 that start with `M1:` to its pads:
   `B+`, `B−` (battery pads, far end), `OUT+`, `OUT−` (load pads), and `CHRG`
   = the pad of the charge LED that goes to TP4056 pin 7 (the LED pad
   **not** connected to the 5 V/resistor side; check with the multimeter in
   diode mode: pin 7 is the second pin from the USB-C on the side of the chip
   that faces the LEDs).  Leave `IN+`/`IN−` unused.""",
        sw2_h="## 6. Power switch SW2",
        sw2="""Bend the three pins of the SS12D00 90° at 1 mm from the body so the switch
lies on its side with the **lever pointing at the board edge** (left edge,
column A side) and the pins go down into **A15, A16, A17** (centre pin =
A16, the common). Solder; the body rests on the board, its lever will stick
out through the slot in the enclosure wall.""",
        u1_h="## 7. D1 mini U1",
        u1="""1. Put the two 8-pin male headers in the perfboard at **A3..A10** and
   **J3..J10** with the **LONG pins down** through the perfboard and the short
   pins up; the plastic spacer rests on the perfboard.
2. Seat the D1 mini on the short pins: **micro-USB toward the USB edge**,
   3V3 at A3 and 5V at J3 (RST at A10, TX at J10). Solder the 16 pins on top of
   the D1 mini.
3. Turn the board over, solder the 16 pins on the solder side (together with the
   wires of table 4 that land on A3..A10 / J3..J10) and **cut the long pins
   flush** — anything longer than 1 mm would touch the battery below.""",
        checks_h="## 8. Checks before powering",
        checks="""With the multimeter (no battery, no USB):
- `GND` (J4) to `3V3` (A3): > 10 kΩ, no short. `GND` to `5V` (J3): no short.
- `BTN` (K9) to `3V3`: ≈ 10 kΩ (R2). Press SW1: `BTN` to `GND` ≈ 0 Ω.
- `RST` (A10) to `BTN` (K9): 0 Ω if JP1 is bridged.
- `CHRG` (K7) to `3V3`: ≈ 10 kΩ (R3).
- J1 pin 1 (X14) to M1 `B+`: 0 Ω; J1 pin 2 (X15) to M1 `B−`: 0 Ω.
- SW2 ON: M1 `OUT+` to D2 anode (O3): 0 Ω; SW2 OFF: open.
Then plug the battery into J1 (red = +, toward row 14), switch SW2 on: the
D1 mini's LED blinks at boot; open the serial console (see README) and
configure Wi-Fi. Plug USB-C into M1 only to charge (red LED = charging,
blue = full).""",
        mic_h="## 9. Microphone lead",
        mic="""Make a 90 mm 6-wire lead with a female 1×6 DuPont housing on the J2 end:
J2 **SCK → M2 SCK**, **WS → WS**, **SD → SD**, **VDD → VDD**, **L/R → L/R**,
**GND → GND**. Solder the other ends to the INMP441 module pads; it goes in
the lid pocket, sound port over the Ø2 mm hole, component side toward the lid.
`L/R` is tied to GND (left channel) by the bare link U17–V17.""",
    ),
    "it": dict(
        title="# Guida di montaggio — millefori (rev C)",
        intro="""Tutto quello che c'è in questa guida deriva da `layout/layout.json`
(generato da `layout/gen_layout.py`); i disegni in `schematic/` e il modello 3D
in `enclosure/` usano gli stessi nomi dei fori, quindi basta seguire le
tabelle. **Nomi dei fori**: tieni la millefori con il **lato componenti in
alto** e il bordo che ospiterà le prese USB **verso di te**; le colonne vanno
**da A a X da sinistra a destra**, le righe **da 1 a 18 dal vicino al
lontano**. Segna A1 con un pennarello prima di iniziare. Quando giri la
scheda per saldare, destra e sinistra si scambiano: il disegno
`perfboard-solder-side.svg` è già specchiato per te.

Si saldano solo componenti a foro passante; i tre moduli (D1 mini, caricatore
TP4056, microfono INMP441) arrivano già montati.""",
        tools="""## Attrezzi e materiali

- Saldatore (≤ 350 °C), stagno 0.5–0.8 mm, flussante, tronchesine.
- Filo nudo stagnato 0.6 mm per i ponticelli corti; filo isolato flessibile
  26 AWG nei colori della tabella (vanno bene altri colori, ma un colore per
  ogni net: scrivi le sostituzioni nella tabella).
- Biadesivo in schiuma da 1 mm (per il modulo caricatore), nastro kapton o PVC.
- Punta da 2.2 mm (4 fori di fissaggio), limetta o tronchesine per gli angoli.
- Multimetro.""",
        prep="""## 1. Preparare la scheda

1. Taglia i quattro angoli della millefori a **5 × 5 mm** (liberano le colonnette delle viti del coperchio).
2. Allarga a Ø2.2 mm i quattro **fori di fissaggio** sui fori di griglia **{mount}**.
   Sugli 8 fori attorno a ciascuno non va saldato nulla (sotto c'è il
   distanziale Ø5 mm).
3. Con il bordo USB verso di te, segna **A1** (vicino a sinistra) e **X18** (lontano a destra).""",
        parts_h="## 2. Saldare i componenti (lato componenti), prima i più bassi",
        parts_cols=("Passo", "Sigla", "Componente", "Reofori nei fori", "Note"),
        links_h="## 3. Ponticelli nudi e ponte di stagno (lato saldature)",
        wires_h="## 4. Fili isolati (lato saldature)",
        wires_intro="""Taglia ogni filo alla lunghezza **Taglio** (= distanza in linea retta + 8 mm),
spela 3 mm alle due estremità, stagna, poi salda ogni capo nel suo foro
**insieme al reoforo già presente** (o da solo dove il foro è vuoto). I fili
stanno distesi sul lato saldature; possono incrociarsi e passare sopra altre
saldature, sono isolati. Falli in quest'ordine.""",
        wires_cols=("#", "Net", "Colore", "Da", "A", "Lunghezza", "Taglio"),
        m1_h="## 5. Modulo caricatore M1",
        m1="""1. Incolla il biadesivo da 1 mm sulla millefori sopra le colonne **R..X,
   righe 1..9** (x 46.3–63.8 mm, y −0.5–25.5 mm dall'angolo A1: il modulo
   sporge di 0.5 mm dal bordo USB così la USB-C arriva alla parete).
2. Premi sopra il modulo TP4056, **USB-C verso il bordo USB**, centrato a
   **x = 55.0 mm** (= 1.1 mm a destra della colonna T).
3. Salda ai suoi pad i cinque fili della tabella 4 che iniziano con `M1:`:
   `B+`, `B−` (pad batteria, estremità lontana), `OUT+`, `OUT−` (pad carico)
   e `CHRG` = il pad del LED di carica che va al pin 7 del TP4056 (il pad del
   LED **non** collegato al lato 5 V/resistenza; verifica col multimetro in
   modalità diodo: il pin 7 è il secondo pin dalla USB-C sul lato del chip
   rivolto verso i LED). Lascia liberi `IN+`/`IN−`.""",
        sw2_h="## 6. Interruttore SW2",
        sw2="""Piega i tre pin dell'SS12D00 a 90° a 1 mm dal corpo, così l'interruttore
sta sdraiato su un fianco con la **levetta verso il bordo della scheda**
(bordo sinistro, lato colonna A) e i pin scendono in **A15, A16, A17** (pin
centrale = A16, il comune). Salda; il corpo appoggia sulla scheda e la
levetta uscirà dalla feritoia nella parete della custodia.""",
        u1_h="## 7. D1 mini U1",
        u1="""1. Infila le due strip maschio da 8 pin nella millefori in **A3..A10** e
   **J3..J10** con i **pin LUNGHI verso il basso** attraverso la millefori e i
   corti verso l'alto; il distanziale di plastica appoggia sulla millefori.
2. Calza il D1 mini sui pin corti: **micro-USB verso il bordo USB**, 3V3 in A3
   e 5V in J3 (RST in A10, TX in J10). Salda i 16 pin sopra il D1 mini.
3. Gira la scheda, salda i 16 pin sul lato saldature (insieme ai fili della
   tabella 4 che arrivano in A3..A10 / J3..J10) e **taglia i pin lunghi a
   filo**: più di 1 mm toccherebbero la batteria sotto.""",
        checks_h="## 8. Verifiche prima di alimentare",
        checks="""Col multimetro (senza batteria né USB):
- `GND` (J4) – `3V3` (A3): > 10 kΩ, nessun corto. `GND` – `5V` (J3): nessun corto.
- `BTN` (K9) – `3V3`: ≈ 10 kΩ (R2). Premendo SW1: `BTN` – `GND` ≈ 0 Ω.
- `RST` (A10) – `BTN` (K9): 0 Ω se JP1 è ponticellato.
- `CHRG` (K7) – `3V3`: ≈ 10 kΩ (R3).
- J1 pin 1 (X14) – M1 `B+`: 0 Ω; J1 pin 2 (X15) – M1 `B−`: 0 Ω.
- SW2 ON: M1 `OUT+` – anodo D2 (O3): 0 Ω; SW2 OFF: aperto.
Poi collega la batteria a J1 (rosso = +, verso la riga 14), accendi SW2: il
LED del D1 mini lampeggia all'avvio; apri la console seriale (vedi README) e
configura il Wi-Fi. Collega la USB-C a M1 solo per caricare (LED rosso =
in carica, blu = carica completa).""",
        mic_h="## 9. Cavetto del microfono",
        mic="""Prepara un cavetto a 6 fili da 90 mm con un connettore femmina DuPont 1×6
sul lato J2: J2 **SCK → M2 SCK**, **WS → WS**, **SD → SD**, **VDD → VDD**,
**L/R → L/R**, **GND → GND**. Salda le altre estremità ai pad del modulo
INMP441; va nella tasca del coperchio, foro acustico sopra il foro Ø2 mm,
lato componenti verso il coperchio. `L/R` è a GND (canale sinistro) tramite
il ponticello nudo U17–V17.""",
    ),
}

PART_ORDER = ["D2", "R2", "R3", "C3", "C4", "J2", "J1", "SW1"]


def table(cols, rows):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def write_guide(lang, data, path):
    g = GUIDE[lang]
    parts = {p["ref"]: p for p in data["parts"]}
    lines = [g["title"], "", g["intro"], "", g["tools"], "",
             g["prep"].format(mount=", ".join(MOUNT)), "", g["parts_h"], ""]
    rows = []
    for i, ref in enumerate(PART_ORDER, 1):
        p = parts[ref]
        leads = ", ".join(f"{pin} → **{h}**" for pin, h in p["pins"].items())
        rows.append((i, ref, p["value"], leads, p["note"]))
    lines += [table(g["parts_cols"], rows), "", g["links_h"], ""]
    links = [w for w in data["wires"] if w["kind"] in ("link", "bridge")]
    lines += [table(("#", "Net", "", "", "mm"),
                    [(w["n"], w["net"], w["frm"], w["to"], w["mm"]) for w in links]), ""]
    lines += [g["wires_h"], "", g["wires_intro"], ""]
    wires = [w for w in data["wires"] if w["kind"] == "wire"]
    lines += [table(g["wires_cols"],
                    [(w["n"], w["net"], w["colour"], w["frm"], w["to"], f'{w["mm"]} mm', f'{int(w["cut_mm"])} mm')
                     for w in wires]), ""]
    lines += [g["m1_h"], "", g["m1"], "", g["sw2_h"], "", g["sw2"], "",
              g["u1_h"], "", g["u1"], "", g["checks_h"], "", g["checks"], "",
              g["mic_h"], "", g["mic"], ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def main():
    errors = check()
    if errors:
        for e in errors:
            print("ERROR:", e)
        raise SystemExit(1)
    here = os.path.dirname(os.path.abspath(__file__))
    data = build_json()
    with open(os.path.join(here, "layout.json"), "w") as f:
        json.dump(data, f, indent=1)
    write_guide("en", data, os.path.join(here, "..", "BUILD.md"))
    write_guide("it", data, os.path.join(here, "..", "BUILD.it.md"))
    print("ok:", len(data["parts"]), "parts,", len(data["wires"]), "wires")


if __name__ == "__main__":
    main()
