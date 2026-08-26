"""
PARAMETER product film - four shots, cut on timeline markers.

  blender -b -P film_param.py -- <first> <last> [w] [h] [samples]

Same geometry and materials as the stills; only the camera and the opening key ramp
are animated. Frames go to renders/film_param/ so the job is resumable.
"""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from enclosure import *
import studio
from studio import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "renders", "film_param")
os.makedirs(OUT, exist_ok=True)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FIRST = int(argv[0]) if len(argv) > 0 else 1
LAST = int(argv[1]) if len(argv) > 1 else 0
RESX = int(argv[2]) if len(argv) > 2 else 854
RESY = int(argv[3]) if len(argv) > 3 else 480
SAMPLES = int(argv[4]) if len(argv) > 4 else 16

FPS = 24
EV = -1.75

# 01 reveal  02 hero  03 orbit  04 technical detail  05 final hero
S_REVEAL, S_HERO_A, S_ORBIT, S_DETAIL, S_HERO_B = 2.5, 2.0, 4.5, 2.0, 2.0
F = lambda s: int(round(s * FPS))
f_rev, f_ha, f_orb, f_det, f_hb = (F(S_REVEAL), F(S_HERO_A), F(S_ORBIT),
                                   F(S_DETAIL), F(S_HERO_B))
CUT1 = 1 + f_rev
CUT2 = CUT1 + f_ha
CUT3 = CUT2 + f_orb
CUT4 = CUT3 + f_det
END = CUT4 + f_hb - 1


