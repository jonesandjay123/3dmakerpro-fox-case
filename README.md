# 3dmakerpro-fox-case

A compact, rigid, 3D-printable carrying case for the **3DMakerpro FOX** scanner that keeps the
scanner **and** its charger and cable together. Pick up one case and you have everything.
Designed for FDM printing on a Bambu Lab A1 mini with no supports.

![closed](renders/01_closed_case.png)

## Status: V1 modelled, validated in CAD, not yet printed

* **Stacked layout:** base with a shallow FOX cradle → accessory tray → slip-over lid.
* **Outside size:** 125 × 82 × 113 mm, a footprint barely larger than the FOX.
* **Scanner cavity:** 115.5 × 72.5 mm (R 5.25). Clearance is 1.25 mm per side and 1.5 mm above.
  Both long sides are open above an 8 mm cradle so you can grip the FOX.
* **Accessory tray:** 539 cm³ usable, equal to the original black accessory box.
* Watertight meshes, no overhangs, no part clashes, and every part fits the A1 mini.
  See [`docs/design.md`](docs/design.md).

**Print this first:** [`exports/fox_fit_test_cradle_ring.stl`](exports/fox_fit_test_cradle_ring.stl)
(~9 g). It checks the FOX cavity before you commit to the full case. The FOX length is the main
open question (photo evidence 111 ± 3 mm vs a 115 mm spec sheet).

## Layout

| Path | Contents |
|---|---|
| `scripts/build_fox_case.py` | Parametric build: every dimension is a named parameter; exports STLs, runs validation, saves the .blend |
| `scripts/render_views.py` | Documentation renders |
| `cad/fox_case_v1.blend` | Editable Blender source (parts, proxies, hidden reference stand) |
| `exports/*.stl` | Print-ready parts, already in print orientation |
| `exports/validation_report.json` | Parameters, derived dimensions, mesh and assembly checks |
| `renders/` | Closed, open, cradle, tray, exploded, section, fit-test and plate views |
| `docs/design.md` | Evidence, layout study, dimensions, print notes, uncertainties, test plan |
| `reference/` | Your photos, the third-party MakerWorld stand STL and its screenshot (unaltered) |

## Rebuild after changing a parameter

Edit the parameter block at the top of `scripts/build_fox_case.py`, then either:

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/build_fox_case.py
```

or run `exec(open("scripts/build_fox_case.py").read())` in Blender (or through the Blender MCP),
optionally followed by `scripts/render_views.py`.

## Parts

| Part | STL | Print |
|---|---|---|
| Fit-test ring | `fox_fit_test_cradle_ring.stl` | as exported, ~9 g |
| Base | `fox_case_v1_base.stl` | upright, ~61 g solid-equivalent |
| Accessory tray | `fox_case_v1_accessory_tray.stl` | upright, ~83 g |
| Lid | `fox_case_v1_lid.stl` | upside down (exported that way), ~146 g |

The third-party stand in `reference/third_party/` (MakerWorld, "Tacco25") is used only as
measurement evidence. None of its geometry is copied into this case.
