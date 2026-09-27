"""
3DMakerpro FOX carrying case - V1 parametric build script for Blender (tested on 5.1.2).

Run either way:
  * Blender MCP / Text Editor:  exec(open("<repo>/scripts/build_fox_case.py").read())
  * Headless:  /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/build_fox_case.py

Units: 1 Blender unit = 1 mm. Everything is rebuilt from the parameters below,
so edit a number and re-run - no destructive manual edits.

Architecture (stacked, see docs/design.md):
    LID  (slip-over sleeve, covers tray + scanner zone, rests on base band shoulder)
    TRAY (open accessory bin, sits on the base end towers between locating lips)
    FOX  (lies flat in a shallow cradle; long sides open above CRADLE_H for fingers)
    BASE (floor + 10 mm band + two end towers that carry the tray)
"""
import bpy, bmesh, math, os, json
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

# ----------------------------------------------------------------------------
# PARAMETERS (mm)
# ----------------------------------------------------------------------------
# FOX design envelope. Best photo estimate is ~111 x 70 x 33; manufacturer spec is
# 115 x 70 x 35; third-party stand has 113.0 mm between its end lips.
# We use a conservative envelope - see docs/design.md "Evidence".
FOX_LENGTH = 113.0
FOX_WIDTH = 70.0
FOX_HEIGHT = 35.0
FOX_CORNER_R = 4.0        # plan-view corner radius (cavity tolerates 1..10 mm)

FOX_CLEARANCE_XY = 1.25   # per side, scanner -> cradle wall
FOX_CLEARANCE_Z = 1.5     # scanner top -> tray underside

FLOOR = 2.4               # base floor thickness
CRADLE_H = 8.0            # long-side capture height above floor (below sensor window)
WALL = 2.0                # base tower walls and tray walls
LID_WALL = 2.4
LID_CLEARANCE = 0.35      # per side, lid sleeve -> base towers
LID_TOP = 2.4
LID_TOP_GAP = 1.0         # tray rim -> lid ceiling (limits tray lift)

WINDOW_STUB = 4.0         # straight tower stub kept on each long side past the corner arc
                          # (small, so the sensor window zone |x| < ~48 mm faces open air)
WINDOW_FILLET = 5.0       # radius at the bottom corners of the finger windows

LIP_H = 2.5               # tray-locating lips on tower tops
LIP_T = 1.2
TRAY_CLEARANCE = 0.3      # per side, tray -> lips
TRAY_FLOOR = 2.0
# Accessory volume requirement = the original black cardboard accessory box
# (charger + cable), per user direction. Outer size measured from photos
# 174530 / 174542 / 174550: ~180 x 68 x 44 mm. The tray depth is derived so the
# tray's usable volume >= the box volume (contents need not keep the box shape).
ACCESSORY_BOX = (180.0, 68.0, 44.0)
ACCESSORY_VOLUME_TARGET = ACCESSORY_BOX[0] * ACCESSORY_BOX[1] * ACCESSORY_BOX[2]  # mm^3
ACCESSORY_HEIGHT = None   # None = derive from ACCESSORY_VOLUME_TARGET; or set a depth in mm

FIT_TEST_H = 10.0         # fit-test ring height
FIT_TEST_WALL = 2.0

# small edge treatments
CH_BED = 0.6              # elephant-foot chamfer on bed edges
CH_GROOVE = 1.0           # V-groove at the lid/base joint (thumb grip)
CH_LID_TOP = 1.2
CH_LID_MOUTH = 0.8        # lead-in chamfer inside lid mouth
CH_LIP = 0.6
SEG = 16                  # segments per 90 deg corner

A1_MINI_BED = (180.0, 180.0, 180.0)

# ----------------------------------------------------------------------------
# DERIVED DIMENSIONS
# ----------------------------------------------------------------------------
CAV_L = FOX_LENGTH + 2 * FOX_CLEARANCE_XY
CAV_W = FOX_WIDTH + 2 * FOX_CLEARANCE_XY
CAV_R = FOX_CORNER_R + FOX_CLEARANCE_XY

