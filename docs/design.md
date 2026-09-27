# FOX carrying case — design notes (V2: one-plate print)

Goal: one rigid, compact, FDM-printable case that carries the **3DMakerpro FOX scanner and its
charger and cable together**.

**V2 driver:** the whole case must print **on one Bambu A1 mini plate (180 × 180 × 180 mm) in a
single job, with no supports.** Each part is designed around how it builds up layer by layer from
the bed.

All geometry comes from [`scripts/build_fox_case.py`](../scripts/build_fox_case.py). Edit a parameter
and re-run it (see [README](../README.md)). Numbers below are current values.

---

## 1. Evidence

### 1.1 Sources and how much each is trusted

1. **Your ruler photos** (`reference/photos/`) are the primary evidence. The camera was very
   close (EXIF: 24 mm-equivalent, focal length ≈ 2795 px at full resolution, subjects 14–20 cm
   away), so **perspective errors of 5–10 % are real**. I corrected for the ruler sitting above or
   below the scanner's outline; I did not just read the ruler.
2. **Third-party stand STL** (`reference/third_party/…parte 2.stl`) is secondary evidence. The
   geometry is exact, but what it means depends on how the designer built it.
3. **Manufacturer spec** ([store.3dmakerpro.com](https://store.3dmakerpro.com/products/fox),
   [filament2print](https://filament2print.com/en/3d-scanners/4463-fox-3dmakerpro-3d-scanner.html)):
   "115 × 70 × 35 mm, 210 g". This is a rounded envelope, used as a cross-check only.
4. **Original foam** (photo 172336) shows orientation only. The FOX lies flat, logo up, and the
   black sensor face is on a **long** side.

### 1.2 Evidence table

| Quantity | Value | Source | Confidence |
|---|---|---|---|
| FOX length, apparent | 103.0 / 105.2 mm | 174047 (ruler ≈138 mm from camera) / 174130 (≈194 mm) | reading ±0.5 |
| **FOX length, perspective-solved** | **111 ± 3 mm** | the two photos solved for a shared ruler-to-outline offset (Δ ≈ 10.8 mm) | medium |
| Stand clear length between end lips | 113.0 mm (lips 3.0 thick, 20 mm tall) | STL, flattened from its 47.2° print tilt | high (geometry) |
| FOX length, manufacturer | 115 mm | spec | low as a body size |
| **FOX width** | **69–71 mm** (66.4 apparent) | 174055, ruler lying on the scanner; spec says 70 | medium-high |
| **FOX height** | **32–35 mm** (≈27 apparent) | 174231 macro, ruler ~10–15 mm in front of the scanner end; spec says 35 | low-medium |
| FOX plan corner radius | ≈3–5 mm | top-down photos | low, but the cavity accepts 1–10 mm |
| Sensor face | long side, 3 lenses behind a black window | 172336, 174120, MakerWorld screenshot | high |
| Sensor window vertical extent | assumed ≈9–28 mm above the scanner bottom | screenshot proportions | **low** |
| Black accessory box | ≈180 × 68 × 44 mm → **539 cm³** | 174530 / 174542 / 174550 | medium |
| Charger (65 W GaN) | ≈52 × 52 mm footprint; thickness not visible | 172336 | low-medium |
| Cable | coiled bundle ≈127 × 48 × 20 mm; can be re-coiled | 172336 | low-medium |

### 1.3 Disagreements, and which source wins

* **Length: photos 111 ± 3, stand ≤ 113, spec 115.** These are not averaged. The photos and the
  stand agree with each other, and the stand physically holds the FOX between lips 113 mm apart,
  so the spec's 115 is treated as an outer envelope. **Design envelope: 113 mm.** The cavity is
  115.5 mm, so even a true 115 mm body still goes in. The fit-test ring settles this.
* **Height: 35 mm** (spec, top of the photo range). A shorter scanner only means more vertical
  play under the tray.
* **Width: 70 mm**, which every source agrees on.
* **Accessory volume** follows your direction: the tray's own inner volume is **≥ the black box's
  539 cm³** (`ACCESSORY_VOLUME_TARGET`).

---

## 2. Layout study (unchanged from V1: stacked wins)

| | A. Side-by-side | **B. Stacked (chosen)** |
|---|---|---|
| Size for 539 cm³ of accessories | ≈125 × 215 × 48 mm | **125 × 82 × 130.5 mm** |
| Footprint | ≈26,900 mm² | **10,250 mm² (−62 %)** |
| Fits the A1 mini | ✗ base/lid > 180 mm | ✓ and the whole case fits on **one plate** |

---

## 3. Designing for one plate

### 3.1 Why V1 couldn't do it

A case with two compartments needs three horizontal plates: base floor, divider (tray floor), and
lid top. In V1 each one printed flat on the bed, which means three footprints of about 125 × 82 mm.
The 180 × 180 mm bed fits only two of those side by side (82 + 8 + 82 = 172 mm). So V1 needed two plates.

### 3.2 The V2 trick: print the lid mouth-down and nest the tray inside it

* The **lid now prints exactly as it's used, mouth down on the bed.** Its "top" is no longer a flat
  plate that would need support. It's a **45° chamfered roof** (self-supporting) that closes to a
  flat ceiling only **40 mm wide**, which the printer spans as a normal bridge.
* Because the lid has no floor, **the bed inside it is free**. The **accessory tray prints nested
  inside the lid**, on the bed, with a **1.85 mm gap** all round (≥ 1.5 mm required).
* Plate = **[BASE] + [LID with TRAY inside]**, which uses **125 × 172 mm** of the 180 × 180 mm bed.
  The tallest part is 120.1 mm (limit 180).

Printing the case fully assembled (print-in-place) was rejected. The tray floor and lid ceiling
would float over 115 × 72 mm voids, needing support inside a closed box where it could never be removed.

### 3.3 Build-up order on the plate (bottom → top)

All three parts print together, layer by layer. Reading the plate from the bed up
(`renders/09_print_progress_sheet.png`):

| Z (mm) | What the printer is laying down | Notes |
|---|---|---|
| 0 – 2.4 | base floor (solid) · tray floor (solid) · lid mouth ring | Base and tray have big first layers (9,900 and 8,300 mm²). The lid touches the bed only with its 1.6 mm wide wall ring (620 mm²), so it gets an outer brim (see 3.5). |
| 2.4 – 10.4 | base band ring (4.75 mm thick walls) · tray walls · lid walls | all vertical walls |
| 10.4 – 38.9 | base C-towers (finger windows are simply "not printed") · tray and lid walls | the U-shaped window bottoms curve *away* from the material, so no overhang |
| 38.9 – 41.4 | base tray-locating lips; **base finished** | lips have a 0.6 mm lead-in chamfer on top |
| 41.4 – 71.0 | tray walls; **tray finished** at z = 71 | the tray top is ~29 mm below the lid roof, so there's no nozzle risk |
| 71 – 100.1 | lid walls only | 2.4 mm walls |
| 100.1 – 117.7 | **lid roof: 45° chamfers** stepping inward every layer | self-supporting. The only "steeper" facets are 5.6 mm² of slivers on the 4 hip valleys, which are concave inside corners that print like the inside of a pyramid. |
| 117.7 – 120.1 | **40 mm bridge** closes the roof, then 2.4 mm of top layers | a normal bridge for the A1 mini |

### 3.4 Where supports go

**Nowhere.** Every part checks support-free in print orientation (`support_free: true` in
`exports/validation_report.json`):

| Part | Down-facing surfaces > 45° from vertical | Bridges | Support |
|---|---|---|---|
| Base | 0 mm² | none | none |
| Tray | 0 mm² | none | none |
| Lid | 5.6 mm² (hip-valley slivers, self-supporting) | one, 40 mm span | none |
| Fit-test ring | 0 mm² | none | none |

### 3.5 Slicer settings (Bambu Studio, A1 mini)

1. Open **`exports/fox_case_A1mini_one_plate.3mf`**. Positions are already on the plate. If asked,
   load it as geometry. You can also use `fox_case_A1mini_one_plate.stl` and **Split → To objects**.
2. **Don't use Auto-Arrange.** It would pull the tray out of the lid, and the parts would no longer fit.
3. **Supports: off.**
4. **Brim, set per object.**
   - Lid: **Outer brim only, ~5 mm.** The lid is 120 mm tall on a 1.6 mm wall ring, and the A1 mini
     moves the bed in Y.
   - Tray: **no brim.** Any brim would bridge the 1.85 mm gap and fuse the tray to the lid.
   - Base: none or auto.
5. 0.2 mm layers, 3 walls, 15 % infill, PLA. Keep the default elephant-foot compensation.
6. Print sequence: **By layer** (the default). By-object printing is impossible because the tray sits
   inside the lid.

Filament, solid-equivalent upper bound: base 61 g + tray 83 g + lid 152 g ≈ **296 g**. Expect
roughly **230–270 g** with 3 walls and 15 % infill. Use the slicer's number for time and weight.

---

## 4. Architecture and dimensions

```
                 ___________________   z 130.5  flat top (40 mm bridge inside)
                /     45° roof      \   z 110.5  roof starts
        ┌──────┘                     └──────┐
        │  ┌──── TRAY (bin, 69 deep) ────┐  │   z 109.9 rim
        │  │  charger + coiled cable     │  │
        │  └──────── tray floor 2.0 ─────┘  │   z 38.9 underside
        │ ▐tower▌  FOX lies flat   ▐tower▌  │   z 37.4 FOX top
        └─▐     ▌▁▁ 8 mm cradle ▁▁▐     ▌───┘   z 10.4 lid mouth rests on base shoulder
           BASE: 2.4 floor, band, C-shaped end towers   z 0
```

| Item | Value |
|---|---|
| FOX design envelope | 113 × 70 × 35 mm, plan R 4 |
| **Scanner cavity** | **115.5 × 72.5 mm, R 5.25**, flat floor |
| Scanner clearance | 1.25 mm per side (XY), 1.5 mm above (Z) |
| Cradle capture height (long sides) | 8 mm; ends captured full height by the towers |
| Finger windows | 97 mm long on both long sides |
| **Case outside** | **125.0 × 82.0 × 130.5 mm** |
| Tray inside (usable) | 112.5 × 69.5 × 69 mm = **538.7 cm³** (target 538.6) |
| Lid roof | 45°, 20 mm chamfer, 40 mm bridge; tray rim to roof ≥ 1.5 mm vertical |
| Lid ↔ tower clearance | 0.35 mm per side, with a 0.6 mm lead-in chamfer on the lips |
| Tray ↔ lip clearance | 0.30 mm per side |
| Walls | lid 2.4 (also normal to the roof), towers 2.0, tray 2.0, base floor 2.4, tray floor 2.0, lid top 2.4 |

**Changes from V1:**
- Lid: flat top replaced by the 45° roof, printed mouth-down, with only 0.4 mm mouth chamfers so
  the first layer stays wide.
- Base: the lead-in chamfer moved onto the base lips.
- Tray-to-roof gap raised to 1.5 mm.
- Case is 17 mm taller (130.5 vs 113.3 mm). That's the price of a support-free roof.
- Footprint unchanged.

Key parameters: `FOX_*`, `FOX_CLEARANCE_*`, `CRADLE_H`, `WALL`, `LID_WALL`, `LID_CLEARANCE`,
`ROOF_CHAMFER` (a bigger value gives a shorter bridge but a taller case), `LID_TOP_GAP`,
`ACCESSORY_VOLUME_TARGET`, `PLATE_GAP`, `NEST_MIN_GAP`. The fit-test ring uses the same cavity
parameters as the base.

---

## 5. Validation (`exports/validation_report.json`)

| Check | Result |
|---|---|
| Watertight / non-manifold edges | 0 on all parts (also re-checked on re-imported STL files) |
| Islands / self-intersections | 1 per part / 0 |
| Supports needed | none (see 3.4) |
| One-plate fit | plate bbox 27.5–152.5 × 4–176 × 0–120.1 mm inside 180³ ✓ |
| Nested tray ↔ lid gap on the plate | 1.85 mm, no clash |
| Base ↔ lid gap on the plate | 8.0 mm |
| Assembled clashes | none (resting contacts checked with a 0.02 mm lift) |
| FOX ↔ cradle wall / tray / lid | 1.25 / 1.5 / ≥ 3.6 mm |
| Tray ↔ lid roof (closed) | 1.06 mm normal to the 45° surface (1.5 mm vertical) |
| Sensor face ↔ base / lid | ≥ 1.05 / 3.4 mm |
| Min wall (1st percentile) | base 1.2 (lips), tray 2.0, lid 2.4, ring 2.0 |

---

## 6. Assembly and use

1. Lay the FOX flat in the base, sensor face toward either long side. Both long sides are open
   above 8 mm, so you pinch the FOX by its long sides to lift it out.
2. Set the tray on the towers between the lips, and put the charger and cable in it.
3. Lower the lid until it sits on the base shoulder. The lip chamfers guide it.

## 7. Remaining uncertainties

1. **FOX length (111–115 mm).** Settle it with the fit-test ring.
2. **FOX height (32–35 mm).** If it's shorter, there's more vertical play under the tray.
3. **Sensor window's lowest edge.** V2 assumes it's above the 8 mm cradle band.
4. **Lid first-layer adhesion.** It's only a wall ring, so use the outer brim.
5. **Lid retention** is a slip fit only; a detent is planned for V3 if you want one.
6. **Turntable and calibration board** aren't carried (they weren't in your photos or brief).

## 8. What to test physically, in order

1. **Print `exports/fox_fit_test_cradle_ring.stl`** on its own (~9 g, roughly 30 min). Lay the
   FOX on the table, drop the ring over it, and check:
   * it goes on and off without force or catching at the corners;
   * the end gap: ~1.25 mm if the FOX is 113 mm long, ~2.25 mm if 111;
   * the side gap: ~1.25 mm;
   * the ring edge sits on the black bezel, not the lens glass.
2. Measure the FOX height (lay it flat, put a stiff card on top, read the height at eye level).
3. Update the `FOX_*` values, re-run the build script, and reprint the ring if anything changed by
   more than ~1 mm.
4. Print the **one-plate 3MF**.
