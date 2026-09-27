"""
3DMakerpro FOX carrying case - V2 "one plate" parametric build script for Blender (5.1.2).

Run either way:
  * Blender MCP / Text Editor:  exec(open("<repo>/scripts/build_fox_case.py").read())
  * Headless:  /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/build_fox_case.py

Units: 1 Blender unit = 1 mm. Everything is rebuilt from the parameters below.

Architecture (stacked, see docs/design.md):
    LID  (sleeve with a 45-deg chamfered roof; covers tray + scanner zone)
    TRAY (open accessory bin, sits on the base end towers between locating lips)
    FOX  (lies flat in a shallow cradle; long sides open above CRADLE_H for fingers)
    BASE (floor + band + two end towers that carry the tray)

Printing (the V2 driver): the WHOLE case prints on ONE Bambu A1 mini plate
(180 x 180 mm), with no supports, every part in its in-use orientation:
    * BASE upright (floor on bed)
    * LID  upright, mouth on the bed. Its roof is 45-deg chamfers (self-supporting)
      plus a short flat bridge, so the lid needs nothing underneath it...
    * ...which leaves the bed inside the lid free: the TRAY prints NESTED inside the lid.
    Plate = [BASE] + [LID with TRAY inside]  ->  125 x 174 mm of the 180 x 180 bed.
"""
import bpy, bmesh, math, os, json, zipfile
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

# ----------------------------------------------------------------------------
# PARAMETERS (mm)
# ----------------------------------------------------------------------------
# FOX design envelope. Best photo estimate ~111 x 70 x 33; manufacturer spec
# 115 x 70 x 35; third-party stand has 113.0 mm between its end lips.
FOX_LENGTH = 113.0
FOX_WIDTH = 70.0
FOX_HEIGHT = 35.0
FOX_CORNER_R = 4.0        # plan-view corner radius (cavity tolerates 1..10 mm)

FOX_CLEARANCE_XY = 1.25   # per side, scanner -> cradle wall
FOX_CLEARANCE_Z = 1.5     # scanner top -> tray underside

FLOOR = 2.4               # base floor thickness
CRADLE_H = 8.0            # long-side capture height above floor (below sensor window)
WALL = 2.0                # base tower walls and tray walls
LID_WALL = 2.4            # lid wall, measured normal to the surface (also on the roof)
LID_CLEARANCE = 0.35      # per side, lid sleeve -> base towers
LID_TOP = 2.4             # flat roof thickness
LID_TOP_GAP = 1.5         # tray rim edge -> lid roof, vertical (limits tray lift)
ROOF_CHAMFER = 20.0       # 45-deg roof chamfer (outer). Larger = shorter bridge, taller case
MAX_BRIDGE = 45.0         # sanity limit for the flat-roof bridge span

WINDOW_STUB = 4.0         # straight tower stub kept on each long side past the corner arc
WINDOW_FILLET = 5.0       # radius at the bottom corners of the finger windows

LIP_H = 2.5               # tray-locating lips on tower tops
LIP_T = 1.2
TRAY_CLEARANCE = 0.3      # per side, tray -> lips
TRAY_FLOOR = 2.0
# Accessory volume requirement = the original black accessory box (charger + cable),
# per user direction. Measured ~180 x 68 x 44 mm (photos 174530/174542/174550).
# The tray's own inner volume must be >= this; the roof headspace is extra slack.
ACCESSORY_BOX = (180.0, 68.0, 44.0)
ACCESSORY_VOLUME_TARGET = ACCESSORY_BOX[0] * ACCESSORY_BOX[1] * ACCESSORY_BOX[2]  # mm^3
ACCESSORY_HEIGHT = None   # None = derive from ACCESSORY_VOLUME_TARGET; or a depth in mm

FIT_TEST_H = 10.0         # fit-test ring height
FIT_TEST_WALL = 2.0

# edge treatments (all chosen to print cleanly)
CH_BED = 0.6              # elephant-foot chamfer on outer bed edges
CH_GROOVE = 1.0           # chamfer on base band top edge (thumb groove at the joint)
LID_MOUTH_RELIEF = 0.4    # tiny chamfers at the lid mouth (it sits on the bed)
LIP_LEADIN = 0.6          # outer top chamfer on the lips: guides the lid down
SEG = 16                  # segments per 90 deg corner

# print plate
A1_MINI_BED = (180.0, 180.0, 180.0)
PLATE_GAP = 8.0           # gap between the two footprints on the plate
NEST_MIN_GAP = 1.5        # min horizontal gap tray <-> lid when printed nested

