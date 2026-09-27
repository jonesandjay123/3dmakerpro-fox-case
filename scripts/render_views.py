"""
Render documentation views of the FOX case (Workbench, fast). Run AFTER
scripts/build_fox_case.py in the same Blender session, passing its globals as BUILD
(scripts/run_all.py does this). Outputs PNGs to renders/.
"""
import bpy, bmesh, math, os
from mathutils import Vector

try:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    ROOT = "/Users/joneswang/Downloads/code/3dmakerpro-fox-case"
OUT = os.path.join(ROOT, "renders")
os.makedirs(OUT, exist_ok=True)
B = globals().get("BUILD", {})
Z_TOP, Z_CRADLE, FLOOR = B.get("Z_TOP", 40.9), B.get("Z_CRADLE", 10.0), B.get("FLOOR", 2.0)
OUT_L, OUT_W, PG = B.get("OUT_L", 125.0), B.get("OUT_W", 82.5), B.get("PLATE_GAP", 8.0)

sc = bpy.context.scene
O = bpy.data.objects
PARTS = ["Base", "Lid", "FitTest", "PROXY_FOX", "PROXY_FOX_SensorFace"]
# V4 palette: charcoal base, teal lid (distinct from the grey V1-V3 full-kit renders)
COLORS = {"Base": (0.17, 0.19, 0.22, 1), "Lid": (0.13, 0.47, 0.52, 1), "FitTest": (0.30, 0.70, 0.40, 1),
          "PROXY_FOX": (0.98, 0.55, 0.08, 1), "PROXY_FOX_SensorFace": (0.04, 0.04, 0.05, 1)}
HOME = {n: O[n].location.copy() for n in PARTS}
HOME_ROT = {n: O[n].rotation_euler.copy() for n in PARTS}

sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light, sh.color_type = "STUDIO", "OBJECT"
sh.show_cavity, sh.cavity_type = True, "BOTH"
sh.show_object_outline, sh.show_shadows = True, False
sc.render.resolution_x, sc.render.resolution_y = 1400, 1000
sc.render.film_transparent = False
if sc.world is None:
    sc.world = bpy.data.worlds.new("World")
sc.world.color = (0.95, 0.95, 0.94)
sc.view_settings.view_transform = "Standard"
for n, c in COLORS.items():
    O[n].color = c

cam_data = bpy.data.cameras.get("DOC_cam") or bpy.data.cameras.new("DOC_cam")
cam = O.get("DOC_cam") or bpy.data.objects.new("DOC_cam", cam_data)
if cam.name not in sc.collection.objects:
    sc.collection.objects.link(cam)
sc.camera = cam
cam_data.clip_end = 5000


def show(names):
    for o in sc.objects:
        if o.type == "MESH":
            o.hide_render = o.name not in names
            o.hide_viewport = o.name not in names


def reset():
    for n in PARTS:
        O[n].location, O[n].rotation_euler = HOME[n].copy(), HOME_ROT[n].copy()
    bpy.context.view_layer.update()


def shoot(fname, target, direction, ortho=None, dist=600, lens=60):
    bpy.context.view_layer.update()
    t, d = Vector(target), Vector(direction).normalized()
    cam.location = t + d * dist
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    if ortho:
        cam_data.type, cam_data.ortho_scale = "ORTHO", ortho
    else:
        cam_data.type, cam_data.lens = "PERSP", lens
    sc.render.filepath = os.path.join(OUT, fname)
    bpy.ops.render.render(write_still=True)


