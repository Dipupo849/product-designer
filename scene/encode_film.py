"""
PNG sequence -> H.264 MP4, via Blender's sequencer.

  blender -b -P encode_film.py -- [name] [fps]

The frames were written with AgX already applied, so the encode runs with a Standard
view transform - otherwise the tone map is applied a second time and the film crushes.
"""
import bpy, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SEQDIR = argv[0] if argv else "film"
NAME = argv[1] if len(argv) > 1 else "couch_film"
FPS = int(argv[2]) if len(argv) > 2 else 24
SEQ = os.path.join(HERE, "renders", SEQDIR)
OUT = os.path.join(HERE, "repo", "media", NAME)
os.makedirs(os.path.dirname(OUT), exist_ok=True)

files = sorted(f for f in os.listdir(SEQ) if f.startswith("f_") and f.endswith(".png"))
if not files:
    raise SystemExit("no frames in " + SEQ)

nums = [int(f[2:-4]) for f in files]
missing = sorted(set(range(min(nums), max(nums) + 1)) - set(nums))
if missing:
    print("WARNING missing frames:", missing[:20], "..." if len(missing) > 20 else "")

sc = bpy.context.scene
sc.sequence_editor_create()
se = sc.sequence_editor
# renamed sequences -> strips in 4.4. Test for the attribute, not its truthiness:
# a freshly created editor has an EMPTY collection, which is falsy.
strips = se.strips if hasattr(se, "strips") else se.sequences

img = bpy.data.images.load(os.path.join(SEQ, files[0]))
W, H = img.size
bpy.data.images.remove(img)

strip = strips.new_image(name="film", filepath=os.path.join(SEQ, files[0]),
                         channel=1, frame_start=1)
for f in files[1:]:
    strip.elements.append(f)
try:
    strip.colorspace_settings.name = "sRGB"
except Exception:
    pass

sc.frame_start, sc.frame_end = 1, len(files)
sc.render.fps = FPS
sc.render.fps_base = 1.0
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
sc.view_settings.view_transform = "Standard"     # frames are already display-referred
sc.view_settings.look = "None"
sc.view_settings.exposure = 0.0
# Blender 5 gates video output behind media_type; FFMPEG is not in the IMAGE enum
if hasattr(sc.render.image_settings, "media_type"):
    sc.render.image_settings.media_type = "VIDEO"
sc.render.image_settings.file_format = "FFMPEG"
ff = sc.render.ffmpeg
ff.format = "MPEG4"
ff.codec = "H264"
ff.constant_rate_factor = "MEDIUM"
ff.ffmpeg_preset = "GOOD"
ff.gopsize = 12
ff.audio_codec = "NONE"
sc.render.filepath = OUT

print(f"ENCODING {len(files)} frames  {W}x{H}  {FPS}fps  -> {OUT}.mp4", flush=True)
bpy.ops.render.render(animation=True)

for cand in (OUT + ".mp4", OUT + "0001-%04d.mp4" % len(files)):
    if os.path.exists(cand):
        if cand != OUT + ".mp4":
            os.replace(cand, OUT + ".mp4")
        print("WROTE %s  %.2f MB" % (OUT + ".mp4",
                                     os.path.getsize(OUT + ".mp4") / 1048576), flush=True)
        break
else:
    print("ENCODE OUTPUT NOT FOUND", flush=True)
