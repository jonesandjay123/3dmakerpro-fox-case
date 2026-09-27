# FOX scanner case — design notes (V4: scanner-only, low profile)

**Scope:** a compact, protective hard case for the **3DMakerpro FOX scanner body only**. The cable
and charger are out of scope for now; they stay in the original black accessory box.

All geometry comes from [`scripts/build_fox_case.py`](../scripts/build_fox_case.py). Edit a parameter
and re-run it (see [README](../README.md)). Every number below is from `exports/validation_report.json`.

## V4 at a glance

| | V4 |
|---|---|
| **Outside** | **125.0 × 82.5 × 40.9 mm** (V3 full kit was 99.1 mm tall, so **−58.2 mm / −59 %**) |
| **FOX cavity** | **115.5 × 73.0 mm, R 5.25** (fit-test derived; measured on the model) |
| **FOX vertical space** | **36.5 mm**, floor → lid ceiling. With a 35 mm stand-in body that leaves **1.5 mm** above the FOX; the lid never touches it |
| **Cradle** | 8 mm capture height; **102 mm finger windows on both long sides** |
| **Lid retention** | 2 printed cantilever snap tabs (lid short ends) that click into grooves in the base end towers |
| **Print** | **one A1 mini plate, one job, no supports**: base upright + lid upside down, side by side |
| **Material** | 111 g solid-equivalent; expect **~89–102 g** at 3 walls / 15 % infill |

```
     ┌────────────────── LID: 2.4 wall, 2.4 flat top, snap tab at each end ──┐   z 40.9
     │                        1.5 mm clear above FOX                          │   z 38.5 ceiling
     │ ▐tower▌            FOX lies flat (36.5 mm space)            ▐tower▌    │
     └─▐     ▌▁▁▁▁▁ 8 mm cradle band; long sides open above ▁▁▁▁▁▐     ▌───┘   z 10.0 lid seat
       BASE: 2.0 floor · band · low C-shaped end towers (to z 22) with snap grooves    z 0
```

---

## 1. Evidence

* **Settled by the physical fit test** (printed ring, 115.5 × 72.5, R 5.25):
  - length fine with ~1 mm play;
  - width lightly gripped, so V3 widened it to **73.0**;
  - corners and the 8 mm cradle looked good.
* **FOX space 36.5 mm** is your measured requirement.
* V4 does **not** re-estimate the FOX from photos, the spec sheet or the third-party stand. That
  history is in `archive/` and the git tags.
* The FOX stand-in used for clearance checks (`FOX_PROXY` 114.4 × 72.4 × 35, R 5) is inferred. It
  isn't a design input.
* **Not yet physically verified:** the 73.0 mm width. The printed ring was 72.5.
  `exports/fox_fit_test_cradle_ring_v3.stl` is still exported for that check.

## 2. What changed from V3

| V3 (full kit) | V4 (scanner only) |
|---|---|
| Accessory tray 112.5 × 70 × 56 above the FOX | **removed**; accessory parameters no longer exist in the build |
| Towers 36.5 mm tall as a tray seat, plus tray lips | **towers only 20 mm** (lid guide + snap grooves), no lips, 0.8 mm lead-in |
| Lid ceiling above the tray (99.1 mm total) | **lid ceiling sits directly above the FOX space: 40.9 mm total** |
| 2 print jobs | **1 job, 1 plate** |
| Grey renders | teal lid / charcoal base, so V4 renders are easy to tell apart |

Kept as-is:
- cavity and corner logic;
- 8 mm cradle band and 102 mm finger windows;
- 1.5 mm tower stubs and R3 window corners, which keep the lens window clear;
- the snap-tab latch;
- the validation and export pipeline.

## 3. Height budget: 40.9 mm

| Layer | mm | |
|---|---|---|
| Base floor | 2.0 | 10 layers; the case bottom |
| FOX space (floor → lid ceiling) | 36.5 | measured requirement; includes the clearance above the FOX |
| Lid top | 2.4 | printed on the bed. At 2.4 mm a ~5 kg press on the middle of the lid is estimated to deflect ~0.5 mm (2.0 mm would be ~0.8 mm), well inside the 1.5 mm gap |
| **Total** | **40.9** | |

Nothing else stacks: the lid seats on the base band shoulder at z = 10, and its sleeve overlaps
the towers. Going lower means eating into the measured 36.5 mm, which V4 deliberately doesn't do.

## 4. Parts

### Base (125.0 × 82.5 × 22.0, printed upright)
* A **2.0 mm floor** with a **solid 10 mm band**, which has 4.75 mm walls on the long sides.
* **Cavity 115.5 × 73.0, R 5.25** with a flat floor.
* **Long sides open above the 8 mm cradle for 102 mm**, so you pinch the FOX by its long sides
  and lift it out (`renders/03_finger_access_lift_out.png`).
* The **C-shaped end towers** (2.0 mm wall) rise to z = 22 and guide the lid. Each carries a
  **detent groove** on its end face and a 0.8 mm lead-in chamfer on top. The towers stop 1.5 mm
  past the corner arcs, so the **lens window faces open air**. The sensor face stays ≥ 0.67 mm
  from the base; only the bezel sits below the 8 mm band.

