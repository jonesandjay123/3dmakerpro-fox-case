# FOX carrying case — V1 design notes

Goal: one rigid, compact, FDM-printable case that carries the **3DMakerpro FOX scanner and its
charger and cable together**. Printer: Bambu Lab A1 mini (180 × 180 × 180 mm).

All geometry comes from [`scripts/build_fox_case.py`](../scripts/build_fox_case.py). Edit a parameter
and re-run it (see [README](../README.md)). Numbers below are the V1 values.

---

## 1. Evidence

### 1.1 Sources and how much each is trusted

1. **Your ruler photos** (`reference/photos/`) are the primary evidence. The camera was very
   close (EXIF: 24 mm-equivalent, focal length ≈ 2795 px at full resolution, subjects 14–20 cm
   away), so **perspective errors of 5–10 % are real**. The ruler usually sits a few mm to
   15 mm above or below the scanner's outline. I corrected for this; I did not just read the ruler.
2. **Third-party stand STL** (`reference/third_party/obj_2_Supoprto Scanner parte 2.stl`) is
   secondary evidence. The geometry is exact, but what it means depends on how the designer
   built it.
3. **Manufacturer spec**, published on [store.3dmakerpro.com/products/fox](https://store.3dmakerpro.com/products/fox)
   and [filament2print](https://filament2print.com/en/3d-scanners/4463-fox-3dmakerpro-3d-scanner.html):
   "115 × 70 × 35 mm, 210 g". This is a rounded marketing envelope, so it's used as a cross-check only.
4. **Original foam** (photo 172336) shows orientation only. The FOX lies flat, logo up, and the
   black sensor face is on a **long** side.

### 1.2 Evidence table

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| FOX length, apparent | 103.0 mm | 174047, ruler on foam, ≈138 mm from camera | reading ±0.5 |
| FOX length, apparent | 105.2 mm | 174130, ruler on foam, ≈194 mm from camera | reading ±0.5 |
| **FOX length, perspective-solved** | **111 ± 3 mm** | two photos solved for a shared ruler-to-outline offset (Δ ≈ 10.8 mm) | medium |
| Stand clear length between end lips | 113.0 mm (lips 3.0 thick, 20 mm tall) | STL, flattened 47.2° tilt | high (geometry) |
| FOX length, manufacturer | 115 mm | spec sheet | low as a body size |
| FOX width, apparent | 66.4 mm | 174055, ruler lying on the scanner | reading ±0.5 |
| **FOX width, corrected** | **69–71 mm** | same photo, 6–11 mm offset | medium-high |
| FOX width, manufacturer | 70 mm | spec | agrees |
| FOX height, apparent | ≈27 mm | 174231 macro; ruler ~10–15 mm in front of the scanner end, camera ≈48 mm away | reading ±1 |
| **FOX height, corrected** | **32–35 mm** | same photo | low-medium |
| FOX height, manufacturer | 35 mm | spec | agrees with the upper end |
| FOX plan corner radius | ≈3–5 mm (visual) | top-down photos | low, but the cavity accepts 1–10 mm |
| Sensor face | long side, 3 lenses plus LEDs behind a black window | 172336, 174120, MakerWorld screenshot | high |
| Sensor window vertical extent | assumed ≈9–28 mm above the scanner bottom | screenshot proportions | **low** |
| Stand plate, rear tab, boss | plate 119 × 75.6 × 3.0; rear stop tab 43 mm wide; mount boss underneath | STL | high |
| Black accessory box | ≈180 × 68 × 44 mm → **539 cm³** | 174530 / 174542 / 174550 | medium |
| Charger (65 W GaN) | ≈52 × 52 mm footprint; thickness not visible (≤ ~41 mm, the box's inner height) | 172336, scaled from the FOX | low-medium |
| Cable | coiled bundle ≈127 × 48 × 20 mm as packed; can be re-coiled | 172336 | low-medium |

### 1.3 Disagreements, and which source wins

* **Length: photos 111 ± 3, stand ≤ 113, spec 115.** These are *not* averaged. The photos and the
  stand agree with each other. The stand holds the FOX between lips 113 mm apart over the bottom
  20 mm, so a 115 mm body at that height would not fit. The 115 figure is treated as an outer
  envelope. **Design envelope: `FOX_LENGTH = 113`.** This is the physical upper bound from the
  stand. With 1.25 mm clearance the cavity is 115.5 mm, so even a true 115 mm body still goes in.
  If the FOX is really ~111 mm, there will be ~2.25 mm of end play. The fit-test ring shows this
  immediately.
* **Height: photos 32–35 vs spec 35.** **Design value: 35.** If the scanner is actually shorter,
  the only cost is extra vertical play under the tray (a 2–3 mm felt pad fixes that). Being too
  short would be worse: the tray wouldn't seat.
* **Width** agrees across all sources: 70 mm.
* **Accessory volume: your direction overrides my first plan.** I originally sized the tray from
  the charger and cable themselves (≈36 mm deep). You asked for the black box container to set the
  volume, so the tray's usable volume is now derived to be **≥ the box's 539 cm³**
  (`ACCESSORY_VOLUME_TARGET`). The contents don't have to keep the box's shape.

---

## 2. Layout study

| | A. Side-by-side (FOX + accessory bin) | **B. Stacked (chosen)** |
|---|---|---|
| Accessory area needed at a ~37 mm usable height | ≈14,800 mm² → ~125 × 215 mm outer | same volume, stacked above the FOX |
| External size | ≈125 × 215 × 48 mm | **125 × 82 × 113.3 mm** |
| Footprint | ≈26,900 mm² | **10,250 mm² (−62 %)** |
| A1 mini fit | ✗ one-piece base/lid exceeds 180 mm | ✓ largest part is 125 × 82 × 103 mm |
| Material | bigger floor and lid top, similar walls | comparable; ~50 cm³ base + 67 tray + 118 lid |
| Usability | lift lid → everything visible | lift lid → accessories; lift tray → FOX (one extra step) |
| Printability | would need split parts and joints | 3 plain parts, no supports |

**B wins clearly.** It has a footprint barely larger than the FOX, it's the only option that fits
the A1 mini without splitting parts, and the extra lift-out step is minor.

---

## 3. V1 architecture

```
        ┌───────────── LID (slip-over sleeve, 2.4 wall) ─────────────┐   z 113.3
        │  ┌──────── TRAY (accessory bin, 69 mm deep) ────────┐      │   z 109.9 rim
        │  │  charger + coiled cable, loose                  │      │
        │  └──────────── tray floor 2.0 ─────────────────────┘      │   z 38.9 underside
        │  ▐tower▌   FOX lies flat (1.5 mm below tray)    ▐tower▌    │   z 37.4 FOX top
        └──▐     ▌▁▁▁▁▁▁ 8 mm cradle band on long sides ▁▁▐     ▌───┘   z 10.4 lid seat
           BASE: 2.4 floor, 10.4 mm band, C-shaped end towers           z 0
```

* **Base.** A 2.4 mm floor and a solid band 10.4 mm tall. Above the band, two **C-shaped end
  towers** (2.0 wall) rise to the tray seat at z = 38.9. On both **long sides the base is open
  above the 8 mm cradle band for 97 mm**, so you pinch the FOX by its long sides to lift it out.
  The towers only reach 4 mm past the corner arcs, so the sensor window faces open air.
  2.5 mm lips on the tower tops locate the tray.
* **Tray.** An open bin, 116.5 × 73.5 × 71 mm outside and **112.5 × 69.5 × 69 mm inside
  (538.7 cm³ ≥ 538.6 cm³ box target)**. No dividers, so the cable doesn't have to be wound any
  particular way. Its floor underside sits 1.5 mm above the FOX, which also stops the scanner
  lifting out of the cradle.
* **Lid.** A 2.4 mm sleeve that slides over the towers with 0.35 mm clearance per side, with a
  0.8 mm lead-in chamfer. It rests on the base band's shoulder at z = 10.4, and its ceiling sits
  1 mm above the tray rim. Matching 1 mm chamfers at the joint form a V-groove for your thumbnail.
* **No hinges, magnets or latches in V1.** The lid is held by gravity and the sleeve fit (see §7).

### 3.1 Key dimensions (V1)

| Item | Value |
|---|---|
| FOX design envelope | 113 × 70 × 35 mm, plan R 4 |
| **Scanner cavity** | **115.5 × 72.5 mm, R 5.25**, flat floor |
| Scanner clearance | 1.25 mm per side (XY), 1.5 mm above (Z) |
| Cradle capture height (long sides) | 8 mm above the floor; ends are captured full height by the towers |
| Finger windows | 97 mm long, both long sides, R5 bottom corners |
| **Case outside** | **125.0 × 82.0 × 113.3 mm** (outer corner R 10) |
| Tray inside (usable) | 112.5 × 69.5 × 69 mm = 538.7 cm³ |
| Lid ↔ tower clearance | 0.35 mm per side |
| Tray ↔ lip clearance | 0.30 mm per side |
| Walls | lid 2.4, towers 2.0, tray 2.0, base floor 2.4, tray floor 2.0, lid top 2.4 |

### 3.2 Parameters

Everything above derives from the parameter block at the top of `build_fox_case.py`:
`FOX_LENGTH, FOX_WIDTH, FOX_HEIGHT, FOX_CORNER_R, FOX_CLEARANCE_XY, FOX_CLEARANCE_Z, FLOOR,
CRADLE_H, WALL, LID_WALL, LID_CLEARANCE, LID_TOP, LID_TOP_GAP, WINDOW_STUB, WINDOW_FILLET, LIP_H,
LIP_T, TRAY_CLEARANCE, TRAY_FLOOR, ACCESSORY_BOX / ACCESSORY_VOLUME_TARGET / ACCESSORY_HEIGHT,
FIT_TEST_H, FIT_TEST_WALL` and a few small chamfer sizes. The fit-test ring uses **the same
`CAV_L/CAV_W/CAV_R`** as the base, so the two cannot drift apart.

---

## 4. Validation (from `exports/validation_report.json`)

| Check | Result |
|---|---|
| Watertight / non-manifold edges | 0 on all 4 parts (also re-checked on the re-imported STL files) |
| Islands (floating geometry) | 1 per part |
| Self-intersections | 0 |
| Overhangs > 45° in print orientation | 0 mm² on every part |
| Min wall (1st percentile) | base 1.2 (tray-locating lips), tray 2.0, lid 2.4, ring 2.0 |
| Thin areas < 1.2 mm | 76 mm² on the base: only the 0.6 mm lead-in chamfer at the lip tops |
| A1 mini fit | ✓ base 125×82×41.4, tray 116.5×73.5×71, lid 125×82×102.9, ring 119.5×76.5×10 |
| Part clashes (assembled) | none; resting contacts checked with a 0.02 mm lift |
| FOX ↔ cradle wall | 1.25 mm per side |
| FOX ↔ tray underside | 1.5 mm |
| FOX ↔ lid | ≥ 3.6 mm |
| Sensor face ↔ base / lid | ≥ 1.05 mm / 3.4 mm (it can only touch the base towers' 4 mm stubs, at the window's very ends) |
| Tray usable volume | 538.7 cm³ ≥ 538.6 cm³ (black box) |
| Charger (52×52×32 proxy) and cable coil proxy in tray | fit, no clash |

Visual checks were done in Blender from several angles, including a long-axis section. See `renders/`.

---

## 5. Printing

| Part | STL | Orientation | Supports | Solid-equivalent PLA |
|---|---|---|---|---|
| Fit-test ring | `fox_fit_test_cradle_ring.stl` | as exported | none | ~9 g |
| Base | `fox_case_v1_base.stl` | upright, floor on bed | none | ~61 g |
| Tray | `fox_case_v1_accessory_tray.stl` | upright, floor on bed | none | ~83 g |
| Lid | `fox_case_v1_lid.stl` | **upside down**, top on bed (exported that way) | none | ~146 g |

Solid-equivalent is the upper bound. With 3 walls and 15 % infill, expect ~230–270 g for the
full case. Suggested settings: 0.2 mm layers, 3 walls, 15 % infill, PLA or PETG. No brim is needed.

**Plates on the A1 mini:** (1) fit-test ring alone first. Then (2) lid + tray together (155 × 125 mm
on the plate), and (3) base. See `renders/08_plate*.png`.

**Assembly:** lay the FOX flat in the base, sensor face toward either long side (both are open) →
set the tray on the towers between the lips → slide the lid down until it sits on the base shoulder.

---

## 6. Remaining uncertainties

1. **FOX length (111–115 mm).** This is the biggest one. The cavity is sized for the conservative
   113 mm envelope. Settle it with the fit-test ring.
2. **FOX height (32–35 mm).** If it's shorter than 35, there's more vertical play under the tray.
3. **Sensor window's lowest edge.** V1 assumes the glass sits above the 8 mm cradle band.
   Verify this, and lower `CRADLE_H` if not.
4. **Plan corner radius.** The cavity tolerates 1–10 mm, and the ring confirms it.
5. **Charger thickness.** It's irrelevant now that the tray is 69 mm deep, but it hasn't been measured.
6. **Turntable and calibration board.** The store lists them in the box, but they weren't in your
   photos or brief, so V1 doesn't carry them.
7. **Lid retention.** A slip fit only. If you carry the case upside down, the lid can slide off.
   A rubber band works for V1; V2 could add a detent bump.
8. **Photo scale.** Every photo dimension carries ~±2–3 mm of perspective uncertainty, which is
   why the evidence table gives ranges.

## 7. What to test physically, in order

1. **Print `exports/fox_fit_test_cradle_ring.stl`** (~9 g, roughly 30 min). Lay the FOX flat on
   the table and drop the ring over it. Check:
   * it goes on and lifts off without force, and doesn't catch at the corners;
   * the end gap. Expect ~1.25 mm per end if the FOX is 113 mm long, or ~2.25 mm if it's 111.
     Measure it (a feeler gauge, stacked paper, or a steel ruler) and report it;
   * the side gap. Expect ~1.25 mm per side;
   * the ring's top edge (10 mm) sits on the black bezel, not the lens glass. The base's band
     is 8 mm, so this check is conservative.
2. **Measure the FOX height** lying flat: put a stiff card on top and read its height at eye level.
3. Adjust `FOX_LENGTH`, `FOX_WIDTH`, `FOX_HEIGHT` (or the clearances), re-run the build, and
   print the ring again if anything changed by more than ~1 mm.
4. Only then print base → tray → lid.