# ----------------------------------------------------------------------------
# DERIVED DIMENSIONS
# ----------------------------------------------------------------------------
SQ2 = math.sqrt(2.0)
CAV_L = FOX_LENGTH + 2 * FOX_CLEARANCE_XY
CAV_W = FOX_WIDTH + 2 * FOX_CLEARANCE_XY
CAV_R = FOX_CORNER_R + FOX_CLEARANCE_XY

TOWER_L = CAV_L + 2 * WALL                     # base tower outer
TOWER_W = CAV_W + 2 * WALL
TOWER_R = CAV_R + WALL

OUT_L = TOWER_L + 2 * (LID_CLEARANCE + LID_WALL)   # case outer footprint
OUT_W = TOWER_W + 2 * (LID_CLEARANCE + LID_WALL)
OUT_R = TOWER_R + LID_CLEARANCE + LID_WALL

Z_CRADLE = FLOOR + CRADLE_H                     # band top = window bottom = lid mouth
Z_SEAT = FLOOR + FOX_HEIGHT + FOX_CLEARANCE_Z   # tray underside
TRAY_INSET = LIP_T + TRAY_CLEARANCE             # tray outer vs tower outer
TRAY_L = TOWER_L - 2 * TRAY_INSET
TRAY_W = TOWER_W - 2 * TRAY_INSET
TRAY_R = TOWER_R - TRAY_INSET


def _rr_area(L, W, R):
    return L * W - (4 - math.pi) * R * R


TRAY_INNER_AREA = _rr_area(TRAY_L - 2 * WALL, TRAY_W - 2 * WALL, TRAY_R - WALL)
if ACCESSORY_HEIGHT is None:
    ACCESSORY_HEIGHT = math.ceil(ACCESSORY_VOLUME_TARGET / TRAY_INNER_AREA)
TRAY_H = TRAY_FLOOR + ACCESSORY_HEIGHT
Z_TRAY_TOP = Z_SEAT + TRAY_H

# Lid roof: inner 45-deg surface must pass LID_TOP_GAP above the tray's outer rim edge,
# which sits NEST (= tray inset + lid clearance) inside the lid's inner wall.
NEST = TRAY_INSET + LID_CLEARANCE
Z_ROOF_IN = Z_TRAY_TOP + LID_TOP_GAP - NEST     # inner roof starts here at the inner wall
Z_ROOF_OUT = Z_ROOF_IN + LID_WALL * (SQ2 - 1)   # outer roof starts (normal wall thickness kept)
Z_TOP = Z_ROOF_OUT + ROOF_CHAMFER
Z_CEIL = Z_TOP - LID_TOP
ROOF_CHAMFER_IN = Z_CEIL - Z_ROOF_IN
LID_IN_W = TOWER_W + 2 * LID_CLEARANCE
BRIDGE_SPAN = LID_IN_W - 2 * ROOF_CHAMFER_IN    # flat ceiling short side (printed as bridge)
WINDOW_HALF = CAV_L / 2 - CAV_R - WINDOW_STUB

