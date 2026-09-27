"""
Render documentation views of the FOX case V1 (Workbench, fast, no lights needed).
Run AFTER scripts/build_fox_case.py in the same Blender session:
    exec(open("<repo>/scripts/render_views.py").read())
Outputs PNGs to renders/.
"""
import bpy, math, os
from mathutils import Vector, Matrix

try:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    ROOT = "/Users/joneswang/Downloads/code/3dmakerpro-fox-case"
OUT = os.path.join(ROOT, "renders")
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
O = bpy.data.objects
PARTS = ["Base", "Tray", "Lid", "FitTest", "PROXY_FOX", "PROXY_FOX_SensorFace",
         "PROXY_Charger", "PROXY_CableCoil"]
COLORS = {"Base": (0.20, 0.23, 0.27, 1), "Tray": (0.45, 0.60, 0.75, 1), "Lid": (0.80, 0.82, 0.86, 1),
          "FitTest": (0.30, 0.70, 0.40, 1), "PROXY_FOX": (0.98, 0.55, 0.08, 1),
          "PROXY_FOX_SensorFace": (0.04, 0.04, 0.05, 1), "PROXY_Charger": (0.10, 0.10, 0.12, 1),
          "PROXY_CableCoil": (0.16, 0.16, 0.17, 1)}
HOME = {n: O[n].location.copy() for n in PARTS}
Z_SEAT = 38.9  # informational; positions below are relative offsets

sc.render.engine = "BLENDER_WORKBENCH"
sh = sc.display.shading
sh.light = "STUDIO"
sh.color_type = "OBJECT"
sh.show_cavity = True
sh.cavity_type = "BOTH"
sh.show_object_outline = True
sh.show_shadows = False
sc.render.resolution_x = 1400
sc.render.resolution_y = 1000
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
        O[n].location = HOME[n]


def shoot(fname, target, direction, ortho=None, dist=600, lens=60):
    t = Vector(target)
    d = Vector(direction).normalized()
    cam.location = t + d * dist
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    if ortho:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = ortho
    else:
        cam_data.type = "PERSP"
        cam_data.lens = lens
    sc.render.filepath = os.path.join(OUT, fname)
    bpy.ops.render.render(write_still=True)


case = ["Base", "Tray", "Lid"]
fox = ["PROXY_FOX", "PROXY_FOX_SensorFace"]
acc = ["PROXY_Charger", "PROXY_CableCoil"]

# 1. closed case
reset(); show(case)
shoot("01_closed_case.png", (0, 0, 55), (1.0, -1.3, 0.9), dist=520, lens=55)

# 2. open case: lid set aside, tray lifted, everything visible
reset(); show(case + fox + acc)
O["Lid"].location = (0, 150, -10.4)          # lid set down beside (bottom edge on table)
for n in ["Tray"] + acc:
    O[n].location.z += 45
shoot("02_open_case.png", (0, 50, 60), (1.0, -1.4, 1.1), dist=720, lens=55)

# 3. FOX location in the base cradle (tray + lid removed)
reset(); show(["Base"] + fox)
shoot("03_fox_in_base_cradle.png", (0, 0, 18), (0.9, -1.4, 1.0), dist=380, lens=55)
shoot("03b_fox_in_base_top.png", (0, 0, 0), (0, 0, 1), ortho=150, dist=400)

# 4. accessory storage
reset(); show(["Tray"] + acc)
shoot("04_accessory_tray.png", (0, 0, 70), (0.6, -1.0, 1.6), dist=420, lens=55)

# 5. exploded stack
reset(); show(case + fox + acc)
O["Lid"].location.z += 190
for n in ["Tray"] + acc:
    O[n].location.z += 80
shoot("05_exploded_stack.png", (0, 0, 165), (1.0, -1.3, 0.35), dist=860, lens=55)

