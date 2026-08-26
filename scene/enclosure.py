"""
PARAMETER - transformer monitor enclosure.
Geometry from the Fusion 360 reference at the dossier dimensions. Units metres.

  external 0.140 W x 0.126 D x 0.054 H      wall 0.0025   lid 0.006
  corner R8               window 0.0715 x 0.0255 centred on the 0.027 axis
  knob   dia 0.015 on the same axis          PCB 0.120 x 0.080
"""
import bpy, math

W, D, H = 0.140, 0.126, 0.054
LID_T, WALL, R_CORNER = 0.006, 0.0025, 0.008
BODY_H = H - LID_T
AXIS_Z = 0.027
WIN_W, WIN_H = 0.0715, 0.0255
WIN_CX = 0.0113
KNOB_CX, KNOB_D = -0.0505, 0.015
PCB_W, PCB_D, PCB_T = 0.120, 0.080, 0.0016
BOSS_INSET, BOSS_D = 0.012, 0.011
FRONT_Y = -D / 2


def box(name, sx, sy, sz, loc, bevel=0.0, segs=4):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(scale=True)
    if bevel > 0:
        b = ob.modifiers.new("bev", "BEVEL")
        b.width, b.segments = bevel, segs
        b.limit_method = "ANGLE"
        b.angle_limit = math.radians(40)
        bpy.ops.object.modifier_apply(modifier=b.name)
    return ob


def boolean(target, cutter, op="DIFFERENCE"):
    m = target.modifiers.new("bool", "BOOLEAN")
    m.operation = op
    m.object = cutter
    m.solver = "EXACT"
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    return target


def cyl(name, r, depth, loc, rot=(0, 0, 0), verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth,
                                        location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    bpy.ops.object.shade_smooth()
    return ob


# ------------------------------------------------------------------ shell
def build_base_shell():
    outer = box("PARAM_base", W, D, BODY_H, (0, 0, BODY_H / 2), bevel=R_CORNER, segs=6)
    inner = box("cut_cavity", W - 2 * WALL, D - 2 * WALL, BODY_H,
                (0, 0, BODY_H / 2 + WALL + 0.001), bevel=R_CORNER - WALL, segs=6)
    boolean(outer, inner)
    win = box("cut_win", WIN_W, 0.03, WIN_H, (WIN_CX, FRONT_Y, AXIS_Z))
    boolean(outer, win)
    kn = cyl("cut_knob", 0.0052, 0.03, (KNOB_CX, FRONT_Y, AXIS_Z),
             rot=(math.radians(90), 0, 0), verts=32)
    boolean(outer, kn)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bx = sx * (W / 2 - BOSS_INSET)
            by = sy * (D / 2 - BOSS_INSET)
            b = cyl("boss", BOSS_D / 2, BODY_H - WALL,
                    (bx, by, WALL + (BODY_H - WALL) / 2), verts=28)
            m = outer.modifiers.new("u", "BOOLEAN")
            m.operation, m.object, m.solver = "UNION", b, "EXACT"
            bpy.context.view_layer.objects.active = outer
            bpy.ops.object.modifier_apply(modifier=m.name)
            bpy.data.objects.remove(b, do_unlink=True)
            h = cyl("bhole", 0.0013, BODY_H, (bx, by, WALL + BODY_H / 2), verts=16)
            boolean(outer, h)
    from studio import smooth_auto
    smooth_auto(outer, 32.0)
    return outer


def build_lid(z=BODY_H - 0.001, exploded=0.0):
    lid = box("PARAM_lid", W, D, LID_T, (0, 0, z + LID_T / 2 + exploded),
              bevel=R_CORNER, segs=6)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bx = sx * (W / 2 - BOSS_INSET)
            by = sy * (D / 2 - BOSS_INSET)
            h = cyl("lh", 0.0017, LID_T * 3, (bx, by, z + LID_T / 2 + exploded), verts=20)
            boolean(lid, h)
            ck = bpy.ops.mesh.primitive_cone_add(
                vertices=20, radius1=0.0032, radius2=0.0017, depth=0.0018,
                location=(bx, by, z + LID_T - 0.0009 + exploded))
            cone = bpy.context.active_object
            boolean(lid, cone)
    from studio import smooth_auto
    smooth_auto(lid, 32.0)
    return lid


# ------------------------------------------------------------------ knob
def build_knob(protrude=0.012):
    """Straight-knurled control knob, knurl as real geometry."""
    n, r, flute = 72, KNOB_D / 2, 0.00035
    depth = protrude
    y0 = FRONT_Y - protrude
    verts, faces = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r - (flute if i % 2 else 0.0)
        verts.append((KNOB_CX + rr * math.cos(a), y0, AXIS_Z + rr * math.sin(a)))
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r - (flute if i % 2 else 0.0)
        verts.append((KNOB_CX + rr * math.cos(a), FRONT_Y + 0.002, AXIS_Z + rr * math.sin(a)))
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
    fc = len(verts); verts.append((KNOB_CX, y0, AXIS_Z))
    bc = len(verts); verts.append((KNOB_CX, FRONT_Y + 0.002, AXIS_Z))
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, fc, j])
        faces.append([n + j, bc, n + i])
    me = bpy.data.meshes.new("PARAM_knob")
    me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new("PARAM_knob", me)
    bpy.context.collection.objects.link(ob)
    b = ob.modifiers.new("bev", "BEVEL"); b.width, b.segments = 0.0006, 2
    b.limit_method = "ANGLE"; b.angle_limit = math.radians(50)
    # indicator line
    ind = box("knob_ind", 0.0012, 0.0004, 0.005,
              (KNOB_CX, y0 - 0.0002, AXIS_Z + 0.0045))
    return ob, ind