TOWER_L = CAV_L + 2 * WALL                     # base tower outer (= lid inner - 2*clearance)
TOWER_W = CAV_W + 2 * WALL
TOWER_R = CAV_R + WALL

OUT_L = TOWER_L + 2 * (LID_CLEARANCE + LID_WALL)   # case outer footprint
OUT_W = TOWER_W + 2 * (LID_CLEARANCE + LID_WALL)
OUT_R = TOWER_R + LID_CLEARANCE + LID_WALL

Z_CRADLE = FLOOR + CRADLE_H                     # band top = window bottom = lid bottom
Z_SEAT = FLOOR + FOX_HEIGHT + FOX_CLEARANCE_Z   # tray underside
TRAY_L = TOWER_L - 2 * (LIP_T + TRAY_CLEARANCE)
TRAY_W = TOWER_W - 2 * (LIP_T + TRAY_CLEARANCE)
TRAY_R = TOWER_R - (LIP_T + TRAY_CLEARANCE)


def _rr_area(L, W, R):
    return L * W - (4 - math.pi) * R * R


TRAY_INNER_AREA = _rr_area(TRAY_L - 2 * WALL, TRAY_W - 2 * WALL, TRAY_R - WALL)
if ACCESSORY_HEIGHT is None:
    ACCESSORY_HEIGHT = math.ceil(ACCESSORY_VOLUME_TARGET / TRAY_INNER_AREA)
TRAY_H = TRAY_FLOOR + ACCESSORY_HEIGHT
Z_TRAY_TOP = Z_SEAT + TRAY_H
Z_LID_CEIL = Z_TRAY_TOP + LID_TOP_GAP
Z_TOP = Z_LID_CEIL + LID_TOP
WINDOW_HALF = CAV_L / 2 - CAV_R - WINDOW_STUB

# ----------------------------------------------------------------------------
# PATHS
# ----------------------------------------------------------------------------
try:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    ROOT = "/Users/joneswang/Downloads/code/3dmakerpro-fox-case"
EXPORTS = os.path.join(ROOT, "exports")
CAD = os.path.join(ROOT, "cad")
COLL = "FOX_CASE_V1"


# ----------------------------------------------------------------------------
# GEOMETRY HELPERS
# ----------------------------------------------------------------------------
def rr_loop(L, W, R, seg=SEG):
    """Rounded-rectangle outline (CCW) centred on origin."""
    R = max(0.05, min(R, L / 2 - 0.01, W / 2 - 0.01))
    cx, cy = L / 2 - R, W / 2 - R
    pts = []
    for (sx, sy, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((sx * cx + R * math.cos(a), sy * cy + R * math.sin(a)))
    return pts


def mesh_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.data.collections[COLL].objects.link(ob)
    return ob


def loft_rr(name, L, W, R, profile):
    """Solid made of rounded-rect loops. profile = [(z, offset), ...] ascending z;
    offset grows/shrinks the rectangle (used for chamfers)."""
    bm = bmesh.new()
    loops = []
    for z, d in profile:
        loops.append([bm.verts.new((x, y, z)) for x, y in rr_loop(L + 2 * d, W + 2 * d, R + d)])
    n = len(loops[0])
    for a, b in zip(loops[:-1], loops[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(loops[0])))
    bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm)


def prism_rr(name, L, W, R, z0, z1):
    return loft_rr(name, L, W, R, [(z0, 0), (z1, 0)])


def extrude_xz(name, pts, y0, y1):
    """Extrude a closed XZ polygon along Y."""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in pts]
    b = [bm.verts.new((x, y1, z)) for x, z in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(a)))
    bm.faces.new(b)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm)


def box(name, x0, x1, y0, y1, z0, z1):
    return extrude_xz(name, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1)


def boolean(target, tool, op):
    m = target.modifiers.new("bool", "BOOLEAN")
    m.operation = op
    m.solver = "EXACT"
    m.object = tool
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(tool, do_unlink=True)
    return target