# plate positions (bed coordinates, origin at bed corner)
PLATE_LID_CENTER = (A1_MINI_BED[0] / 2, A1_MINI_BED[1] / 2 - (OUT_W + PLATE_GAP) / 2)
PLATE_BASE_CENTER = (A1_MINI_BED[0] / 2, A1_MINI_BED[1] / 2 + (OUT_W + PLATE_GAP) / 2)

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
    """Solid made of rounded-rect loops. profile = [(z, offset), ...] ascending z.
    A negative offset shrinks the loop (true 2D offset: radius shrinks too), so
    a 1:1 dz/offset gives an exact 45-deg chamfer."""
    # insert a loop exactly where the corner radius reaches zero, so the offset stays
    # exact (45 deg everywhere) instead of interpolating an arc into a sharp corner
    prof = [profile[0]]
    for (z0, d0), (z1, d1) in zip(profile[:-1], profile[1:]):
        dstar = 0.05 - R
        if (d0 - dstar) * (d1 - dstar) < 0:
            prof.append((z0 + (dstar - d0) / (d1 - d0) * (z1 - z0), dstar))
        prof.append((z1, d1))
    bm = bmesh.new()
    loops = []
    for z, d in prof:
        loops.append([bm.verts.new((x, y, z)) for x, y in rr_loop(L + 2 * d, W + 2 * d, R + d)])
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
    # tray-locating lips: 1.2 mm outer ring on the tower tops, outer lead-in chamfer
    lip = loft_rr("t_lip", TOWER_L, TOWER_W, TOWER_R,
                  [(Z_SEAT - 0.01, 0), (Z_SEAT + LIP_H - LIP_LEADIN, 0), (Z_SEAT + LIP_H, -LIP_LEADIN)])
    lip_in = prism_rr("t_lipin", TOWER_L - 2 * LIP_T, TOWER_W - 2 * LIP_T, TOWER_R - LIP_T,
                      Z_SEAT - 0.5, Z_SEAT + LIP_H + 1)
    boolean(lip, lip_in, "DIFFERENCE")
    boolean(band, lip, "UNION")
    cav = prism_rr("t_cav", CAV_L, CAV_W, CAV_R, FLOOR, Z_TOP + 10)
    boolean(band, cav, "DIFFERENCE")
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
    """Printed exactly as used: mouth on the bed, 45-deg roof, short flat bridge."""
    r = LID_MOUTH_RELIEF
    lid = loft_rr("Lid", OUT_L, OUT_W, OUT_R,
                  [(Z_CRADLE, -r), (Z_CRADLE + r, 0), (Z_ROOF_OUT, 0), (Z_TOP, -ROOF_CHAMFER)])
    c = LID_CLEARANCE
    inner = loft_rr("t_lin", TOWER_L, TOWER_W, TOWER_R,
                    [(Z_CRADLE - 1, c + r + 1), (Z_CRADLE + r, c), (Z_ROOF_IN, c),
                     (Z_CEIL, c - ROOF_CHAMFER_IN)])
    boolean(lid, inner, "DIFFERENCE")
    return lid


def build_fit_test():
    ring = loft_rr("FitTest", CAV_L + 2 * FIT_TEST_WALL, CAV_W + 2 * FIT_TEST_WALL, CAV_R + FIT_TEST_WALL,
                   [(0, -CH_BED), (CH_BED, 0), (FIT_TEST_H, 0)])
    hole = loft_rr("t_fh", CAV_L, CAV_W, CAV_R,
                   [(-1, 1 + 0.5), (0.5, 0), (FIT_TEST_H + 1, 0)])  # anti-elephant-foot flare
    boolean(ring, hole, "DIFFERENCE")
    return ring


def build_proxies():
    """Non-printed reference bodies for clearance checks and renders."""
    fox = loft_rr("PROXY_FOX", FOX_LENGTH, FOX_WIDTH, FOX_CORNER_R,
                  [(FLOOR, -2.0), (FLOOR + 2.0, 0), (FLOOR + FOX_HEIGHT - 4.0, 0), (FLOOR + FOX_HEIGHT, -4.0)])
    sensor = box("PROXY_FOX_SensorFace", -FOX_LENGTH / 2 + 8, FOX_LENGTH / 2 - 8,
                 -FOX_WIDTH / 2 - 0.2, -FOX_WIDTH / 2 + 1.5, FLOOR + 9, FLOOR + FOX_HEIGHT - 7)
    chg = loft_rr("PROXY_Charger", 52, 52, 6, [(Z_SEAT + TRAY_FLOOR, 0), (Z_SEAT + TRAY_FLOOR + 32, 0)])
    chg.location.x = TRAY_L / 2 - WALL - 26 - 1.5
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
    # down-facing surfaces in print orientation
    overhang, bridge, bed = 0.0, [], 0.0
    for f in bm.faces:
        c = f.calc_center_median()
        a = f.calc_area()
        if f.normal.z < -0.99 and c.z <= zmin + 0.05:
            bed += a                              # first-layer contact
        elif f.normal.z < -0.99:
            bridge.append(f)                      # flat ceiling, printed as a bridge
        elif f.normal.z < -0.7075:
            overhang += a                         # steeper than 45 deg: would need support
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
        "volume_cm3": round(vol / 1000, 2), "pla_g_solid_est": round(vol / 1000 * 1.24, 1),
        "size_print_mm": [round(s, 2) for s in size],
        "first_layer_contact_mm2": round(bed, 0),
        "overhang_steeper_than_45deg_mm2": round(overhang, 1),
        "bridge_area_mm2": round(bridge_area, 0), "bridge_span_mm": bridge_span,
        # < 10 mm2 tolerance: the only steeper facets are slivers along the 4 hip valleys of
        # the lid roof (concave inside corners where two 45-deg faces meet) - self-supporting.
        "support_free": overhang < 10.0 and (bridge_span is None or bridge_span <= MAX_BRIDGE),
        "wall_thickness_p1_mm": round(p1, 2) if p1 else None,
    }


