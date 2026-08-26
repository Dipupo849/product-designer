"""
COUCH - 2.5-seat leather sofa.
Geometry reconstructed from the 3ds Max reference at the dimensions recorded in the
dossier. Units are metres; 1 Blender unit = 1 m.

  overall      1.920 W x 0.820 D x 0.800 H
  seat height  0.430          cushion 0.130
  arm height   0.620          arm width 0.090
  back rake    14 deg         leg splay 8 deg on both axes
  tufting      11 buttons at 0.150 pitch, 0.694 above floor
"""
import bpy, bmesh, math
from mathutils import Vector

# ---------------------------------------------------------------- dimensions
W, D, H = 1.920, 0.820, 0.800
HALF_W, HALF_D = W / 2, D / 2          # x in [-.96,.96]  y in [-.41,.41] (+y = back)
SEAT_H, CUSH_T = 0.430, 0.130
DECK_H = SEAT_H - CUSH_T               # 0.300
FRAME_BOT = 0.260                      # underside of upholstery / top of legs
ARM_H, ARM_W = 0.620, 0.090
BACK_T = 0.110
RAKE = math.radians(14.0)
SPLAY = math.radians(8.0)
N_BUTTON, BUTTON_PITCH, BUTTON_Z = 11, 0.150, 0.694
CROWN = 0.008

ARM_HW, BACK_HW = ARM_W / 2, BACK_T / 2
ARM_CX = HALF_W - ARM_HW               # 0.915  arm centreline
BACK_CY = HALF_D - BACK_HW             # 0.355  back centreline
CORNER_R = 0.110


