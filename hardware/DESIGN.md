# Hardware design — ESP8266 D1 mini battery button with audio

Single source of truth for dimensions and the electrical design. The 3D
enclosure (SolidCraft), the schematic / perfboard layout (CADCraft) and the
firmware all follow this file.

Revision B (2026-10-26): audio recording added. The CR2032 supply of revision A
was dropped because minutes of recording (ESP8266 + Wi-Fi ≈ 75 mA) are far
beyond what a coin cell can deliver (≈ 4 mAh per 3-minute press; a CR2032
collapses above a few mA continuous). The supercapacitor bank, R1 and the
"SW2 off before USB" rule are gone with it.

## 1. Power architecture (LiPo 3.7 V, 1000 mAh)

```
BT1 LiPo 803040 ─ M1 TP4056 charger + DW01 protection (USB-C) ─ OUT+ ─ SW2 ─ D2 1N5819 ─ D1 mini "5V" pin
                                                                                           └─ on-board ME6211 LDO → 3V3
GND ─────────────────────────────────────────────────────────────────────────────────────── D1 mini "G"
```

- The battery enters the D1 mini on its **5V pin** through Schottky D2
  (1N5819 DO-41, Vf ≈ 0.3 V). The on-board LDO regulates to 3.3 V (it simply passes
  through when the LiPo is nearly empty; the ESP works down to 2.5 V).
- USB programming puts 5 V on the same rail; D2 blocks any current into the
  LiPo. USB may be plugged at any time, with SW2 in any position.
- Charging only through the TP4056's own USB-C port. Its CHRG output (open
  drain, low while charging) goes to D0/GPIO16 (10 kΩ pull-up R3) so the firmware can publish a
  "charging" sensor.
- Budget: deep-sleep standby ≈ 0.25 mA (D1 mini LDO + CH340 leakage, TP4056
  idle < 10 µA) ⇒ **≈ 4 months**. Recording ≈ 75 mA ⇒ 1000 mAh ≈ 13 h of
  audio ≈ **250 three-minute presses** per charge. Charge at 500 mA ≈ 2.5 h.
- Battery voltage is not measured (A0 is free but the firmware does not use it:
  `ADC_VCC` would need A0 floating, add a divider + `analogRead` if wanted).

## 2. Button wiring

```
3V3 ─ R2 10k ─┬─ D1 (GPIO5)           (input, pressed = LOW)
              ├─ JP1 ─ RST            (closed = battery mode, wake from deep sleep)
              ├─ C3 100 nF ─ GND      (noise filter / RC debounce)
              └─ SW1 (12×12 tactile, 100 gf) ─ GND
```

- JP1 closed: a press pulls RST low → wake from deep sleep. The wake itself is
  the "button pressed" event. A second press during a recording restarts the
  board: the partial file is finalised on boot and a new recording starts.
- JP1 open: `always_on` mode (USB powered); GPIO5 is debounced and a press
  during a recording stops it early.
- The on-board LED (GPIO2, active-low) is on while recording.

## 3. Audio path (I2S MEMS microphone)

Revision B.1: the electret + MAX9814 + internal ADC path of the first B draft
was dropped after bench testing: the ESP8266's only ADC is read through the
Wi-Fi PHY (`system_adc_read`, flash-resident, up to 220 µs per sample) and
calling it from a timer interrupt crashes the chip as soon as there is TCP
traffic (Exception 0 in the ISR). A digital I2S microphone is filled by DMA
with no CPU involvement and no interaction with the radio.

```
M2 INMP441 breakout   SCK ← D7 (GPIO13)   WS ← D5 (GPIO14)   SD → D6 (GPIO12)
                      L/R → GND (left channel)   VDD ← D2 (GPIO4), power gated, 1.4 mA   GND → GND
M1 TP4056 CHRG ──┬── D0 (GPIO16)   (open drain, low = charging)
                 └── R3 10 kΩ → 3V3
```

