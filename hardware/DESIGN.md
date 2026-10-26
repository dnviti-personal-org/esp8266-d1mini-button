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
BT1 LiPo 803040 ─ M1 TP4056 charger + DW01 protection (USB-C) ─ OUT+ ─ SW2 ─ D2 SS14 ─ D1 mini "5V" pin
                                                                                           └─ on-board ME6211 LDO → 3V3
GND ─────────────────────────────────────────────────────────────────────────────────────── D1 mini "G"
```

- The battery enters the D1 mini on its **5V pin** through Schottky D2
  (SS14, Vf ≈ 0.3 V). The on-board LDO regulates to 3.3 V (it simply passes
  through when the LiPo is nearly empty; the ESP works down to 2.5 V).
- USB programming puts 5 V on the same rail; D2 blocks any current into the
  LiPo. USB may be plugged at any time, with SW2 in any position.
- Charging only through the TP4056's own USB-C port. Its CHRG output (open
  drain, low while charging) goes to D6/GPIO12 so the firmware can publish a
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
| M1 | TP4056 charger module with DW01/FS8205 protection, USB-C (03962A) | 26 × 17.5 mm, 1.0 A default (R_PROG 1.2 kΩ); change R_PROG to 2.4 kΩ for 0.5 A |
| M2 | INMP441 I2S MEMS microphone breakout | 11 × 14 mm, 6 pins (VDD GND SD WS SCK L/R), 1.4 mA, mounted under the lid, 6 wires to the perfboard |
| R3 | 10 kΩ 1/4 W (pull-up for CHRG on GPIO16) | axial |
| J1 | JST-PH 2-pin right-angle header (battery) | 2.0 mm pitch |
| SW1 | Tactile switch 12 × 12 mm, THT, 7.3 mm actuator, **low force 100 gf** (e.g. Omron B3F-4000) | standard 12×12 footprint |
| SW2 | SPDT slide switch SS12D00 (power) | 8.6 × 3.6 mm body, 3 pins 3.0 mm pitch, actuator 2 mm |
| D2 | Schottky diode SS14 / 1N5819 (battery → 5V pin) | axial / SMA on pads |
| C3 | 100 nF ceramic X7R | 2.54 mm pitch |
| C4 | 100 µF 6.3 V low-ESR electrolytic (3V3 rail) | Ø5 × 11 mm radial |
| R2 | 10 kΩ 1/4 W | axial |
| JP1 | 2-pin header 2.54 mm + shunt (or solder bridge) | |
| — | 4 × M2 × 8 mm self-tapping screws (PCB), 4 × M2.5 × 10 mm (lid), 4 × Ø8 mm adhesive rubber feet, double-sided foam tape for the LiPo | |

## 5. Perfboard placement (mm, origin = perfboard bottom-left corner, X along 70 mm, Y along 50 mm, top view)

The tactile switch sits at the **geometric centre of the enclosure** so the
big key cap is centred on the lid. The LiPo lies on the enclosure floor
**under** the perfboard.

| Ref | Center (x, y) | Footprint | Orientation |
|---|---|---|---|
| U1 D1 mini | (15.8, 25.0) | 25.6 (X) × 34.2 (Y) | micro-USB toward the **y = 0** edge, antenna toward y = 50 |
| SW1 button | (35.0, 25.0) | 12 × 12 | exact centre of the enclosure (cavity 40, 28) |
| M1 TP4056 | (52.5, 9.5) | 26 (X) × 17.5 (Y), x 39.5 → 65.5 | USB-C toward the **y = 0** edge (protrudes ≈ 1.5 mm), on male header pins |
| J2 mic header | (54.0, 36.0) | 6 pins 2.54 along Y | wires to M2 in the lid (SCK WS SD L/R VDD GND) |
| R3 | (44.0, 47.5) | axial, 10 mm along X | pads at x 39 and 49 |
| J1 battery | (66.0, 24.0) | 6 (X) × 5 (Y) | wires leave toward x = 70 and go under the board |
| D2 | (34.0, 7.0) | axial, 10 mm along X | cathode (band) toward U1 |
| R2 | (34.0, 13.0) | axial, 10 mm along X | |
| C3 | (36.0, 35.0) | 2.54 pitch | |
| C4 | (36.0, 42.0) | Ø5 × 11 lying flat along X | |
| JP1 | (34.0, 47.5) | 2 pins along X | |
| SW2 slide | (67.0, 36.0) | 3.6 (X) × 8.6 (Y) | actuator points to the **x = 70** edge |
| BT1 LiPo | (35.0, 25.0) **under the board** | 40 (X) × 30 (Y) × 8 | taped to the floor |
| Mounting holes | (3,3) (67,3) (3,47) (67,47) | Ø2.2 | drill if the board has none |

Solder pins protrude ≈ 1.5 mm below the perfboard. Tallest parts above the perfboard top surface: U1 stack ≈ 7.0 mm (header
2.5 + PCB 1.0 + shield/USB 3.5), M1 ≈ 6.8 (header 2.5 + PCB 1.0 + USB-C 3.3),
J2 header ≈ 8 mm, SW1 actuator top 7.3 mm. micro-USB receptacle centre ≈ 5.2 mm
above the perfboard at x = 15.8 on the y = 0 edge; USB-C receptacle centre
≈ 5.2 mm above the perfboard at x = 54 on the y = 0 edge.

## 6. Enclosure (3D print, PETG or PLA, 0.2 mm layers) — designed for an elderly user

Ergonomic requirements: one **big, domed, high-contrast key cap** (Ø52 mm,
8 mm proud of the lid), low actuation force (100 gf tactile switch), no sharp
edges, rubber feet so the box does not slide when pressed.

- Three parts: **base** (floor + walls + 4 PCB standoffs + 4 lid screw bosses
  + 4 rubber-foot recesses), **lid** (round hole for the key cap, microphone
  pocket, charge-LED window), **key cap / plunger**.
- Cavity: **80 × 56 × 24 mm** (7 mm taller than rev. A for the LiPo under the
  board: 8 mm cell + 1.5 mm solder pins under the perfboard + 1.5 mm air). The perfboard (70 × 50) sits at cavity offset (5, 3): x 5 → 75,
  y 3 → 53. Walls 2 mm, floor 2 mm, lid 2 mm ⇒ outer **84 × 60 × 28 mm**.
  Outer vertical edges rounded r = 4 mm, bottom and lid-top edges r = 1.5 mm.
- PCB standoffs: Ø5 mm × **11 mm** tall, Ø1.6 mm pilot hole, at cavity
  (8, 6), (72, 6), (8, 50), (72, 50). The LiPo (40 × 30 × 8) lies on the floor
  between them, centred at cavity (40, 28).
- Lid bosses: Ø6 mm in the four inner corners (centres 3 mm from each wall),
  full cavity height, Ø2.0 mm pilot holes for M2.5 self-tapping screws; the
  lid has matching Ø2.8 mm countersunk holes.
- Programming USB slot through the **y = 0 wall**: 12 mm wide × 7 mm tall,
  centre at cavity x = 20.8, z = 17.7 above the inner floor (11 standoff +
  1.6 perfboard + 5.2).
- Charging USB-C slot through the **y = 0 wall**: 10 mm wide × 5 mm tall,
  centre at cavity x = 57.5, z = 17.7.
- Slide-switch slot through the **x = 80 wall**: 8 mm wide (along y) × 3.5 mm
  tall, centre at cavity y = 39, z ≈ 14.8 above the inner floor.
- Rubber-foot recesses under the floor: Ø8 × 0.8 mm, 6 mm in from each corner.
- Key-cap hole in the lid: **Ø52.6 mm**, centred at cavity (40, 28) — the lid
  centre.
- **Microphone pocket** on the lid underside at cavity (74, 28): a 12 × 15 mm
  (x × y) recess 1.2 mm deep for the INMP441 breakout and a Ø2 mm sound hole
  through the lid at the pocket centre. The board is held with a drop of glue
  or foam tape, port facing the hole; 6 wires run to J2 on the perfboard.
- **Charge-LED window** in the lid: 6 (x) × 3 (y) mm slot centred at cavity
  (66.5, 11), just outside the key-cap flange on the TP4056 side (the module's
  LEDs are seen obliquely; add a short light pipe or mount M1 with its LEDs
  toward x = 70 if needed).
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
