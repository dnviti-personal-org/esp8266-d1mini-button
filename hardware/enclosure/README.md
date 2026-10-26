# Enclosure (rev. B.3) — 3D-printed box for the ESP8266 D1 mini button

Parametric CAD built with **SolidCraft** (`solidcraft-cli`) from the JSON scripts
in this folder. Dimensions follow `../DESIGN.md` §6 (hardware revision B.3: LiPo
under the board, charging USB-C, INMP441 microphone, big domed key cap,
perfboard at cavity offset (5, 1.5) with notched corners) except for the
deviations listed at the end.

## Files

| File | What it is |
|---|---|
| `base.script.json` → `base.solidcraft`, `base.stl`, `base.step` | Box: 2 mm floor + 2 mm walls around the 80 × 56 × 24 mm cavity, 4 PCB standoffs Ø5 × 11 at cavity (39, 4.5) (39, 48.5) (11, 41.5) (69, 22.5), 4 lid screw bosses Ø6, programming micro-USB slot 14 × 9 and charging USB-C slot 12 × 8 (y = 0 wall), slide-switch slot 8 × 3.5 at cavity y = 37.5, z = 16.8 (x = 80 wall), 4 rubber-foot recesses Ø8 × 0.8. Outer 84 × 60 × 26 mm. |
| `lid.script.json` → `lid.solidcraft`, `lid.stl`, `lid.step` | 84 × 60 × 2 mm plate with the Ø52.6 key-cap hole, 4 countersunk Ø2.8 screw holes, 1 mm alignment lips on the short sides (the right one in two segments), INMP441 microphone pocket 11.5 × 15 × 1.2 mm on the underside with a Ø2 sound hole, and the 10 × 2.5 charge-LED window at cavity (62, 4.5). Bounding box 84 × 60 × 3.5 mm (2 plate + 1.5 lips). |
| `plunger.script.json` → `plunger.solidcraft`, `plunger.stl`, `plunger.step` | Key cap: Ø52 domed cap, Ø55 retaining flange, Ø8 stem. Bounding box Ø55 × 13.8 mm. Unchanged from rev. A. |
| `assembly.script.json` → `assembly.solidcraft` | The three printed parts, exploded by the `explode` parameter (14 mm; 0 = assembled). |
| `electronics.script.json` → `electronics.solidcraft`, `electronics.step`, `electronics.stl` | Simplified block/cylinder models of every electronic part at the DESIGN.md §5 positions, one body per reference designator (PCB1 with notched corners, PCB1_pins, U1, SW1, M1, J2, J1, SW2, D2, R2, R3, C3, C4, BT1, M2; JP1 is a solder bridge and is not modelled), coloured. Base coordinates (world = cavity + 2). |
| `full-assembly.script.json` → `full-assembly.solidcraft`, `full-assembly.step`, `full-assembly.stl` | Base + electronics + lid + key cap + M2, assembled (`explode` = 0). |
| `full-assembly-exploded.script.json`, `full-assembly-nolid.script.json`, `full-assembly-section.script.json`, `full-assembly-check.script.json` | Variants of the full assembly: `explode` = 14; lid/cap/M2 removed (`solid.remove`, used for the "nolid" renders — a `show_lid` parameter is not possible because a SolidCraft parameter cannot drive visibility); everything in front of world y = 29 removed or cut (1 mm beside the key-cap centre, along X — the revolve seam at y = 30 itself cannot be cut) for the section render; `inspect.interference` on all bodies. |
| `base-iso.png`, `base-top.png`, `base-bottom.png`, `lid-iso.png`, `lid-bottom.png`, `lid-underside.png` (mic pocket + lips), `plunger-iso.png`, `assembly-iso.png` | Snapshots of the printed parts. |
| `full-top-nolid.png`, `full-iso-nolid.png`, `full-iso.png`, `full-exploded.png`, `full-section.png` | Full assembly with electronics: top and iso without lid/cap, closed, exploded, and sectioned at the key-cap centre. |

The base and lid are modelled with the **outer bottom-left corner at the
origin**; cavity coordinates from DESIGN.md are world coordinates + (2, 2, 2).
The lid's z = 0 is its underside (lips go to negative z). The key cap is
centred on the Z axis with z = 0 at the flange underside.

## Rebuilding

From WSL (Windows paths because the CLI is a Windows executable; copy the
scripts to a Windows folder first):

