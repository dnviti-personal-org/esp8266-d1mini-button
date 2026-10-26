# Bill of materials — ESP8266 D1 mini MQTT battery button

Expanded from [DESIGN.md](DESIGN.md) section 3. Reference designators match
`schematic/schematic.svg` and `schematic/perfboard-layout.svg`. Manufacturer
part numbers are examples: any part with the same package and ratings works.

## Parts

| Ref | Qty | Part | Value / rating | Package / notes | Example MPN |
|---|---|---|---|---|---|
| U1 | 1 | Wemos / LOLIN D1 mini (ESP8266, CH340) | — | 34.2 × 25.6 mm, 2 × 8 pins 2.54 mm, rows 22.86 mm apart; soldered with its male pins (no female headers) | LOLIN D1 mini V4.0.0 (or V3 / clone) |
| PCB1 | 1 | Perfboard, single side | — | 70 × 50 mm, 2.54 mm pitch, 24 × 18 holes, FR-4 1.6 mm | generic 5 × 7 cm FR-4 protoboard |
| BT1 | 1 | CR2032 coin-cell holder, THT | 20 mm cell | ≈ 24 × 24 mm footprint, 6 mm tall with cell, 2 pins, cell loads from the top | Keystone 3034 (alt. MPD BH800S, generic 2-pin) |
| — | 1 | CR2032 lithium cell | 3.0 V, ≈ 220 mAh | — | Panasonic CR2032, Energizer CR2032 |
| SW1 | 1 | Tactile switch 12 × 12 mm, THT | 7.3 mm actuator, **low force 100 gf** | standard 12 × 12 footprint, 4 pins | Omron B3F-4000 (alt. B3F-4055 160 gf) |
| SW2 | 1 | SPDT slide switch (power) | 50 V 0.5 A | 8.6 × 3.6 mm body, 3 pins 3.0 mm pitch, 2 mm actuator | SS12D00 (G3/G4/G5 lever length) |
| C1, C2 | 2 | Supercapacitor, EDLC, cylindrical radial, low ESR | 2.7 V 3.3 F | Ø8 × 20 mm, pitch 3.5 mm, mounted lying flat along X | Eaton HV0810-2R7335-R, KEMET FC0H335ZFTBR24, generic 2.7 V 3.3 F |
| C3 | 1 | Ceramic capacitor X7R | 100 nF 50 V | 2.54 mm pitch | Vishay K104K15X7RF53H5, generic |
| C4 | 1 | Electrolytic capacitor, low ESR | 100 µF 6.3 V (10 V ok) | Ø5 × 11 mm radial, lying flat along X | Panasonic EEUFR1A101 (10 V), Nichicon UPW |
| R1 | 1 | Resistor, axial | 68 Ω 1/4 W 5 % | axial, 10 mm along X | Yageo CFR-25JB-52-68R |
| R2 | 1 | Resistor, axial | 10 kΩ 1/4 W 5 % | axial, 10 mm along X | Yageo CFR-25JB-52-10K |
| JP1 | 1 | 2-pin header 2.54 mm + shunt (or a solder bridge) | — | 2 pins along X | generic 1 × 2 male header + 2.54 mm jumper cap |
| — | 4 | Screw M2 × 8 mm self-tapping | — | PCB to base standoffs | generic |
| — | 4 | Screw M2.5 × 10 mm self-tapping | — | lid to base bosses | generic |
| — | 4 | Adhesive rubber foot Ø8 mm | — | under the base, so the box does not slide when pressed | 3M SJ5302 / generic bumpon |
| — | — | Hook-up wire, solder | — | 0.5 mm² or wire-wrap wire for the perfboard links | — |

Not used by default: 2 × 8-pin female headers for U1 (would add 8.5 mm of
height and no longer fit the enclosure).

## Wiring / netlist

Perfboard top view, origin at the bottom-left corner (see
`schematic/perfboard-layout.svg` for the part centres).

| Net | Connected pins |
|---|---|
| **VBAT** | BT1 (+), SW2 pin 1 (common) |
| **VBAT_SW** (switched cell) | SW2 pin 2 (ON position), R1 pin 1 |
| **VCAP / 3V3** | R1 pin 2, C1 (+), C4 (+), U1 pin `3V3`, R2 pin 1 |
| **CMID** (series mid-point) | C1 (−), C2 (+) |
| **GND** | BT1 (−), C2 (−), C4 (−), C3 pin 2, SW1 pins 3-4, U1 pin `G` |
| **BTN** | R2 pin 2, C3 pin 1, SW1 pins 1-2, U1 pin `D1` (GPIO5), JP1 pin 1 |
| **RST** | JP1 pin 2, U1 pin `RST` |
| n.c. | U1 pin `A0` — **must stay unconnected** (`ADC_MODE(ADC_VCC)` reads VCC internally) |
| on board | U1 `D4` (GPIO2) drives the D1 mini's own LED (active-low): one blink per publish; nothing to wire |

Notes:

- SW2 is SPDT; its third pin (OFF position) is left unconnected.
- Mind the polarity of C1, C2 (EDLC, 2.7 V each: the series pair is rated 5.4 V,
  = 1.65 F) and of C4. The perfboard drawing marks + / − at the lead end.
- U1 is fed **directly on its 3V3 pin**, bypassing the on-board LDO.
- JP1 closed = battery mode (a press pulls RST low and wakes U1 from deep
  sleep). JP1 open = `always_on` mode (USB powered, GPIO5 polled).

## Caveats

- **Battery life ≈ 4–6 weeks of standby**: a D1 mini powered on its 3V3 pin
  still draws ~0.2–0.3 mA (LDO back-feed + CH340 leakage), not the ~20 µA of a
  bare ESP module. For longer life swap U1 for a bare ESP-12F, or the CR2032
  for a CR123A / 2 × AAA.
- **USB only with SW2 OFF**: never connect the micro-USB while SW2 is ON, the
  USB 3.3 V LDO would push current back into the lithium cell. Switch SW2 off
  before programming.
- A0 must stay unconnected (the firmware uses `ADC_MODE(ADC_VCC)`).
- Several presses in quick succession are fine: the cell refills the
  supercapacitor bank through R1 (τ ≈ 112 s); the first insertion current is
  limited to ≤ 45 mA.
