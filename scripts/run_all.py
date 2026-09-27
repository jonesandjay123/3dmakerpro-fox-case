"""
Full pipeline: build + validate + export, then render the documentation views.
    /Applications/Blender.app/Contents/MacOS/Blender -b --python scripts/run_all.py
    uv run --with pillow python scripts/annotate_renders.py      # dimension labels
"""
import os

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = "/Users/joneswang/Downloads/code/3dmakerpro-fox-case/scripts"

build = {"__name__": "__main__", "__file__": os.path.join(HERE, "build_fox_case.py")}
exec(open(build["__file__"]).read(), build)
render = {"__name__": "__main__", "__file__": os.path.join(HERE, "render_views.py"), "BUILD": build}
exec(open(render["__file__"]).read(), render)
import bpy
bpy.ops.wm.save_mainfile()
