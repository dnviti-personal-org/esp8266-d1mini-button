# Hardware design — ESP8266 D1 mini battery button

Single source of truth for dimensions and the electrical design. The 3D
enclosure (SolidCraft), the schematic / perfboard layout (CADCraft) and the
firmware all follow this file.

## 1. Power architecture (CR2032, 3.0 V nominal)

The ESP8266 draws ~80 mA average and 300–400 mA peaks while Wi-Fi is active.
A CR2032 (≈220 mAh, internal resistance 10–40 Ω, ~3 mA continuous rating)
cannot source that directly: its voltage collapses under load. The design
therefore uses the cell as an **energy reservoir** and a **supercapacitor bank
as the power source** during the ~2–4 s a transmission takes:

```
BT1 (CR2032) ─ SW2 (slide, power) ─ R1 68Ω ─┬─ VCAP ─── D1 mini "3V3" pin
                                            ├─ C1 ┐  2 × 2.7 V 3.3 F EDLC in series
                                            │  C2 ┘  (= 1.65 F, 5.4 V rated)
                                            └─ C4 100 µF low-ESR (HF peaks)
GND ────────────────────────────────────────┴───────── D1 mini "G" pin
```

- The ESP runs in **deep sleep** between presses (wake on RST). The button
  press is itself the event: boot → Wi-Fi → MQTT publish → deep sleep.
- Per press: ~3 s × 80 mA = 0.24 C → ΔV on 1.65 F ≈ 0.15 V. Several presses
  in quick succession are fine; the cell refills the bank through R1
  (τ ≈ 112 s).
- R1 limits the cell current (≤ 45 mA at first insertion, then < 5 mA).
- The D1 mini is fed **directly on its 3V3 pin**, bypassing the on-board LDO.
- **Standby current** of a D1 mini powered this way is ~0.2–0.3 mA (LDO
  back-feed + CH340 leakage), not the 20 µA of a bare ESP module. Expected
  battery life: **≈ 4–6 weeks** of standby. If longer life is needed, swap the
  D1 mini for a bare ESP-12F module, or the CR2032 for a CR123A / 2×AAA.
- **Never connect USB while SW2 is ON**: the USB LDO (3.3 V) would push current
  back into the lithium cell. SW2 OFF for programming is mandatory.

## 2. Button wiring

```
3V3 ─ R2 10k ─┬─ D1 (GPIO5)           (input, pressed = LOW)
              ├─ JP1 ─ RST            (closed = battery mode, wake from deep sleep)
              ├─ C3 100 nF ─ GND      (noise filter / RC debounce)
              └─ SW1 (12×12 tactile) ─ GND
```

- JP1 closed: a press pulls RST low → wake from deep sleep. The firmware reads
  the reset reason: wake-from-deep-sleep ⇒ "button pressed" event.
- JP1 open: `always_on` mode, the firmware debounces GPIO5 and publishes
  ON/OFF edges continuously (USB powered use).
- Battery voltage is read with `ADC_MODE(ADC_VCC)`; **A0 stays unconnected**.
- The on-board LED (GPIO2, active-low) blinks once on publish.

## 3. Bill of materials

| Ref | Part | Package / notes |
|---|---|---|
| U1 | Wemos / LOLIN D1 mini (ESP8266, CH340) | 34.2 × 25.6 mm, 2 × 8 pins 2.54 mm, rows 22.86 mm apart |
| PCB1 | Perfboard 50 × 70 mm, 2.54 mm pitch, single side | 18 × 24 holes, FR-4 1.6 mm |
| BT1 | CR2032 holder, THT, 20 mm coin | e.g. Keystone 3034 / generic 2-pin, footprint ≈ 24 × 24 mm, 6 mm tall with cell |
| SW1 | Tactile switch 12 × 12 mm, THT, 7.3 mm actuator | pins at 12.5 × 12.5 mm... use standard 12×12 footprint |
| SW2 | SPDT slide switch SS12D00 (power) | 8.6 × 3.6 mm body, 3 pins 3.0 mm pitch, actuator 2 mm |
| C1, C2 | Supercapacitor 2.7 V 3.3 F, cylindrical radial, low ESR | Ø8 × 20 mm, pitch 3.5 mm, mounted lying flat |
| C3 | 100 nF ceramic X7R | 2.54 mm pitch |
| C4 | 100 µF 6.3 V low-ESR electrolytic | Ø5 × 11 mm radial |
| R1 | 68 Ω 1/4 W | axial |
| R2 | 10 kΩ 1/4 W | axial |
| JP1 | 2-pin header 2.54 mm + shunt (or solder bridge) | |
| — | Female headers 2 × 8 pins (optional, to make U1 removable) | adds 8.5 mm height: **not used by default**, U1 soldered with its male pins |
| — | 4 × M2 × 8 mm self-tapping screws (PCB), 4 × M2.5 × 10 mm (lid) | |

