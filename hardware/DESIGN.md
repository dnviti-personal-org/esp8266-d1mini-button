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
- Battery voltage is not measured: the single ADC input A0 is used by the
  microphone.

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

## 3. Audio path

```
MIC1 electret Ø9.7 mm ─ M2 MAX9814 preamp module (AGC, 60 dB max) ─ OUT ─ A0 (D1 mini 220k/100k divider → ADC 0–1 V)
                        M2 VDD ← D5 (GPIO14)   power gated, ≈ 3 mA when on
                        M2 GAIN, A/R: floating (60 dB, 1:4000 attack/release)
```

- The capsule sits in the lid, 2 wires to the MAX9814 "MIC" pads (the stock
  capsule on the module is removed or left unused — its pads are in parallel).
- Sampling: timer ISR at 8 kHz, 10-bit ADC stored as 8-bit unsigned PCM, WAV
  container, written to LittleFS (3 MB partition ⇒ up to 240 s per file).
- After the recording the ESP serves `http://<ip>/rec.wav` and publishes a
  JSON on MQTT (`<prefix>/<mac>/recording`); Home Assistant downloads it
  (`downloader` integration, see `homeassistant/`). The ESP stays awake until
  the file has been streamed once or 90 s elapse, then sleeps.

## 4. Bill of materials

| Ref | Part | Package / notes |
|---|---|---|
| U1 | Wemos / LOLIN D1 mini (ESP8266, CH340, 4 MB flash) | 34.2 × 25.6 mm, 2 × 8 pins 2.54 mm, rows 22.86 mm apart |
| PCB1 | Perfboard 50 × 70 mm, 2.54 mm pitch, single side | 18 × 24 holes, FR-4 1.6 mm |
| BT1 | LiPo 3.7 V 1000 mAh 803040 with JST-PH 2.0 plug | 8 × 30 × 40 mm, lies under the perfboard |
| M1 | TP4056 charger module with DW01/FS8205 protection, USB-C (03962A) | 26 × 17.5 mm, 1.0 A default (R_PROG 1.2 kΩ); change R_PROG to 2.4 kΩ for 0.5 A |
| M2 | MAX9814 electret preamp module with AGC (Adafruit 1713 or clone) | 26 × 15.3 mm, 6 pins: VDD GND OUT GAIN AR + MIC pads |
| MIC1 | Electret condenser capsule Ø9.7 × 6.7 mm, 2 pins (e.g. CUI CMC-9767-130T, PUI AOM-6738P) | mounted in the lid, 2 wires to M2 |
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
| M1 TP4056 | (54.0, 9.5) | 26 (X) × 17.5 (Y) | USB-C toward the **y = 0** edge (protrudes ≈ 1.5 mm), on male header pins |
| M2 MAX9814 | (54.0, 36.0) | 15.3 (X) × 26 (Y) | pins toward y = 50; MIC pads toward SW1 |
| J1 battery | (66.0, 24.0) | 6 (X) × 5 (Y) | wires leave toward x = 70 and go under the board |
| D2 | (36.0, 7.0) | axial, 10 mm along X | cathode (band) toward U1 |
| R2 | (36.0, 13.0) | axial, 10 mm along X | |
| C3 | (36.0, 35.0) | 2.54 pitch | |
| C4 | (36.0, 42.0) | Ø5 × 11 lying flat along X | |
| JP1 | (34.0, 47.5) | 2 pins along X | |
| SW2 slide | (67.0, 36.0) | 3.6 (X) × 8.6 (Y) | actuator points to the **x = 70** edge |
| BT1 LiPo | (35.0, 25.0) **under the board** | 40 (X) × 30 (Y) × 8 | taped to the floor |
| Mounting holes | (3,3) (67,3) (3,47) (67,47) | Ø2.2 | drill if the board has none |

