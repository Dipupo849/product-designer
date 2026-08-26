"""
COUCH product film - five shots, cut on timeline markers.

  blender -b -P film_couch.py -- <first> <last> [w] [h] [samples]

Renders a PNG sequence into renders/film/ so a long job is resumable: re-run with the
missing range. encode_film.py turns the sequence into an MP4.

Geometry, proportions and materials are identical to the stills - only the camera,
and the key light during the opening reveal, are animated.
"""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from couch import *
from studio import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "renders", "film")
os.makedirs(OUT, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FIRST = int(argv[0]) if len(argv) > 0 else 1
LAST = int(argv[1]) if len(argv) > 1 else 0          # 0 = to the end
RESX = int(argv[2]) if len(argv) > 2 else 854
RESY = int(argv[3]) if len(argv) > 3 else 480
SAMPLES = int(argv[4]) if len(argv) > 4 else 24

FPS = 24
BLACK = (0.030, 0.029, 0.030, 1.0)

# ---- shot lengths in seconds -------------------------------------------------
# 01 reveal  02 hero 3/4  03 orbit  04 material  05 construction  06 final hero
S_REVEAL, S_HERO_A, S_ORBIT, S_MAT, S_CONS, S_HERO_B = 3.0, 2.5, 6.0, 2.5, 2.0, 3.0
F = lambda s: int(round(s * FPS))
f_rev, f_ha, f_orb, f_mat, f_cons, f_hb = (F(S_REVEAL), F(S_HERO_A), F(S_ORBIT),
                                           F(S_MAT), F(S_CONS), F(S_HERO_B))
CUT1 = 1 + f_rev            # -> hero three-quarter
CUT2 = CUT1 + f_ha          # -> orbit
CUT3 = CUT2 + f_orb         # -> material detail
CUT4 = CUT3 + f_mat         # -> construction detail
CUT5 = CUT4 + f_cons        # -> final hero
END = CUT5 + f_hb - 1


# ------------------------------------------------------------------ scene
def build():
    clear_scene()
    lea = mat_leather("aniline_hide", base=BLACK, rough=0.36)
    btn = mat_leather("button", base=BLACK, rough=0.26, sheen=0.22, grain=900, bump=0.06)
    welt_m = mat_leather("welt", base=BLACK, rough=0.46, sheen=0.12, grain=760, bump=0.09)
    wood = mat_wood()
    rail = build_rail(); assign(rail, lea)
    panel, buttons = build_back_panel(); assign(panel, lea)
    for b in build_buttons(buttons): assign(b, btn)
    assign(build_cushion(), lea)
    assign(build_apron(), lea)
    assign(build_welt(), welt_m)
    assign(build_seat_welt(), welt_m)
    for lg in build_legs(): assign(lg, wood)
    cyc = drum()
    assign(cyc, mat_simple("cyc", (0.300, 0.292, 0.282, 1), rough=0.62))
    world_studio()
    rig_studio(key=132.0, fill=24.0, rim=52.0)


def cam(name, lens, fstop):
    cd = bpy.data.cameras.new(name)
    cd.lens, cd.dof.use_dof, cd.dof.aperture_fstop = lens, True, fstop
    ob = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(ob)
    return ob


def aim(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()


def set_key_interp(kind="BEZIER"):
    """Blender 5 moved fcurves behind slotted actions; setting the default before
    inserting is version-proof and does the same job."""
    try:
        ed = bpy.context.preferences.edit
        ed.keyframe_new_interpolation_type = kind
        if kind == "BEZIER":
            ed.keyframe_new_handle_type = "AUTO_CLAMPED"
    except Exception:
        pass


def key_cam(ob, frame, loc, target, focus=None, interp="BEZIER"):
    set_key_interp(interp)
    ob.location = Vector(loc)
    aim(ob, target)
    ob.data.dof.focus_distance = (Vector(focus or target) - Vector(loc)).length
    ob.keyframe_insert("location", frame=frame)
    ob.keyframe_insert("rotation_euler", frame=frame)
    ob.data.keyframe_insert("dof.focus_distance", frame=frame)


def orbit_pos(deg, dist, h, pivot=(0.0, 0.0, 0.0)):
    a = math.radians(deg)
    return (pivot[0] + dist * math.sin(a), pivot[1] - dist * math.cos(a), h)


def setup():
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, END
    T_BODY = (0.0, 0.0, 0.47)
    FOCUS_NEAR = (-0.35, -0.30, 0.45)

    # 01 REVEAL - low, wide, slow push while the rig comes up out of near-black
    c1 = cam("cam_reveal", 58.0, 5.6)
    key_cam(c1, 1, orbit_pos(34, 7.90, 0.26), (0, 0, 0.40), focus=FOCUS_NEAR)
    key_cam(c1, CUT1 - 1, orbit_pos(27, 6.40, 0.62), (0, 0, 0.45), focus=FOCUS_NEAR)

    kl = bpy.data.objects["KEY"]
    kl.data.energy = 1.5;   kl.data.keyframe_insert("energy", frame=1)
    kl.data.energy = 22.0;  kl.data.keyframe_insert("energy", frame=int(1 + f_rev * 0.32))
    kl.data.energy = 132.0; kl.data.keyframe_insert("energy", frame=CUT1 - 1)
    rl = bpy.data.objects["RIM"]
    rl.data.energy = 4.0;   rl.data.keyframe_insert("energy", frame=1)
    rl.data.energy = 52.0;  rl.data.keyframe_insert("energy", frame=int(1 + f_rev * 0.58))
    fl = bpy.data.objects["FILL"]
    fl.data.energy = 0.0;   fl.data.keyframe_insert("energy", frame=1)
    fl.data.energy = 24.0;  fl.data.keyframe_insert("energy", frame=CUT1 - 1)

    # 02 HERO THREE-QUARTER - catalogue composition, slow drift in
    c2 = cam("cam_hero_a", 85.0, 7.1)
    key_cam(c2, CUT1, orbit_pos(23, 6.35, 0.84), T_BODY, focus=FOCUS_NEAR)
    key_cam(c2, CUT2 - 1, orbit_pos(21, 5.95, 0.79), T_BODY, focus=FOCUS_NEAR)

    # 03 ORBIT - one continuous 360, constant speed, leaving from the hero angle
    c3 = cam("cam_orbit", 70.0, 6.3)
    steps = 12
    for i in range(steps + 1):
        fr = CUT2 + round(i * (f_orb - 1) / steps)
        key_cam(c3, fr, orbit_pos(21.0 + 360.0 * i / steps, 5.80, 0.86),
                (0, 0, 0.46), focus=(0, 0, 0.46), interp="LINEAR")

    # 04 MATERIAL DETAIL - lateral slide along the tufting row
    c4 = cam("cam_material", 90.0, 8.0)
    t_a = (-0.330, 0.268, 0.700)
    t_b = (0.180, 0.268, 0.700)
    key_cam(c4, CUT3, (t_a[0] + 0.205, -0.115, 0.812), t_a, focus=t_a)
    key_cam(c4, CUT4 - 1, (t_b[0] + 0.205, -0.115, 0.812), t_b, focus=t_b)

    # 05 CONSTRUCTION DETAIL - upholstery meeting frame and leg
    c5 = cam("cam_construction", 80.0, 6.3)
    t_leg = (0.870, -0.330, 0.235)
    key_cam(c5, CUT4, (1.70, -1.34, 0.68), t_leg, focus=t_leg)
    key_cam(c5, CUT5 - 1, (1.28, -0.94, 0.44), t_leg, focus=t_leg)

    # 06 FINAL HERO - return home and hold
    c6 = cam("cam_hero_b", 85.0, 7.1)
    key_cam(c6, CUT5, orbit_pos(25, 6.15, 0.82), T_BODY, focus=FOCUS_NEAR)
    key_cam(c6, END, orbit_pos(21, 5.52, 0.77), T_BODY, focus=FOCUS_NEAR)

    for frame, c in ((1, c1), (CUT1, c2), (CUT2, c3), (CUT3, c4), (CUT4, c5), (CUT5, c6)):
        mk = sc.timeline_markers.new(c.name, frame=frame)
        mk.camera = c
    sc.camera = c1
    return sc


def render_range(sc):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 4
    sc.render.resolution_x, sc.render.resolution_y = RESX, RESY
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.compression = 20
    sc.render.filepath = os.path.join(OUT, "f_")
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Base Contrast"
    except Exception:
        pass
    sc.view_settings.exposure = 0.45
    last = LAST if LAST else END
    for fr in range(FIRST, min(last, END) + 1):
        path = os.path.join(OUT, "f_%04d.png" % fr)
        if os.path.exists(path):
            continue
        sc.frame_set(fr)
        sc.render.filepath = path[:-4]
        bpy.ops.render.render(write_still=True)
        print("FRAME %d/%d" % (fr, END), flush=True)


build()
sc = setup()
print("SHOTS reveal=1-%d hero=%d-%d orbit=%d-%d material=%d-%d construction=%d-%d "
      "final=%d-%d  END=%d (%.1fs)"
      % (CUT1 - 1, CUT1, CUT2 - 1, CUT2, CUT3 - 1, CUT3, CUT4 - 1, CUT4, CUT5 - 1,
         CUT5, END, END, END / FPS), flush=True)
render_range(sc)
print("FILM RANGE DONE", flush=True)
