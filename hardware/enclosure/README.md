# Enclosure — 3D-printed box for the ESP8266 D1 mini button

Parametric CAD built with **SolidCraft** (`solidcraft-cli`) from the JSON scripts
in this folder. Dimensions follow `../DESIGN.md` §5 (big domed key cap for an
elderly user) except for the deviations listed at the end.

## Files

| File | What it is |
|---|---|
| `base.script.json` → `base.solidcraft`, `base.stl`, `base.step` | Box: 2 mm floor + 2 mm walls around the 80 × 56 × 17 mm cavity, 4 PCB standoffs, 4 lid screw bosses, USB and slide-switch slots, 4 rubber-foot recesses. Outer 84 × 60 × 19 mm. |
| `lid.script.json` → `lid.solidcraft`, `lid.stl`, `lid.step` | 84 × 60 × 2 mm plate with the Ø52.6 key-cap hole, 4 countersunk Ø2.8 screw holes and two 1 mm alignment lips (1.5 mm tall) on the short sides. Bounding box 84 × 60 × 3.5 mm. |
| `plunger.script.json` → `plunger.solidcraft`, `plunger.stl`, `plunger.step` | Key cap: Ø52 domed cap, Ø55 retaining flange, Ø8 stem. Bounding box Ø55 × 13.8 mm. |
| `assembly.script.json` → `assembly.solidcraft` | All three bodies in place, exploded by the `explode` parameter (14 mm; set to 0 for the assembled position). For checking/rendering only. |
| `base-iso.png`, `base-top.png`, `base-bottom.png`, `lid-iso.png`, `lid-bottom.png`, `plunger-iso.png`, `assembly-iso.png` | Snapshots rendered from the scripts. |

All scripts place the base/lid with the **outer bottom-left corner at the
origin**; cavity coordinates from DESIGN.md are world coordinates + (2, 2, 2).
The key cap is modelled centred on the Z axis with z = 0 at the flange underside.

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
```

`solidcraft-cli eval <script>` prints bounding box, volume and mass of each body.

### Parameters

`base.script.json` and `lid.script.json` start with `parameters.add` commands
(`wall`, `floor_t`, `cav_x`, `cav_y`, `cav_z`, `r_vert`, `r_edge`, `boss_d`,
`standoff_d/h`, `usb_*`, `sw_*`, `foot_*`, `lip_*`, `cap_hole_d`, `cap_x`,
`cap_y`). All box/cylinder sizes and positions are expressions of these.
Limitations of the SolidCraft script format: fillet edge picks and hole
positions are numeric 3D points, so after changing the outer size (`cav_x`,
`cav_y`, `wall`, `cav_z`) you must also update the `edges:` points of the two
fillets and the `position:` of the `solid.hole` commands (they are the
boss/standoff centres on the top faces). The key cap is a single revolved
profile with numeric coordinates (see "Key cap numbers").

## Key cap numbers (z from the flange underside, mm)

| Feature | Ø | z range | Note |
|---|---|---|---|
| Stem | 8 | −2.3 … 0 | tip rests 0.3 mm above the tactile-switch actuator |
| Flange | 55 | 0 … 1.5 | bears on the lid underside, r 0.5 edge fillet |
| Rim | 52 | 1.5 … 7.5 | 2 mm inside the lid + 4 mm proud; 0.3 mm radial clearance in the Ø52.6 hole |
| Dome | 52 → 0 | 7.5 … 11.5 | spherical, R = 86.5 mm, rises 4 mm; r 2 fillet where it meets the rim |

Assembled (cavity z, inner floor = 0): lid underside 17, flange 15.5–17,
stem tip 13.2 (actuator top 12.9 + 0.3 play), cap top 27 = 8 mm above the lid
top (19). Travel ≈ 0.5 mm, limited by the switch.

## Printing

Material PETG or PLA, 0.2 mm layers, 3 perimeters, 15–20 % infill.

| Part | Orientation | Supports |
|---|---|---|
| Base | floor on the bed (as modelled) | None needed. The USB (12 × 7) and switch (8 × 3.5) slots are bridged through a 2 mm wall; the 12 mm USB bridge prints fine, enable supports only if your printer bridges badly. |
| Lid | **top face on the bed** (flip 180° in the slicer) | None: the lips point up, the 90° countersinks become 45° overhangs. |
| Key cap | **dome up**, stem on the bed (as modelled) | Supports under the flange ring (2.3 mm tall, "on build plate only" is enough). Print in a bright colour (red/yellow). |

Lid and cap: the cap must slide freely in the lid hole — if it binds, sand the
rim or raise `cap_hole_d` to 53.

## Assembly

1. Screw the perfboard to the 4 standoffs (M2 × 4–5 mm self-tapping, Ø1.6 pilots; the PCB sits at cavity offset (5, 3)).
2. Route the micro-USB to the slot in the y = 0 wall and the slide switch to the slot in the x = 80 wall; check the switch actuator is centred under cavity (40, 28).
3. Drop the key cap into the lid **from the inside** (stem down) — the Ø55 flange retains it.
4. Lower the lid onto the base, lips first (they align the lid on the short walls), and fix with 4 × M2.5 × 10 mm self-tapping screws into the Ø2.0 boss pilots (countersunk from the top).
5. Stick Ø8 rubber feet into the four recesses under the floor.

## Deviations from DESIGN.md §5

- **Stem length 2.3 mm instead of "≈ 3.8 mm below the flange"**: 3.8 mm is the
  distance from the *lid underside* to the actuator (17 − 12.9 − 0.3); the
  flange is 1.5 mm thick, so the stem below the flange is 3.8 − 1.5 = 2.3 mm.
  A 3.8 mm stem would hold the switch 1.2 mm pressed at rest.
- **Top/bottom outer edge fillet r 1.5** is applied to the base bottom edge loop
  and the lid top edge loop (the outer top/bottom of the assembled box), not to
  the rim where lid and base meet.
- **Alignment lip** (not in DESIGN.md, from the task notes): only along the two
  short walls (x = 0 and x = 80), 1 mm wide, 1.5 mm tall, 0.2 mm clearance to
  the wall, ending 0.5 mm clear of the bosses. The long sides have none because
  the Ø55 flange (y 2.5–57.5) would collide with a lip there.
- **Slide-switch slot** cut starts 0.5 mm inside the wall (cavity x 79.5) — no
  visible effect, avoids a sliver boolean with the corner boss.
- Standoff pilot holes are 5 mm deep (4 mm standoff + 1 mm into the floor),
  boss pilot holes 9 mm deep (for 10 mm screws through the 2 mm lid).
- Added for comfort/printability: r 2 fillet on the cap's rim/dome edge, r 0.5
  on the flange edge; the key-cap hole, flange and dome were otherwise kept as
  specified. Boss pilot holes and PCB pilot holes as specified (Ø2.0 / Ø1.6).
- Masses from SolidCraft (PETG 1.29 g/cm³, solid): base ≈ 27 g, lid ≈ 7 g, key
  cap ≈ 25 g (solid cap; use infill).