Tallest parts above the perfboard top surface: U1 stack ≈ 7.0 mm (header
2.5 + PCB 1.0 + shield/USB 3.5), M1 ≈ 6.8 (header 2.5 + PCB 1.0 + USB-C 3.3),
M2 ≈ 5 mm, SW1 actuator top 7.3 mm. micro-USB receptacle centre ≈ 5.2 mm
above the perfboard at x = 15.8 on the y = 0 edge; USB-C receptacle centre
≈ 5.2 mm above the perfboard at x = 54 on the y = 0 edge.

## 6. Enclosure (3D print, PETG or PLA, 0.2 mm layers) — designed for an elderly user

Ergonomic requirements: one **big, domed, high-contrast key cap** (Ø52 mm,
8 mm proud of the lid), low actuation force (100 gf tactile switch), no sharp
edges, rubber feet so the box does not slide when pressed.

- Three parts: **base** (floor + walls + 4 PCB standoffs + 4 lid screw bosses
  + 4 rubber-foot recesses), **lid** (round hole for the key cap, microphone
  socket, charge-LED window), **key cap / plunger**.
- Cavity: **80 × 56 × 23 mm** (6 mm taller than rev. A for the LiPo under the
  board). The perfboard (70 × 50) sits at cavity offset (5, 3): x 5 → 75,
  y 3 → 53. Walls 2 mm, floor 2 mm, lid 2 mm ⇒ outer **84 × 60 × 27 mm**.
  Outer vertical edges rounded r = 4 mm, bottom and lid-top edges r = 1.5 mm.
- PCB standoffs: Ø5 mm × **10 mm** tall, Ø1.6 mm pilot hole, at cavity
  (8, 6), (72, 6), (8, 50), (72, 50). The LiPo (40 × 30 × 8) lies on the floor
  between them, centred at cavity (40, 28).
- Lid bosses: Ø6 mm in the four inner corners (centres 3 mm from each wall),
  full cavity height, Ø2.0 mm pilot holes for M2.5 self-tapping screws; the
  lid has matching Ø2.8 mm countersunk holes.
- Programming USB slot through the **y = 0 wall**: 12 mm wide × 7 mm tall,
  centre at cavity x = 20.8, z = 16.7 above the inner floor (10 standoff +
  1.6 perfboard + 5.2).
- Charging USB-C slot through the **y = 0 wall**: 10 mm wide × 5 mm tall,
  centre at cavity x = 59, z = 16.7.
- Slide-switch slot through the **x = 80 wall**: 8 mm wide (along y) × 3.5 mm
  tall, centre at cavity y = 39, z ≈ 13.8 above the inner floor.
- Rubber-foot recesses under the floor: Ø8 × 0.8 mm, 6 mm in from each corner.
- Key-cap hole in the lid: **Ø52.6 mm**, centred at cavity (40, 28) — the lid
  centre.
- **Microphone socket** in the lid at cavity (74, 28): Ø7 mm through-hole
  (sound opening, optionally 7 × Ø1.5 holes in a hex pattern instead) and,
  on the lid underside, a ring Ø9.9 inner / Ø12.5 outer, 4 mm tall, that holds
  the Ø9.7 capsule by friction (glue a drop if loose). The capsule's wires run
  to M2 on the perfboard.
- **Charge-LED window** in the lid: 6 (x) × 3 (y) mm slot centred at cavity
  (59, 16), above the TP4056 LEDs.
- Key cap: Ø52 mm, domed top (spherical dome rising 4 mm over a 4 mm tall
  cylindrical rim = 8 mm proud of the lid at rest), retaining flange Ø55 × 1.5
  mm under the lid, central stem Ø8 reaching the tactile switch actuator
  (actuator top 18.9 mm above the inner floor, lid underside at 23 mm, flange
  1.5 mm ⇒ stem ≈ 2.3 mm below the flange, tip at 19.2 mm, 0.3 mm play).
  Radial clearance 0.3 mm in the lid hole; the 2 mm thick lid is the guide.
  Travel ≈ 0.5 mm; the tactile switch is the return spring. Inserted from
  inside before closing the lid. Print the cap in a bright contrasting colour
  (red or yellow).
- Antenna side (y = 56 wall) left plain, no metal anywhere in the enclosure.