## 4. Perfboard placement (mm, origin = perfboard bottom-left corner, X along 70 mm, Y along 50 mm, top view)

| Ref | Center (x, y) | Footprint | Orientation |
|---|---|---|---|
| U1 D1 mini | (15.8, 25.0) | 25.6 (X) × 34.2 (Y) | micro-USB toward the **y = 0** edge, antenna toward y = 50 |
| SW1 button | (52.0, 32.0) | 12 × 12 | — |
| BT1 holder | (52.0, 12.0) | ≈ 24 × 24 | cell loads from the top |
| C1 | (34.0, 36.0) | Ø8 × 20, lying flat along Y | y 26 → 46 |
| C2 | (42.0, 36.0) | Ø8 × 20, lying flat along Y | y 26 → 46 |
| C4 | (36.0, 18.0) | Ø5 × 11 lying flat along Y | |
| R1 | (33.0, 10.0) | axial, 10 mm along Y | |
| R2 | (33.0, 3.5) | axial, 10 mm along X | |
| C3 | (40.0, 4.0) | 2.54 pitch | |
| JP1 | (32.0, 44.0) | 2 pins along X | |
| SW2 slide | (66.0, 40.0) | 8.6 (Y) × 3.6 (X) | actuator points to the **x = 70** edge |
| Mounting holes | (3,3) (67,3) (3,47) (67,47) | Ø2.2 | drill if the board has none |

Tallest parts above the perfboard top surface: U1 stack ≈ 7.0 mm (header
2.5 + PCB 1.0 + shield/USB 3.5), C1/C2 8 mm, BT1 with cell 6 mm, SW1 actuator
top 7.3 mm. micro-USB receptacle centre ≈ 5.2 mm above the perfboard, at
perfboard x = 15.8 on the y = 0 edge (protrudes ~1 mm past the board edge).

## 5. Enclosure (3D print, PETG or PLA, 0.2 mm layers)

- Two parts + plunger: **base** (floor + walls + 4 PCB standoffs + 4 lid screw
  bosses), **lid** (with round hole for the plunger), **plunger** (key cap).
- Cavity: 73 × 53 × 17 mm (perfboard 70 × 50 sits centred with 1.5 mm
  clearance on each side). Walls 2 mm, floor 2 mm, lid 2 mm ⇒ outer
  77 × 57 × 21 mm. Outer vertical edges rounded r = 3 mm.
- PCB standoffs: Ø5 mm × 4 mm tall, Ø1.6 mm pilot hole, at the perfboard
  mounting holes above (cavity coordinates = perfboard + 1.5 mm on x and y).
- Lid bosses: Ø6 mm in the four inner corners, full cavity height, Ø2.0 mm
  pilot holes for M2.5 self-tapping screws; the lid has matching Ø2.8 mm
  countersunk holes.
- USB slot in the **y = 0 wall**: 12 mm wide × 7 mm tall, centre at cavity
  x = 17.3, z = 10.7 above the inner floor (4 standoff + 1.6 perfboard + 5.2).
- Slide-switch slot in the **x = 73 wall**: 8 mm wide (along y) × 3.5 mm tall,
  centre at cavity y = 41.5, z ≈ 7.8 above the inner floor.
- Plunger hole in the lid: Ø28.6 mm, centre at cavity (53.5, 33.5).
- Plunger: cap Ø28 mm × 3 mm, 4 mm proud of the lid at rest, with a retaining
  flange Ø32 mm × 1.5 mm under the lid and a central Ø6 mm stem reaching the
  tactile switch actuator (actuator top is 12.9 mm above the inner floor,
  lid underside at 17 mm). Travel ≈ 0.5 mm; the tactile switch is the return
  spring. Inserted from inside before closing the lid.
- Four ventilation / Wi-Fi friendly: no metal, antenna side (y = 50 wall)
  left plain.