# ------------------------------------------------------------------ display
FONT = {
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "z": [".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
}
LINE1 = "230.4V   1.24A"
LINE2 = "P 284W  50.0Hz"


def build_display(y_face):
    """16x2 STN module: emissive panel plus real dot-matrix glyph geometry."""
    act_w, act_h = 0.0645, 0.0164
    x0 = WIN_CX - act_w / 2
    z1 = AXIS_Z + act_h / 2
    cell_w, cell_h = act_w / 16, act_h / 2
    dot_w, dot_h = cell_w / 5 * 0.78, cell_h / 8 * 0.80
    panel = box("LCD_panel", WIN_W + 0.006, 0.001, WIN_H + 0.006,
                (WIN_CX, y_face + 0.0018, AXIS_Z))
    verts, faces = [], []

    def add_dot(cx, cz):
        i = len(verts)
        hw, hh, y = dot_w / 2, dot_h / 2, y_face + 0.0011
        verts.extend([(cx - hw, y, cz - hh), (cx + hw, y, cz - hh),
                      (cx + hw, y, cz + hh), (cx - hw, y, cz + hh)])
        faces.append([i, i + 1, i + 2, i + 3])

    for row, text in enumerate((LINE1, LINE2)):
        for col, ch in enumerate(text[:16]):
            g = FONT.get(ch, FONT[" "])
            for dy in range(7):
                for dx in range(5):
                    if g[dy][dx] != "#":
                        continue
                    cx = x0 + col * cell_w + (dx + 0.5) * (cell_w / 5)
                    cz = z1 - row * cell_h - (dy + 0.5) * (cell_h / 8)
                    add_dot(cx, cz)
    me = bpy.data.meshes.new("LCD_glyphs")
    me.from_pydata(verts, [], faces); me.update()
    glyphs = bpy.data.objects.new("LCD_glyphs", me)
    bpy.context.collection.objects.link(glyphs)
    bezel = box("LCD_bezel", WIN_W + 0.010, 0.006, WIN_H + 0.010,
                (WIN_CX, y_face + 0.0045, AXIS_Z))
    return panel, glyphs, bezel


# ------------------------------------------------------------------ board
def build_board(z=WALL + 0.005, exploded=0.0):
    zz = z + exploded
    pcb = box("PCB", PCB_W, PCB_D, PCB_T, (0, 0, zz))
    parts = []

    def part(name, sx, sy, sz, x, y, tag):
        ob = box(name, sx, sy, sz, (x, y, zz + PCB_T / 2 + sz / 2), bevel=0.0004, segs=2)
        parts.append((ob, tag))
        return ob

    # 1 PZEM-004T energy meter, left column (mains side)
    part("PZEM", 0.0355, 0.0760, 0.0016, -0.0405, 0.000, "pcb_blue")
    part("PZEM_cap", 0.0150, 0.0090, 0.0110, -0.0405, -0.0230, "cap_yellow")
    part("PZEM_term", 0.0230, 0.0090, 0.0105, -0.0405, -0.0330, "term_green")
    part("PZEM_ic1", 0.0090, 0.0040, 0.0018, -0.0470, 0.0130, "ic_black")
    part("PZEM_ic2", 0.0090, 0.0040, 0.0018, -0.0340, 0.0130, "ic_black")
    part("PZEM_ct", 0.0140, 0.0080, 0.0060, -0.0405, 0.0320, "term_white")
    # 2 ESP32 devkit, upper centre
    part("ESP32", 0.0475, 0.0280, 0.0016, 0.0000, 0.0230, "pcb_black")
    part("ESP32_can", 0.0160, 0.0180, 0.0030, -0.0080, 0.0250, "shield")
    part("ESP32_usb", 0.0075, 0.0055, 0.0027, 0.0170, 0.0140, "shield")
    part("ESP32_h1", 0.0470, 0.0025, 0.0085, 0.0000, 0.0355, "header")
    part("ESP32_h2", 0.0470, 0.0025, 0.0085, 0.0000, 0.0105, "header")
    # 3 transformer, centre
    part("TRAFO", 0.0375, 0.0325, 0.0260, 0.0000, -0.0165, "trafo")
    part("TRAFO_bob", 0.0250, 0.0335, 0.0180, 0.0000, -0.0165, "bobbin")
    # 4 voltage sensor, upper right
    part("VSENSE", 0.0200, 0.0230, 0.0016, 0.0470, 0.0250, "pcb_blue")
    part("VSENSE_t", 0.0150, 0.0090, 0.0100, 0.0470, 0.0300, "term_green")
    # 5 AC-DC 5 V module, lower right
    part("ACDC", 0.0220, 0.0330, 0.0016, 0.0465, -0.0180, "pcb_green")
    part("ACDC_c1", 0.0080, 0.0080, 0.0110, 0.0400, -0.0080, "cap_blue")
    part("ACDC_c2", 0.0080, 0.0080, 0.0110, 0.0400, -0.0290, "cap_blue")
    part("ACDC_tr", 0.0110, 0.0110, 0.0105, 0.0530, -0.0180, "trafo")
    # standoffs
    for x in (-0.0150, 0.0230):
        part(f"hex{x}", 0.0060, 0.0060, 0.0075, x, -0.0165, "brass")
    return pcb, parts


def build_rotary(z):
    body = box("ROTARY", 0.0180, 0.0180, 0.0150, (KNOB_CX, FRONT_Y + 0.021, AXIS_Z))
    shaft = cyl("ROT_shaft", 0.0030, 0.020, (KNOB_CX, FRONT_Y + 0.008, AXIS_Z),
                rot=(math.radians(90), 0, 0), verts=24)
    return body, shaft