def u_notch_pts(half, z0, z_top, r, seg=SEG):
    """Finger-window outline in XZ: rectangle with rounded bottom corners."""
    pts = [(-half, z_top)]
    for i in range(seg + 1):
        a = math.radians(180 + 90 * i / seg)
        pts.append((-half + r + r * math.cos(a), z0 + r + r * math.sin(a)))
    for i in range(seg + 1):
        a = math.radians(270 + 90 * i / seg)
        pts.append((half - r + r * math.cos(a), z0 + r + r * math.sin(a)))
    pts.append((half, z_top))
    return pts


# ----------------------------------------------------------------------------
# PARTS (built in assembled position, Z=0 at bottom of base)
# ----------------------------------------------------------------------------
def build_base():
    band = loft_rr("Base", OUT_L, OUT_W, OUT_R,
                   [(0, -CH_BED), (CH_BED, 0), (Z_CRADLE - CH_GROOVE, 0), (Z_CRADLE, -CH_GROOVE)])
    towers = prism_rr("t_towers", TOWER_L, TOWER_W, TOWER_R, 1.0, Z_SEAT)
    boolean(band, towers, "UNION")
    # tray-locating lips: outer ring on tower tops, with a lead-in chamfer inside
    lip = loft_rr("t_lip", TOWER_L, TOWER_W, TOWER_R, [(Z_SEAT - 0.01, 0), (Z_SEAT + LIP_H, 0)])
    lip_in = loft_rr("t_lipin", TOWER_L - 2 * LIP_T, TOWER_W - 2 * LIP_T, TOWER_R - LIP_T,
                     [(Z_SEAT - 0.5, 0), (Z_SEAT + LIP_H - CH_LIP, 0), (Z_SEAT + LIP_H + 0.01, CH_LIP)])
    boolean(lip, lip_in, "DIFFERENCE")
    boolean(band, lip, "UNION")
    # scanner cavity
    cav = prism_rr("t_cav", CAV_L, CAV_W, CAV_R, FLOOR, Z_TOP + 10)
    boolean(band, cav, "DIFFERENCE")
    # finger windows through both long sides (and lips) down to cradle height
    win = extrude_xz("t_win", u_notch_pts(WINDOW_HALF, Z_CRADLE, Z_TOP + 10, WINDOW_FILLET),
                     -OUT_W, OUT_W)
    boolean(band, win, "DIFFERENCE")
    return band


def build_tray():
    tray = loft_rr("Tray", TRAY_L, TRAY_W, TRAY_R,
                   [(Z_SEAT, -CH_BED), (Z_SEAT + CH_BED, 0), (Z_TRAY_TOP, 0)])
    inner = loft_rr("t_tin", TRAY_L - 2 * WALL, TRAY_W - 2 * WALL, TRAY_R - WALL,
                    [(Z_SEAT + TRAY_FLOOR, 0), (Z_TRAY_TOP - 0.5, 0), (Z_TRAY_TOP + 0.01, 0.51)])
    boolean(tray, inner, "DIFFERENCE")
    return tray


def build_lid():
    lid = loft_rr("Lid", OUT_L, OUT_W, OUT_R,
                  [(Z_CRADLE, -CH_GROOVE), (Z_CRADLE + CH_GROOVE, 0),
                   (Z_TOP - CH_LID_TOP, 0), (Z_TOP, -CH_LID_TOP)])
    c = LID_CLEARANCE
    inner = loft_rr("t_lin", TOWER_L, TOWER_W, TOWER_R,
                    [(Z_CRADLE - 1, c + CH_LID_MOUTH + 1), (Z_CRADLE + CH_LID_MOUTH, c),
                     (Z_LID_CEIL, c)])
    boolean(lid, inner, "DIFFERENCE")
    return lid