- GPIO12/13/14 are the ESP8266's fixed I2S RX pins; the charger sense therefore
  moved to GPIO16 (no internal pull-up: R3 provides it) and the mic power to GPIO4.
- Sampling: 8 kHz, 24-bit frames read as 16-bit, mono, WAV container, with a
  configurable digital gain (`mic_gain`, ×1…×64, default ×8).
- The samples go to a RAM ring buffer (1 s of pre-roll) and are streamed live
  over HTTP (`http://<ip>/rec.wav`, fixed-length WAV). Home Assistant starts the
  download when the ESP publishes the JSON on `<prefix>/<mac>/recording`
  (`downloader` integration, see `homeassistant/`). The ESP stays awake until
  the file has been streamed once or the client never shows up (15 s), then sleeps.
- The breakout (11 × 14 mm) sits in a pocket under the lid with its sound port
  over a Ø2 mm hole. No flash is written during recording.

## 4. Bill of materials

| Ref | Part | Package / notes |
|---|---|---|
| U1 | Wemos / LOLIN D1 mini (ESP8266, CH340, 4 MB flash) | 34.2 × 25.6 mm, 2 × 8 pins 2.54 mm, rows 22.86 mm apart |
| PCB1 | Perfboard 50 × 70 mm, 2.54 mm pitch, single side | 18 × 24 holes, FR-4 1.6 mm |
| BT1 | LiPo 3.7 V 1000 mAh 803040 with JST-PH 2.0 plug | 8 × 30 × 40 mm, lies under the perfboard |
| M1 | TP4056 charger module with DW01/FS8205 protection, USB-C (03962A) | 17.5 × 26 mm (USB-C on the short edge), 1.0 A default (R_PROG 1.2 kΩ); change R_PROG to 2.4 kΩ for 0.5 A |
| M2 | INMP441 I2S MEMS microphone breakout | 11 × 14 mm, 6 pins (VDD GND SD WS SCK L/R), 1.4 mA, mounted under the lid, 6 wires to the perfboard |
| R3 | 10 kΩ 1/4 W (pull-up for CHRG on GPIO16) | axial |
| J1 | JST-PH 2-pin right-angle header (battery) | 2.0 mm pitch |
| J2 | 1×6 right-angle pin header 2.54 mm (microphone wires) | 2.5 mm tall; or solder the wires directly |
| SW1 | Tactile switch 12 × 12 mm, THT, 7.3 mm actuator, **low force 100 gf** (e.g. Omron B3F-4000) | standard 12×12 footprint |
| SW2 | SPDT slide switch SS12D00 (power) | 8.6 × 3.6 mm body, 3 pins 3.0 mm pitch, actuator 2 mm |
| D2 | Schottky diode 1N5819 DO-41 (battery → 5V pin) | axial, through-hole (no SMD parts anywhere on the perfboard) |
| C3 | 100 nF ceramic X7R | 2.54 mm pitch |
| C4 | 100 µF 6.3 V low-ESR electrolytic (3V3 rail) | Ø5 × 11 mm radial |
| R2 | 10 kΩ 1/4 W | axial |
| JP1 | Solder bridge (two pads 2.54 mm apart); closed = battery mode | no header: nothing tall under the key cap |
| — | 4 × M2 × 8 mm self-tapping screws (PCB), 4 × M2.5 × 10 mm (lid), 4 × Ø8 mm adhesive rubber feet, double-sided foam tape for the LiPo | |

## 5. Perfboard placement — rev C, on the 2.54 mm hole grid

Generated layout: **`hardware/layout/gen_layout.py` → `layout.json`** is the
single source of truth for every lead position and every wire; the build
guide (`hardware/BUILD.md`, Italian `BUILD.it.md`), the 2D drawings and the
3D model are derived from it. Do not edit the tables below by hand: change
the generator and rerun it.

