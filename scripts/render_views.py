"""
Render documentation views of the FOX case (Workbench, fast). Run AFTER
scripts/build_fox_case.py in the same Blender session, passing its globals as BUILD:
    g = {...}; exec(open(".../build_fox_case.py").read(), g)
    exec(open(".../render_views.py").read(), {"BUILD": g, "__file__": ...})
Outputs PNGs to renders/.
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
Z_TOP, Z_SEAT, Z_CRADLE = B.get("Z_TOP", 99.1), B.get("Z_SEAT", 38.5), B.get("Z_CRADLE", 10.0)
OUT_W = B.get("OUT_W", 82.5)

sc = bpy.context.scene
O = bpy.data.objects
PARTS = ["Base", "Tray", "Lid", "FitTest", "PROXY_FOX", "PROXY_FOX_SensorFace",
         "PROXY_Charger", "PROXY_CableCoil"]
COLORS = {"Base": (0.20, 0.23, 0.27, 1), "Tray": (0.45, 0.60, 0.75, 1), "Lid": (0.80, 0.82, 0.86, 1),
          "FitTest": (0.30, 0.70, 0.40, 1), "PROXY_FOX": (0.98, 0.55, 0.08, 1),
          "PROXY_FOX_SensorFace": (0.04, 0.04, 0.05, 1), "PROXY_Charger": (0.10, 0.10, 0.12, 1),
          "PROXY_CableCoil": (0.16, 0.16, 0.17, 1)}
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
sc.world.color = (0.94, 0.94, 0.95)
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
    """Boolean-cut copies of objects (for sections). Returns the copy names."""
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


case = ["Base", "Tray", "Lid"]
fox = ["PROXY_FOX", "PROXY_FOX_SensorFace"]
acc = ["PROXY_Charger", "PROXY_CableCoil"]

# 01 closed case
reset(); show(case)
shoot("01_closed_case.png", (0, 0, Z_TOP / 2), (1.0, -1.3, 0.8), dist=480, lens=55)

# 02 open case with the FOX inside (lid and tray set aside)
reset(); show(case + fox + acc)
O["Lid"].location = (0, 125, -Z_CRADLE)
O["Tray"].location = (150, 0, -Z_SEAT)
for n in acc:
    O[n].location.x += 150; O[n].location.z -= Z_SEAT
shoot("02_open_case_fox_inside.png", (60, 50, 20), (0.7, -1.3, 1.1), dist=720, lens=50)

# 03 accessory tray installed (lid off)
reset(); show(["Base", "Tray"] + fox + acc)
shoot("03_tray_installed.png", (0, 0, Z_SEAT), (0.9, -1.3, 1.1), dist=480, lens=55)

# 03b FOX in the cradle
reset(); show(["Base"] + fox)
shoot("03b_fox_in_cradle.png", (0, 0, 18), (0.9, -1.4, 1.0), dist=360, lens=55)

# 04 exploded: base -> FOX -> tray -> lid
reset(); show(case + fox + acc)
O["PROXY_FOX"].location.z += 25; O["PROXY_FOX_SensorFace"].location.z += 25
for n in ["Tray"] + acc:
    O[n].location.z += 70
O["Lid"].location.z += 140
shoot("04_exploded_stack.png", (0, 0, 115), (1.0, -1.3, 0.35), dist=820, lens=55)

# 05 section through the long axis: total stacked height
reset()
sec = cut_copies(case + fox + acc, (0, -100, 100), (400, 200, 400), "DOC_sec_")
show(sec)
shoot("05_section_stack_height.png", (0, 0, Z_TOP / 2), (0, -1, 0), ortho=200, dist=500)
shoot("05b_section_3q.png", (0, 0, Z_TOP / 2), (0.7, -1.2, 0.5), dist=460, lens=55)
drop(sec)

# 06 top-down proof: the tray is ONE open bin, no divider
reset(); show(["Tray"])
shoot("06_tray_top_no_divider.png", (0, 0, Z_SEAT), (0, 0, 1), ortho=135, dist=400)
show(["Tray"] + acc)
shoot("06b_tray_top_with_charger_and_cable.png", (0, 0, Z_SEAT), (0, 0, 1), ortho=135, dist=400)

# 07 lid retention: section through a snap tab (plane y = 0), close-up
reset()
tab = cut_copies(["Base", "Lid"], (0, -100, 100), (400, 200, 400), "DOC_tab_")
show(tab)
xl = B.get("OUT_L", 125.0) / 2
shoot("07_snap_tab_section.png", (xl - 6, 0, Z_CRADLE + 8), (0, -1, 0), ortho=34, dist=300)
drop(tab)
show(["Lid"])
shoot("07b_lid_underside_tabs.png", (0, 0, Z_TOP / 2), (0.8, -1.0, -0.9), dist=460, lens=55)

# 08 fit-test ring (V3 cavity)
reset(); show(["FitTest"] + fox)
O["FitTest"].location = (0, 0, B.get("FLOOR", 2.0))
shoot("08_fit_test_ring_v3.png", (0, 0, 15), (0.9, -1.4, 1.1), dist=360, lens=55)

# 09 print plates (A1 mini 180 x 180): A = base + tray, B = lid upside down
reset()
bed = bpy.data.objects.new("DOC_bed", bpy.data.meshes.new("DOC_bed"))
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=90); bm.to_mesh(bed.data); bm.free()
sc.collection.objects.link(bed); bed.color = (0.62, 0.62, 0.60, 1)
TRAY_W, PG = B.get("TRAY_W", 74.0), B.get("PLATE_GAP", 8.0)
O["Base"].location = (0, -(OUT_W + PG) / 2, 0)
O["Tray"].location = (0, (TRAY_W + PG) / 2, -Z_SEAT)
show(["DOC_bed", "Base", "Tray"])
shoot("09_plate_A_base_and_tray.png", (0, 0, 20), (0.45, -0.9, 1.0), dist=620, lens=50)
reset()
O["Lid"].rotation_euler = (math.pi, 0, 0)
O["Lid"].location = (0, 0, Z_TOP)
show(["DOC_bed", "Lid"])
shoot("09_plate_B_lid.png", (0, 0, 30), (0.45, -0.9, 1.0), dist=620, lens=50)
bpy.data.objects.remove(bed, do_unlink=True)

reset()
show(PARTS)
print(sorted(os.listdir(OUT)))
