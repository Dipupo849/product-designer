"""Geometry-only smoke test: build both products, report stats, no render."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from couch import *
from studio import *
import enclosure


def stats(tag):
    tot_v = tot_f = 0
    print(f"\n--- {tag} ---")
    for ob in sorted(bpy.context.scene.objects, key=lambda o: o.name):
        if ob.type != "MESH":
            print(f"  {ob.name:26s} {ob.type}")
            continue
        v, f = len(ob.data.vertices), len(ob.data.polygons)
        tot_v += v; tot_f += f
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = [min(p[i] for p in bb) for i in range(3)]
        hi = [max(p[i] for p in bb) for i in range(3)]
        print(f"  {ob.name:26s} v={v:7d} f={f:7d}  "
              f"x[{lo[0]:+.3f},{hi[0]:+.3f}] y[{lo[1]:+.3f},{hi[1]:+.3f}] z[{lo[2]:+.3f},{hi[2]:+.3f}]"
              f"  mat={(ob.data.materials[0].name if ob.data.materials and ob.data.materials[0] else 'NONE')}")
    print(f"  TOTAL cage v={tot_v} f={tot_f}")


from mathutils import Vector

# ---- COUCH
clear_scene()
lea = mat_leather("hide"); wood = mat_wood()
r = build_rail(); assign(r, lea)
p, btns = build_back_panel(); assign(p, lea)
for b in build_buttons(btns): assign(b, lea)
c = build_cushion(); assign(c, lea)
a = build_apron(); assign(a, lea)
w = build_welt(); assign(w, lea)
for lg in build_legs(): assign(lg, wood)
stats("COUCH")
print(f"  buttons: {len(btns)} at {btns[0]:.3f} .. {btns[-1]:.3f}")

# ---- PARAMETER
clear_scene()
base = enclosure.build_base_shell()
pan, gly, bez = enclosure.build_display(enclosure.FRONT_Y)
kb, ind = enclosure.build_knob()
rb, rs = enclosure.build_rotary(enclosure.AXIS_Z)
pcb, parts = enclosure.build_board()
lid = enclosure.build_lid()
stats("PARAMETER")
print(f"  board parts: {len(parts)}")
print(f"  glyph faces: {len(gly.data.polygons)} (dot matrix)")
print("\nSMOKE OK")