def mats():
    m = {}
    abs_m, nt, bsdf, geo = studio._fresh("abs_ral9001")
    N, L = nt.nodes, nt.links
    nz = N.new("ShaderNodeTexNoise"); nz.location = (-700, 0)
    nz.inputs["Scale"].default_value = 900.0
    nz.inputs["Detail"].default_value = 4.0
    L.new(geo.outputs["Position"], nz.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.location = (-320, 0)
    bp.inputs["Strength"].default_value = 0.10
    bp.inputs["Distance"].default_value = 0.0004
    L.new(nz.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Base Color"].default_value = (0.710, 0.678, 0.588, 1)
    bsdf.inputs["Roughness"].default_value = 0.55
    set_in(bsdf, ["IOR"], 1.53)
    set_in(bsdf, ["Sheen Weight", "Sheen"], 0.05)
    m["abs"] = abs_m
    m["knob"] = mat_simple("knob_abs", (0.035, 0.035, 0.036, 1), rough=0.62, ior=1.53)
    m["ind"] = mat_simple("knob_ind", (0.72, 0.70, 0.66, 1), rough=0.5)
    m["lcd"] = mat_emissive("stn_backlight", (0.108, 0.243, 0.760, 1), 14.0)
    m["glyph"] = mat_simple("stn_glyph", (0.010, 0.016, 0.048, 1), rough=0.55)
    m["bezel"] = mat_simple("lcd_bezel", (0.030, 0.031, 0.034, 1), rough=0.60)
    m["ic"] = mat_simple("ic", (0.022, 0.022, 0.024, 1), rough=0.42)
    m["steel"] = mat_metal("a2_steel", (0.560, 0.560, 0.565, 1), rough=0.24)
    return m


def build():
    clear_scene()
    M = mats()
    assign(build_base_shell(), M["abs"])
    panel, glyphs, bezel = build_display(FRONT_Y)
    assign(panel, M["lcd"]); assign(glyphs, M["glyph"]); assign(bezel, M["bezel"])
    kb, ind = build_knob(); assign(kb, M["knob"]); assign(ind, M["ind"])
    rb, rs = build_rotary(AXIS_Z); assign(rb, M["ic"]); assign(rs, M["steel"])
    assign(build_lid(), M["abs"])
    cyc = drum(r_floor=0.52, cove=0.13, r_wall=0.66, wall_h=0.55, seg=96, rings=12)
    assign(cyc, mat_simple("cyc", (0.300, 0.292, 0.282, 1), rough=0.62))
    world_studio(top=0.05, bottom=0.012)
    t = (0, 0, 0.027)
    area_light("KEY", (-0.30, -0.34, 0.46), t, 0.70, 0.90, 18.0, (1.0, 0.985, 0.96))
    area_light("FILL", (0.46, -0.16, 0.22), t, 0.45, 0.55, 3.4, (0.95, 0.97, 1.0))
    area_light("RIM", (0.10, 0.42, 0.34), t, 0.55, 0.16, 7.6, (1.0, 0.98, 0.95))


def cam(name, lens, fstop):
    cd = bpy.data.cameras.new(name)
    cd.lens, cd.dof.use_dof, cd.dof.aperture_fstop = lens, True, fstop
    ob = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(ob)
    return ob


def set_key_interp(kind="BEZIER"):
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
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()
    ob.data.dof.focus_distance = (Vector(focus or target) - Vector(loc)).length
    ob.keyframe_insert("location", frame=frame)
    ob.keyframe_insert("rotation_euler", frame=frame)
    ob.data.keyframe_insert("dof.focus_distance", frame=frame)


def orbit_pos(deg, dist, h):
    a = math.radians(deg)
    return (dist * math.sin(a), -dist * math.cos(a), h)


def setup():
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, END
    T = (0.0, 0.0, 0.026)
    FOCUS = (0.02, -0.055, 0.030)

    # 01 REVEAL - out of near-black, slow push, display already lit
    c1 = cam("cam_reveal", 85.0, 8.0)
    key_cam(c1, 1, orbit_pos(36, 0.700, 0.042), (0, 0, 0.022), focus=(0.0, -0.06, 0.027))
    key_cam(c1, CUT1 - 1, orbit_pos(31, 0.505, 0.155), T, focus=(0.0, -0.055, 0.028))

    kl = bpy.data.objects["KEY"]
    kl.data.energy = 0.35; kl.data.keyframe_insert("energy", frame=1)
    kl.data.energy = 3.4;  kl.data.keyframe_insert("energy", frame=int(1 + f_rev * 0.32))
    kl.data.energy = 18.0; kl.data.keyframe_insert("energy", frame=CUT1 - 1)
    rl = bpy.data.objects["RIM"]
    rl.data.energy = 0.8;  rl.data.keyframe_insert("energy", frame=1)
    rl.data.energy = 7.6;  rl.data.keyframe_insert("energy", frame=int(1 + f_rev * 0.58))
    fl = bpy.data.objects["FILL"]
    fl.data.energy = 0.0;  fl.data.keyframe_insert("energy", frame=1)
    fl.data.energy = 3.4;  fl.data.keyframe_insert("energy", frame=CUT1 - 1)

    # 02 HERO - three-quarter, slow drift
    c2 = cam("cam_hero_a", 85.0, 8.0)
    key_cam(c2, CUT1, orbit_pos(44, 0.478, 0.208), T, focus=FOCUS)
    key_cam(c2, CUT2 - 1, orbit_pos(41, 0.446, 0.194), T, focus=FOCUS)

    # 03 ORBIT - continuous 360 leaving from the hero angle
    c3 = cam("cam_orbit", 70.0, 9.0)
    steps = 12
    for i in range(steps + 1):
        fr = CUT2 + round(i * (f_orb - 1) / steps)
        key_cam(c3, fr, orbit_pos(41.0 + 360.0 * i / steps, 0.438, 0.186), T,
                focus=T, interp="LINEAR")

    # 04 TECHNICAL DETAIL - knurled control across to the display window
    c4 = cam("cam_detail", 100.0, 5.6)
    t_a = (KNOB_CX, FRONT_Y - 0.004, AXIS_Z)
    t_b = (WIN_CX - 0.008, FRONT_Y, AXIS_Z)
    key_cam(c4, CUT3, (t_a[0] - 0.032, FRONT_Y - 0.150, AXIS_Z + 0.042), t_a, focus=t_a)
    key_cam(c4, CUT4 - 1, (t_b[0] - 0.012, FRONT_Y - 0.152, AXIS_Z + 0.030), t_b, focus=t_b)

    # 05 FINAL HERO - return home and hold
    c5 = cam("cam_hero_b", 85.0, 8.0)
    key_cam(c5, CUT4, orbit_pos(45, 0.470, 0.203), T, focus=FOCUS)
    key_cam(c5, END, orbit_pos(41, 0.424, 0.189), T, focus=FOCUS)

    for frame, c in ((1, c1), (CUT1, c2), (CUT2, c3), (CUT3, c4), (CUT4, c5)):
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
    sc.render.resolution_x, sc.render.resolution_y = RESX, RESY
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.compression = 20
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Base Contrast"
    except Exception:
        pass
    sc.view_settings.exposure = EV
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
print("SHOTS reveal=1-%d hero=%d-%d orbit=%d-%d detail=%d-%d final=%d-%d  END=%d (%.1fs)"
      % (CUT1 - 1, CUT1, CUT2 - 1, CUT2, CUT3 - 1, CUT3, CUT4 - 1, CUT4, END, END,
         END / FPS), flush=True)
render_range(sc)
print("FILM RANGE DONE", flush=True)
