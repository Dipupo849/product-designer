"""Shot driver for PARAMETER.  blender -b -P render_param.py -- <shot> [preview]"""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enclosure, studio
from enclosure import *
from studio import *

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SHOT = argv[0] if argv else "hero"
PREVIEW = len(argv) > 1 and argv[1] == "preview"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders")
os.makedirs(OUT, exist_ok=True)
RES = (520, 330) if PREVIEW else (1240, 780)
SAMPLES = 20 if PREVIEW else 110
EV = -1.75   # cut: 0.300 backdrop read sRGB 193


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
    studio.set_in(bsdf, ["IOR"], 1.53)
    studio.set_in(bsdf, ["Sheen Weight", "Sheen"], 0.05)
    m["abs"] = abs_m

    m["knob"] = mat_simple("knob_abs", (0.035, 0.035, 0.036, 1), rough=0.62, ior=1.53)
    m["ind"] = mat_simple("knob_ind", (0.72, 0.70, 0.66, 1), rough=0.5)
    m["lcd"] = mat_emissive("stn_backlight", (0.108, 0.243, 0.760, 1), 14.0)
    m["glyph"] = mat_simple("stn_glyph", (0.010, 0.016, 0.048, 1), rough=0.55)
    m["bezel"] = mat_simple("lcd_bezel", (0.030, 0.031, 0.034, 1), rough=0.60)
    m["pcb_green"] = mat_simple("fr4_green", (0.055, 0.170, 0.085, 1), rough=0.45)
    m["pcb_blue"] = mat_simple("fr4_blue", (0.045, 0.090, 0.230, 1), rough=0.45)
    m["pcb_black"] = mat_simple("fr4_black", (0.030, 0.031, 0.033, 1), rough=0.48)
    m["cap_yellow"] = mat_simple("x2_cap", (0.520, 0.430, 0.090, 1), rough=0.42)
    m["cap_blue"] = mat_simple("elec_cap", (0.045, 0.110, 0.330, 1), rough=0.30)
    m["term_green"] = mat_simple("terminal", (0.075, 0.235, 0.110, 1), rough=0.40)
    m["term_white"] = mat_simple("connector", (0.640, 0.620, 0.580, 1), rough=0.48)
    m["ic_black"] = mat_simple("ic", (0.022, 0.022, 0.024, 1), rough=0.42)
    m["shield"] = mat_metal("tin_shield", (0.560, 0.565, 0.570, 1), rough=0.28)
    m["header"] = mat_simple("header", (0.026, 0.026, 0.028, 1), rough=0.50)
    m["trafo"] = mat_simple("trafo_core", (0.048, 0.036, 0.028, 1), rough=0.55)
    m["bobbin"] = mat_simple("bobbin", (0.310, 0.205, 0.095, 1), rough=0.52)
    m["brass"] = mat_metal("brass", (0.550, 0.417, 0.190, 1), rough=0.28)
    m["steel"] = mat_metal("a2_steel", (0.560, 0.560, 0.565, 1), rough=0.24)
    return m


def cam_at(loc, target, lens=85.0, fstop=8.0, focus=None):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    fp = Vector(focus if focus else target)
    cd.dof.focus_distance = (fp - Vector(loc)).length
    ob = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = ob
    return ob


def rig_small(key=17.0, fill=3.2, rim=6.5, t=(0, 0, 0.027)):
    area_light("KEY", (-0.30, -0.34, 0.46), t, 0.70, 0.90, key, (1.0, 0.985, 0.96))
    area_light("FILL", (0.46, -0.16, 0.22), t, 0.45, 0.55, fill, (0.95, 0.97, 1.0))
    area_light("RIM", (0.10, 0.42, 0.34), t, 0.55, 0.16, rim, (1.0, 0.98, 0.95))


def build(lid=True, board=False, exploded=0.0, rotary=True):
    clear_scene()
    M = mats()
    base = build_base_shell(); assign(base, M["abs"])
    panel, glyphs, bezel = build_display(FRONT_Y)
    assign(panel, M["lcd"]); assign(glyphs, M["glyph"]); assign(bezel, M["bezel"])
    if rotary:
        kb, ind = build_knob()
        assign(kb, M["knob"]); assign(ind, M["ind"])
        rb, rs = build_rotary(AXIS_Z)
        assign(rb, M["ic_black"]); assign(rs, M["steel"])
    if board:
        pcb, parts = build_board(exploded=exploded)
        assign(pcb, M["pcb_green"])
        for ob, tag in parts:
            assign(ob, M.get(tag, M["ic_black"]))
    if lid:
        ld = build_lid(exploded=exploded * 2.4 if exploded else 0.0)
        assign(ld, M["abs"])
    return M


