"""
Stamp final dimensions onto the documentation renders, reading exports/validation_report.json.
Run after render_views.py:   uv run --with pillow python scripts/annotate_renders.py
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, "exports", "validation_report.json")))
D = R["derived"]
L, W, H = D["case_outer_mm"]
Z = D["z_levels_mm"]
REN = os.path.join(ROOT, "renders")
font = ImageFont.load_default(size=30)
small = ImageFont.load_default(size=24)
INK, ACC = (25, 25, 30), (200, 70, 20)

# closed case caption
p = os.path.join(REN, "01_closed_case.png")
im = Image.open(p).convert("RGB")
d = ImageDraw.Draw(im)
d.text((40, 30), "FOX case %s  -  %.1f x %.1f x %.1f mm" % (R["version"], L, W, H), fill=INK, font=font)
d.text((40, 72), "height %.1f mm vs V2 130.5 mm (%+.1f mm)" % (H, D["height_change_vs_v2_mm"]),
       fill=ACC, font=small)
im.save(p)

# section: orthographic, ortho_scale 200 over 1400 px, centred on (x=0, z=H/2)
p = os.path.join(REN, "05_section_stack_height.png")
im = Image.open(p).convert("RGB")
d = ImageDraw.Draw(im)
s = 1400 / 200.0
def px(x, z):
    return (700 + x * s, 500 - (z - H / 2) * s)
xr = L / 2 + 7
def vdim(z0, z1, x, label, col, left=False):
    (u0, v0), (u1, v1) = px(x, z0), px(x, z1)
    d.line([(u0, v0), (u1, v1)], fill=col, width=3)
    for v in (v0, v1):
        d.line([(u0 - 10, v), (u0 + 10, v)], fill=col, width=3)
    tw = d.textlength(label, font=small)
    d.text((u0 - 16 - tw if left else u0 + 16, (v0 + v1) / 2 - 14), label, fill=col, font=small)
vdim(0, H, xr, "%.1f mm total" % H, ACC)
vdim(Z["floor_top"], Z["tray_underside"], -L / 2 - 7, "FOX space %.1f" % (Z["tray_underside"] - Z["floor_top"]), INK, left=True)
vdim(Z["tray_floor_top"], Z["tray_top"], -L / 2 - 7, "tray %.0f deep" % (Z["tray_top"] - Z["tray_floor_top"]), INK, left=True)
(u0, v0), (u1, _) = px(-L / 2, -5), px(L / 2, -5)
d.line([(u0, v0), (u1, v0)], fill=INK, width=3)
d.text(((u0 + u1) / 2 - 60, v0 + 6), "%.1f mm" % L, fill=INK, font=small)
d.text((30, 25), "Section on the long axis  -  base / FOX / open tray / lid", fill=INK, font=font)
im.save(p)

# tray top-down proof
p = os.path.join(REN, "06_tray_top_no_divider.png")
im = Image.open(p).convert("RGB")
d = ImageDraw.Draw(im)
tl, tw, th, _ = D["tray_inner_mm"]
d.text((40, 30), "Accessory tray: ONE open bin, no divider  (%.1f x %.1f x %.0f mm inside)" % (tl, tw, th),
       fill=INK, font=font)
chk = R["tray_divider_check"]
d.text((40, 72), "%d/%d grid rays reach the floor unobstructed" % (chk["rays"] - chk["rays_blocked_above_floor"], chk["rays"]),
       fill=ACC, font=small)
im.save(p)
print("annotated")
