"""Shot driver for COUCH.  blender -b -P render_couch.py -- <shot> [preview]"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import couch, studio
from couch import *
from studio import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SHOT = argv[0] if argv else "studio"
PREVIEW = len(argv) > 1 and argv[1] == "preview"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders")
os.makedirs(OUT, exist_ok=True)

RES = (520, 330) if PREVIEW else (1240, 780)
SAMPLES = 20 if PREVIEW else 110
EV = 0.45   # lift: 0.345 backdrop read sRGB 84
INT_SAMPLES = 24 if PREVIEW else 190   # interiors carry more GI noise

BLACK = (0.030, 0.029, 0.030, 1.0)
COGNAC = (0.128, 0.049, 0.021, 1.0)


def build_sofa(leather_base=BLACK):
    clear_scene()
    lea = mat_leather("aniline_hide", base=leather_base, rough=0.36)
    welt_m = mat_leather("welt", base=leather_base, rough=0.46, sheen=0.12, grain=760, bump=0.09)
    wood = mat_wood()

    rail = build_rail();                 assign(rail, lea)
    panel, buttons = build_back_panel(); assign(panel, lea)
    btn_m = mat_leather("button", base=leather_base, rough=0.26, sheen=0.22,
                        grain=900, bump=0.06)
    for b in build_buttons(buttons):     assign(b, btn_m)
    cush = build_cushion();              assign(cush, lea)
    apron = build_apron();               assign(apron, lea)
    welt = build_welt();                 assign(welt, welt_m)
    swelt = build_seat_welt();           assign(swelt, welt_m)
    for lg in build_legs():              assign(lg, wood)
    return rail


def add_rug():
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    r = bpy.context.active_object
    r.name = "rug"
    r.scale = (2.60, 1.85, 0.012)
    r.location = (0.05, -0.62, 0.006)
    bpy.ops.object.transform_apply(scale=True)
    b = r.modifiers.new("bevel", "BEVEL"); b.width, b.segments = 0.004, 2
    assign(r, mat_wool_rug())
    return r


def add_side_table():
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.215, depth=0.028,
                                        location=(1.36, -0.16, 0.505))
    top = bpy.context.active_object; top.name = "table_top"
    bpy.ops.object.shade_smooth()
    assign(top, mat_simple("table_top", (0.615, 0.585, 0.545, 1), rough=0.22, ior=1.55))
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.017, depth=0.49,
                                        location=(1.36, -0.16, 0.246))
    col = bpy.context.active_object; col.name = "table_col"
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.155, depth=0.012,
                                        location=(1.36, -0.16, 0.006))
    base = bpy.context.active_object; base.name = "table_base"
    bpy.ops.object.shade_smooth()
    met = mat_metal("blackened_steel", (0.052, 0.050, 0.049, 1), rough=0.34)
    assign(col, met); assign(base, met)


def add_wall_oval():
    """The oval-framed wall piece present in the source 3ds Max scene."""
    bpy.ops.mesh.primitive_torus_add(major_radius=0.40, minor_radius=0.018,
                                     major_segments=64, minor_segments=16,
                                     location=(-0.02, 0.545, 1.62),
                                     rotation=(math.radians(90), 0, 0))
    t = bpy.context.active_object; t.name = "wall_oval"
    t.scale = (1.0, 0.66, 1.0)
    bpy.ops.object.shade_smooth()
    assign(t, mat_metal("oval_frame", (0.075, 0.072, 0.070, 1), rough=0.38))


def wall_with_window(name, x, y0, y1, z0, z1, wy0, wy1, wz0, wz1, flip=False):
    """Wall in the YZ plane at x, built as four quads around a rectangular opening."""
    quads = [(y0, y1, z0, wz0), (y0, y1, wz1, z1),
             (y0, wy0, wz0, wz1), (wy1, y1, wz0, wz1)]
    verts, faces = [], []
    for (a0, a1, b0, b1) in quads:
        if a1 - a0 <= 1e-6 or b1 - b0 <= 1e-6:
            continue
        i = len(verts)
        verts += [(x, a0, b0), (x, a1, b0), (x, a1, b1), (x, a0, b1)]
        faces.append([i, i + 1, i + 2, i + 3] if not flip else [i + 3, i + 2, i + 1, i])
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def build_interior():
    """5.4 x 3.8 m contemporary room; north window on the left wall."""
    X0, X1 = -2.70, 2.70
    Y0, Y1 = -4.80, 0.56
    ZC = 2.90
    plaster = mat_simple("lime_plaster", (0.612, 0.598, 0.572, 1), rough=0.86)
    oak = mat_oak_floor()

    bpy.ops.mesh.primitive_plane_add(size=1.0)
    fl = bpy.context.active_object; fl.name = "floor"
    fl.scale = (X1 - X0, Y1 - Y0, 1); fl.location = ((X0 + X1) / 2, (Y0 + Y1) / 2, 0)
    bpy.ops.object.transform_apply(scale=True)
    assign(fl, oak)

    bpy.ops.mesh.primitive_plane_add(size=1.0)
    cl = bpy.context.active_object; cl.name = "ceiling"
    cl.scale = (X1 - X0, Y1 - Y0, 1); cl.location = ((X0 + X1) / 2, (Y0 + Y1) / 2, ZC)
    bpy.ops.object.transform_apply(scale=True)
    assign(cl, plaster)

    bpy.ops.mesh.primitive_plane_add(size=1.0, rotation=(math.radians(90), 0, 0))
    bw = bpy.context.active_object; bw.name = "back_wall"
    bw.scale = (X1 - X0, ZC, 1); bw.location = ((X0 + X1) / 2, Y1, ZC / 2)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    assign(bw, plaster)

    bpy.ops.mesh.primitive_plane_add(size=1.0, rotation=(math.radians(90), 0, math.radians(90)))
    rw = bpy.context.active_object; rw.name = "right_wall"
    rw.scale = (Y1 - Y0, ZC, 1); rw.location = (X1, (Y0 + Y1) / 2, ZC / 2)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    assign(rw, plaster)

    lw = wall_with_window("left_wall", X0, Y0, Y1, 0.0, ZC, -2.35, -0.45, 0.42, 2.32)
    assign(lw, plaster)

    # daylight through the opening
    sky = area_light("WINDOW", (X0 - 0.55, -1.40, 1.37), (0.2, -0.6, 0.85),
                     2.10, 2.10, 86.0, (0.93, 0.965, 1.0))
    area_light("BOUNCE", (2.30, -1.10, 1.30), (0.1, -0.2, 0.60),
               2.2, 1.8, 7.0, (1.0, 0.95, 0.88))
    world_studio(top=0.10, bottom=0.035)
    return fl


# ------------------------------------------------------------------ shots
def shot_studio(alt=False):
    build_sofa(COGNAC if alt else BLACK)
    cyc = cyclorama()
    assign(cyc, mat_simple("cyc", (0.345, 0.335, 0.322, 1), rough=0.62))
    world_studio()
    rig_studio(key=132.0, fill=24.0, rim=52.0)
    camera("cam", distance=5.60, height=0.78, azimuth_deg=22.0,
           target=(0, 0, 0.46), lens=85.0, fstop=7.1,
           focus_point=(-0.35, -0.30, 0.45))
    render(os.path.join(OUT, "couch_alt.png" if alt else "couch_studio.png"), RES, SAMPLES, exposure=EV)


def shot_front():
    build_sofa()
    cyc = cyclorama()
    assign(cyc, mat_simple("cyc", (0.345, 0.335, 0.322, 1), rough=0.62))
    world_studio()
    rig_studio(key=122.0, fill=48.0, rim=38.0)
    camera("cam", distance=8.60, height=0.60, azimuth_deg=0.0,
           target=(0, 0, 0.44), lens=135.0, fstop=11.0)
    render(os.path.join(OUT, "couch_front.png"), RES, SAMPLES, exposure=EV)


def shot_rear():
    build_sofa()
    cyc = cyclorama(rotz=180.0)
    assign(cyc, mat_simple("cyc", (0.300, 0.292, 0.282, 1), rough=0.62))
    world_studio()
    rig_studio(key=120.0, fill=46.0, rim=40.0)
    camera("cam", distance=5.20, height=1.08, azimuth_deg=146.0,
           target=(0, 0.05, 0.50), lens=85.0, fstop=5.6,
           focus_point=(0.30, 0.30, 0.62))
    render(os.path.join(OUT, "couch_rear.png"), RES, SAMPLES, exposure=EV)


def shot_detail():
    """Macro on a single tuft: button, welt above it, hide grain. Raking key."""
    build_sofa()
    cyc = cyclorama()
    assign(cyc, mat_simple("cyc", (0.300, 0.292, 0.282, 1), rough=0.62))
    world_studio()
    tgt = (-0.150, 0.271, 0.700)
    # small raking key close in, so the pore grain and the dimple both read
    area_light("KEY", (-0.62, -0.52, 1.28), tgt, 0.55, 0.75, 4.6, (1.0, 0.985, 0.96))
    area_light("FILL", (0.68, -0.44, 0.72), tgt, 0.40, 0.40, 0.55, (0.95, 0.97, 1.0))
    area_light("RIM", (-0.10, 1.15, 1.35), tgt, 1.2, 0.30, 2.0, (1.0, 0.98, 0.95))
    camera_at((0.132, -0.260, 0.854), tgt, lens=90.0, fstop=11.0, focus=tgt)
    render(os.path.join(OUT, "couch_detail.png"), RES, SAMPLES, exposure=EV)


def shot_hero():
    build_sofa()
    build_interior()
    add_rug(); add_side_table(); add_wall_oval()
    camera("cam", distance=3.55, height=1.16, azimuth_deg=34.0,
           target=(0, 0.02, 0.52), lens=40.0, fstop=4.0,
           focus_point=(0.55, -0.25, 0.50))
    render(os.path.join(OUT, "couch_hero.png"), RES, INT_SAMPLES, exposure=EV)


def shot_lifestyle():
    build_sofa()
    build_interior()
    add_rug(); add_side_table(); add_wall_oval()
    camera("cam", distance=3.45, height=1.28, azimuth_deg=31.0,
           target=(-0.02, 0.04, 0.60), lens=32.0, fstop=4.0,
           focus_point=(0.25, -0.22, 0.52))
    render(os.path.join(OUT, "couch_lifestyle.png"), RES, INT_SAMPLES, exposure=EV)


def shot_clay():
    """Same geometry, same camera as the studio plate - materials stripped to clay."""
    build_sofa()
    cyc = cyclorama()
    assign(cyc, mat_simple("cyc", (0.345, 0.335, 0.322, 1), rough=0.62))
    world_studio()
    rig_studio(key=125.0, fill=38.0, rim=42.0)
    clay_override()
    camera("cam", distance=5.60, height=0.78, azimuth_deg=22.0,
           target=(0, 0, 0.46), lens=85.0, fstop=7.1,
           focus_point=(-0.35, -0.30, 0.45))
    render(os.path.join(OUT, "couch_clay.png"), RES, SAMPLES, exposure=EV)


SHOTS = {
    "studio": shot_studio, "front": shot_front, "rear": shot_rear,
    "detail": shot_detail, "hero": shot_hero, "lifestyle": shot_lifestyle,
    "alt": lambda: shot_studio(alt=True), "clay": shot_clay,
}
SHOTS[SHOT]()
