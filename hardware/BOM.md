# Bill of materials — ESP8266 D1 mini MQTT battery button (rev C, LiPo + I2S audio)

Expanded from [DESIGN.md](DESIGN.md) section 4. Reference designators match
`schematic/schematic.svg`, `schematic/perfboard-layout.svg` (component side) and
`schematic/perfboard-solder-side.svg` (mirrored, all wires); every lead and wire
position comes from `layout/layout.json`. **Assembly instructions: [BUILD.md](BUILD.md)
(Italian: [BUILD.it.md](BUILD.it.md)).** Manufacturer part numbers are examples:
any part with the same package and ratings works.

No SMD part is soldered by hand: the three modules (U1, M1, M2) are the only
pre-assembled SMD items; everything else is through-hole.

## Parts

| Ref | Qty | Part | Value / rating | Package / notes | Example MPN |
|---|---|---|---|---|---|
| U1 | 1 | Wemos / LOLIN D1 mini (ESP8266, CH340, 4 MB flash) | — | 34.2 × 25.6 mm, 2 × 8 pins 2.54 mm, rows 22.86 mm apart; pins in A3..A10 and J3..J10, micro-USB on the y = 0 edge | LOLIN D1 mini V4.0.0 (or V3 / clone) |
| — | 2 | Male pin header 1 × 8, 2.54 mm (for U1) | — | long (6 mm) side down through the perfboard, short side through the D1 mini; tails trimmed flush after soldering | generic 1 × 40 breakable header, cut to 8 |
| PCB1 | 1 | Perfboard, single side | — | 70 × 50 mm, 2.54 mm pitch, 24 × 18 holes (A..X × 1..18), FR-4 1.6 mm; corners notched 5 × 5 mm; holes L1, L18, C17, X11 drilled Ø2.2 | generic 5 × 7 cm FR-4 protoboard |
| BT1 | 1 | LiPo cell 803040 with JST-PH 2.0 plug (M1 provides the protection) | 3.7 V 1000 mAh | 8 × 30 × 40 mm, taped to the enclosure floor under the perfboard | generic 803040 1000 mAh (e.g. EEMB LP803040) |
| M1 | 1 | TP4056 Li-ion charger module with DW01A + FS8205A protection, USB-C | 1.0 A default (R_PROG 1.2 kΩ); fit 2.4 kΩ for 0.5 A | 17.5 × 26 mm module "03962A" (USB-C variant); **glued flat on the perfboard with 1 mm double-sided foam tape** over columns R..X rows 1..9, USB-C over the y = 0 edge; **wired from its pads B+, B−, OUT+, OUT−, CHRG (no header pins)**; IN+/IN− unused | TP4056 03962A USB-C (generic) |
| M2 | 1 | INMP441 I2S MEMS microphone breakout | 1.8–3.3 V, 1.4 mA, 24-bit I2S | 11 × 14 mm, 6 pins VDD GND SD WS SCK L/R; in a pocket under the lid, sound port over a Ø2 mm hole; 6-wire lead to J2 | generic INMP441 breakout (TDK InvenSense INMP441 capsule) |
| J2 | 1 | Right-angle 1 × 6 male header 2.54 mm (microphone lead) | — | pins in Q17..V17 = SCK, WS, SD, VDD, L/R, GND (pins 1–6), bent pins toward row 18 | Harwin M20-9730646, generic 1 × 6 right-angle header |
| — | 1 | 6-way female DuPont lead (J2 → M2) | — | ≈ 90 mm, 1 × 6 female housing on the J2 end, wires soldered to the M2 pads | generic pre-crimped DuPont lead, 6 ways |
| R3 | 1 | Resistor, axial (CHRG pull-up on GPIO16) | 10 kΩ 1/4 W 5 % | axial, leads in K7 – O7 | Yageo CFR-25JB-52-10K |
| J1 | 1 | JST-PH 2-pin right-angle header (battery) | 2.0 mm pitch | pins spread to 2.54 mm into X14 (+), X15 (−); opening toward the x = 70 edge | JST S2B-PH-K-S |
| SW1 | 1 | Tactile switch 12 × 12 mm, THT | actuator **7.3 mm** (B3F-4000), **low force 100 gf** | standard 12 × 12 footprint, pins in K9 P9 K11 P11; 8.5 mm actuator variants such as Würth 430476085716 collide with the key-cap stem | Omron B3F-4000 (alt. B3F-4055 160 gf) |
| SW2 | 1 | SPDT slide switch (power) | 50 V 0.5 A | **SS12D00G4 (4 mm lever)**, 8.6 × 3.6 mm body, 3 pins 3.0 mm pitch; **mounted on its side at the x = 0 board edge, pins bent 90°** into A15 (ON) A16 (COM) A17 (NC), lever through the wall slot | SS12D00G4 |
| D2 | 1 | Schottky diode (battery → 5V pin), THT | 40 V 1 A, Vf ≈ 0.3 V | axial DO-41, leads in K3 (cathode, band) – O3 | ON 1N5819 (ST 1N5819, Vishay 1N5819) |
| C3 | 1 | Ceramic capacitor X7R | 100 nF 50 V | 2.54 mm pitch, leads in Q11 – Q12 | Vishay K104K15X7RF53H5, generic |
| C4 | 1 | Electrolytic capacitor, low ESR (3V3 rail) | 100 µF 6.3 V (10 V ok) | Ø5 × 11 mm radial, leads bent 90°, body lying flat toward column X; − in Q14, + in Q15 | Panasonic EEUFR1A101 (10 V), Nichicon UPW |
| R2 | 1 | Resistor, axial | 10 kΩ 1/4 W 5 % | axial, leads in K5 – O5 | Yageo CFR-25JB-52-10K |
| JP1 | — | Solder bridge (no part): pads A10 (RST) and A11 (BTN), 2.54 mm apart | — | bridged with solder on the solder side = battery mode (RST wake); open = `always_on` | — |
| — | 1 | Insulated hook-up wire kit, 26 AWG stranded, ≥ 12 colours | — | 22 wires, ≈ 0.8 m in total (lengths in BUILD.md); one colour per net, see the colour map below | generic 26 AWG silicone wire kit |
| — | 1 | Bare tinned copper wire 0.6 mm | — | links K3–J3 and U17–V17 | generic |
| — | 1 | Double-sided foam tape, 1 mm | — | holds M1 on the perfboard and the LiPo on the enclosure floor | 3M VHB / generic 1 mm foam tape |
| — | 4 | Screw M2 × 8 mm self-tapping | — | PCB to base standoffs | generic |
| — | 4 | Screw M2.5 × 10 mm self-tapping | — | lid to base bosses | generic |
| — | 4 | Adhesive rubber foot Ø8 mm | — | under the base, so the box does not slide when pressed | 3M SJ5302 / generic bumpon |

