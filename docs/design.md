# FOX carrying case — design notes (V3: compact)

Goal: one rigid, compact, FDM-printable case that carries the **3DMakerpro FOX scanner, its
cable and its charger together**. Printer: Bambu Lab A1 mini (180 × 180 × 180 mm per part).

All geometry comes from [`scripts/build_fox_case.py`](../scripts/build_fox_case.py). Edit a parameter
and re-run it (see [README](../README.md)). Numbers below are current V3 values, taken from
`exports/validation_report.json`.

## V3 at a glance

| | V3 |
|---|---|
| **Outside** | **125.0 × 82.5 × 99.1 mm** (V2 was 130.5 mm tall, so **−31.4 mm**) |
| **FOX cavity** | **115.5 × 73.0 mm, R 5.25**, from the physical fit test |
| **FOX vertical space** | **36.5 mm** clear (floor top → tray underside) |
| **Accessory tray** | **112.5 × 70.0 × 56 mm inside**, **one open bin, no divider** |
| **Lid retention** | 2 printed cantilever snap tabs (lid short ends) that click into grooves in the base |
| **Print** | 2 jobs, no supports: (A) base + tray, (B) lid upside down |
| **Material** | ≈ 249 g solid-equivalent; expect ~195–225 g at 3 walls / 15 % infill |

---

## 1. Evidence (V3 order of authority)

1. **Physical fit test (new, primary).** You printed the V2 ring (cavity 115.5 × 72.5, R 5.25):
   * **Length 115.5:** a little over ~1 mm total free play. Kept.
   * **Width 72.5:** it fits, but grips the FOX lightly. **Widened by 0.5 → 73.0**, so the FOX drops in
     without friction.
   * **Corners R 5.25:** behaved well. Kept.
   * **Cradle height (8 mm band):** looked right. Kept.
2. **Your physical height measurement:** reserve **36.5 mm** for the scanner region. It's used as
   the clear height from the base floor to the tray underside.
3. **Your accessory measurement:** the charger is **~56 wide × 52 tall**. Charger + cable laid out
   in a row need ~56 × 52 × 172 mm. **Your decision:** keep the 125 × 82 footprint, don't reproduce
   the 172 mm row. The tray is one open bin **~56 mm deep** (charger at one end, cable coiled freely
   beside it), with a total height target of ~98–100 mm.
4. The V1/V2 photo analysis, third-party stand STL and spec sheet are superseded wherever they
   conflict with 1–3. The history is in §9.

The FOX stand-in body used for clearance checks (`FOX_PROXY` = 114.4 × 72.4 × 35, R 5) is
*inferred* from the ring test. It isn't a design input.

## 2. What changed from V2 and why

