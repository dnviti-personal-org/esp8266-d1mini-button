# Enclosure (rev. B.1) — 3D-printed box for the ESP8266 D1 mini button

Parametric CAD built with **SolidCraft** (`solidcraft-cli`) from the JSON scripts
in this folder. Dimensions follow `../DESIGN.md` §6 (hardware revision B.1: LiPo
under the board, charging USB-C, INMP441 microphone, big domed key cap) except for the
deviations listed at the end.

## Files

| File | What it is |
|---|---|
| `base.script.json` → `base.solidcraft`, `base.stl`, `base.step` | Box: 2 mm floor + 2 mm walls around the 80 × 56 × 23 mm cavity, 4 PCB standoffs Ø5 × 10, 4 lid screw bosses Ø6, programming micro-USB slot 12 × 7 and charging USB-C slot 10 × 5 (y = 0 wall), slide-switch slot 8 × 3.5 (x = 80 wall), 4 rubber-foot recesses Ø8 × 0.8. Outer 84 × 60 × 25 mm. |
| `lid.script.json` → `lid.solidcraft`, `lid.stl`, `lid.step` | 84 × 60 × 2 mm plate with the Ø52.6 key-cap hole, 4 countersunk Ø2.8 screw holes, 1 mm alignment lips on the short sides (the right one in two segments), INMP441 microphone pocket 11.5 × 15 × 1.2 mm on the underside with a Ø2 sound hole, and the 6 × 3 charge-LED window. Bounding box 84 × 60 × 3.5 mm (2 plate + 1.5 lips). |
| `plunger.script.json` → `plunger.solidcraft`, `plunger.stl`, `plunger.step` | Key cap: Ø52 domed cap, Ø55 retaining flange, Ø8 stem. Bounding box Ø55 × 13.8 mm. Unchanged from rev. A. |
| `assembly.script.json` → `assembly.solidcraft` | All three bodies in place, exploded by the `explode` parameter (14 mm; set 0 for the assembled position). For checking/rendering only. |
| `base-iso.png`, `base-top.png`, `base-bottom.png`, `lid-iso.png`, `lid-bottom.png`, `lid-underside.png` (mic pocket + lips), `plunger-iso.png`, `assembly-iso.png` | Snapshots rendered from the scripts. |

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

Assembled (cavity z, inner floor = 0): lid underside 23, flange 21.5–23,
stem tip 19.2 (actuator top 18.9 + 0.3 play), cap top 33 = 8 mm above the lid
top (25). Travel ≈ 0.5 mm, limited by the switch. The LiPo (8 mm) lies under
the perfboard (underside at 10 mm).

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
2. Screw the perfboard to the 4 standoffs (M2 × 4–5 mm self-tapping, Ø1.6 pilots; the PCB sits at cavity offset (5, 3), 10 mm above the floor).
3. Route the micro-USB and USB-C to their slots in the y = 0 wall and the slide switch to the slot in the x = 80 wall (USB-C centred at cavity x = 57.5); check the tactile switch is centred under cavity (40, 28).
4. Glue (drop of CA or foam tape) the INMP441 breakout into the pocket on the lid underside, port over the Ø2 sound hole, and run its 6 wires (SCK WS SD L/R VDD GND) to J2 on the perfboard.
5. Drop the key cap into the lid **from the inside** (stem down) — the Ø55 flange retains it.
6. Lower the lid onto the base, lips first (they align the lid on the short walls), and fix with 4 × M2.5 × 10 mm self-tapping screws into the Ø2.0 boss pilots (countersunk from the top). The TP4056 charge LEDs are visible through the 6 × 3 window near the USB-C corner.
7. Stick Ø8 rubber feet into the four recesses under the floor.

## Deviations from DESIGN.md §6

- Charge-LED window at cavity (66.5, 11) as DESIGN.md §6 now records (the
  original (59, 16) was inside the key-cap hole); nearest corner 0.65 mm
  outside the flange. `led_x`/`led_y` are parameters.
- **Mic pocket 11.5 mm wide instead of 12**, still centred at cavity (74, 28):
  spans cavity x 68.25–79.75, i.e. 0.75 mm clear of the Ø55 key-cap flange
  (edge at 67.5) and 0.25 mm from the wall; a 12 mm pocket would end exactly
  at the wall. The INMP441 PCB (11 × 14) has 0.25/0.5 mm play. The right-side
  alignment lip is omitted over the pocket's y range (+0.5 mm each side) so
  the board, which protrudes 0.4 mm below the lid, can sit there; the lip is
  two segments (y 8.5–22 and 38–51.5 world).
- **Stem 2.3 mm** as in §6 (tip at 19.2 = 18.9 + 0.3).
- r 1.5 fillet applied to the base bottom edge loop and the lid top edge loop.
- **Alignment lip** (not in DESIGN.md): only along the two short walls, 1 mm
  wide, 1.5 mm tall, 0.2 mm clearance; the Ø55 flange would hit a lip on the
  long walls.
- Slide-switch slot cut starts 0.5 mm inside the wall (no visible effect; avoids
  a sliver boolean with the corner boss).
- Standoff pilot holes are Ø1.6 × 6 mm deep (not through the 10 mm standoff);
  boss pilot holes Ø2.0 × 9 mm deep (10 mm screws through the 2 mm lid).
- Added for comfort/printability: r 2 fillet on the cap's rim/dome edge, r 0.5
  on the flange edge.
- Masses from SolidCraft (PETG 1.29 g/cm³, solid): base ≈ 32.5 g, lid ≈ 6.9 g,
  key cap ≈ 25 g (solid cap; use infill).
