"""Materials, lighting rig, cameras and render driver. Cycles, physically based."""
import bpy, math
from mathutils import Vector


def set_in(node, names, value):
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return True
    return False


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves,
                  bpy.data.lights, bpy.data.cameras, bpy.data.objects):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def _fresh(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (960, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (620, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    geo = nt.nodes.new("ShaderNodeNewGeometry"); geo.location = (-1000, 0)
    return m, nt, bsdf, geo


# ------------------------------------------------------------------ leather
def mat_leather(name="leather", base=(0.030, 0.029, 0.030, 1.0),
                rough=0.42, sheen=0.15, grain=520.0, bump=0.13):
    m, nt, bsdf, geo = _fresh(name)
    N, L = nt.nodes, nt.links

    vor = N.new("ShaderNodeTexVoronoi"); vor.location = (-760, 240)
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = grain
    L.new(geo.outputs["Position"], vor.inputs["Vector"])
    r1 = N.new("ShaderNodeValToRGB"); r1.location = (-540, 240)
    r1.color_ramp.elements[0].position = 0.00
    r1.color_ramp.elements[1].position = 0.13
    L.new(vor.outputs["Distance"], r1.inputs["Fac"])
    b1 = N.new("ShaderNodeBump"); b1.location = (-300, 240)
    b1.inputs["Strength"].default_value = bump
    b1.inputs["Distance"].default_value = 0.0015
    L.new(r1.outputs["Color"], b1.inputs["Height"])

    nz = N.new("ShaderNodeTexNoise"); nz.location = (-760, -100)
    nz.inputs["Scale"].default_value = 78.0
    nz.inputs["Detail"].default_value = 6.0
    L.new(geo.outputs["Position"], nz.inputs["Vector"])
    b2 = N.new("ShaderNodeBump"); b2.location = (-60, 60)
    b2.inputs["Strength"].default_value = 0.055
    b2.inputs["Distance"].default_value = 0.004
    L.new(nz.outputs["Fac"], b2.inputs["Height"])
    L.new(b1.outputs["Normal"], b2.inputs["Normal"])
    L.new(b2.outputs["Normal"], bsdf.inputs["Normal"])

    nz2 = N.new("ShaderNodeTexNoise"); nz2.location = (-760, -420)
    nz2.inputs["Scale"].default_value = 24.0
    L.new(geo.outputs["Position"], nz2.inputs["Vector"])
    r2 = N.new("ShaderNodeValToRGB"); r2.location = (-500, -420)
    r2.color_ramp.elements[0].color = (max(rough - 0.08, 0.05),) * 3 + (1,)
    r2.color_ramp.elements[1].color = (min(rough + 0.08, 0.95),) * 3 + (1,)
    L.new(nz2.outputs["Fac"], r2.inputs["Fac"])
    L.new(r2.outputs["Color"], bsdf.inputs["Roughness"])

    bsdf.inputs["Base Color"].default_value = base
    set_in(bsdf, ["IOR"], 1.5)
    set_in(bsdf, ["Sheen Weight", "Sheen"], sheen)
    set_in(bsdf, ["Sheen Roughness"], 0.35)
    return m


# ------------------------------------------------------------------ wood
def mat_wood(name="ebonised_ash", base=(0.021, 0.019, 0.018, 1.0), rough=0.46):
    m, nt, bsdf, geo = _fresh(name)
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); tc.location = (-1000, 200)
    wav = N.new("ShaderNodeTexWave"); wav.location = (-700, 200)
    wav.wave_type = "BANDS"; wav.bands_direction = "Z"
    wav.inputs["Scale"].default_value = 5.0
    wav.inputs["Distortion"].default_value = 18.0
    wav.inputs["Detail"].default_value = 4.0
    L.new(tc.outputs["Object"], wav.inputs["Vector"])
    b = N.new("ShaderNodeBump"); b.location = (-300, 120)
    b.inputs["Strength"].default_value = 0.10
    b.inputs["Distance"].default_value = 0.002
    L.new(wav.outputs["Fac"], b.inputs["Height"])
    L.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    r = N.new("ShaderNodeValToRGB"); r.location = (-420, -220)
    r.color_ramp.elements[0].color = (rough - 0.06,) * 3 + (1,)
    r.color_ramp.elements[1].color = (rough + 0.06,) * 3 + (1,)
    L.new(wav.outputs["Fac"], r.inputs["Fac"])
    L.new(r.outputs["Color"], bsdf.inputs["Roughness"])
    bsdf.inputs["Base Color"].default_value = base
    set_in(bsdf, ["IOR"], 1.52)
    return m


def mat_simple(name, base, rough=0.5, metallic=0.0, ior=1.5):
    m, nt, bsdf, geo = _fresh(name)
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    set_in(bsdf, ["IOR"], ior)
    return m


def mat_metal(name, base, rough=0.30):
    return mat_simple(name, base, rough=rough, metallic=1.0)


def mat_emissive(name, color, strength):
    m, nt, bsdf, geo = _fresh(name)
    N, L = nt.nodes, nt.links
    em = N.new("ShaderNodeEmission"); em.location = (620, -240)
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    out = [n for n in N if n.type == "OUTPUT_MATERIAL"][0]
    L.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def mat_oak_floor(name="oak_floor"):
    m, nt, bsdf, geo = _fresh(name)
    N, L = nt.nodes, nt.links
    # plank seams
    wav = N.new("ShaderNodeTexWave"); wav.location = (-760, 260)
    wav.wave_type = "BANDS"; wav.bands_direction = "Y"
    wav.wave_profile = "SAW"
    wav.inputs["Scale"].default_value = 4.2
    wav.inputs["Distortion"].default_value = 0.6
    L.new(geo.outputs["Position"], wav.inputs["Vector"])
    seam = N.new("ShaderNodeValToRGB"); seam.location = (-540, 260)
    seam.color_ramp.elements[0].position = 0.0
    seam.color_ramp.elements[1].position = 0.045
    L.new(wav.outputs["Fac"], seam.inputs["Fac"])
    b = N.new("ShaderNodeBump"); b.location = (-300, 200)
    b.inputs["Strength"].default_value = 0.25
    b.inputs["Distance"].default_value = 0.004
    L.new(seam.outputs["Color"], b.inputs["Height"])
    # grain
    grain = N.new("ShaderNodeTexNoise"); grain.location = (-760, -60)
    grain.inputs["Scale"].default_value = 8.0
    grain.inputs["Detail"].default_value = 8.0
    L.new(geo.outputs["Position"], grain.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB"); ramp.location = (-500, -60)
    ramp.color_ramp.elements[0].color = (0.196, 0.132, 0.078, 1)
    ramp.color_ramp.elements[1].color = (0.318, 0.226, 0.140, 1)
    L.new(grain.outputs["Fac"], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    L.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.34
    set_in(bsdf, ["IOR"], 1.5)
    return m


def mat_wool_rug(name="wool_rug"):
    """Flat grey read as a card rectangle; wool needs tonal break-up and sheen."""
    m, nt, bsdf, geo = _fresh(name)
    N, L = nt.nodes, nt.links
    nz = N.new("ShaderNodeTexNoise"); nz.location = (-760, 0)
    nz.inputs["Scale"].default_value = 42.0
    nz.inputs["Detail"].default_value = 8.0
    L.new(geo.outputs["Position"], nz.inputs["Vector"])
    r = N.new("ShaderNodeValToRGB"); r.location = (-500, 0)
    r.color_ramp.elements[0].color = (0.196, 0.184, 0.166, 1)
    r.color_ramp.elements[1].color = (0.310, 0.293, 0.266, 1)
    L.new(nz.outputs["Fac"], r.inputs["Fac"])
    L.new(r.outputs["Color"], bsdf.inputs["Base Color"])
    b = N.new("ShaderNodeBump"); b.location = (-280, -220)
    b.inputs["Strength"].default_value = 0.35
    b.inputs["Distance"].default_value = 0.004
    L.new(nz.outputs["Fac"], b.inputs["Height"])
    L.new(b.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.95
    set_in(bsdf, ["Sheen Weight", "Sheen"], 0.45)
    set_in(bsdf, ["Sheen Roughness"], 0.5)
    return m


def assign(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)


def clay_override(exclude=("cyc", "ground", "floor", "ceiling"), shade=0.235):
    """Strip every material to matte clay - the geometry pass for CAD/render comparisons."""
    clay = mat_simple("clay", (shade, shade, shade * 1.02, 1), rough=0.66, ior=1.45)
    for ob in bpy.context.scene.objects:
        if ob.type not in {"MESH", "CURVE"}:
            continue
        if any(ob.name.startswith(p) for p in exclude):
            continue
        try:
            ob.data.materials.clear()
            ob.data.materials.append(clay)
        except Exception:
            pass
    return clay


def smooth_auto(ob, deg=32.0):
    """Smooth curved faces, keep hard edges hard. Auto-smooth moved twice in 4.x."""
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(deg))
        return
    except Exception:
        pass
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(deg))
        return
    except Exception:
        pass
    try:
        bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=math.radians(deg))
    except Exception:
        bpy.ops.object.shade_smooth()


# ------------------------------------------------------------------ world
def world_studio(top=0.055, bottom=0.012):
    w = bpy.data.worlds.new("studio") if not bpy.data.worlds else bpy.data.worlds[0]
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld"); out.location = (400, 0)
    bg = nt.nodes.new("ShaderNodeBackground"); bg.location = (200, 0)
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-500, 0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); sep.location = (-320, 0)
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (-140, 0)
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (bottom, bottom, bottom * 1.05, 1)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = (top, top, top * 1.08, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bg.inputs["Strength"].default_value = 1.0
    return w


# ------------------------------------------------------------------ lights
def area_light(name, loc, target, size, size_y, energy, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = size, size_y
    ld.energy = energy
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def rig_studio(target=(0, 0, 0.45), key=900.0, fill=170.0, rim=420.0):
    """Key 3x4 m at 45 deg, fill 2x3 m opposite, narrow strip rim behind."""
    area_light("KEY", (-1.70, -2.75, 2.30), target, 3.0, 4.0, key, (1.0, 0.985, 0.96))
    area_light("FILL", (3.05, -0.55, 1.60), target, 2.0, 3.0, fill, (0.95, 0.97, 1.0))
    area_light("RIM", (-0.55, 1.95, 1.85), target, 2.6, 0.5, rim, (1.0, 0.975, 0.94))
    return True


# ------------------------------------------------------------------ backdrop
def cyclorama(y_flat=1.9, radius=1.7, back_h=5.0, width=9.0, front=-7.0, rotz=0.0):
    """Seamless studio sweep: floor running into a curved back wall."""
    prof = [(front, 0.0), (y_flat, 0.0)]
    for i in range(1, 17):
        a = (math.pi / 2) * (i / 16)
        prof.append((y_flat + radius * math.sin(a), radius * (1 - math.cos(a))))
    prof.append((y_flat + radius, back_h))
    verts, faces = [], []
    for (y, z) in prof:
        verts.append((-width, y, z))
        verts.append((width, y, z))
    for i in range(len(prof) - 1):
        a = i * 2
        faces.append([a, a + 1, a + 3, a + 2])
    me = bpy.data.meshes.new("cyc")
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("cyc", me)
    bpy.context.collection.objects.link(ob)
    ob.rotation_euler = (0.0, 0.0, math.radians(rotz))
    return ob


def drum(r_floor=6.5, cove=1.5, r_wall=8.0, wall_h=6.5, seg=96, rings=14):
    """Seamless cyclorama drum: floor, coved wall, revolved 360 deg. A one-sided
    sweep shows its own edge as soon as the camera orbits past it."""
    prof = [(0.0, 0.0), (r_floor, 0.0)]
    for i in range(1, rings + 1):
        a = -math.pi / 2 + (math.pi / 2) * (i / rings)
        prof.append((r_floor + cove * math.cos(a), cove + cove * math.sin(a)))
    prof.append((r_wall, wall_h))

    verts, faces = [], []
    verts.append((0.0, 0.0, 0.0))                      # floor centre
    for (r, z) in prof[1:]:
        for k in range(seg):
            t = 2 * math.pi * k / seg
            verts.append((r * math.cos(t), r * math.sin(t), z))
    for k in range(seg):                               # centre fan
        faces.append([0, 1 + k, 1 + (k + 1) % seg])
    nrings = len(prof) - 1
    for i in range(nrings - 1):
        a, b = 1 + i * seg, 1 + (i + 1) * seg
        for k in range(seg):
            k2 = (k + 1) % seg
            faces.append([a + k, a + k2, b + k2, b + k])
    me = bpy.data.meshes.new("cyc")
    me.from_pydata(verts, [], faces)
    me.validate(); me.update()
    for pgn in me.polygons:
        pgn.use_smooth = True
    ob = bpy.data.objects.new("cyc", me)
    bpy.context.collection.objects.link(ob)
    return ob


def ground_plane(size=40.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    ob = bpy.context.active_object
    ob.name = "ground"
    return ob


# ------------------------------------------------------------------ camera
def camera(name, distance, height, azimuth_deg, target, lens=50.0, fstop=5.6,
           focus_point=None, shift_y=0.0):
    """Azimuth 0 = straight on the front (-Y); positive rotates to the right (+X)."""
    a = math.radians(azimuth_deg)
    loc = Vector((distance * math.sin(a), -distance * math.cos(a), height))
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.shift_y = shift_y
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    fp = Vector(focus_point if focus_point else target)
    cd.dof.focus_distance = (fp - loc).length
    ob = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - loc).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = ob
    return ob


def camera_at(loc, target, lens=85.0, fstop=8.0, focus=None):
    """Explicit placement. Use for macros, where distance-from-origin is meaningless."""
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


# ------------------------------------------------------------------ render
def render(path, res=(1600, 1000), samples=200, exposure=0.0, transparent=False):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        sc.cycles.device = "CPU"
    except Exception:
        pass
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.012
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 12
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 6
    sc.cycles.transmission_bounces = 8
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    sc.render.filepath = path
    sc.view_settings.view_transform = "AgX"
    for look in ("AgX - Base Contrast", "AgX - Medium High Contrast", "None"):
        try:
            sc.view_settings.look = look
            break
        except TypeError:
            continue
    sc.view_settings.exposure = exposure
    bpy.ops.render.render(write_still=True)
    print("WROTE", path, flush=True)