Grid: 24 columns **A..X** along X and 18 rows **1..18** along Y, pitch 2.54 mm,
hole A1 at (5.79, 3.41) from the board's bottom-left corner, component-side
view, USB edge at y = 0 (col X = x 64.21, row 18 = y 46.59). Perfboard
70 × 50 × 1.6, corners notched **5 × 5**, mounting holes = grid holes
**L1, L18, C17, X11** drilled Ø2.2 (nothing soldered on the 8 holes around
each: the Ø5 standoff is underneath). Perfboard origin at cavity
**(2.46, 1.73)**, chosen so that SW1's actuator lands exactly under the key
cap at cavity (40, 28).

| Ref | Leads in holes | Notes |
|---|---|---|
| U1 D1 mini | A3..A10 (3V3 D8 D7 D6 D5 D0 A0 RST), J3..J10 (5V GND D4 D3 D2 D1 RX TX) | PCB x 4.42 → 30.02, y 0.28 → 34.48; micro-USB on the y = 0 edge (face ≈ 1 mm inside the wall); headers long side down, trimmed flush |
| SW1 B3F-4000 | K9 P9 (contact 1), K11 P11 (contact 2) | body 31.54 → 43.54 × 20.27 → 32.27; 12.5 mm pins spread to 12.7 |
| D2 1N5819 | K3 (cathode, band) – O3 | row 3 |
| R2 10 k | K5 – O5 | BTN pull-up |
| R3 10 k | K7 – O7 | CHRG pull-up |
| C3 100 nF | Q11 – Q12 | |
| C4 100 µF | Q14 (−) – Q15 (+) | lying flat toward +x, body 47 → 58.5 |
| J2 1×6 right-angle | Q17..V17 = SCK WS SD VDD L/R GND | bent pins toward row 18 |
| J1 JST-PH | X14 (+) – X15 (−) | mouth toward +x; the plug lives in the 7.5 mm gap between board edge (cavity 72.46) and wall |
| SW2 SS12D00G4 | A15 (ON) A16 (COM) A17 (NC) | laid on its side at the **x = 0** edge, lever through the x = 0 wall; pins bent 90° |
| M1 TP4056 USB-C | glued (1 mm foam tape), x 46.29 → 63.79, y −0.5 → 25.5 | USB-C centred x 55.04 = cavity 57.5; wired from its pads B+ B− OUT+ OUT− CHRG |
| JP1 | solder bridge A10–A11 | closed = battery mode |
| BT1 LiPo | cavity (40, 28) under the board | leads + plug in the right-hand gap to J1 |
| M2 INMP441 | lid pocket at cavity (74, 28) | 6-wire lead to J2 |

Wiring: 2 bare links (K3–J3, U17–V17), 1 solder bridge (A10–A11) and 22
insulated 26 AWG wires on the solder side, one colour per net (GND black,
3V3 red, 5V orange, VSW yellow, VBAT brown, BAT− grey, BTN white, CHRG
violet, MICPWR green, SCK blue, WS pink, SD turquoise); full list with
lengths in `BUILD.md`. Max two wire ends per hole. The wires lie flat under
the board (≈ 1.5 mm incl. solder) above the LiPo.

Solder pins protrude ≤ 1 mm below the perfboard: **mount U1 with the long
(6 mm) side of its header pins down through the perfboard and trim the tails
flush after soldering**; the short 3 mm side goes through the D1 mini board.
Tallest parts above the perfboard: U1 stack ≈ 7.3 mm (spacer 2.5 + PCB 1.5 +
shield/USB 3.3), SW1 actuator 7.3, J1 6, SW2 3.6 (on its side), C4 5.5, M1 ≈
5.5 (foam 1 + PCB 1 + USB-C 3.3), J2 2.5.

## 6. Enclosure (3D print, PETG or PLA, 0.2 mm layers) — designed for an elderly user

Ergonomic requirements: one **big, domed, high-contrast key cap** (Ø52 mm,
8 mm proud of the lid), low actuation force (100 gf tactile switch), no sharp
edges, rubber feet so the box does not slide when pressed.

- Three parts: **base** (floor + walls + 4 PCB standoffs + 4 lid screw bosses
  + 4 rubber-foot recesses), **lid** (round hole for the key cap, microphone
  pocket, charge-LED window), **key cap / plunger**.
