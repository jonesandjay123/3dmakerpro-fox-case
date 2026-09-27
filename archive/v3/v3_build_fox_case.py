"""
3DMakerpro FOX carrying case - V3 "compact" parametric build script for Blender (5.1.2).

Run either way:
  * Blender MCP / Text Editor:  exec(open("<repo>/scripts/build_fox_case.py").read())
  * Headless:  /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/build_fox_case.py

Units: 1 Blender unit = 1 mm. Everything is rebuilt from the parameters below.

Architecture (stacked, see docs/design.md):
    LID  (slip-over sleeve, flat top, 2 snap tabs on the short ends)
    TRAY (ONE open accessory bin - deliberately NO divider - on the base end towers)
    FOX  (lies flat in a shallow cradle; long sides open above CRADLE_H for fingers)
    BASE (floor + band + two C-shaped end towers that carry the tray)

V3 drivers: physically fit-tested FOX cavity (115.5 x 73.0), 36.5 mm FOX space,
user-measured accessory envelope, minimum total height. Two print jobs are fine
(V2's one-plate constraint and the cardboard-box volume target are dropped).
"""
import bpy, bmesh, math, os, json, zipfile, struct
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

VERSION = "V3"

# ----------------------------------------------------------------------------
# PARAMETERS (mm)
# ----------------------------------------------------------------------------
# FOX cavity - PHYSICALLY FIT-TESTED with the printed V2 ring:
#   115.5 long : ~1 mm total free play            -> keep
#   72.5 wide  : fitted but lightly gripped        -> +0.5 -> 73.0
#   R 5.25     : corners behaved well              -> keep
FOX_CAVITY_LENGTH = 115.5
FOX_CAVITY_WIDTH = 73.0
FOX_CAVITY_R = 5.25
FOX_INTERNAL_HEIGHT = 36.5   # clear height: base floor top -> tray underside (measured requirement)

# Stand-in FOX body for clearance checks / renders only (not a design input),
# inferred from the ring test: ~1 mm total play in length, ~0 in width at 72.5.
FOX_PROXY = (114.4, 72.4, 35.0, 5.0)   # L, W, H, plan corner R (corners fit well in the test)

FLOOR = 2.0
CRADLE_H = 8.0            # long-side capture height (worked in the ring test)
WALL = 2.0                # base tower walls and tray walls
LID_WALL = 2.4
LID_CLEARANCE = 0.35      # per side, lid sleeve -> base towers
LID_TOP = 2.0
LID_TOP_GAP = 1.0         # tray rim -> lid ceiling (limits tray lift)

WINDOW_STUB = 1.5         # tower stub past the corner arc; short, so the lens window
                          # (|x| < ~49 mm) faces open air - the FOX only has ~0.3 mm side play
WINDOW_FILLET = 3.0       # finger-window bottom corner radius (small: keeps clear of the lens window ends)

LIP_H = 2.5               # tray-locating lips on tower tops
LIP_T = 1.2
TRAY_CLEARANCE = 0.3      # per side, tray -> lips
TRAY_FLOOR = 1.6

# Accessories (user measurement): charger ~56 wide x 52 tall; charger + cable laid flat
# in a row need ~56 x 52 x 172. User decision: keep the 125 x 82 footprint (the 172 mm
# run is NOT reproduced) - ONE open bin, deliberately NO divider; the charger sits at one
# end and the cable is coiled freely in the remaining space. Inner depth ~56 (55-58 ok)
# gives a 52 mm charger sensible headroom; target total height ~98-100 mm.
ACCESSORY_ENVELOPE = (172.0, 56.0, 52.0)   # as measured laid flat (reference only)
CHARGER = (52.0, 56.0, 52.0)               # proxy: X (depth, assumed), Y (width), Z (height)
ACCESSORY_TRAY_HEIGHT = 56.0               # usable inner depth