def cut_copies(names, cutter_loc, cutter_scale, prefix):
    cutter = bpy.data.objects.new(prefix + "cut", bpy.data.meshes.new(prefix + "cut"))
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(cutter.data); bm.free()
    cutter.scale, cutter.location = cutter_scale, cutter_loc
    sc.collection.objects.link(cutter)
    bpy.context.view_layer.update()
    out = []
    for n in names:
        c = O[n].copy(); c.data = O[n].data.copy(); c.name = prefix + n
        sc.collection.objects.link(c)
        c.hide_viewport = False          # modifier_apply silently fails on hidden objects
        m = c.modifiers.new("cut", "BOOLEAN"); m.operation = "DIFFERENCE"; m.solver = "EXACT"; m.object = cutter
        bpy.context.view_layer.objects.active = c
        bpy.ops.object.modifier_apply(modifier="cut")
        c.color = COLORS[n]
        out.append(c.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return out


def drop(names):
    for n in names:
        bpy.data.objects.remove(O[n], do_unlink=True)


case = ["Base", "Lid"]
fox = ["PROXY_FOX", "PROXY_FOX_SensorFace"]

# 01 closed case
reset(); show(case)
shoot("01_closed_case.png", (0, 0, Z_TOP / 2), (1.0, -1.3, 0.8), dist=420, lens=55)

# 02 open case with the FOX inside (lid set down beside it)
reset(); show(case + fox)
O["Lid"].location = (0, OUT_W + 25, -Z_CRADLE)
shoot("02_open_case_fox_inside.png", (0, (OUT_W + 25) / 2, 10), (0.8, -1.3, 1.2), dist=520, lens=50)

# 03 finger access: FOX pinched and lifted out through the long-side windows
reset(); show(["Base"] + fox)
for n in fox:
    O[n].location.z += 16
    O[n].rotation_euler = (0, math.radians(-6), 0)
shoot("03_finger_access_lift_out.png", (0, 0, 18), (0.35, -1.3, 0.55), dist=330, lens=55)
reset(); show(["Base"] + fox)
shoot("03b_fox_in_cradle.png", (0, 0, 12), (0.9, -1.4, 1.0), dist=330, lens=55)

# 04 exploded: base -> FOX -> lid
reset(); show(case + fox)
for n in fox:
    O[n].location.z += 22
O["Lid"].location.z += 62
shoot("04_exploded.png", (0, 0, 55), (1.0, -1.3, 0.45), dist=560, lens=55)

# 05 side section through the case: scanner clearance and total height
reset()
sec = cut_copies(case + fox, (0, -100, 100), (400, 200, 400), "DOC_sec_")
show(sec)
shoot("05_section_clearance.png", (0, 0, Z_TOP / 2), (0, -1, 0), ortho=200, dist=500)
shoot("05b_section_3q.png", (0, 0, Z_TOP / 2), (0.7, -1.2, 0.55), dist=380, lens=55)
drop(sec)
sec = cut_copies(case + fox, (-100, 0, 100), (200, 400, 400), "DOC_sx_")   # cross-section
show(sec)
shoot("05c_cross_section_width.png", (0, 0, Z_TOP / 2), (1, 0, 0), ortho=120, dist=500)
drop(sec)

# 06 one A1 mini plate: base upright + lid upside down, side by side
reset()
bed = bpy.data.objects.new("DOC_bed", bpy.data.meshes.new("DOC_bed"))
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=90); bm.to_mesh(bed.data); bm.free()
sc.collection.objects.link(bed); bed.color = (0.62, 0.62, 0.60, 1)
O["Base"].location = (0, -(OUT_W + PG) / 2, 0)
O["Lid"].rotation_euler = (math.pi, 0, 0)
O["Lid"].location = (0, (OUT_W + PG) / 2, Z_TOP)
show(["DOC_bed", "Base", "Lid"])
shoot("06_one_plate_A1mini.png", (0, 0, 15), (0.45, -0.9, 1.0), dist=560, lens=50)
shoot("06b_one_plate_top.png", (0, 0, 0), (0, 0, 1), ortho=260, dist=400)
bpy.data.objects.remove(bed, do_unlink=True)

# 07 lid retention: section through a snap tab (plane y = 0) and lid underside
reset()
tab = cut_copies(case, (0, -100, 100), (400, 200, 400), "DOC_tab_")
show(tab)
shoot("07_snap_tab_section.png", (OUT_L / 2 - 6, 0, Z_CRADLE + 8), (0, -1, 0), ortho=34, dist=300)
drop(tab)
reset(); show(["Lid"])
shoot("07b_lid_underside_tabs.png", (0, 0, Z_TOP / 2), (0.8, -1.0, -0.9), dist=400, lens=55)

# 08 optional reference fit ring (same cavity)
reset(); show(["FitTest"] + fox)
O["FitTest"].location = (0, 0, FLOOR)
shoot("08_fit_test_ring.png", (0, 0, 15), (0.9, -1.4, 1.1), dist=330, lens=55)

reset()
show(PARTS)
print(sorted(os.listdir(OUT)))