```
SC="/mnt/c/Program Files/SolidCraft/solidcraft-cli.exe"
WD='C:\Users\<you>\esp-button-cad\enclosure'
"$SC" run "$WD\base.script.json"    --out "$WD\base.stl"    --out "$WD\base.step"    --save "$WD\base.solidcraft"
"$SC" run "$WD\lid.script.json"     --out "$WD\lid.stl"     --out "$WD\lid.step"     --save "$WD\lid.solidcraft"
"$SC" run "$WD\plunger.script.json" --out "$WD\plunger.stl" --out "$WD\plunger.step" --save "$WD\plunger.solidcraft"
"$SC" run "$WD\assembly.script.json" --save "$WD\assembly.solidcraft"
"$SC" snapshot "$WD\base.script.json" --out "$WD\base-iso.png" --view iso --width 1000 --height 750 --no-grid
"$SC" snapshot "$WD\lid.script.json"  --out "$WD\lid-underside.png" --camera '{"target":[42,30,0],"yaw":0.6,"pitch":-0.9,"distance":230}' --no-grid
```

`solidcraft-cli eval <script>` prints bounding box, volume and mass of each body.
`assembly.script.json` is the lid script, then the base parameters, the lid
move, the key-cap script, the cap move, and finally the base script
(parameters deduplicated by name); regenerate it the same way after editing a
part script.

### Parameters

`base.script.json` and `lid.script.json` start with `parameters.add` commands
(`wall`, `floor_t`, `cav_x/y/z`, `r_vert`, `r_edge`, `boss_d`, `standoff_d/h`,
`usb_*` (programming), `usbc_*` (charging), `sw_*`, `foot_*`, `lip_*`,
`cap_hole_d`, `cap_x/y`, `mic_x/y`, `mic_hole_d`, `mic_pocket_w/l/d`, `led_*`). All box/cylinder sizes and
positions are expressions of these. Limitation of the SolidCraft script
format: fillet edge picks and `solid.hole` positions are numeric 3D points
(boss/standoff/mic centres on the top faces), so after changing `cav_x`,
`cav_y`, `cav_z`, `wall`, `standoff_h` or `mic_x/y` also update those points.
The key cap is a single revolved profile with numeric coordinates.

## Key cap numbers (z from the flange underside, mm)

| Feature | Ø | z range | Note |
|---|---|---|---|
| Stem | 8 | −2.3 … 0 | tip rests 0.3 mm above the tactile-switch actuator |
| Flange | 55 | 0 … 1.5 | bears on the lid underside, r 0.5 edge fillet |
| Rim | 52 | 1.5 … 7.5 | 2 mm inside the lid + 4 mm proud; 0.3 mm radial clearance in the Ø52.6 hole |
| Dome | 52 → 0 | 7.5 … 11.5 | spherical, R = 86.5 mm, rises 4 mm; r 2 fillet where it meets the rim |

Assembled (cavity z, inner floor = 0): lid underside 24, flange 22.5–24,
stem tip 20.2 (actuator top 19.9 + 0.3 play), cap top 34 = 8 mm above the lid
top (26). Travel ≈ 0.5 mm, limited by the switch. The LiPo (8 mm) lies under
the perfboard (underside at 11 mm, solder pins down to 9.5 mm).

## Printing

Material PETG or PLA, 0.2 mm layers, 3 perimeters, 15–20 % infill.

| Part | Orientation | Supports |
|---|---|---|
| Base | floor on the bed (as modelled) | None needed. The three wall slots are bridged through a 2 mm wall; the 12 mm USB bridge prints fine, enable supports only if your printer bridges badly. |
| Lid | **top face on the bed** (flip 180° in the slicer) | None: the lips point up, the mic pocket is a plain recess, the 90° countersinks become 45° overhangs. |
| Key cap | **dome up**, stem on the bed (as modelled) | Supports under the flange ring (2.3 mm tall, "on build plate only" is enough). Print in a bright colour (red/yellow). |

If the cap binds in the lid hole, sand the rim or raise `cap_hole_d` to 53.
The INMP441 board (11 × 14 × 1.6) sits in the 11.5 × 15 × 1.2 pocket and
protrudes 0.4 mm below the lid; nothing in the base is in the way there.

## Assembly