| V2 driver | V3 |
|---|---|
| Whole case on one plate, no supports, at any height cost (roof + nested tray → 130.5 mm) | **Dropped.** Two print jobs are fine; carrying a smaller case every day matters more |
| Tray volume ≥ cardboard box (539 cm³) | **Dropped.** Tray sized for the real charger (52 tall) + free cable coil |
| Cavity 115.5 × 72.5, space 36.5 | **115.5 × 73.0** (fit test), 36.5 kept as a hard requirement |
| Slip-fit lid | **Snap-tab retention** |
| Lid printed mouth-down with a 45° roof | Lid printed **upside down with a flat top**: big first layer, no bridge, lower |
| Floor 2.4, tray floor 2.0, lid top 2.4 | 2.0 / 1.6 / 2.0 (height trimmed where it isn't structural) |

## 3. Height budget: why 99.1 mm is the practical minimum

| Layer (bottom → top) | mm | Why it can't shrink |
|---|---|---|
| Base floor | 2.0 | 10 solid layers; also the case bottom |
| FOX space | 36.5 | your measured requirement |
| Tray floor | 1.6 | 8 layers; the tray is stiffened by its 2 mm walls |
| Tray inner depth | 56.0 | charger 52 + ~4 headroom (you chose 55–58; 56 used) |
| Tray rim → lid ceiling | 1.0 | limits tray lift; keeps the FOX captured |
| Lid top | 2.0 | printed on the bed; 10 layers |
| **Total** | **99.1** | |

The only big lever left is the tray depth: each 1 mm off `ACCESSORY_TRAY_HEIGHT` takes 1 mm off
the case. If your charger can lie on a thinner face, set the parameter and rebuild (at a 34 mm
depth the case would be ~77 mm tall).

## 4. Architecture

```
        ┌───────────────── LID (flat top, 2.4 wall, snap tabs at both ends) ─┐  z 99.1
        │  ┌──────── TRAY: ONE open bin, 112.5 × 70 × 56 inside ────────┐   │  z 96.1 rim
        │  │  charger (52 tall) at one end · cable coiled freely beside   │   │
        │  └──────────────────── tray floor 1.6 ──────────────────────────┘   │  z 38.5
        │ ▐tower▌      FOX lies flat, 36.5 mm space            ▐tower▌      │
        └─▐     ▌▁▁▁▁ 8 mm cradle band (long sides open above) ▁▁▐     ▌─────┘  z 10.0 lid seat
          BASE: 2.0 floor · band · C-shaped end towers · snap grooves         z 0
```

* **Base.** A 2.0 mm floor and a solid 10 mm band (walls 4.75 mm on the long sides). Above it, two
  **C-shaped end towers** (2.0 wall) rise to the tray seat at z = 38.5. **Both long sides are open
  above the 8 mm cradle for 102 mm**, so you pinch the FOX by its long sides to lift it out. The
  tower stubs stop 1.5 mm past the corner arcs, so the lens window faces open air.
  2.5 mm lips on the tower tops locate the tray and carry a 0.6 mm lead-in for the lid.
* **FOX cavity 115.5 × 73.0, R 5.25** with a flat floor. With the stand-in body that leaves
  ~0.55 mm per end and ~0.3 mm per side. The sensor face stays ≥ 0.67 mm clear of the base and
  2.45 mm clear of the lid; only the bezel is below the 8 mm band.
* **Tray.** **One open bin with no divider, rib or molded pocket.** It's 116.5 × 74.0 × 57.6 mm
  outside and **112.5 × 70.0 × 56 mm inside (≈ 440 cm³)**. It sits on the towers, 1.5 mm
  above the FOX, so it also keeps the FOX from lifting out of the cradle.
* **Lid.** A 2.4 mm sleeve with 0.35 mm clearance per side over the towers and a 0.8 mm lead-in at
  the mouth. It rests on the base band shoulder at z = 10. A matching 1 mm chamfer at the joint
  forms a thumb groove.

### 4.1 Lid retention: snap tabs

* **Tabs.** Each short end of the lid has two 1 mm slots, 20 mm long from the mouth up. They free
  a **10 mm wide, 2.4 mm thick cantilever tab**.
* **Bump.** Near the tab's free end, an inward bump stands **0.35 + 0.4 mm** proud of the lid wall.
  The lower ramp is 30° from vertical, for easy closing. The upper ramp is 45°, which is firm to
  open and is also the steepest face the lid can print without support.
* **Groove.** A matching groove, 0.2 mm oversize, is cut into each base tower end wall. The bump
  overlaps the tower face by **0.4 mm**, and that overlap is the click.
* **Beam estimate** (PLA, E ≈ 3.5 GPa, μ ≈ 0.3, order of magnitude only):
  - **closing** ≈ 13 N total;
  - **opening** ≈ 22 N total (≈ 2.3 kgf);
  - tab-root strain 0.36 %, far below PLA's limit.

  The FOX plus base weigh ~0.3 kg, so the base will not fall away when you lift the closed case by
  the lid. You open it deliberately by holding the band and pulling the lid.
* **Tuning:** `LID_RETENTION["engage"]` (0.4). Use 0.3 if it's too stiff, or 0.5 for a firmer hold.

See `renders/07_snap_tab_section.png` (bump seated in the groove) and `07b_lid_underside_tabs.png`.

## 5. Printing

| Job | Part | Orientation | First layer | Supports |
|---|---|---|---|---|
| **A** | Base (125 × 82.5 × 41.0) | upright, floor on bed | 9,990 mm² | none |
| **A** | Tray (116.5 × 74.0 × 57.6) | upright, floor on bed | 8,370 mm² | none |
| **B** | Lid (125 × 82.5 × 89.1) | **upside down**, flat top on bed | 9,750 mm² | none |

* Ready-made plates: `exports/fox_case_v3_plate_A_base_and_tray.3mf` and
  `exports/fox_case_v3_plate_B_lid.3mf`. Individual STLs are already in print orientation.
* **Support-free.** 0 mm² of down-facing surface steeper than 45° on every part, and no bridges.
  The only non-vertical features:
  - the 45° release ramps on the lid bumps and in the base grooves;
  - the ≤45° chamfers;
  - the finger-window bottoms, which curve *away* from the material.
* Suggested settings: 0.2 mm layers, 3 walls, 15 % infill, PLA or PETG, no brim needed.
* **Material:** base 56 + tray 68 + lid 126 = **249 g solid-equivalent**. Expect **~195–225 g**
  sliced. Use the slicer's number for time.

## 6. Validation (`exports/validation_report.json`)

| Check | Result |
|---|---|
| FOX cavity | 115.5 × 73.0 mm, R 5.25 ✓ |
| FOX vertical space | 36.5 mm ✓ (stand-in 35 mm body → 1.5 mm to the tray) |
| FOX stand-in ↔ cradle | 0.3 mm per side, no clash |
| Sensor face ↔ base / lid | 0.67 / 2.45 mm |
| Finger access | 102 mm windows, both long sides, above the 8 mm band |
| Tray is divider-free | **568 / 568** grid rays dropped into the tray reach the floor unobstructed |
| Charger (52 × 56 × 52) + cable-coil stand-in (54 × 64 × 40) | both fit side by side, with no clash with each other, the tray or the lid; charger top 4.85 mm below the lid |
| Lid / base retention | bump seated in groove without clash; 0.4 mm engagement |
| Watertight / islands / self-intersections | 0 non-manifold edges, 1 island, 0 self-intersections on every part (also re-checked on re-imported STLs) |
| Min wall (1st percentile) | base 1.2 (lips), tray 1.6 (floor), lid 2.0 (top) |
| A1 mini per part / plates | all ✓; plate A 125 × 164.5, plate B 125 × 82.5 |
| Assembly clashes | none (resting contacts checked with a 0.02 mm lift) |

**What the checks don't prove.** The charger and cable stand-ins show the space is
*plausible*. They are not a packing proof. The charger's third dimension (depth) wasn't measured
and is assumed to be ≤ 52 mm. The cable's real coiled shape varies.

## 7. Assembly and use

1. Drop the FOX into the base cradle, sensor face toward either long side.
2. Put the tray on the towers (it drops between the lips). Charger at one end, cable coiled freely.
3. Push the lid down until both tabs click. To open, hold the base band and pull the lid up.

## 8. What still needs physical testing

1. **Width 73.0.** Optionally reprint `exports/fox_fit_test_cradle_ring_v3.stl` (~9 g) to confirm
   the FOX now drops in and lifts out freely.
2. **Charger + cable in the 112.5 × 70 × 56 tray.** Especially the charger's depth, and whether the
   cable coils into the ~58 × 70 mm left beside it.
3. **Snap-tab feel.** How firm it is to open and close. Tune `engage`.
4. **FOX top clearance.** 36.5 mm is reserved. If the FOX itself is close to 36.5 mm tall, there's
   no Z margin, so tell me and I'll add some.
5. **Lens window vs the 8 mm band** (it looked fine in the ring test).

## 9. History

| | V1 | V2 | **V3** |
|---|---|---|---|
| Outside (mm) | 125 × 82 × 113.3 | 125 × 82 × 130.5 | **125 × 82.5 × 99.1** |
| FOX cavity | 115.5 × 72.5 | 115.5 × 72.5 | **115.5 × 73.0** (fit-tested) |
| Accessory tray | 539 cm³ (box volume) | 539 cm³ | **one open bin, 56 deep** |
| Print | 2 plates | 1 plate, nested | **2 plates** |
| Retention | slip fit | slip fit | **snap tabs** |

* V1 and V2 are tagged in git (`v1`, `v2`).
* V2's printable files and key renders are kept in `archive/v2/`. That includes the ring used for
  the physical test: `archive/v2/fox_fit_test_cradle_ring.stl`.
* V1/V2 evidence work (perspective-corrected photo measurements, third-party stand analysis:
  113.0 mm between its lips) is in the git history of this file.
