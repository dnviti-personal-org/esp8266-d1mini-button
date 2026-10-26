# Bill of materials — ESP8266 D1 mini MQTT battery button (rev B.1, LiPo + I2S audio)

Expanded from [DESIGN.md](DESIGN.md) section 4. Reference designators match
`schematic/schematic.svg` and `schematic/perfboard-layout.svg`. Manufacturer
part numbers are examples: any part with the same package and ratings works.

## Parts

| Ref | Qty | Part | Value / rating | Package / notes | Example MPN |
|---|---|---|---|---|---|
| U1 | 1 | Wemos / LOLIN D1 mini (ESP8266, CH340, 4 MB flash) | — | 34.2 × 25.6 mm, 2 × 8 pins 2.54 mm, rows 22.86 mm apart; soldered with its male pins (no female headers) | LOLIN D1 mini V4.0.0 (or V3 / clone) |
| PCB1 | 1 | Perfboard, single side | — | 70 × 50 mm, 2.54 mm pitch, 24 × 18 holes, FR-4 1.6 mm | generic 5 × 7 cm FR-4 protoboard |
| BT1 | 1 | LiPo cell 803040 with protection-less JST-PH 2.0 plug (M1 provides the protection) | 3.7 V 1000 mAh | 8 × 30 × 40 mm, taped to the enclosure floor under the perfboard | generic 803040 1000 mAh (e.g. EEMB LP803040, Adafruit 2011-class) |
| M1 | 1 | TP4056 Li-ion charger module with DW01A + FS8205A protection, USB-C | 1.0 A default (R_PROG 1.2 kΩ); fit 2.4 kΩ for 0.5 A | 26 × 17.5 mm module "03962A" (USB-C variant), soldered on male header pins; pads B+ B− OUT+ OUT− IN+ IN−, CHRG/STDBY LED pads | TP4056 03962A USB-C (generic) |
| M2 | 1 | INMP441 I2S MEMS microphone breakout | 1.8–3.3 V, 1.4 mA, 24-bit I2S | 11 × 14 mm, 6 pins VDD GND SD WS SCK L/R; mounted in a pocket under the lid, sound port over a Ø2 mm hole; 6 wires to J2 | generic INMP441 breakout (TDK InvenSense INMP441 capsule) |
| J2 | 1 | 6-pin header 2.54 mm (microphone wires) | — | 1 × 6 along Y; mates a 6-way DuPont / pre-crimped lead to M2 | generic 1 × 6 male pin header (or JST-XH B6B-XH-A) |
| R3 | 1 | Resistor, axial (CHRG pull-up on GPIO16) | 10 kΩ 1/4 W 5 % | axial, 10 mm along X | Yageo CFR-25JB-52-10K |
| J1 | 1 | JST-PH 2-pin right-angle header (battery) | 2.0 mm pitch | mates with the BT1 plug | JST S2B-PH-K-S |
| SW1 | 1 | Tactile switch 12 × 12 mm, THT | 7.3 mm actuator, **low force 100 gf** | standard 12 × 12 footprint, 4 pins | Omron B3F-4000 (alt. B3F-4055 160 gf) |
| SW2 | 1 | SPDT slide switch (power) | 50 V 0.5 A | 8.6 × 3.6 mm body, 3 pins 3.0 mm pitch, 2 mm actuator | SS12D00 (G3/G4/G5 lever length) |
| D2 | 1 | Schottky diode (battery → 5V pin) | 40 V 1 A, Vf ≈ 0.3 V | axial DO-41 (1N5819) or SMA (SS14) on pads | Vishay SS14 / ON 1N5819 |
| C3 | 1 | Ceramic capacitor X7R | 100 nF 50 V | 2.54 mm pitch | Vishay K104K15X7RF53H5, generic |
| C4 | 1 | Electrolytic capacitor, low ESR (3V3 rail) | 100 µF 6.3 V (10 V ok) | Ø5 × 11 mm radial, lying flat along X | Panasonic EEUFR1A101 (10 V), Nichicon UPW |
| R2 | 1 | Resistor, axial | 10 kΩ 1/4 W 5 % | axial, 10 mm along X | Yageo CFR-25JB-52-10K |
| JP1 | 1 | 2-pin header 2.54 mm + shunt (or a solder bridge) | — | 2 pins along X | generic 1 × 2 male header + 2.54 mm jumper cap |
| — | 4 | Screw M2 × 8 mm self-tapping | — | PCB to base standoffs | generic |
| — | 4 | Screw M2.5 × 10 mm self-tapping | — | lid to base bosses | generic |
| — | 4 | Adhesive rubber foot Ø8 mm | — | under the base, so the box does not slide when pressed | 3M SJ5302 / generic bumpon |
| — | 1 | Double-sided foam tape | — | holds the LiPo on the enclosure floor | 3M VHB 4910 / generic |
| — | — | Hook-up wire, solder | — | perfboard links; 6-wire lead lid (M2) → J2, ≈ 8 cm | — |