# Lid retention: 2 cantilever snap tabs cut into the lid's short end walls; an inward
# bump on each tab clicks into a groove on the base tower end wall.
LID_RETENTION = dict(
    tab_width=10.0,        # tab width (Y)
    tab_length=20.0,       # free length from the lid mouth up to the tab root
    slot=1.0,              # slot width on each side of the tab
    engage=0.4,            # radial overlap bump <-> tower face (the "click")
    bump_z=1.2,            # bump starts this far above the lid mouth
    insert_angle=30.0,     # lower ramp, deg from vertical (easy closing)
    release_angle=45.0,    # upper ramp, deg from vertical (= steepest support-free face)
    crest=0.6,             # flat crest height of the bump
    groove_clear=0.2,      # extra groove size around the bump
)

FIT_TEST_H = 10.0
FIT_TEST_WALL = 2.0

CH_BED = 0.6              # elephant-foot chamfer on bed edges
CH_GROOVE = 1.0           # V-groove at the lid/base joint (thumb grip)
CH_LID_TOP = 1.2          # lid top outer edge (on the bed when printing)
CH_LID_MOUTH = 0.8        # lead-in chamfer inside the lid mouth
LIP_LEADIN = 0.6          # outer top chamfer on the lips (guides lid + tab bumps)
SEG = 16

A1_MINI_BED = (180.0, 180.0, 180.0)
PLATE_GAP = 8.0
PLA_DENSITY = 1.24
V2_HEIGHT = 130.54

# ----------------------------------------------------------------------------
# DERIVED DIMENSIONS
# ----------------------------------------------------------------------------
CAV_L, CAV_W, CAV_R = FOX_CAVITY_LENGTH, FOX_CAVITY_WIDTH, FOX_CAVITY_R
TOWER_L, TOWER_W, TOWER_R = CAV_L + 2 * WALL, CAV_W + 2 * WALL, CAV_R + WALL
OUT_L = TOWER_L + 2 * (LID_CLEARANCE + LID_WALL)
OUT_W = TOWER_W + 2 * (LID_CLEARANCE + LID_WALL)
OUT_R = TOWER_R + LID_CLEARANCE + LID_WALL

Z_CRADLE = FLOOR + CRADLE_H                  # band top = window bottom = lid mouth
Z_SEAT = FLOOR + FOX_INTERNAL_HEIGHT         # tray underside
TRAY_INSET = LIP_T + TRAY_CLEARANCE
TRAY_L, TRAY_W, TRAY_R = TOWER_L - 2 * TRAY_INSET, TOWER_W - 2 * TRAY_INSET, TOWER_R - TRAY_INSET
TRAY_H = TRAY_FLOOR + ACCESSORY_TRAY_HEIGHT
Z_TRAY_TOP = Z_SEAT + TRAY_H
Z_LID_CEIL = Z_TRAY_TOP + LID_TOP_GAP
Z_TOP = Z_LID_CEIL + LID_TOP
TOTAL_CASE_HEIGHT = Z_TOP
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
COLL = "FOX_CASE"