def build_fit_test():
    ring = loft_rr("FitTest", CAV_L + 2 * FIT_TEST_WALL, CAV_W + 2 * FIT_TEST_WALL, CAV_R + FIT_TEST_WALL,
                   [(0, -CH_BED), (CH_BED, 0), (FIT_TEST_H, 0)])
    hole = loft_rr("t_fh", CAV_L, CAV_W, CAV_R,
                   [(-1, 1 + 0.5), (0.5, 0), (FIT_TEST_H + 1, 0)])  # 0.5 mm anti-elephant-foot flare
    boolean(ring, hole, "DIFFERENCE")
    ring.location.x = 0
    return ring


def build_proxies():
    """Non-printed reference bodies for clearance checks and renders."""
    fox = loft_rr("PROXY_FOX", FOX_LENGTH, FOX_WIDTH, FOX_CORNER_R,
                  [(FLOOR, -2.0), (FLOOR + 2.0, 0), (FLOOR + FOX_HEIGHT - 4.0, 0), (FLOOR + FOX_HEIGHT, -4.0)])
    sensor = box("PROXY_FOX_SensorFace", -FOX_LENGTH / 2 + 8, FOX_LENGTH / 2 - 8,
                 -FOX_WIDTH / 2 - 0.2, -FOX_WIDTH / 2 + 1.5, FLOOR + 9, FLOOR + FOX_HEIGHT - 7)
    chg = loft_rr("PROXY_Charger", 52, 52, 6, [(Z_SEAT + TRAY_FLOOR, 0), (Z_SEAT + TRAY_FLOOR + 32, 0)])
    chg.location.x = TRAY_L / 2 - WALL - 26 - 1.5
    # coiled cable approximated as a flat oval ring
    coil = loft_rr("PROXY_CableCoil", 52, 62, 24, [(Z_SEAT + TRAY_FLOOR, 0), (Z_SEAT + TRAY_FLOOR + 22, 0)])
    coil_in = loft_rr("t_ci", 28, 38, 12, [(Z_SEAT + TRAY_FLOOR - 1, 0), (Z_SEAT + TRAY_FLOOR + 23, 0)])
    boolean(coil, coil_in, "DIFFERENCE")
    coil.location.x = -(TRAY_L / 2 - WALL - 26 - 1.5)
    for o in (fox, sensor, chg, coil):
        o["proxy"] = True
    return [fox, sensor, chg, coil]