def smoothstep(a, b, x):
    if b == a:
        return 0.0
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- helpers
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves,
                  bpy.data.lights, bpy.data.cameras, bpy.data.objects):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def new_mesh(name, verts, faces, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def set_in(node, names, value):
    """Principled socket names moved around between Blender versions."""
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return True
    return False


# ---------------------------------------------------------------- rail path
def rail_path(samples_straight=44, samples_corner=16):
    """
    Centreline of the continuous back+arm rail, walked front-left -> back -> front-right.
    Returns [(x, y, nx, ny, s)] with outward normal and cumulative arc length.
    """
    pts = []
    y_corner = BACK_CY - CORNER_R          # 0.245
    y_front = -HALF_D + 0.045

    # left arm, front -> back
    for i in range(samples_straight + 1):
        t = i / samples_straight
        pts.append((-ARM_CX, y_front + t * (y_corner - y_front), -1.0, 0.0))
    # left back corner: centre (-ARM_CX+R, y_corner), 180deg -> 90deg
    cx, cy = -ARM_CX + CORNER_R, y_corner
    for i in range(1, samples_corner + 1):
        a = math.pi - (math.pi / 2) * (i / samples_corner)
        pts.append((cx + CORNER_R * math.cos(a), cy + CORNER_R * math.sin(a),
                    math.cos(a), math.sin(a)))
    # back span
    x0, x1 = -ARM_CX + CORNER_R, ARM_CX - CORNER_R
    n_back = samples_straight * 2
    for i in range(1, n_back + 1):
        pts.append((x0 + (x1 - x0) * (i / n_back), BACK_CY, 0.0, 1.0))
    # right back corner: 90deg -> 0deg
    cx = ARM_CX - CORNER_R
    for i in range(1, samples_corner + 1):
        a = (math.pi / 2) * (1 - i / samples_corner)
        pts.append((cx + CORNER_R * math.cos(a), cy + CORNER_R * math.sin(a),
                    math.cos(a), math.sin(a)))
    # right arm, back -> front
    for i in range(1, samples_straight + 1):
        t = i / samples_straight
        pts.append((ARM_CX, y_corner + t * (y_front - y_corner), 1.0, 0.0))

    out, s = [], 0.0
    for i, (x, y, nx, ny) in enumerate(pts):
        if i:
            s += math.dist((x, y), (pts[i - 1][0], pts[i - 1][1]))
        out.append((x, y, nx, ny, s))
    return out


def rail_profile(hw, top, arc=11):
    """Cross-section loop: outer face up, over the rounded top, inner face down."""
    r = hw
    ring = [(hw, FRAME_BOT), (hw, top - r)]
    for k in range(1, arc):
        a = math.pi * k / arc
        ring.append((hw * math.cos(a), (top - r) + r * math.sin(a)))
    ring += [(-hw, top - r), (-hw, FRAME_BOT)]
    return ring


def build_rail():
    path = rail_path()
    total = path[-1][4]
    arm_len = path[0][4]  # 0
    # arc length at which the rise into the back starts / ends
    rise_a, rise_b = 0.26, 1.10
    rings, ring_len = [], None

    for (x, y, nx, ny, s) in path:
        # symmetric parameter: distance from nearest front tip
        ds = min(s, total - s)
        k = smoothstep(rise_a, rise_b, ds)
        top = ARM_H + (H - ARM_H) * k
        hw = ARM_HW + (BACK_HW - ARM_HW) * k
        # gentle crown across the back span only
        if abs(y - BACK_CY) < 1e-6:
            u = (x + ARM_CX) / (2 * ARM_CX)
            top += CROWN * math.sin(math.pi * u)
        prof = rail_profile(hw, top)
        ring_len = len(prof)
        rings.append([(x + nx * u, y + ny * u, v) for (u, v) in prof])

    verts, faces = [], []
    for ring in rings:
        verts.extend(ring)
    for i in range(len(rings) - 1):
        a, b = i * ring_len, (i + 1) * ring_len
        for j in range(ring_len):
            j2 = (j + 1) % ring_len
            faces.append([a + j, a + j2, b + j2, b + j])
    # flat caps at the two arm tips; bevel+subsurf rounds them off
    faces.append(list(range(ring_len - 1, -1, -1)))
    base = (len(rings) - 1) * ring_len
    faces.append(list(range(base, base + ring_len)))

    ob = new_mesh("COUCH_rail", verts, faces)
    bev = ob.modifiers.new("bevel", "BEVEL")
    bev.width, bev.segments, bev.limit_method = 0.020, 4, "ANGLE"
    bev.angle_limit = math.radians(35)
    sub = ob.modifiers.new("subsurf", "SUBSURF")
    sub.levels, sub.render_levels = 1, 2
    return ob


# ---------------------------------------------------------------- tufted back
PANEL_X0, PANEL_X1 = -ARM_CX + ARM_HW, ARM_CX - ARM_HW    # -0.87 .. 0.87
PANEL_Z0, PANEL_Z1 = SEAT_H - 0.020, H - 0.032            # 0.410 .. 0.768
PANEL_Y = BACK_CY - BACK_HW                               # 0.300, flush with rail
BULGE, PULL, SIGMA = 0.030, 0.016, 0.048
BUTTON_X = [(i - (N_BUTTON - 1) / 2) * BUTTON_PITCH for i in range(N_BUTTON)]


def panel_surface(x, z):
    """World y of the cover at (x, z): raked plane, pillowed, pulled in at each button."""
    tx = (x - PANEL_X0) / (PANEL_X1 - PANEL_X0)
    tz = (z - PANEL_Z0) / (PANEL_Z1 - PANEL_Z0)
    tx = min(max(tx, 0.0), 1.0); tz = min(max(tz, 0.0), 1.0)
    y_plane = PANEL_Y - (PANEL_Z1 - z) * math.tan(RAKE)
    edge = math.sin(math.pi * tx) ** 0.55 * math.sin(math.pi * tz) ** 0.55
    pull = sum(PULL * math.exp(-(math.dist((x, z), (bx, BUTTON_Z)) / SIGMA) ** 2)
               for bx in BUTTON_X)
    return y_plane - BULGE * edge + pull * edge


def build_back_panel():
    """Inner face of the back: raked, pillowed between buttons, pulled in at each."""
    nx_, nz_ = 150, 54
    x0, x1 = PANEL_X0, PANEL_X1
    z0, z1 = PANEL_Z0, PANEL_Z1
    y_top = PANEL_Y
    buttons = BUTTON_X

    verts, faces = [], []
    for iz in range(nz_ + 1):
        tz = iz / nz_
        z = z0 + tz * (z1 - z0)
        for ix in range(nx_ + 1):
            x = x0 + (ix / nx_) * (x1 - x0)
            verts.append((x, panel_surface(x, z), z))
    for iz in range(nz_):
        for ix in range(nx_):
            a = iz * (nx_ + 1) + ix
            b = a + 1
            c = a + nx_ + 2
            d = a + nx_ + 1
            faces.append([a, b, c, d])

    ob = new_mesh("COUCH_back_panel", verts, faces)
    sol = ob.modifiers.new("solid", "SOLIDIFY")
    sol.thickness, sol.offset = 0.028, -1.0
    sub = ob.modifiers.new("subsurf", "SUBSURF")
    sub.levels, sub.render_levels = 0, 1
    return ob, buttons


def build_buttons(buttons):
    obs = []
    for i, bx in enumerate(buttons):
        y = panel_surface(bx, BUTTON_Z) - 0.003
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.013, segments=28, ring_count=14,
                                             location=(bx, y, BUTTON_Z))
        ob = bpy.context.active_object
        ob.name = f"COUCH_button_{i:02d}"
        ob.scale = (1.0, 0.50, 1.0)
        bpy.ops.object.shade_smooth()
        obs.append(ob)
    return obs