Removed since rev A: CR2032 + holder, supercapacitors C1/C2, R1 68 Ω.
Removed since the first rev B draft: MIC1 electret capsule and the MAX9814 preamp
(the ESP8266 ADC cannot be sampled from an ISR while Wi-Fi is active); the
I2S microphone needs no ADC.
Not used by default: 2 × 8-pin female headers for U1 (would add 8.5 mm of
height and no longer fit the enclosure).

## Wiring / netlist

Perfboard top view, origin at the bottom-left corner (see
`schematic/perfboard-layout.svg` for the part centres).

| Net | Connected pins |
|---|---|
| **VBAT** | BT1 (+) → J1 pin 1 → M1 `B+` |
| **BAT−** | BT1 (−) → J1 pin 2 → M1 `B−` (goes through the DW01/FS8205 protection inside M1; *not* the GND net) |
| **VSW** (switched battery) | M1 `OUT+` → SW2 common; SW2 ON contact → D2 anode |
| **5V** | D2 cathode (band), U1 pin `5V` (on-board ME6211 LDO → 3V3); USB programming puts 5 V here too, D2 blocks back-feed |
| **3V3** | U1 pin `3V3`, C4 (+), R2 pin 1, R3 pin 1 |
| **GND** | M1 `OUT−`, U1 pin `G`, C4 (−), C3 pin 2, SW1 pins 3-4, J2 pin 6 → M2 `GND`, J2 pin 4 → M2 `L/R` (left channel) |
| **BTN** | R2 pin 2, C3 pin 1, SW1 pins 1-2, U1 pin `D1` (GPIO5), JP1 pin 1 |
| **RST** | JP1 pin 2, U1 pin `RST` |
| **MICPWR** | U1 pin `D2` (GPIO4, output) → J2 pin 5 → M2 `VDD` (power gated, 1.4 mA when on) |
| **I2S_SCK** | U1 pin `D7` (GPIO13, I2S bit clock out) → J2 pin 1 → M2 `SCK` |
| **I2S_WS** | U1 pin `D5` (GPIO14, I2S word select out) → J2 pin 2 → M2 `WS` |
| **I2S_SD** | M2 `SD` → J2 pin 3 → U1 pin `D6` (GPIO12, I2S data in) |
| **CHRG** | M1 `CHRG` LED pad (open drain, low = charging) → U1 pin `D0` (GPIO16, input), R3 pin 2 (10 kΩ pull-up to 3V3: GPIO16 has no internal pull-up) |
| **LED** | U1 `D4` (GPIO2) drives the D1 mini's own LED (active-low): on while recording; nothing to wire |
| n.c. | U1 `A0` (unused in rev B.1); SW2 OFF contact; M1 `IN+`/`IN−` (USB-C input, nothing soldered) |

Notes:

- Mind the polarity of C4 and the orientation of D2 (band toward U1).
- JP1 closed = battery mode (a press pulls RST low and wakes U1 from deep
  sleep). JP1 open = `always_on` mode (USB powered, GPIO5 polled).
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