# ----------------------------------------------------------------------------
# VALIDATION
# ----------------------------------------------------------------------------
def world_bm(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    bm.normal_update()
    return bm


def mesh_stats(ob, print_matrix=None):
    bm = world_bm(ob)
    if print_matrix is not None:
        bm.transform(print_matrix)
        bm.normal_update()
    nonman_e = sum(1 for e in bm.edges if not e.is_manifold)
    nonman_v = sum(1 for v in bm.verts if not v.is_manifold)
    # connected components (islands)
    seen, islands = set(), 0
    for f in bm.faces:
        if f.index in seen:
            continue
        islands += 1
        stack = [f]
        seen.add(f.index)
        while stack:
            g = stack.pop()
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
    vol = bm.calc_volume(signed=True)
    zs = [v.co.z for v in bm.verts]
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    size = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    zmin = min(zs)
    # overhangs in print orientation: down-facing > 45 deg from vertical, not on bed
    over_area = 0.0
    for f in bm.faces:
        if f.normal.z < -0.7075 and f.calc_center_median().z > zmin + 0.05:
            over_area += f.calc_area()
    # self intersection (non-adjacent triangle overlap)
    bm_t = bm.copy()
    bmesh.ops.triangulate(bm_t, faces=bm_t.faces)
    tree = BVHTree.FromBMesh(bm_t)
    bm_t.faces.ensure_lookup_table()
    self_hits = 0
    for i, j in tree.overlap(tree):
        if i >= j:
            continue
        vi = {v.index for v in bm_t.faces[i].verts}
        vj = {v.index for v in bm_t.faces[j].verts}
        if not (vi & vj):
            self_hits += 1
    # wall thickness: cast inward from face centres
    thick = []
    for f in bm_t.faces:
        c = f.calc_center_median()
        n = f.normal
        hit = tree.ray_cast(c - n * 0.001, -n, 200)
        if hit[0] is not None:
            thick.append((hit[3] + 0.001, f.calc_area()))
    bm_t.free()
    bm.free()
    thick.sort()
    tot = sum(a for _, a in thick)
    acc, p1 = 0, None
    for t, a in thick:
        acc += a
        if acc >= 0.01 * tot:
            p1 = t
            break
    thin_area = sum(a for t, a in thick if t < 1.19)
    return {
        "nonmanifold_edges": nonman_e, "nonmanifold_verts": nonman_v, "islands": islands,
        "self_intersections": self_hits, "volume_cm3": round(vol / 1000, 2),
        "pla_g_solid_est": round(vol / 1000 * 1.24, 1),
        "size_print_mm": [round(s, 2) for s in size],
        "fits_a1_mini": all(s <= b for s, b in zip(size, A1_MINI_BED)),
        "overhang_area_mm2": round(over_area, 1),
        "wall_thickness_p1_mm": round(p1, 2) if p1 else None,
        "area_thinner_than_1p2mm_mm2": round(thin_area, 1),
    }


def bvh_of(ob):
    bm = world_bm(ob)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def min_gap(a, b, samples=None):
    """Smallest distance from a's vertices to b's surface (a assumed outside b)."""
    tb = bvh_of(b)
    best = 1e9
    for v in a.data.vertices:
        p = a.matrix_world @ v.co
        loc, n, i, d = tb.find_nearest(p)
        if d is not None and d < best:
            best = d
    return best


def interferes(a, b, lift=0.0):
    """True if a and b overlap. lift raises `a` first so parts that merely rest on
    each other (lid on shoulder, scanner on floor) are not reported as clashing."""
    old = a.location.z
    a.location.z += lift
    bpy.context.view_layer.update()
    hit = len(bvh_of(a).overlap(bvh_of(b))) > 0
    a.location.z = old
    bpy.context.view_layer.update()
    return hit


def side_gap(a, b, zmin):
    """Min distance from a's vertices above zmin to b (excludes resting contact)."""
    tb = bvh_of(b)
    best = 1e9
    for v in a.data.vertices:
        p = a.matrix_world @ v.co
        if p.z < zmin:
            continue
        d = tb.find_nearest(p)[3]
        if d is not None and d < best:
            best = d
    return best


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
def main(export=True, save=True):
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = "MILLIMETERS"

    if COLL in bpy.data.collections:
        c = bpy.data.collections[COLL]
        for o in list(c.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    else:
        c = bpy.data.collections.new(COLL)
        sc.collection.children.link(c)

    base = build_base()
    tray = build_tray()
    lid = build_lid()
    fit = build_fit_test()
    fit.location.y = -(OUT_W + 40)  # park beside the assembly
    proxies = build_proxies()

    # print orientations (applied to world coords before export/checks):
    # base and tray upright, lid upside down (top on bed), fit ring as-is.
    orient = {
        base: Matrix.Identity(4),
        tray: Matrix.Translation((0, 0, -Z_SEAT)),
        lid: Matrix.Translation((0, 0, Z_TOP)) @ Matrix.Rotation(math.pi, 4, "X"),
        fit: Matrix.Translation((0, (OUT_W + 40), 0)),
    }

    report = {"parameters": {k: v for k, v in globals().items()
                             if k.isupper() and isinstance(v, (int, float, tuple))}}
    report["derived"] = {
        "cavity_mm": [round(CAV_L, 2), round(CAV_W, 2), "R%.2f" % CAV_R],
        "case_outer_mm": [round(OUT_L, 2), round(OUT_W, 2), round(Z_TOP, 2)],
        "tray_inner_mm": [round(TRAY_L - 2 * WALL, 2), round(TRAY_W - 2 * WALL, 2), ACCESSORY_HEIGHT],
        "tray_usable_volume_cm3": None,
        "finger_window_length_mm": round(2 * WINDOW_HALF, 2),
        "z_levels_mm": {"floor_top": FLOOR, "cradle_top_and_lid_bottom": Z_CRADLE,
                        "tray_underside": Z_SEAT, "tray_top": Z_TRAY_TOP, "case_top": Z_TOP},
    }
    # usable accessory volume = tray inner cavity
    tin = loft_rr("t_meas", TRAY_L - 2 * WALL, TRAY_W - 2 * WALL, TRAY_R - WALL, [(0, 0), (ACCESSORY_HEIGHT, 0)])
    bm = world_bm(tin)
    report["derived"]["tray_usable_volume_cm3"] = round(bm.calc_volume() / 1000, 1)
    bm.free()
    bpy.data.objects.remove(tin, do_unlink=True)

    parts = {"base": base, "tray": tray, "lid": lid, "fit_test": fit}
    report["parts"] = {k: mesh_stats(o, orient[o]) for k, o in parts.items()}

    fox = bpy.data.objects["PROXY_FOX"]
    chg = bpy.data.objects["PROXY_Charger"]
    coil = bpy.data.objects["PROXY_CableCoil"]
    sensor = bpy.data.objects["PROXY_FOX_SensorFace"]
    report["assembly"] = {
        "clash_base_tray(resting)": interferes(tray, base, lift=0.02),
        "clash_base_lid(resting)": interferes(lid, base, lift=0.02),
        "clash_tray_lid": interferes(tray, lid),
        "clash_fox_base(resting)": interferes(fox, base, lift=0.02),
        "clash_fox_tray": interferes(fox, tray),
        "clash_fox_lid": interferes(fox, lid),
        "clash_charger_tray(resting)": interferes(chg, tray, lift=0.02),
        "clash_cable_tray(resting)": interferes(coil, tray, lift=0.02),
        "clash_sensor_face_base": interferes(sensor, base),
        "gap_fox_side_to_base_mm": round(side_gap(fox, base, FLOOR + 2.5), 2),
        "gap_fox_top_to_tray_mm": round(min_gap(fox, tray), 2),
        "gap_fox_to_lid_mm": round(min_gap(fox, lid), 2),
        "gap_tray_top_to_lid_mm": round(min_gap(tray, lid), 2),
        "gap_sensor_face_to_base_mm": round(min_gap(sensor, base), 2),
        "gap_sensor_face_to_lid_mm": round(min_gap(sensor, lid), 2),
    }

    if export:
        os.makedirs(EXPORTS, exist_ok=True)
        names = {"base": "fox_case_v1_base.stl", "tray": "fox_case_v1_accessory_tray.stl",
                 "lid": "fox_case_v1_lid.stl", "fit_test": "fox_fit_test_cradle_ring.stl"}
        for k, o in parts.items():
            tmp = o.copy()
            tmp.data = o.data.copy()
            bpy.data.collections[COLL].objects.link(tmp)
            tmp.data.transform(orient[o] @ o.matrix_world)
            tmp.matrix_world = Matrix.Identity(4)
            # drop to bed
            zmin = min(v.co.z for v in tmp.data.vertices)
            tmp.data.transform(Matrix.Translation((0, 0, -zmin)))
            bpy.ops.object.select_all(action="DESELECT")
            tmp.select_set(True)
            bpy.context.view_layer.objects.active = tmp
            bpy.ops.wm.stl_export(filepath=os.path.join(EXPORTS, names[k]),
                                  export_selected_objects=True, global_scale=1.0,
                                  use_scene_unit=False, ascii_format=False)
            bpy.data.objects.remove(tmp, do_unlink=True)
        with open(os.path.join(EXPORTS, "validation_report.json"), "w") as fh:
            json.dump(report, fh, indent=2, default=str)

    if save:
        os.makedirs(CAD, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CAD, "fox_case_v1.blend"))
    return report


REPORT = main()
print(json.dumps(REPORT, indent=1, default=str))
