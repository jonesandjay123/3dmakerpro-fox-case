"""
Stamp final dimensions onto the documentation renders, reading exports/validation_report.json.
Run after render_views.py:   uv run --with pillow python scripts/annotate_renders.py
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, "exports", "validation_report.json")))
D, M = R["derived"], R["measured"]
L, W, H = D["case_outer_mm"]
Z = D["z_levels_mm"]
REN = os.path.join(ROOT, "renders")
font = ImageFont.load_default(size=30)
small = ImageFont.load_default(size=24)
INK, ACC = (25, 25, 30), (200, 70, 20)


def stamp(name, title, sub=None):
    p = os.path.join(REN, name)
    im = Image.open(p).convert("RGB")
    d = ImageDraw.Draw(im)
    d.text((40, 30), title, fill=INK, font=font)
    if sub:
        d.text((40, 72), sub, fill=ACC, font=small)
    im.save(p)


stamp("01_closed_case.png", "FOX scanner case %s  -  %.1f x %.1f x %.1f mm" % (R["version"], L, W, H),
      "scanner only  |  %.1f mm lower than V3 (99.1 mm)" % -D["height_change_vs_v3_mm"])
stamp("03_finger_access_lift_out.png", "Finger access: long sides open above the %.0f mm cradle for %.0f mm"
      % (D["cradle_capture_height_mm"], D["finger_window_length_mm"]))
stamp("06_one_plate_A1mini.png", "One A1 mini plate: base upright + lid upside down  (%.0f x %.0f mm of 180 x 180)"
      % tuple(R["one_plate"]["footprint_mm"]), "no supports, no nesting, no auto-arrange needed")

# section: orthographic, ortho_scale 200 over 1400 px, centred on (x=0, z=H/2)
p = os.path.join(REN, "05_section_clearance.png")
im = Image.open(p).convert("RGB")
d = ImageDraw.Draw(im)
s = 1400 / 200.0
def px(x, z):
    return (700 + x * s, 500 - (z - H / 2) * s)
def vdim(z0, z1, x, label, col, left=False):
    (u0, v0), (u1, v1) = px(x, z0), px(x, z1)
    d.line([(u0, v0), (u1, v1)], fill=col, width=3)
    for v in (v0, v1):
        d.line([(u0 - 10, v), (u0 + 10, v)], fill=col, width=3)
    tw = d.textlength(label, font=small)
    d.text((u0 - 16 - tw if left else u0 + 16, (v0 + v1) / 2 - 14), label, fill=col, font=small)
vdim(0, H, L / 2 + 6, "%.1f mm total" % H, ACC)
vdim(Z["floor_top"], Z["lid_ceiling"], -L / 2 - 6, "FOX space %.1f" % M["floor_to_lid_ceiling_mm"], INK, left=True)
(u0, v0), (u1, _) = px(-L / 2, -4), px(L / 2, -4)
d.line([(u0, v0), (u1, v0)], fill=INK, width=3)
d.text(((u0 + u1) / 2 - 50, v0 + 6), "%.1f mm" % L, fill=INK, font=small)
d.text((30, 25), "Side section: FOX (35 mm stand-in) with %.1f mm clear to the lid" % M["fox_proxy_top_clearance_mm"],
       fill=INK, font=font)
d.text((30, 65), "cavity %.1f x %.1f mm  |  cradle %.0f mm  |  lid seats on the base band at z = %.0f"
       % (M["cavity_length_mm"], M["cavity_width_mm"], D["cradle_capture_height_mm"], Z["cradle_top_and_lid_mouth"]),
       fill=ACC, font=small)
im.save(p)
print("annotated")