Wire colour map (net → colour, from `layout/gen_layout.py` `NET_COLOUR`):
GND black, 3V3 red, 5V orange, VSW yellow, VBAT brown, BAT− grey, BTN white,
RST bare (solder bridge), CHRG violet, MICPWR green, I2S_SCK blue, I2S_WS pink,
I2S_SD turquoise. Any colours work, but keep one colour per net and note the
substitutions in the BUILD.md table. 5V is a bare link in rev C (no orange wire).

Removed since rev A: CR2032 + holder, supercapacitors C1/C2, R1 68 Ω.
Removed since the first rev B draft: MIC1 electret capsule and the MAX9814 preamp
(the ESP8266 ADC cannot be sampled from an ISR while Wi-Fi is active); the
I2S microphone needs no ADC.
Removed in rev C: the SS14 (SMA) alternative for D2 and the header pins under M1
(the module is glued and wired from its pads); nothing SMD is soldered by hand.
Not used by default: 2 × 8-pin female headers for U1 (would add 8.5 mm of
height and no longer fit the enclosure).

## Wiring / netlist

Hole names are perfboard grid coordinates (columns A..X, rows 1..18, component-side
view, USB edge toward you); the wire numbers are those of `layout/layout.json`,
BUILD.md section 3–4 and `schematic/perfboard-solder-side.svg`.