# ----------------------------------------------------------------------------
# GEOMETRY HELPERS
# ----------------------------------------------------------------------------
def rr_loop(L, W, R, seg=SEG):
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
    """Solid from rounded-rect loops, profile = [(z, offset)] ascending z. Offsets are true
    2D offsets (radius shrinks too), so dz == offset gives an exact 45-deg chamfer."""
    prof = [profile[0]]
    for (z0, d0), (z1, d1) in zip(profile[:-1], profile[1:]):
        dstar = 0.05 - R
        if (d0 - dstar) * (d1 - dstar) < 0:
            prof.append((z0 + (dstar - d0) / (d1 - d0) * (z1 - z0), dstar))
        prof.append((z1, d1))
    bm = bmesh.new()
    loops = [[bm.verts.new((x, y, z)) for x, y in rr_loop(L + 2 * d, W + 2 * d, R + d)] for z, d in prof]
    n = len(loops[0])
    for a, b in zip(loops[:-1], loops[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(loops[0])))
    bm.faces.new(loops[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm)


def prism_rr(name, L, W, R, z0, z1):
    return loft_rr(name, L, W, R, [(z0, 0), (z1, 0)])


def extrude_xz(name, pts, y0, y1):
    """Extrude a closed XZ polygon along Y (normals recalculated, so winding is free)."""
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
    pts = [(-half, z_top)]
    for i in range(seg + 1):
        a = math.radians(180 + 90 * i / seg)
        pts.append((-half + r + r * math.cos(a), z0 + r + r * math.sin(a)))
    for i in range(seg + 1):
        a = math.radians(270 + 90 * i / seg)
        pts.append((half - r + r * math.cos(a), z0 + r + r * math.sin(a)))
    pts.append((half, z_top))
    return pts


def bump_profile(x_wall, direction, h, z0, crest):
    """XZ outline of a detent ridge rising from the wall plane x_wall by h, pointing along
    `direction` (+1/-1 in X). Lower ramp at insert_angle, upper ramp at release_angle
    (both from vertical). The base is buried 1 mm behind the wall plane."""
    R = LID_RETENTION
    z_b = z0 + h * math.tan(math.radians(R["insert_angle"]))
    z_c = z_b + crest
    z_d = z_c + h * math.tan(math.radians(R["release_angle"]))
    back = -direction * 1.0
    return [(x_wall + back, z0 - 0.01), (x_wall, z0), (x_wall + direction * h, z_b),
            (x_wall + direction * h, z_c), (x_wall, z_d), (x_wall + back, z_d + 0.01)]


# ----------------------------------------------------------------------------
# PARTS (assembled position, Z=0 at bottom of base)
# ----------------------------------------------------------------------------
def build_base():
    R = LID_RETENTION
    band = loft_rr("Base", OUT_L, OUT_W, OUT_R,
                   [(0, -CH_BED), (CH_BED, 0), (Z_CRADLE - CH_GROOVE, 0), (Z_CRADLE, -CH_GROOVE)])
    towers = prism_rr("t_towers", TOWER_L, TOWER_W, TOWER_R, 1.0, Z_SEAT)
    boolean(band, towers, "UNION")
    lip = loft_rr("t_lip", TOWER_L, TOWER_W, TOWER_R,
                  [(Z_SEAT - 0.01, 0), (Z_SEAT + LIP_H - LIP_LEADIN, 0), (Z_SEAT + LIP_H, -LIP_LEADIN)])
    lip_in = prism_rr("t_lipin", TOWER_L - 2 * LIP_T, TOWER_W - 2 * LIP_T, TOWER_R - LIP_T,
                      Z_SEAT - 0.5, Z_SEAT + LIP_H + 1)
    boolean(lip, lip_in, "DIFFERENCE")
    boolean(band, lip, "UNION")
    cav = prism_rr("t_cav", CAV_L, CAV_W, CAV_R, FLOOR, Z_TOP + 10)
    boolean(band, cav, "DIFFERENCE")
    win = extrude_xz("t_win", u_notch_pts(WINDOW_HALF, Z_CRADLE, Z_TOP + 10, WINDOW_FILLET), -OUT_W, OUT_W)
    boolean(band, win, "DIFFERENCE")
    # detent grooves in both tower end walls: the lid bump shape, grown by groove_clear
    g, c = R["groove_clear"], LID_CLEARANCE
    for sign in (+1, -1):
        pts = bump_profile(sign * (TOWER_L / 2 + c), -sign, c + R["engage"] + g,
                           Z_CRADLE + R["bump_z"] - g, R["crest"] + 2 * g)
        cut = extrude_xz("t_groove", pts, -(R["tab_width"] / 2 + 1), R["tab_width"] / 2 + 1)
        boolean(band, cut, "DIFFERENCE")
    return band


def build_tray():
    tray = loft_rr("Tray", TRAY_L, TRAY_W, TRAY_R,
                   [(Z_SEAT, -CH_BED), (Z_SEAT + CH_BED, 0), (Z_TRAY_TOP, 0)])
    inner = loft_rr("t_tin", TRAY_L - 2 * WALL, TRAY_W - 2 * WALL, TRAY_R - WALL,
                    [(Z_SEAT + TRAY_FLOOR, 0), (Z_TRAY_TOP - 0.5, 0), (Z_TRAY_TOP + 0.01, 0.51)])
    boolean(tray, inner, "DIFFERENCE")
    return tray


def build_lid():
    R = LID_RETENTION
    lid = loft_rr("Lid", OUT_L, OUT_W, OUT_R,
                  [(Z_CRADLE, -CH_GROOVE), (Z_CRADLE + CH_GROOVE, 0),
                   (Z_TOP - CH_LID_TOP, 0), (Z_TOP, -CH_LID_TOP)])
    c = LID_CLEARANCE
    inner = loft_rr("t_lin", TOWER_L, TOWER_W, TOWER_R,
                    [(Z_CRADLE - 1, c + CH_LID_MOUTH + 1), (Z_CRADLE + CH_LID_MOUTH, c), (Z_LID_CEIL, c)])
    boolean(lid, inner, "DIFFERENCE")
    for sign in (+1, -1):
        # two slots through the end wall free a cantilever tab from the mouth upward
        x_in, x_out = sign * (TOWER_L / 2 - 1), sign * (OUT_L / 2 + 1)
        for ys in (+1, -1):
            y0, y1 = ys * R["tab_width"] / 2, ys * (R["tab_width"] / 2 + R["slot"])
            s = box("t_slot", min(x_in, x_out), max(x_in, x_out), min(y0, y1), max(y0, y1),
                    Z_CRADLE - 1, Z_CRADLE + R["tab_length"])
            boolean(lid, s, "DIFFERENCE")
        # inward bump on the tab: stands clearance + engage proud of the lid inner face
        pts = bump_profile(sign * (TOWER_L / 2 + c), -sign, c + R["engage"],
                           Z_CRADLE + R["bump_z"], R["crest"])
        b = extrude_xz("t_bump", pts, -(R["tab_width"] / 2 - 0.5), R["tab_width"] / 2 - 0.5)
        boolean(lid, b, "UNION")
    return lid


def build_fit_test():
    ring = loft_rr("FitTest", CAV_L + 2 * FIT_TEST_WALL, CAV_W + 2 * FIT_TEST_WALL, CAV_R + FIT_TEST_WALL,
                   [(0, -CH_BED), (CH_BED, 0), (FIT_TEST_H, 0)])
    hole = loft_rr("t_fh", CAV_L, CAV_W, CAV_R, [(-1, 1 + 0.5), (0.5, 0), (FIT_TEST_H + 1, 0)])
    boolean(ring, hole, "DIFFERENCE")
    return ring


def build_proxies():
    L, W, H, r = FOX_PROXY
    fox = loft_rr("PROXY_FOX", L, W, r, [(FLOOR, -2.0), (FLOOR + 2.0, 0), (FLOOR + H - 4.0, 0), (FLOOR + H, -4.0)])
    sensor = box("PROXY_FOX_SensorFace", -L / 2 + 8, L / 2 - 8, -W / 2 - 0.2, -W / 2 + 1.5, FLOOR + 9, FLOOR + H - 7)
    zf = Z_SEAT + TRAY_FLOOR
    tin_l = TRAY_L - 2 * WALL
    cw, cd, ch = CHARGER
    chg = loft_rr("PROXY_Charger", cw, cd, 5, [(zf, 0), (zf + ch, 0)])
    chg.location.x = tin_l / 2 - cw / 2 - 1.0
    # cable coiled freely beside the charger: stand-in loose coil ~54 x 64 x 40
    coil = loft_rr("PROXY_CableCoil", 54, 64, 20, [(zf, 0), (zf + 40, 0)])
    coil_in = loft_rr("t_ci", 30, 40, 10, [(zf - 1, 0), (zf + 41, 0)])
    boolean(coil, coil_in, "DIFFERENCE")
    coil.location.x = -(tin_l / 2 - 27 - 1.0)
    for o in (fox, sensor, chg, coil):
        o["proxy"] = True
    return [fox, sensor, chg, coil]


# ----------------------------------------------------------------------------
# VALIDATION
# ----------------------------------------------------------------------------
def world_bm(ob, extra=None):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform((extra or Matrix.Identity(4)) @ ob.matrix_world)
    bm.normal_update()
    return bm


def mesh_stats(ob, print_matrix):
    bm = world_bm(ob, print_matrix)
    nonman_e = sum(1 for e in bm.edges if not e.is_manifold)
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
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    size = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    zmin = min(zs)
    overhang, bridge, bed = 0.0, [], 0.0
    for f in bm.faces:
        c, a = f.calc_center_median(), f.calc_area()
        if f.normal.z < -0.99 and c.z <= zmin + 0.05:
            bed += a
        elif f.normal.z < -0.99:
            bridge.append(f)
        elif f.normal.z < -0.7075:
            overhang += a
    bridge_area = sum(f.calc_area() for f in bridge)
    bridge_span = None
    if bridge:
        bx = [v.co.x for f in bridge for v in f.verts]
        by = [v.co.y for f in bridge for v in f.verts]
        bridge_span = round(min(max(bx) - min(bx), max(by) - min(by)), 1)
    bm_t = bm.copy()
    bmesh.ops.triangulate(bm_t, faces=bm_t.faces)
    tree = BVHTree.FromBMesh(bm_t)
    bm_t.faces.ensure_lookup_table()
    self_hits = 0
    for i, j in tree.overlap(tree):
        if i < j and not ({v.index for v in bm_t.faces[i].verts} & {v.index for v in bm_t.faces[j].verts}):
            self_hits += 1
    thick = []
    for f in bm_t.faces:
        c, n = f.calc_center_median(), f.normal
        hit = tree.ray_cast(c - n * 0.001, -n, 200)
        if hit[0] is not None:
            thick.append((hit[3] + 0.001, f.calc_area()))
    bm_t.free()
    bm.free()
    thick.sort()
    tot, acc, p1 = sum(a for _, a in thick), 0, None
    for t, a in thick:
        acc += a
        if acc >= 0.01 * tot:
            p1 = t
            break
    return {
        "nonmanifold_edges": nonman_e, "islands": islands, "self_intersections": self_hits,
        "volume_cm3": round(vol / 1000, 2), "pla_g_solid_est": round(vol / 1000 * PLA_DENSITY, 1),
        "size_print_mm": [round(s, 2) for s in size],
        "fits_a1_mini": all(s <= b for s, b in zip(size, A1_MINI_BED)),
        "first_layer_contact_mm2": round(bed, 0),
        "overhang_steeper_than_45deg_mm2": round(overhang, 1),
        "bridge_area_mm2": round(bridge_area, 0), "bridge_span_mm": bridge_span,
        "support_free": overhang < 10.0 and (bridge_span is None or bridge_span <= 45.0),
        "wall_thickness_p1_mm": round(p1, 2) if p1 else None,
    }


def bvh_of(ob, extra=None):
    bm = world_bm(ob, extra)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def min_gap(a, b, a_extra=None, b_extra=None, zmin=None):
    tb = bvh_of(b, b_extra)
    M = (a_extra or Matrix.Identity(4)) @ a.matrix_world
    best = 1e9
    for v in a.data.vertices:
        p = M @ v.co
        if zmin is not None and p.z < zmin:
            continue
        d = tb.find_nearest(p)[3]
        if d is not None and d < best:
            best = d
    return best


def interferes(a, b, lift=0.0, a_extra=None, b_extra=None):
    ea = Matrix.Translation((0, 0, lift)) @ (a_extra or Matrix.Identity(4))
    return len(bvh_of(a, ea).overlap(bvh_of(b, b_extra))) > 0


def divider_free(tray, n=24):
    """Drop rays into the tray on an n x n grid: each must land on the tray floor.
    Any internal wall or rib would stop a ray higher up."""
    t = bvh_of(tray)
    xi, yi = (TRAY_L - 2 * WALL) / 2 - 0.8, (TRAY_W - 2 * WALL) / 2 - 0.8
    zfloor = Z_SEAT + TRAY_FLOOR
    rays = bad = 0
    for i in range(n):
        for j in range(n):
            x, y = -xi + 2 * xi * i / (n - 1), -yi + 2 * yi * j / (n - 1)
            if abs(x) > xi - 3 and abs(y) > yi - 3:
                continue
            loc = t.ray_cast(Vector((x, y, Z_TRAY_TOP + 5)), Vector((0, 0, -1)), 500)[0]
            rays += 1
            if loc is None or abs(loc.z - zfloor) > 0.05:
                bad += 1
    return {"rays": rays, "rays_blocked_above_floor": bad, "divider_free": bad == 0}


def retention_estimate():
    """Beam estimate of the snap-tab hold (PLA E ~3.5 GPa, friction ~0.3). Order of magnitude."""
    R = LID_RETENTION
    E, mu = 3500.0, 0.3
    I = R["tab_width"] * LID_WALL ** 3 / 12
    F_r = 3 * E * I * R["engage"] / R["tab_length"] ** 3
    t = math.tan(math.radians(R["release_angle"]))
    F_rel = F_r * (t + mu) / (1 - mu * t)
    ti = math.tan(math.radians(R["insert_angle"]))
    F_ins = F_r * (ti + mu) / (1 - mu * ti)
    strain = 1.5 * LID_WALL * R["engage"] / R["tab_length"] ** 2
    return {"tab_radial_force_N": round(F_r, 1),
            "close_force_total_N": round(2 * F_ins, 1),
            "open_force_total_N": round(2 * F_rel, 1),
            "tab_root_strain_pct": round(100 * strain, 2)}


# ----------------------------------------------------------------------------
# EXPORT
# ----------------------------------------------------------------------------
def baked_mesh(ob, M):
    bm = world_bm(ob, M)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    verts = [tuple(v.co) for v in bm.verts]
    idx = {v: i for i, v in enumerate(bm.verts)}
    tris = [tuple(idx[v] for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, tris


def write_stl(path, meshes):
    with open(path, "wb") as fh:
        fh.write(b"FOX case".ljust(80, b" "))
        fh.write(struct.pack("<I", sum(len(t) for _, t in meshes)))
        for verts, tris in meshes:
            for t in tris:
                a, b, c = (Vector(verts[i]) for i in t)
                nrm = (b - a).cross(c - a)
                nrm = nrm.normalized() if nrm.length > 0 else nrm
                fh.write(struct.pack("<12fH", *nrm, *a, *b, *c, 0))


def write_3mf(path, objects):
    parts = []
    for i, (name, verts, tris) in enumerate(objects, start=1):
        vs = "".join('<vertex x="%.4f" y="%.4f" z="%.4f"/>' % v for v in verts)
        ts = "".join('<triangle v1="%d" v2="%d" v3="%d"/>' % t for t in tris)
        parts.append('<object id="%d" name="%s" type="model"><mesh><vertices>%s</vertices>'
                     '<triangles>%s</triangles></mesh></object>' % (i, name, vs, ts))
    items = "".join('<item objectid="%d"/>' % i for i in range(1, len(objects) + 1))
    model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<resources>%s</resources><build>%s</build></model>' % ("".join(parts), items))
    ctypes = ('<?xml version="1.0" encoding="UTF-8"?>'
              '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
              '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
              '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
              '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ctypes)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
def main(export=True, save=True):
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 0.001
    sc.unit_settings.length_unit = "MILLIMETERS"
    for cname in (COLL, "FOX_CASE_V1"):
        if cname in bpy.data.collections:
            c = bpy.data.collections[cname]
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            if cname != COLL:
                bpy.data.collections.remove(c)
    if COLL not in bpy.data.collections:
        sc.collection.children.link(bpy.data.collections.new(COLL))

    base, tray, lid, fit = build_base(), build_tray(), build_lid(), build_fit_test()
    fit.location.y = -(OUT_W + 40)
    build_proxies()
    bpy.context.view_layer.update()   # make .location changes live in matrix_world
    O = bpy.data.objects
    fox, sensor, chg, coil = O["PROXY_FOX"], O["PROXY_FOX_SensorFace"], O["PROXY_Charger"], O["PROXY_CableCoil"]

    # print orientations: base + tray upright, lid upside down (flat top on the bed)
    flip = Matrix.Translation((0, 0, Z_TOP)) @ Matrix.Rotation(math.pi, 4, "X")
    orient = {base: Matrix.Identity(4), tray: Matrix.Translation((0, 0, -Z_SEAT)),
              lid: flip, fit: Matrix.Translation((0, OUT_W + 40, 0))}
    cx, cy = A1_MINI_BED[0] / 2, A1_MINI_BED[1] / 2
    plates = {
        "plate_A_base_and_tray": {
            base: Matrix.Translation((cx, cy - (OUT_W + PLATE_GAP) / 2, 0)) @ orient[base],
            tray: Matrix.Translation((cx, cy + (TRAY_W + PLATE_GAP) / 2, 0)) @ orient[tray]},
        "plate_B_lid": {lid: Matrix.Translation((cx, cy, 0)) @ orient[lid]},
    }

    report = {"version": VERSION,
              "parameters": {k: v for k, v in globals().items()
                             if k.isupper() and isinstance(v, (int, float, tuple, dict))}}
    tin_l, tin_w, tin_r = TRAY_L - 2 * WALL, TRAY_W - 2 * WALL, TRAY_R - WALL
    report["derived"] = {
        "case_outer_mm": [round(OUT_L, 2), round(OUT_W, 2), round(TOTAL_CASE_HEIGHT, 2)],
        "height_change_vs_v2_mm": round(TOTAL_CASE_HEIGHT - V2_HEIGHT, 2),
        "fox_cavity_mm": [CAV_L, CAV_W, "R%.2f" % CAV_R],
        "fox_internal_height_mm": round(Z_SEAT - FLOOR, 2),
        "tray_inner_mm": [round(tin_l, 2), round(tin_w, 2), ACCESSORY_TRAY_HEIGHT, "R%.2f" % tin_r],
        "tray_inner_volume_cm3": round((tin_l * tin_w - (4 - math.pi) * tin_r ** 2) * ACCESSORY_TRAY_HEIGHT / 1000, 1),
        "finger_window_length_mm": round(2 * WINDOW_HALF, 2),
        "z_levels_mm": {"floor_top": FLOOR, "cradle_top_and_lid_mouth": Z_CRADLE,
                        "tray_underside": Z_SEAT, "tray_floor_top": round(Z_SEAT + TRAY_FLOOR, 2),
                        "tray_top": round(Z_TRAY_TOP, 2), "lid_ceiling": round(Z_LID_CEIL, 2),
                        "case_top": round(Z_TOP, 2)},
    }
    parts = {"base": base, "tray": tray, "lid": lid, "fit_test": fit}
    report["parts"] = {k: mesh_stats(o, orient[o]) for k, o in parts.items()}
    report["tray_divider_check"] = divider_free(tray)
    report["lid_retention"] = {
        "type": "2 cantilever snap tabs in the lid short ends + matching grooves in the base towers",
        "bump_overlap_with_tower_face_mm": LID_RETENTION["engage"],
        "closed_bump_sits_in_groove_without_clash": not interferes(lid, base, lift=0.02),
        **retention_estimate()}
    report["assembly"] = {
        "clash_base_tray(resting)": interferes(tray, base, lift=0.02),
        "clash_base_lid(resting)": interferes(lid, base, lift=0.02),
        "clash_tray_lid": interferes(tray, lid),
        "clash_fox_base(resting)": interferes(fox, base, lift=0.02),
        "clash_fox_tray": interferes(fox, tray),
        "clash_fox_lid": interferes(fox, lid),
        "clash_charger_tray(resting)": interferes(chg, tray, lift=0.02),
        "clash_cable_tray(resting)": interferes(coil, tray, lift=0.02),
        "clash_charger_lid": interferes(chg, lid),
        "clash_charger_cable": interferes(chg, coil),
        "clash_sensor_face_base": interferes(sensor, base),
        "gap_fox_proxy_side_to_cradle_mm": round(min_gap(fox, base, zmin=FLOOR + 2.5), 2),
        "gap_fox_proxy_top_to_tray_mm": round(min_gap(fox, tray), 2),
        "gap_tray_top_to_lid_mm": round(min_gap(tray, lid), 2),
        "gap_charger_top_to_lid_mm": round(min_gap(chg, lid), 2),
        "gap_sensor_face_to_base_mm": round(min_gap(sensor, base), 2),
        "gap_sensor_face_to_lid_mm": round(min_gap(sensor, lid), 2),
    }
    report["plates"] = {}
    for pname, objs in plates.items():
        pts = []
        for o, M in objs.items():
            bm = world_bm(o, M)
            pts += [v.co.copy() for v in bm.verts]
            bm.free()
        mn = [min(p[i] for p in pts) for i in range(3)]
        mx = [max(p[i] for p in pts) for i in range(3)]
        report["plates"][pname] = {"bbox_min": [round(v, 1) for v in mn], "bbox_max": [round(v, 1) for v in mx],
                                   "fits_bed": all(mn[i] >= 0 and mx[i] <= A1_MINI_BED[i] for i in range(3))}
    solid = sum(report["parts"][k]["pla_g_solid_est"] for k in ("base", "tray", "lid"))
    report["material"] = {"solid_equivalent_g": round(solid, 1),
                          "expected_sliced_g_3walls_15pct": [round(solid * 0.78), round(solid * 0.9)]}

    if export:
        os.makedirs(EXPORTS, exist_ok=True)
        for f in os.listdir(EXPORTS):
            if f.endswith((".stl", ".3mf")):
                os.remove(os.path.join(EXPORTS, f))
        names = {"base": "fox_case_v3_base.stl", "tray": "fox_case_v3_accessory_tray.stl",
                 "lid": "fox_case_v3_lid.stl", "fit_test": "fox_fit_test_cradle_ring_v3.stl"}
        for k, o in parts.items():
            write_stl(os.path.join(EXPORTS, names[k]), [baked_mesh(o, orient[o])])
        for pname, objs in plates.items():
            write_3mf(os.path.join(EXPORTS, "fox_case_v3_%s.3mf" % pname),
                      [(o.name, *baked_mesh(o, M)) for o, M in objs.items()])
        write_3mf(os.path.join(EXPORTS, "fox_case_v3_assembled.3mf"),
                  [(o.name, *baked_mesh(o, Matrix.Identity(4))) for o in (base, tray, lid)])
        with open(os.path.join(EXPORTS, "validation_report.json"), "w") as fh:
            json.dump(report, fh, indent=2, default=str)
    if save:
        os.makedirs(CAD, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CAD, "fox_case.blend"))
    return report


REPORT = main()
print(json.dumps(REPORT, indent=1, default=str))