- Cavity: **80 × 56 × 24 mm** (7 mm taller than rev. A for the LiPo under the
  board: 8 mm cell + 1.5 mm solder pins under the perfboard + 1.5 mm air).
  The perfboard (70 × 50, corners notched 5 × 5) sits at cavity offset
  **(2.46, 1.73)** (see §5): x 2.46 → 72.46, y 1.73 → 51.73. Walls 2 mm, floor 2 mm, lid 2 mm ⇒ outer **84 × 60 × 28 mm**.
  Outer vertical edges rounded r = 4 mm, bottom and lid-top edges r = 1.5 mm.
- PCB standoffs: Ø5 mm × **11 mm** tall, Ø1.6 mm pilot hole, at cavity
  **(36.19, 5.14), (36.19, 48.32), (13.33, 45.78), (66.67, 30.54)** (= grid
  holes L1, L18, C17, X11 + offset). The LiPo (40 × 30 × 8) lies on the floor
  between them, centred at cavity (40, 28).
- Lid bosses: Ø6 mm in the four inner corners (centres 3 mm from each wall),
  full cavity height, Ø2.0 mm pilot holes for M2.5 self-tapping screws; the
  lid has matching Ø2.8 mm countersunk holes.
- Programming micro-USB slot through the **y = 0 wall**: **14 mm wide × 9 mm
  tall** (the plug's overmold enters the wall so the shell seats fully),
  centre at cavity x = 19.68 (U1's micro-USB), z = 17.7 above the inner
  floor (11 standoff + 1.6 perfboard + 5.2).
- Charging USB-C slot through the **y = 0 wall**: **12 mm wide × 8 mm tall**,
  centre at cavity x = 57.5, z = 16.2 (M1 is glued flat: foam 1 + PCB 1 +
  receptacle centre 1.6 above the board top at 12.6).
- Slide-switch slot through the **x = 0 wall**: 8 mm wide (along y) × 4 mm
  tall, centre at cavity y = 43.24 (SW2's common pin A16), z = 14.75 (knob
  of the side-laid switch resting on the board top). The 4 mm lever ends
  inside the slot, ≈ 0.5 mm below the outer wall face: it is operated with a
  fingertip and cannot be knocked by accident.
- Rubber-foot recesses under the floor: Ø8 × 0.8 mm, 6 mm in from each corner.
- Key-cap hole in the lid: **Ø52.6 mm**, centred at cavity (40, 28) — the lid
  centre.
- **Microphone pocket** on the lid underside at cavity (74, 28): a 12 × 15 mm
  (x × y) recess 1.2 mm deep for the INMP441 breakout and a Ø2 mm sound hole
  through the lid at the pocket centre. The board is held with a drop of glue
  or foam tape, port facing the hole; 6 wires run to J2 on the perfboard.
- **Charge-LED window** in the lid: 10 (x) × 2.5 (y) mm slot centred at
  cavity (62, 4.5) (the closest spot to the TP4056 LEDs that clears the key-cap
  flange by 0.5 mm; the LEDs are seen obliquely), in
  the strip between the wall and the key-cap flange.
- Key cap: Ø52 mm, domed top (spherical dome rising 4 mm over a 4 mm tall
  cylindrical rim = 8 mm proud of the lid at rest), retaining flange Ø55 × 1.5
  mm under the lid, central stem Ø8 reaching the tactile switch actuator
  (actuator top 19.9 mm above the inner floor, lid underside at 24 mm, flange
  1.5 mm ⇒ stem ≈ 2.3 mm below the flange, tip at 20.2 mm, 0.3 mm play).
  Radial clearance 0.3 mm in the lid hole; the 2 mm thick lid is the guide.
  Travel ≈ 0.5 mm; the tactile switch is the return spring. Inserted from
  inside before closing the lid. Print the cap in a bright contrasting colour
  (red or yellow).
- Antenna side (y = 56 wall) left plain, no metal anywhere in the enclosure.