### Lid (125.0 × 82.5 × 30.9, printed upside down)
* A **2.4 mm sleeve with a 2.4 mm flat top**. It has 0.35 mm clearance per side over the towers
  and a 0.8 mm lead-in at the mouth, and it seats on the base band at z = 10. Matching 1 mm
  chamfers at the joint form a thumb groove.
* Inside there is **1.5 mm above the FOX** (35 mm stand-in) and **2.45 mm in front of the sensor
  face**. The lid doesn't touch the FOX, even with the FOX lifted 0.5 mm.

### Retention: snap tabs
* **Tabs.** Two 1 mm slots, 20 mm long, at each lid end free a **10 mm × 2.4 mm cantilever tab**.
* **Bump.** Each tab has an inward bump that overlaps the tower face by
  **`RETENTION_ENGAGEMENT` = 0.4 mm**. Its lower ramp is 30° from vertical, for an easy click shut.
  Its upper ramp is 45°: firm to open, and the steepest face that prints without support.
* **Groove.** The matching groove in the base is 0.2 mm oversize. With the lid closed the bump
  sits in it without clashing.
* **Estimate** (PLA, beam theory, order of magnitude):
  - **closing ≈ 13 N**;
  - **opening ≈ 22 N** (≈ 2.3 kgf);
  - tab strain 0.36 %.
  - The FOX plus base weigh ~0.25 kg, so lifting the closed case by the lid won't drop the base.
* **Tuning:** use 0.3 for a lighter feel (~17 N to open), or 0.5 for a firmer hold (~28 N).
* The latch adds no external structure: the tabs are flush with the lid wall.

## 5. Printing: one A1 mini plate

* `exports/fox_case_v4_A1mini_one_plate.3mf`: **base upright** and **lid upside down**, side by
  side. It uses **125 × 170 mm** of the 180 × 180 bed, with a 5 mm gap between parts and ≥ 5 mm
  margins. Open it as-is; **no auto-arrange needed**.
* **Support-free.** 0 mm² of down-facing surface steeper than 45° on both parts, and no bridges.
* **Big first layers.** The base puts 9,990 mm² on the bed and the lid 9,750 mm², so no brim is needed.
* Settings: 0.2 mm layers, 3 walls, 15 % infill, PLA or PETG.
* Filament: base 48 g + lid 63 g = **111 g solid-equivalent**, so expect **~89–102 g**.
* Individual STLs (`fox_case_v4_base.stl`, `fox_case_v4_lid.stl`) are exported in the same
  orientations.

## 6. Validation

| Check | Result |
|---|---|
| Cavity (measured by ray cast on the model) | **115.5 × 73.0 mm** ✓ |
| Floor → lid ceiling (measured) | **36.5 mm** ✓ |
| FOX top clearance (35 mm stand-in) | **1.5 mm**; `lid_presses_on_fox: false` |
| FOX stand-in ↔ cradle wall | 0.3 mm per side (0.55 per end) |
| Sensor face ↔ base / lid | 0.67 / 2.45 mm |
| Finger access | 102 mm on both long sides, above the 8 mm band |
| Lid / base fit | 0.35 mm per side on the towers; lid seats on the band; no clash |
| Positive retention | bump seated in groove, 0.4 mm engagement |
| Watertight / non-manifold / self-intersections / islands | 0 / 0 / 0 / 1 on every part (also on re-imported STLs) |
| Min wall (1st percentile) | base 2.0, lid 2.4 |
| Supports | none (both parts `support_free: true`) |
| Per-part A1 mini fit | ✓ base 125 × 82.5 × 22.0, lid 125 × 82.5 × 30.9 |
| One-plate fit | ✓ bbox 27.5–152.5 × 5–175 mm, 5 mm between parts, no clash |
| Outside | **125.0 × 82.5 × 40.9 mm** |
| Material | 111 g solid-equivalent, ~89–102 g sliced |

## 7. Assembly and use

1. Drop the FOX in, sensor face toward either long side.
2. Push the lid straight down until both tabs click.
3. To open, hold the base band and pull the lid up.
4. Lift the FOX out by pinching its long sides through the windows.

## 8. Remaining physical tests

1. **Width 73.0.** Print `fox_fit_test_cradle_ring_v3.stl` (~9 g) or the full plate, and confirm
   the FOX drops in and lifts out without friction.
2. **Top clearance.** 36.5 mm is reserved. If the FOX itself is close to 36.5 mm tall, there's
   almost no Z margin; tell me and I'll add some (+1 mm on the case).
3. **Snap feel.** Tune `RETENTION_ENGAGEMENT` (0.3–0.5) to taste.
4. **Lens window vs the 8 mm band** (fine in the ring test).

## 9. History

| | V1 | V2 | V3 | **V4** |
|---|---|---|---|---|
| Scope | FOX + accessories | same | same | **FOX only** |
| Outside (mm) | 125 × 82 × 113.3 | 125 × 82 × 130.5 | 125 × 82.5 × 99.1 | **125 × 82.5 × 40.9** |
| Cavity | 115.5 × 72.5 | 115.5 × 72.5 | 115.5 × 73.0 | **115.5 × 73.0** |
| Print | 2 plates | 1 plate (nested) | 2 plates | **1 plate** |
| Retention | slip | slip | snap tabs | **snap tabs** |

* Git tags `v1`, `v2`, `v3`.
* `archive/v2/` and `archive/v3/` hold the printable files, key renders, and V3's design notes
  and build script.