1. Tape the LiPo (40 × 30 × 8) to the inner floor, centred between the standoffs (cavity (40, 28)), leads toward the charger.
2. Screw the perfboard to the 4 standoffs (M2 × 8 mm self-tapping, Ø1.6 pilots at perfboard holes (34, 3) (34, 47) (6, 40) (64, 21); the board sits at cavity offset (5, 1.5), 11 mm above the floor, with its four corners notched 4 × 4 mm to clear the lid bosses).
3. Route the micro-USB and USB-C to their slots in the y = 0 wall and the slide switch to the slot in the x = 80 wall (micro-USB face ≈ 0.5 mm and USB-C face ≈ 0.75 mm inside the wall); check the tactile switch is centred under cavity (40, 28).
4. Glue (drop of CA or foam tape) the INMP441 breakout into the pocket on the lid underside, port over the Ø2 sound hole, and run its 6 wires (SCK WS SD L/R VDD GND) to J2 on the perfboard.
5. Drop the key cap into the lid **from the inside** (stem down) — the Ø55 flange retains it.
6. Lower the lid onto the base, lips first (they align the lid on the short walls), and fix with 4 × M2.5 × 10 mm self-tapping screws into the Ø2.0 boss pilots (countersunk from the top). The TP4056 charge LEDs are visible through the 6 × 3 window near the USB-C corner.
7. Stick Ø8 rubber feet into the four recesses under the floor.

## Deviations from DESIGN.md §6

- **Charge-LED window centred at cavity (62, 4.5) instead of (57.5, 4.5)**
  (10 × 2.5 as specified): at x = 57.5 its NE corner (52.5, 5.75) is 25.5 mm
  from the key-cap centre, 2 mm under the Ø55 flange; moving it to x = 62
  (nearest corner (57, 5.75), r = 28.0) gives the required 0.5 mm. It is far
  from the short-side lips. The TP4056 LEDs (cavity x ≈ 67–69, y ≈ 7.4–8.6)
  are then seen obliquely through the window's right end; a light pipe or
  moving the LEDs is still advisable. `led_x`/`led_y` are parameters.
- **Mic pocket 11.5 mm wide instead of 12**, still centred at cavity (74, 28):
  spans cavity x 68.25–79.75, i.e. 0.75 mm clear of the Ø55 key-cap flange
  (edge at 67.5) and 0.25 mm from the wall; a 12 mm pocket would end exactly
  at the wall. The INMP441 PCB (11 × 14) has 0.25/0.5 mm play. The right-side
  alignment lip is omitted over the pocket's y range (+0.5 mm each side) so
  the board, which protrudes 0.4 mm below the lid, can sit there; the lip is
  two segments (y 8.5–22 and 38–51.5 world).
- **Stem 2.3 mm** as in §6 (tip at 20.2 = 19.9 + 0.3).
- r 1.5 fillet applied to the base bottom edge loop and the lid top edge loop.
- **Alignment lip** (not in DESIGN.md): only along the two short walls, 1 mm
  wide, 1.5 mm tall, 0.2 mm clearance; the Ø55 flange would hit a lip on the
  long walls.
- Slide-switch slot cut starts 0.5 mm inside the wall (no visible effect; avoids
  a sliver boolean with the corner boss).
- Standoff pilot holes are Ø1.6 × 6 mm deep (not through the 11 mm standoff);
  boss pilot holes Ø2.0 × 9 mm deep (10 mm screws through the 2 mm lid).
- Added for comfort/printability: r 2 fillet on the cap's rim/dome edge, r 0.5
  on the flange edge.
- Masses from SolidCraft (PETG 1.29 g/cm³, solid): base ≈ 34 g, lid ≈ 6.9 g,
  key cap ≈ 25 g (solid cap; use infill).

## Electronics model and clearances (rev. B.3)

`electronics.script.json` places simplified bodies at the §5 perfboard
coordinates. Parameters: `pcb_x0`/`pcb_y0` = 7/3.5 mm (perfboard origin, world
= cavity (5, 1.5) + wall), `pcb_z0` = 13 mm (board underside = floor 2 +
standoff 11), `pcb_t` = 1.6, `pcb_top` = 14.6 mm (cavity 12.6), `lipo_x/y`,
`m2_z`. Every part position is an expression of these. Modelling notes: PCB1
70 × 50 × 1.6 with four 4 × 4 corner notches; `PCB1_pins` = 52 × 36 × 1.5
solder-pin zone under the board (perfboard x 9–61, y 7–43, kept clear of the
standoffs); U1 = two header strips 2.54 × 20.3 × 2.5 + PCB 25.6 × 34.2 × 1.0
(y 0–34.2) + ESP-12 shield 15.5 × 24 × **3.5** + micro-USB 8 × 6 × **3.5**
protruding 1 mm past the board edge (3.5 instead of 3 so the stack top is
board + 7.0 as DESIGN.md states); M1 = two header strips + PCB 26 × 17.5 × 1.0
+ USB-C 9 × 7.3 × 3.3 centred on the module (perfboard x = 52.5, matching the
slot) + two LEDs; J2 = right-angle body 15.24 × 2.54 × 2.5 + bent-pin plate
15.24 × 6 × 0.64 at board + 1.3 toward y = 50; SW2 body 1 mm above the board
with the 2 × 2 × 2 actuator at board + 3.2; JP1 (solder bridge) omitted.