def backdrop(shade=(0.300, 0.292, 0.282, 1), rotz=0.0):
    cyc = cyclorama(y_flat=0.30, radius=0.34, back_h=1.2, width=1.6, front=-1.4, rotz=rotz)
    assign(cyc, mat_simple("cyc", shade, rough=0.62))
    world_studio(top=0.05, bottom=0.012)
    return cyc


def shot_hero():
    build(lid=True, board=False)
    backdrop(); rig_small(key=18.0, fill=3.4, rim=7.6)
    cam_at((0.300, -0.330, 0.205), (0, 0, 0.026), lens=85.0, fstop=8.0,
           focus=(0.02, -0.055, 0.030))
    render(os.path.join(OUT, "param_hero.png"), RES, SAMPLES, exposure=EV)


def shot_front():
    build(lid=True, board=False)
    backdrop(); rig_small(key=17.0, fill=6.5, rim=5.0)
    cam_at((0.0, -0.62, 0.027), (0, 0, 0.027), lens=120.0, fstop=11.0)
    render(os.path.join(OUT, "param_front.png"), RES, SAMPLES, exposure=EV)


def shot_rear():
    build(lid=True, board=False)
    backdrop(rotz=180.0); rig_small(key=16.0, fill=3.0, rim=8.4)
    cam_at((-0.230, 0.320, 0.185), (0, 0, 0.026), lens=85.0, fstop=8.0)
    render(os.path.join(OUT, "param_rear.png"), RES, SAMPLES, exposure=EV)


def shot_top():
    build(lid=False, board=True)
    backdrop(); rig_small(key=20.0, fill=5.4, rim=3.8)
    cam_at((0.0, -0.002, 0.560), (0, 0, 0.02), lens=100.0, fstop=11.0)
    render(os.path.join(OUT, "param_top.png"), RES, SAMPLES, exposure=EV)


def shot_exploded():
    build(lid=True, board=True, exploded=0.030)
    backdrop(); rig_small(key=19.0, fill=4.2, rim=6.9)
    cam_at((0.360, -0.400, 0.330), (0, 0, 0.055), lens=85.0, fstop=11.0,
           focus=(0.0, 0.0, 0.05))
    render(os.path.join(OUT, "param_exploded.png"), RES, SAMPLES, exposure=EV)


def shot_controls():
    build(lid=True, board=False)
    backdrop(); rig_small(key=15.0, fill=3.4, rim=5.4)
    cam_at((-0.052, -0.145, 0.052), (-0.020, -0.060, 0.027), lens=100.0, fstop=4.0,
           focus=(-0.050, -0.070, 0.027))
    render(os.path.join(OUT, "param_controls.png"), RES, SAMPLES, exposure=EV)


def shot_studio():
    build(lid=True, board=False)
    backdrop(shade=(0.420, 0.412, 0.398, 1))
    rig_small(key=18.0, fill=4.6, rim=6.1)
    cam_at((0.215, -0.400, 0.150), (0, 0, 0.026), lens=100.0, fstop=9.0,
           focus=(0.0, -0.05, 0.027))
    render(os.path.join(OUT, "param_studio.png"), RES, SAMPLES, exposure=EV)


def shot_clay():
    """Geometry pass: identical build and camera to the hero plate, materials stripped."""
    build(lid=True, board=False)
    backdrop(); rig_small(key=18.0, fill=6.9, rim=6.1)
    clay_override()
    cam_at((0.300, -0.330, 0.205), (0, 0, 0.026), lens=85.0, fstop=8.0,
           focus=(0.02, -0.055, 0.030))
    render(os.path.join(OUT, "param_clay.png"), RES, SAMPLES, exposure=EV)


SHOTS = {"hero": shot_hero, "front": shot_front, "rear": shot_rear, "top": shot_top,
         "exploded": shot_exploded, "controls": shot_controls, "studio": shot_studio,
         "clay": shot_clay}
SHOTS[SHOT]()