# 6. section view (cut copies at the YZ... plane through the long axis, front half removed)
reset()
sec = []
cutter = bpy.data.objects.new("DOC_cut", bpy.data.meshes.new("DOC_cut"))
import bmesh
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
bm.to_mesh(cutter.data); bm.free()
cutter.scale = (400, 200, 400)
cutter.location = (0, -100, 100)
sc.collection.objects.link(cutter)
bpy.context.view_layer.update()
for n in case + fox + acc:
    c = O[n].copy(); c.data = O[n].data.copy(); c.name = "DOC_sec_" + n
    sc.collection.objects.link(c)
    c.hide_viewport = False
    m = c.modifiers.new("cut", "BOOLEAN"); m.operation = "DIFFERENCE"; m.solver = "EXACT"; m.object = cutter
    bpy.context.view_layer.objects.active = c
    bpy.ops.object.modifier_apply(modifier="cut")
    c.color = COLORS[n]
    sec.append(c.name)
bpy.data.objects.remove(cutter, do_unlink=True)
show(sec)
shoot("06_section_long_axis.png", (0, 0, 57), (0, -1, 0), ortho=190, dist=500)
shoot("06b_section_3q.png", (0, 0, 57), (0.7, -1.2, 0.5), dist=520, lens=55)
for n in sec:
    bpy.data.objects.remove(O[n], do_unlink=True)

# 7. fit-test ring over the FOX
reset(); show(["FitTest"] + fox)
O["FitTest"].location = (0, 0, 2.4)
shoot("07_fit_test_ring.png", (0, 0, 15), (0.9, -1.4, 1.1), dist=380, lens=55)

# 8. the single A1 mini plate: base + lid with the tray nested inside it
reset()
bed = bpy.data.objects.new("DOC_bed", bpy.data.meshes.new("DOC_bed"))
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=90); bm.to_mesh(bed.data); bm.free()
sc.collection.objects.link(bed); bed.color = (0.62, 0.62, 0.60, 1)
g = globals().get("BUILD", {})
PB = g.get("PLATE_BASE_CENTER", (90, 135)); PL = g.get("PLATE_LID_CENTER", (90, 45))
ZC = g.get("Z_CRADLE", 10.4); ZS = g.get("Z_SEAT", 38.9)
place = {"Base": (PB[0] - 90, PB[1] - 90, 0), "Lid": (PL[0] - 90, PL[1] - 90, -ZC),
         "Tray": (PL[0] - 90, PL[1] - 90, -ZS)}
for n, loc in place.items():
    O[n].location = loc
show(["DOC_bed", "Base", "Lid", "Tray"])
shoot("08_one_plate_A1mini.png", (0, 0, 40), (0.45, -0.9, 1.0), dist=700, lens=50)
shoot("08b_one_plate_top.png", (0, 0, 0), (0, 0, 1), ortho=200, dist=600)

# 9. print progress: the same plate cut at several heights (layers grow from the bed up)
import bmesh as _bm
frames = [2.4, 10.4, 41.4, 71.0, 105.0, 125.0]
for k, h in enumerate(frames):
    names = []
    cut = bpy.data.objects.new("DOC_zcut", bpy.data.meshes.new("DOC_zcut"))
    b = _bm.new(); _bm.ops.create_cube(b, size=1.0); b.to_mesh(cut.data); b.free()
    cut.scale = (400, 400, 400); cut.location = (0, 0, h + 200)
    sc.collection.objects.link(cut)
    bpy.context.view_layer.update()   # make the cutter's transform live before applying
    for n in ("Base", "Lid", "Tray"):
        c = O[n].copy(); c.data = O[n].data.copy(); c.name = "DOC_p_" + n
        sc.collection.objects.link(c)
        c.hide_viewport = False   # modifier_apply silently fails on hidden objects
        m = c.modifiers.new("cut", "BOOLEAN"); m.operation = "DIFFERENCE"; m.solver = "EXACT"; m.object = cut
        bpy.context.view_layer.objects.active = c
        bpy.ops.object.modifier_apply(modifier="cut")
        c.color = COLORS[n]
        names.append(c.name)
    bpy.data.objects.remove(cut, do_unlink=True)
    show(["DOC_bed"] + names)
    shoot("09_print_progress_%d_z%03d.png" % (k + 1, round(h)), (0, 0, 35), (0.45, -0.9, 1.0), dist=700, lens=50)
    for n in names:
        bpy.data.objects.remove(O[n], do_unlink=True)
bpy.data.objects.remove(bed, do_unlink=True)

# restore scene for the saved .blend
reset()
show(PARTS)
O["Lid"].hide_viewport = False
print(sorted(os.listdir(OUT)))
