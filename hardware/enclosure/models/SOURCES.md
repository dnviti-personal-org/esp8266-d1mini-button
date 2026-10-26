# Sources of the STEP models used by `electronics.script.json`

All files are unmodified copies; the scripts reference them by file name
(staged on the Windows side under `C:\Users\daniele\esp-button-cad\models\`
when rebuilding — adjust the `M` path at the top of the generator or the
`file.insert_step` paths if you move them).

## KiCad packages3D (licence: CC-BY-SA 4.0 with the KiCad library exception)

Source: https://gitlab.com/kicad/libraries/kicad-packages3D (release 8/9), file
`<Library>.3dshapes/<name>.step`.

| File | KiCad library | Used as |
|---|---|---|
| `USB_Micro-B_Molex_47346-0001.step` | Connector_USB.3dshapes | U1 micro-USB receptacle (placed on the shield side of the D1 mini) |
| `PinHeader_1x08_P2.54mm_Vertical.step` | Connector_PinHeader_2.54mm.3dshapes | U1 pin headers (×2, flipped: long pins down) |
| `PinHeader_1x06_P2.54mm_Horizontal.step` | Connector_PinHeader_2.54mm.3dshapes | J2 right-angle mic header (pins trimmed to 6 mm) |
| `SW_PUSH-12mm_Wuerth-430476085716.step` | Button_Switch_THT.3dshapes | SW1 tactile 12 × 12 — this is the 8.5 mm-actuator variant; the BOM part is an Omron B3F-4000 (7.3 mm), so `electronics.script.json` cuts the actuator to 7.3 mm. The real Würth part would need 1.2 mm more key-cap stem. |
| `SW_Slide_SPDT_Straight_CK_OS102011MS2Q.step` | Button_Switch_THT.3dshapes | SW2 slide switch (laid on its side) |
| `JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal.step` | Connector_JST.3dshapes | J1 battery connector |
| `USB_C_Receptacle_GCT_USB4125-xx-x_6P_TopMnt_Horizontal.step` | Connector_USB.3dshapes | M1 USB-C receptacle |
| `SOIC-8_3.9x4.9mm_P1.27mm.step` | Package_SO.3dshapes | M1 TP4056 |
| `SOT-23-6.step` | Package_TO_SOT_SMD.3dshapes | M1 DW01A |
| `TSSOP-8_4.4x3mm_P0.65mm.step` | Package_SO.3dshapes | M1 FS8205A |
| `LED_0603_1608Metric.step` | LED_SMD.3dshapes | M1 charge / full LEDs |
| `R_0603_1608Metric.step`, `C_0603_1608Metric.step`, `C_0805_2012Metric.step` | Resistor_SMD / Capacitor_SMD.3dshapes | M1 passives, M2 decoupling cap |
| `D_DO-41_SOD81_P10.16mm_Horizontal.step` | Diode_THT.3dshapes | D2 |
| `R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal.step` | Resistor_THT.3dshapes | R2, R3 |
| `C_Disc_D5.0mm_W2.5mm_P5.00mm.step` | Capacitor_THT.3dshapes | C3 |
| `CP_Radial_D5.0mm_P2.00mm.step` | Capacitor_THT.3dshapes | C4 (laid flat; the KiCad body is 5 mm long, the real part is 11 mm) |

## Technariumas / shd18badge (licence: Apache-2.0)

| File | Source | Used as |
|---|---|---|
| `WEMOS_D1_mini_Technariumas.step` | https://github.com/Technariumas/shd18badge (hardware/3d) | U1 D1 mini board, ESP-12 shield, CH340, reset button, passives. Its micro-USB body sits on the underside and was removed (`solid.remove "USB Micro"`); the Molex micro-B above replaces it on the shield side. |

Not used (staged only): `WEMOS_D1_mini_light.step` (KiCad, simpler, USB also on
the underside), `ESP-12E.step`, `PinSocket_1x08_P2.54mm_Vertical.step`,
`D_SMA.step`, `LED_0805_2012Metric.step`.

Built in the script (no STEP available): PCB1 perfboard, M1 TP4056 module PCB,
pads, pins and spacers, M2 INMP441 breakout (PCB, capsule, pads), BT1 LiPo
pouch, kapton band, leads and PHR-2 plug, JP1 solder bridge, C4 lead stubs.

Rev. C notes: C3 (2.54 mm disc) and C4 (Ø5 × 11 electrolytic) are built in
`electronics.script.json` instead of using `C_Disc_D5.0mm_W2.5mm_P5.00mm.step`
and `CP_Radial_D5.0mm_P2.00mm.step` (wrong pitch / 5 mm body); those two files
are kept here but no longer referenced. `SW_Slide_SPDT_Straight_CK_OS102011MS2Q.step`
stands in for the SS12D00G4 of the BOM (no KiCad model): its straight pins are
removed and bent ones are built into A15–A17; its body is 4.7 mm tall where the
SS12D00 is 3.7.