# ---------------------------------------------------------------- cushion
def build_cushion():
    """Bench cushion as a closed plump slab: bevel + subsurf reads as upholstery,
    where a solidified grid read as a flat plank."""
    x0, x1 = -ARM_CX + ARM_HW + 0.006, ARM_CX - ARM_HW - 0.006
    y0, y1 = -HALF_D + 0.022, 0.222
    z0, z1 = DECK_H - 0.004, SEAT_H
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    ob.name = "COUCH_cushion"
    ob.scale = (x1 - x0, y1 - y0, z1 - z0)
    ob.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    bpy.ops.object.transform_apply(scale=True)
    # a few cuts so subsurf has somewhere to hold the length
    bpy.ops.object.modifier_add(type="SUBSURF")
    md = ob.modifiers[-1]; md.subdivision_type = "SIMPLE"; md.levels = md.render_levels = 2
    bpy.ops.object.modifier_apply(modifier=md.name)
    bev = ob.modifiers.new("bevel", "BEVEL")
    bev.width, bev.segments, bev.limit_method = 0.052, 6, "ANGLE"
    bev.angle_limit = math.radians(30)
    sub = ob.modifiers.new("subsurf", "SUBSURF")
    sub.levels, sub.render_levels = 1, 2
    bpy.ops.object.shade_smooth()
    return ob


def build_seat_welt():
    """Welt cord round the cushion's front and two sides, at cushion mid height."""
    x0, x1 = -ARM_CX + ARM_HW + 0.012, ARM_CX - ARM_HW - 0.012
    y_f, y_b = -HALF_D + 0.028, 0.20
    z = (DECK_H + SEAT_H) / 2 - 0.004
    r = 0.055
    pts = []
    pts.append((x0, y_b))
    n = 10
    for i in range(n + 1):                       # front-left round
        a = math.pi + (math.pi / 2) * (i / n)
        pts.append((x0 + r + r * math.cos(a), y_f + r + r * math.sin(a)))
    for i in range(n + 1):                       # front-right round
        a = -math.pi / 2 + (math.pi / 2) * (i / n)
        pts.append((x1 - r + r * math.cos(a), y_f + r + r * math.sin(a)))
    pts.append((x1, y_b))
    cu = bpy.data.curves.new("COUCH_seat_welt_curve", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution, cu.resolution_u = 0.0028, 5, 4
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts):
        sp.points[i].co = (x, y, z, 1.0)
    ob = bpy.data.objects.new("COUCH_seat_welt", cu)
    bpy.context.collection.objects.link(ob)
    return ob


def build_apron():
    """Frame band between the cushion and the legs."""
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    ob.name = "COUCH_apron"
    ob.scale = (2 * (HALF_W - 0.012), 2 * (HALF_D - 0.012), DECK_H - FRAME_BOT)
    ob.location = (0, 0, (DECK_H + FRAME_BOT) / 2)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bev = ob.modifiers.new("bevel", "BEVEL")
    bev.width, bev.segments = 0.010, 3
    bpy.ops.object.shade_smooth()
    return ob


# ---------------------------------------------------------------- welt + legs
def build_welt():
    """Piping along the top of the rail - the one seam allowed to show."""
    path = rail_path(samples_straight=40, samples_corner=14)
    total = path[-1][4]
    cu = bpy.data.curves.new("COUCH_welt_curve", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution = 0.0026, 5
    cu.resolution_u = 4
    sp = cu.splines.new("POLY")
    sp.points.add(len(path) - 1)
    for i, (x, y, nx, ny, s) in enumerate(path):
        ds = min(s, total - s)
        k = smoothstep(0.26, 1.10, ds)
        top = ARM_H + (H - ARM_H) * k
        hw = ARM_HW + (BACK_HW - ARM_HW) * k
        if abs(y - BACK_CY) < 1e-6:
            u = (x + ARM_CX) / (2 * ARM_CX)
            top += CROWN * math.sin(math.pi * u)
        # ride just outboard of the crown
        sp.points[i].co = (x + nx * hw * 0.70, y + ny * hw * 0.70, top - hw * 0.52, 1.0)
    ob = bpy.data.objects.new("COUCH_welt", cu)
    bpy.context.collection.objects.link(ob)
    return ob


def build_legs():
    legs = []
    xs = [(-ARM_CX, -1), (ARM_CX, 1)]
    ys = [(-HALF_D + 0.056, -1), (HALF_D - 0.140, 1)]
    length = FRAME_BOT / math.cos(SPLAY * math.sqrt(2))
    for (x, sx) in xs:
        for (y, sy) in ys:
            bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.019, radius2=0.0105,
                                            depth=length + 0.03)
            ob = bpy.context.active_object
            ob.name = "COUCH_leg"
            ob.rotation_euler = (sy * SPLAY, -sx * SPLAY, 0)
            ob.location = (x, y, FRAME_BOT / 2)
            bpy.context.view_layer.update()
            from mathutils import Vector as _V
            minz = min((ob.matrix_world @ _V(c)).z for c in ob.bound_box)
            ob.location.z -= minz            # stand the splayed leg on the floor
            bpy.ops.object.shade_smooth()
            legs.append(ob)
    return legs