Checked with `solidcraft-cli eval full-assembly.script.json` (body bounding
boxes) and `solidcraft-cli run full-assembly-check.script.json --results`
(`inspect.interference`, 18 bodies: **no interference**; the Lid/Base pair is
reported "unchecked" because they only touch).

Reference heights (cavity z, inner floor = 0): lid underside **24.0**; key-cap
flange underside **22.5** at rest, **22.0** pressed (0.5 mm travel); the
flange covers the Ø55 circle around cavity (40, 28). Board top 12.6.

| Part | Top z (cavity) | Under the flange? | Reference | Clearance at rest / pressed | Status |
|---|---|---|---|---|---|
| U1 D1 mini stack (shield, micro-USB) | 19.6 | yes | flange 22.5 | 2.9 / 2.4 | OK |
| SW1 actuator (centre = cavity (40, 28)) | 19.9 | yes (centre) | stem tip 20.2 | 0.3 play by design; 0.5 travel | OK |
| M1 TP4056 USB-C top | 19.4 | yes (corner r = 23.8) | flange 22.5 | 3.1 / 2.6 | OK |
| M1 PCB / LEDs | 16.1 / 16.9 | partly | flange 22.5 | 6.4 / 5.6 | OK |
| J2 right-angle header | 15.1 | yes | flange 22.5 | 7.4 / 6.9 | OK |
| J1 JST-PH | 18.6 | no (nearest r = 28.0) | lid 24.0 / M2 underside 23.6 | 5.4 / 5.0 | OK |
| SW2 body | 18.6 | no | lid 24.0 / M2 underside 23.6 | 5.4 / 5.0 | OK |
| SW2 actuator (2 × 2 × 2, z 15.8–17.8, y 36.5–38.5) | 17.8 | no | wall slot z 15.05–18.55, y 33.5–41.5 | 0.75 above and below, 3.0 each side; tip 4.2 mm inside the wall (reachable with a fingernail or pen) | OK |
| D2, R2, R3 (Ø2.5 axial) | 15.85 | yes | flange 22.5 | 6.65 / 6.15 | OK |
| C3 | 17.6 | yes | flange 22.5 | 4.9 / 4.4 | OK |
| C4 (Ø5 along X) | 18.1 | yes | flange 22.5 | 4.4 / 3.9 | OK |
| BT1 LiPo (top 8.0) | 8.0 | – | solder-pin zone bottom 9.5 | 1.5; ≥ 4 mm from every standoff in XY | OK |
| M2 INMP441 (z 23.6–25.2, x 68.5–79.5) | – | lateral | flange edge x 67.5 (z 22.5–24) | 1.0 lateral; 1.0 to each lip segment | tight but OK |
| PCB1 corners (notched 4 × 4) | 12.6 | – | Ø6 lid bosses | no overlap; the boss circle ends 0.26 mm inside the notch | OK |
| PCB1 vs standoffs / pin zone | – | – | Ø5 standoffs at cavity (39, 4.5) (39, 48.5) (11, 41.5) (69, 22.5) | holes free of modules; pin zone ≥ 0.5 mm from the standoffs | OK |
| Micro-USB receptacle (U1) | z 16.1–19.6, x 16.8–24.8 | – | slot z 13.2–22.2, x 13.8–27.8 | 3.0 each side in x, 2.9 / 2.6 in z; face 0.5 mm inside the wall | OK |
| USB-C receptacle (M1) | z 16.1–19.4, x 53–62 | – | slot z 13.7–21.7, x 51.5–63.5 | 1.5 each side in x, 2.4 / 2.3 in z; face 0.75 mm inside the wall | OK |
| LED window (cavity x 57–67, y 3.25–5.75) | – | – | flange r 27.5 | 0.5 (corner (57, 5.75) at r = 28.0) | OK (minimum) |

Nothing is below 1 mm except the designed 0.3 mm switch play and the 0.5 mm
flange/LED-window margin; `inspect.interference` finds no overlap anywhere.