| Net | Connected pins | Wires |
|---|---|---|
| **VBAT** | BT1 (+) → J1 pin 1 (X14) → M1 `B+` | 20 brown |
| **BAT−** | BT1 (−) → J1 pin 2 (X15) → M1 `B−` (goes through the DW01/FS8205 protection inside M1; *not* the GND net) | 21 grey |
| **VSW** (switched battery) | M1 `OUT+` → SW2 common (A16); SW2 ON contact (A15) → D2 anode (O3) | 18, 19 yellow |
| **5V** | D2 cathode (band, K3) → U1 pin `5V` (J3) (on-board ME6211 LDO → 3V3); USB programming puts 5 V here too, D2 blocks back-feed | 1 bare link |
| **3V3** | U1 pin `3V3` (A3), R2 pin 2 (O5), R3 pin 2 (O7), C4 (+) (Q15) | 13, 14, 15 red |
| **GND** | U1 pin `G` (J4), SW1 pins 2a/2b (K11, P11), C3 pin 2 (Q12), C4 (−) (Q14), J2 pin 6 (V17) → M2 `GND`, J2 pin 5 (U17) → M2 `L/R` (left channel), M1 `OUT−` | 7, 8, 9, 10, 12 black; 11 bare link |
| **BTN** | R2 pin 1 (K5), SW1 pins 1a/1b (K9, P9), C3 pin 1 (Q11), U1 pin `D1` GPIO5 (J8), JP1 pad A11 | 3, 4, 5, 6 white |
| **RST** | U1 pin `RST` (A10) — JP1 solder bridge A10–A11 to BTN | 2 bridge |
| **MICPWR** | U1 pin `D2` GPIO4 (J7, output) → J2 pin 4 (T17) → M2 `VDD` (power gated, 1.4 mA when on) | 22 green |
| **I2S_SCK** | U1 pin `D7` GPIO13 (A5, I2S bit clock out) → J2 pin 1 (Q17) → M2 `SCK` | 23 blue |
| **I2S_WS** | U1 pin `D5` GPIO14 (A7, I2S word select out) → J2 pin 2 (R17) → M2 `WS` | 24 pink |
| **I2S_SD** | M2 `SD` → J2 pin 3 (S17) → U1 pin `D6` GPIO12 (A6, I2S data in) | 25 turquoise |
| **CHRG** | M1 `CHRG` LED pad (open drain, low = charging) → R3 pin 1 (K7) → U1 pin `D0` GPIO16 (A8, input); R3 = 10 kΩ pull-up to 3V3 (GPIO16 has no internal pull-up) | 16, 17 violet |
| **LED** | U1 `D4` (GPIO2) drives the D1 mini's own LED (active-low): on while recording; nothing to wire | — |
| n.c. | U1 `A0`, `D3`, `D8`, `RX`, `TX`; SW2 NC contact (A17); M1 `IN+`/`IN−` (USB-C input, nothing soldered) | — |

Notes:

- Mind the polarity of C4 (stripe = −, toward row 14) and the orientation of D2
  (band toward column K, next to U1's 5V pin).
- JP1 is a solder bridge: bridged = battery mode (a press pulls RST low and
  wakes U1 from deep sleep); open = `always_on` mode (USB powered, GPIO5 polled).
- Rev C: the perfboard has 5 × 5 mm corner notches and mounting holes at the
  grid holes L1, L18, C17, X11 (Ø2.2, Ø5 standoff underneath: keep the 8 holes
  around each free); the perfboard origin sits at cavity (2.46, 1.73) and the
  LiPo is centred under the key cap at cavity (40, 28).
- Battery voltage is **not** measured; A0 is left unconnected. GPIO12/13/14 are
  the ESP8266's fixed I2S RX pins, which is why CHRG moved to GPIO16 and the
  mic power to GPIO4.

## Caveats

- **Charge only via M1's USB-C port** (TP4056). Never feed the LiPo from the
  D1 mini USB: D2 blocks it anyway.
- **USB programming is allowed at any time**, with SW2 in any position (D2
  blocks back-feed into the cell) — the rev A "SW2 OFF before USB" rule no
  longer applies.
- **Rev B: LiPo replaces the CR2032** because audio recording draws ≈ 75 mA
  for minutes (≈ 4 mAh per 3-minute press), far beyond a coin cell.
- Expected endurance: deep-sleep standby ≈ 0.25 mA (D1 mini LDO + CH340
  leakage, TP4056 idle < 10 µA) ⇒ ≈ 4 months; recording ≈ 75 mA ⇒ 1000 mAh ≈
  13 h of audio ≈ 250 three-minute presses per charge; charge at 500 mA ≈ 2.5 h.
- Rev B.1: the electret + MAX9814 + ADC path was dropped after bench tests (the
  ESP8266 ADC read goes through the Wi-Fi PHY and crashes when called from an
  ISR under TCP traffic); the INMP441 is filled by I2S DMA with no CPU or radio
  interaction. A0 stays unconnected.
- M1's `CHRG` pad: the LED pad that goes to TP4056 pin 7 (not the 5 V/resistor
  side); check with the multimeter in diode mode before soldering (BUILD.md §5).