def bvh_of(ob, extra=None):
    bm = world_bm(ob, extra)
    t = BVHTree.FromBMesh(bm)
    bm.free()
    return t


def min_gap(a, b, a_extra=None, b_extra=None, zmin=None):
    """Smallest distance from a's vertices (optionally only above zmin) to b's surface."""
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
    """True if a and b overlap. lift raises `a` first so parts that merely rest on
    each other (lid on shoulder, scanner on floor) are not reported as clashing."""
    ea = Matrix.Translation((0, 0, lift)) @ (a_extra or Matrix.Identity(4))
    return len(bvh_of(a, ea).overlap(bvh_of(b, b_extra))) > 0


# ----------------------------------------------------------------------------
# EXPORT
# ----------------------------------------------------------------------------
def baked_mesh(ob, M):
    """Triangulated (verts, tris) of ob transformed by M."""
    bm = world_bm(ob, M)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    verts = [tuple(v.co) for v in bm.verts]
    idx = {v: i for i, v in enumerate(bm.verts)}
    tris = [tuple(idx[v] for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, tris


def write_stl(path, meshes):
    import struct
    with open(path, "wb") as fh:
        fh.write(b"FOX case".ljust(80, b" "))
        n = sum(len(t) for _, t in meshes)
        fh.write(struct.pack("<I", n))
        for verts, tris in meshes:
            for t in tris:
                a, b, c = (Vector(verts[i]) for i in t)
                nrm = (b - a).cross(c - a)
                nrm = nrm.normalized() if nrm.length > 0 else nrm
                fh.write(struct.pack("<12fH", *nrm, *a, *b, *c, 0))


def write_3mf(path, objects):
    """Minimal 3MF core file: objects = [(name, verts, tris)] already in bed coordinates."""
    parts = []
    for i, (name, verts, tris) in enumerate(objects, start=1):
        vs = "".join('<vertex x="%.4f" y="%.4f" z="%.4f"/>' % v for v in verts)
        ts = "".join('<triangle v1="%d" v2="%d" v3="%d"/>' % t for t in tris)
        parts.append('<object id="%d" name="%s" type="model"><mesh><vertices>%s</vertices>'
                     '<triangles>%s</triangles></mesh></object>' % (i, name, vs, ts))
    items = "".join('<item objectid="%d"/>' % i for i in range(1, len(objects) + 1))
    model = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model unit="millimeter" xml:lang="en-US" '
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
    fox = bpy.data.objects["PROXY_FOX"]
    sensor = bpy.data.objects["PROXY_FOX_SensorFace"]
    chg = bpy.data.objects["PROXY_Charger"]
    coil = bpy.data.objects["PROXY_CableCoil"]

    # print orientation = use orientation for every part; just drop each to z=0
    orient = {
        base: Matrix.Identity(4),
        tray: Matrix.Translation((0, 0, -Z_SEAT)),
        lid: Matrix.Translation((0, 0, -Z_CRADLE)),
        fit: Matrix.Translation((0, OUT_W + 40, 0)),
    }
    # the single A1 mini plate: base + (lid with tray nested inside)
    plate = {
        base: Matrix.Translation((*PLATE_BASE_CENTER, 0)) @ orient[base],
        lid: Matrix.Translation((*PLATE_LID_CENTER, 0)) @ orient[lid],
        tray: Matrix.Translation((*PLATE_LID_CENTER, 0)) @ orient[tray],
    }

    report = {"parameters": {k: v for k, v in globals().items()
                             if k.isupper() and isinstance(v, (int, float, tuple))}}
    tin = loft_rr("t_meas", TRAY_L - 2 * WALL, TRAY_W - 2 * WALL, TRAY_R - WALL, [(0, 0), (ACCESSORY_HEIGHT, 0)])
    bm = world_bm(tin)
    tray_vol = bm.calc_volume() / 1000
    bm.free()
    bpy.data.objects.remove(tin, do_unlink=True)
    report["derived"] = {
        "cavity_mm": [round(CAV_L, 2), round(CAV_W, 2), "R%.2f" % CAV_R],
        "case_outer_mm": [round(OUT_L, 2), round(OUT_W, 2), round(Z_TOP, 2)],
        "tray_inner_mm": [round(TRAY_L - 2 * WALL, 2), round(TRAY_W - 2 * WALL, 2), ACCESSORY_HEIGHT],
        "tray_usable_volume_cm3": round(tray_vol, 1),
        "accessory_target_cm3": round(ACCESSORY_VOLUME_TARGET / 1000, 1),
        "finger_window_length_mm": round(2 * WINDOW_HALF, 2),
        "lid_roof_bridge_span_mm": round(BRIDGE_SPAN, 1),
        "z_levels_mm": {"floor_top": FLOOR, "cradle_top_and_lid_mouth": Z_CRADLE,
                        "tray_underside": Z_SEAT, "tray_top": round(Z_TRAY_TOP, 2),
                        "lid_roof_start_outer": round(Z_ROOF_OUT, 2), "case_top": round(Z_TOP, 2)},
    }
    parts = {"base": base, "tray": tray, "lid": lid, "fit_test": fit}
    report["parts"] = {k: mesh_stats(o, orient[o]) for k, o in parts.items()}

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
        "gap_fox_side_to_base_mm": round(min_gap(fox, base, zmin=FLOOR + 2.5), 2),
        "gap_fox_top_to_tray_mm": round(min_gap(fox, tray), 2),
        "gap_fox_to_lid_mm": round(min_gap(fox, lid), 2),
        "gap_tray_to_lid_mm": round(min_gap(tray, lid), 2),
        "gap_sensor_face_to_base_mm": round(min_gap(sensor, base), 2),
        "gap_sensor_face_to_lid_mm": round(min_gap(sensor, lid), 2),
    }

    # plate checks
    pts = []
    for o, M in plate.items():
        bm = world_bm(o, M)
        pts += [v.co.copy() for v in bm.verts]
        bm.free()
    pmin = [min(p[i] for p in pts) for i in range(3)]
    pmax = [max(p[i] for p in pts) for i in range(3)]
    report["plate"] = {
        "layout": "single A1 mini plate: base + lid with tray printed nested inside it",
        "bbox_min_mm": [round(v, 2) for v in pmin], "bbox_max_mm": [round(v, 2) for v in pmax],
        "fits_bed": all(pmin[i] >= 0 and pmax[i] <= A1_MINI_BED[i] for i in range(3)),
        "clash_base_vs_lid": interferes(base, lid, a_extra=plate[base] @ Matrix.Identity(4),
                                        b_extra=plate[lid]),
        "clash_tray_vs_lid_nested": interferes(tray, lid, a_extra=plate[tray], b_extra=plate[lid]),
        "nested_gap_tray_to_lid_mm": round(min_gap(tray, lid, plate[tray], plate[lid]), 2),
        "gap_base_to_lid_mm": round(min_gap(base, lid, plate[base], plate[lid]), 2),
        "tallest_part_mm": round(pmax[2] - pmin[2], 2),
    }
    report["plate"]["nested_gap_ok"] = report["plate"]["nested_gap_tray_to_lid_mm"] >= NEST_MIN_GAP

    if export:
        os.makedirs(EXPORTS, exist_ok=True)
        for f in os.listdir(EXPORTS):
            if f.endswith((".stl", ".3mf")):
                os.remove(os.path.join(EXPORTS, f))
        names = {"base": "fox_case_base.stl", "tray": "fox_case_accessory_tray.stl",
                 "lid": "fox_case_lid.stl", "fit_test": "fox_fit_test_cradle_ring.stl"}
        for k, o in parts.items():
            v, t = baked_mesh(o, orient[o])
            write_stl(os.path.join(EXPORTS, names[k]), [(v, t)])
        plate_objs = [("Base", *baked_mesh(base, plate[base])),
                      ("Lid", *baked_mesh(lid, plate[lid])),
                      ("AccessoryTray (nested in lid)", *baked_mesh(tray, plate[tray]))]
        write_3mf(os.path.join(EXPORTS, "fox_case_A1mini_one_plate.3mf"), plate_objs)
        write_stl(os.path.join(EXPORTS, "fox_case_A1mini_one_plate.stl"),
                  [(v, t) for _, v, t in plate_objs])
        with open(os.path.join(EXPORTS, "validation_report.json"), "w") as fh:
            json.dump(report, fh, indent=2, default=str)

    if save:
        os.makedirs(CAD, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(CAD, "fox_case.blend"))
    return report


REPORT = main()
print(json.dumps(REPORT, indent=1, default=str))
