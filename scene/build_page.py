"""
Rebuild stages 05 and 06 of the dossier around the actual renders.

  build_page.py            -> artifact.html (data URIs, self-contained)
                              repo/index.html (img/ files, srcset + lazy)
"""
import os, json, sys, re, base64

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "dossier.html")
MAN = os.path.join(HERE, "manifest.json")

manifest = json.load(open(MAN)) if os.path.exists(MAN) else {}
have = set(manifest)

# ---------------------------------------------------------------- shot table
COUCH = [
    ("couch_hero",      "HERO 01",      "Three-quarter visualization, contemporary interior",
     "50 mm · f/4 · camera 0.96 m · north window key"),
    ("couch_studio",    "HERO 02",      "Studio visualization, seamless neutral sweep",
     "85 mm · f/7.1 · 3 × 4 m key at 45° · strip rim"),
    ("couch_front",     "VIEW 01",      "Front elevation, long lens",
     "135 mm · f/11 · camera 7.4 m · perspective flattened"),
    ("couch_rear",      "VIEW 02",      "Rear three-quarter — the outside back",
     "85 mm · f/5.6 · rim-led, proves the single continuous skin"),
    ("couch_detail",    "DETAIL 01",    "Tufting, welt cord and hide grain",
     "105 mm · f/4 · 0.62 m · focus on the button crown"),
    ("couch_lifestyle", "LIFESTYLE 01", "Contemporary interior, north light",
     "35 mm · f/3.5 · eye level 1.50 m"),
    ("couch_alt",       "FINISH 01",    "Alternate colourway — cognac aniline",
     "Same geometry and rig; base colour swapped in the material graph"),
]
PARAM = [
    ("param_hero",     "HERO 03",     "Three-quarter product visualization",
     "85 mm · f/8 · 0.70 × 0.90 m key softbox"),
    ("param_studio",   "HERO 04",     "Studio visualization, light sweep",
     "100 mm · f/9 · lifted backdrop"),
    ("param_front",    "VIEW 03",     "Front elevation, display driven",
     "120 mm · f/11 · STN backlight at 14 W emissive"),
    ("param_rear",     "VIEW 04",     "Rear elevation — unbroken face",
     "85 mm · f/8 · no rear features exist in the source"),
    ("param_top",      "VIEW 05",     "Plan, lid removed",
     "100 mm · f/11 · nadir · all ten components in place"),
    ("param_exploded", "ASSEMBLY 01", "Exploded assembly",
     "85 mm · f/11 · lid +75 mm, board +30 mm on the boss axis"),
    ("param_controls", "DETAIL 02",   "Control interface and display window",
     "100 mm · f/4 · knurl and dot matrix at true scale"),
]

CAPTION_NOTE = ("Path-traced in Blender Cycles from geometry rebuilt to the dossier "
                "dimensions. Not a photograph, not an AI-generated image.")


def img_tag(name, cls="", sizes="100vw", eager=False):
    """Artifact build inlines; repo build references files with srcset."""
    m = manifest[name]
    alt = ALT.get(name, name.replace("_", " "))
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    if MODE == "artifact":
        return (f'<img class="{cls}" src="{m["embed"]}" alt="{alt}" '
                f'width="{m["w"]}" height="{m["h"]}" {load} decoding="async">')
    files = m["files"]
    srcset = ", ".join(f'{v["file"]} {w}w' for w, v in sorted(files.items()))
    big = files[max(files)]["file"]
    return (f'<img class="{cls}" src="{big}" srcset="{srcset}" sizes="{sizes}" '
            f'alt="{alt}" width="{m["w"]}" height="{m["h"]}" {load} decoding="async">')


ALT = {
    "couch_hero": "The black leather sofa seen at three-quarters in a contemporary room with an oak floor and north-facing window.",
    "couch_studio": "The sofa isolated on a neutral studio sweep with a soft contact shadow.",
    "couch_front": "Straight-on front view of the sofa showing the continuous top rail and eleven button tufts.",
    "couch_rear": "Rear three-quarter view showing the unbroken outside back.",
    "couch_detail": "Macro of a self-covered button, the welt cord and the pore grain of the hide.",
    "couch_lifestyle": "Wide interior view with the sofa, a rug, a side table and an oval wall piece.",
    "couch_alt": "The same sofa rendered in cognac aniline leather instead of black.",
    "couch_clay": "Untextured clay pass of the sofa geometry at the studio camera.",
    "param_hero": "Three-quarter view of the cream ABS instrument enclosure with its display lit.",
    "param_studio": "Studio view of the enclosure on a light sweep.",
    "param_front": "Front view of the enclosure, display showing live readings.",
    "param_rear": "Rear view of the enclosure showing an unbroken face.",
    "param_top": "Plan view with the lid removed, showing the populated board.",
    "param_exploded": "Exploded view: lid, board and base separated on the boss axis.",
    "param_controls": "Close-up of the knurled control knob and the display window edge.",
    "param_clay": "Untextured clay pass of the enclosure geometry at the hero camera.",
}


def shot_fig(name, sid, desc, tech, lead=False):
    if name not in have:
        return ""
    cls = "shot shot-lead" if lead else "shot"
    sizes = "(max-width: 900px) 100vw, 1200px" if lead else "(max-width: 700px) 100vw, 620px"
    return f"""<figure class="{cls}">
  {img_tag(name, "shot-img", sizes, eager=lead)}
  <figcaption class="shot-cap">
    <span class="shot-id">{sid}</span>
    <span class="shot-desc">{desc}</span>
    <span class="shot-tech">{tech}</span>
  </figcaption>
</figure>"""


def gallery(rows, lead_first=True):
    out, rows = [], list(rows)
    if lead_first and rows and rows[0][0] in have:
        out.append(shot_fig(*rows[0], lead=True))
        rows = rows[1:]
    figs = [shot_fig(*r) for r in rows]
    figs = [f for f in figs if f]
    if figs:
        out.append('<div class="shotgrid">' + "".join(figs) + "</div>")
    return "\n".join(out)


def before_after(clay, final, title, note):
    if clay not in have or final not in have:
        return ""
    uid = clay.replace("_", "-")
    return f"""<div class="ba rv">
  <div class="ba-head">
    <span class="lbl lbl-a">From CAD to visualization</span>
    <h3>{title}</h3>
    <p>{note}</p>
  </div>
  <div class="ba-stage" id="ba-{uid}">
    <div class="ba-base">{img_tag(final, "ba-img", "(max-width:900px) 100vw, 1100px")}</div>
    <div class="ba-clip">{img_tag(clay, "ba-img", "(max-width:900px) 100vw, 1100px")}</div>
    <span class="ba-tag ba-tag-l">Source geometry</span>
    <span class="ba-tag ba-tag-r">Final visualization</span>
    <input class="ba-range" type="range" min="0" max="100" value="50" step="0.1"
           aria-label="Reveal source geometry against final visualization">
    <div class="ba-divider" aria-hidden="true"></div>
  </div>
  <p class="ba-foot mono">Source geometry &rarr; Final visualization</p>
</div>"""


def progression():
    steps = [
        ("Technical source", "Fusion 360 / 3ds Max reference", "svg-elev"),
        ("3D model", "Rebuilt geometry, clay pass", "couch_clay"),
        ("Material development", "Aniline hide, ebonised ash", "couch_detail"),
        ("Photorealistic visualization", "Cycles, path traced", "couch_studio"),
        ("Final product", "Catalogue plate", "couch_hero"),
    ]
    cells = []
    for i, (title, sub, key) in enumerate(steps):
        if key == "svg-elev":
            media = ('<div class="prog-svg">'
                     '<svg viewBox="0 0 240 120" role="img" aria-label="Front elevation line drawing">'
                     '<path fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round" '
                     'd="M24 92 L24 44 C24 40 27 37 31 37 L36 37 C42 37 43 30 44 25 '
                     'C45 19 48 16 53 16 L187 16 C192 16 195 19 196 25 C197 30 198 37 204 37 '
                     'L209 37 C213 37 216 40 216 44 L216 92 Z"/>'
                     '<path fill="none" stroke="currentColor" stroke-width="2" opacity=".5" '
                     'd="M36 76 L204 76 M44 37 L44 76 M196 37 L196 76"/>'
                     '<path fill="none" stroke="currentColor" stroke-width="3" '
                     'd="M40 92 L34 116 M200 92 L206 116"/>'
                     '</svg></div>')
        elif key in have:
            media = f'<div class="prog-img">{img_tag(key, "", "220px")}</div>'
        else:
            continue
        cells.append(f'<li class="prog-step"><span class="prog-n mono">{i+1:02d}</span>'
                     f'{media}<h4>{title}</h4><p>{sub}</p></li>')
    return ('<ol class="prog rv">' + "".join(cells) + "</ol>") if cells else ""


FILMS = [
    ("couch_film", "COUCH", "couch_film_poster", "couch_hero", "19 s · 456 frames · six shots",
     [("0:00", "01 Reveal", "Rig rises out of near-black on a slow push"),
      ("0:03", "02 Hero three-quarter", "Catalogue composition, slow drift in"),
      ("0:05", "03 360° orbit", "One continuous revolution, constant speed"),
      ("0:11", "04 Material detail", "Tufting, welt cord and hide grain"),
      ("0:14", "05 Construction detail", "Upholstery meeting frame and leg"),
      ("0:16", "06 Final hero", "Returns home and holds")]),
    ("param_film", "PARAMETER", "param_film_poster", "param_hero", "13 s · 312 frames · five shots",
     [("0:00", "01 Reveal", "Out of near-black, display already lit"),
      ("0:02", "02 Hero", "Three-quarter product angle"),
      ("0:04", "03 360° orbit", "Full revolution showing shell and lid line"),
      ("0:09", "04 Technical detail", "Knurled control across to the display window"),
      ("0:11", "05 Final hero", "Returns home and holds")]),
]


def media_path(name):
    return os.path.join(HERE, "repo", "media", name + ".mp4")


def poster_src(poster, fallback):
    key = poster if poster in manifest else (fallback if fallback in manifest else None)
    if not key:
        return ""
    m = manifest[key]
    return m["embed"] if MODE == "artifact" else m["files"][max(m["files"])]["file"]


def video_tag(name, poster, fallback):
    src = "media/%s.mp4" % name
    if MODE == "artifact":
        with open(media_path(name), "rb") as f:
            src = "data:video/mp4;base64," + base64.b64encode(f.read()).decode()
    ps = poster_src(poster, fallback)
    pa = ' poster="%s"' % ps if ps else ""
    # preload="none" - nothing downloads until the viewer presses play
    return ('<video class="film-v" controls playsinline preload="none"%s>'
            '<source src="%s" type="video/mp4">'
            "This browser cannot play the file; it is also in the repository under "
            "<code>media/</code>.</video>" % (pa, src))


def film_card(entry):
    name, title, poster, fallback, meta, shots = entry
    rows = "".join(
        '<li class="fs-row"><span class="fs-t mono">%s</span>'
        '<span class="fs-n">%s</span><span class="fs-d">%s</span></li>' % (t, n, d)
        for (t, n, d) in shots)
    return ('<figure class="film">'
            '<div class="film-stage">%s</div>'
            '<figcaption class="film-cap">'
            '<span class="shot-id">Product film — %s</span>'
            '<span class="shot-tech">%s</span>'
            '<ol class="film-shots">%s</ol>'
            "</figcaption></figure>"
            % (video_tag(name, poster, fallback), title, meta, rows))


def film_section():
    ready = [f for f in FILMS if os.path.exists(media_path(f[0]))]
    head = ('<span class="lbl">Stage 06</span>'
            "<h2>Product Film</h2>")
    if not ready:
        body = ('<div class="motion rv"><div class="motion-head">'
                '<span class="lbl lbl-a">Not yet rendered</span>'
                "<h3>The films are still rendering</h3></div>"
                '<div class="motion-frame"><p class="motion-note">No MP4 exists yet, so '
                "nothing is embedded here. This panel is a placeholder, not a still "
                "presented as footage.</p></div></div>")
        lede = ("Two cinematic product films. They are not published until the MP4 files "
                "actually exist.")
    else:
        body = ('<div class="filmgrid">' + "".join(film_card(f) for f in ready) + "</div>")
        lede = ("Two films, path-traced frame by frame in Blender Cycles at 854 × 480, "
                "24 fps — 768 frames in total. Nothing is interpolated from stills and "
                "nothing is AI-generated. The product itself never moves: across every "
                "frame the geometry, proportions and materials are the ones used for the "
                "stills, and only the camera and the opening light ramp are animated.")
    return f"""<section class="sec" id="s06">
  <div class="wrap bind">
    <span class="bind-n">06</span>
    <div class="sec-head rv">
      {head}
      <p>{lede}</p>
    </div>
    <div class="stack">
      <div class="motion-wrap rv">{body}</div>
    </div>
  </div>
</section>"""


PRODUCTS = [
    dict(
        key="couch_hero", name="COUCH", sub="2.5-seat leather sofa",
        statement=(
            "One continuous rail. The back crown falls without a break into both arms and "
            "terminates at the same height each side &mdash; no separate arm component, no "
            "visible join, no vertical seam anywhere on the outside back. The mass sits on "
            "four splayed tapered legs that lift it 260&nbsp;mm clear of the floor, so the "
            "shadow gap runs uninterrupted end to end. Everything heavy is above the rail "
            "line; everything below it is thin."),
        cols=[
            ("Dimensions", [("Overall W × D × H", "1920 × 820 × 800"),
                            ("Seat height / depth", "430 / 580"),
                            ("Arm height", "620"),
                            ("Floor footprint", "1820 × 704"),
                            ("Back rake / leg splay", "14° / 8°")]),
            ("Materials", [("Cover", "full-aniline hide"),
                           ("Hide thickness", "1.4–1.6 mm"),
                           ("Legs", "ebonised solid ash"),
                           ("Frame", "beech + birch ply"),
                           ("Glides", "5 mm wool felt")]),
            ("Construction", [("Tufting", "11 buttons at 150 pitch"),
                              ("Suspension", "8 × 50 elastic webbing"),
                              ("Seat foam", "HR 30 core + 25 HR 35"),
                              ("Welt", "Ø6 cord, rail and seat"),
                              ("Leg fixing", "M8 hanger bolt")]),
        ]),
    dict(
        key="param_hero", name="PARAMETER", sub="Transformer monitor enclosure",
        statement=(
            "A bench instrument that puts 230&nbsp;VAC metering behind a shell you would "
            "leave on a desk. The whole front face carries two features: one window and one "
            "knob. All four lid screws are driven from the top, every cable entry is at the "
            "rear, and the internal layout keeps a single straight boundary between the "
            "mains section and everything at SELV."),
        cols=[
            ("Dimensions", [("Overall W × D × H", "140 × 126 × 54"),
                            ("Internal cavity", "135 × 121 × 44"),
                            ("Wall / lid", "2.5 / 6.0"),
                            ("Display aperture", "71.5 × 25.5"),
                            ("Corner radius", "R8.0")]),
            ("Materials", [("Shell", "ABS, RAL 9001"),
                           ("Texture", "MT-11020 bead blast"),
                           ("Knob", "Ø15 knurled ABS"),
                           ("Window", "1.5 mm clear PMMA"),
                           ("Seal", "Ø2 silicone cord")]),
            ("Construction", [("Carrier", "80 × 120 FR-4"),
                              ("Fixings", "4 × M3 × 10 CSK A2"),
                              ("Standoffs", "M3 × 5 brass"),
                              ("Isolation", "basic, ≥ 6.4 creepage"),
                              ("Ingress", "IP54")]),
        ]),
]


def product_block(pd, secondary=False):
    if pd["key"] not in have:
        return ""
    cols = "".join(
        '<div class="pspec-col"><h4>%s</h4><ul class="speclist">%s</ul></div>' % (
            title, "".join('<li><span class="k">%s</span><span class="v">%s</span></li>'
                           % (k, v) for (k, v) in rows))
        for (title, rows) in pd["cols"])
    return f"""<article class="prod{' prod-second' if secondary else ''} rv">
  <div class="prod-hero">{img_tag(pd['key'], 'prod-img', '(max-width:1100px) 100vw, 1100px')}</div>
  <div class="prod-body">
    <span class="lbl lbl-a">{'Secondary project' if secondary else 'Lead project'}</span>
    <h3 class="prod-name">{pd['name']}</h3>
    <p class="prod-sub">{pd['sub']}</p>
    <p class="prod-statement">{pd['statement']}</p>
    <div class="pspec">{cols}</div>
  </div>
</article>"""


def opener():
    """A recruiter should meet the finished product before any prose."""
    if "couch_studio" not in have:
        return ""
    return f"""<div class="wrap">
  <figure class="opener rv">
    {img_tag("couch_studio", "opener-img", "(max-width:1200px) 100vw, 1200px", eager=True)}
    <figcaption class="opener-cap">
      <span class="opener-name">COUCH</span>
      <span class="opener-sub">2.5-seat leather sofa &middot; full-aniline hide, ebonised ash</span>
      <span class="opener-tech">Path-traced in Blender Cycles &middot; 1920 &times; 820 &times; 800 mm</span>
    </figcaption>
  </figure>
</div>"""


def credibility():
    """Was four paragraphs before the reader saw anything. Claim up front, detail on demand."""
    return """<div class="wrap" style="margin-top:clamp(20px,3vw,34px)">
  <div class="cred rv">
    <p class="cred-line">
      <strong>Every product image on this page is a real render.</strong> Path-traced in
      Blender&nbsp;Cycles from geometry rebuilt to the source dimensions &mdash; not a
      photograph, and nothing on this page is AI-generated.
    </p>
    <details class="cred-more">
      <summary><span class="lbl lbl-a">What that does and does not mean</span></summary>
      <div class="cred-body">
        <p><strong>The geometry is a reconstruction.</strong> Rebuilt from the 3ds&nbsp;Max
          and Fusion&nbsp;360 references to the dimensions recorded here &mdash; not the
          original 1.03&nbsp;M-quad asset or the original parametric solid. Silhouette,
          proportion, component placement and every feature carry across; nothing was added
          to make a render look better. The enclosure has no rear features because the
          source model has none. The clay comparisons in stage&nbsp;05 show the same model
          with its materials stripped, at the same camera.</p>
        <p><strong>The engine is not the one in the original brief.</strong> Stage&nbsp;05's
          specification was written for V-Ray or Corona against
          <span class="mono">PhysCamera002</span>. These plates were rendered in Cycles, so
          read those settings as intent and the result as the Cycles equivalent. No image
          here is presented as a V-Ray or Corona render.</p>
        <p><strong>Dimensions are reconstructed, not measured</strong> &mdash;
          proportionally derived and internally consistent, but not read off the original
          parametric model. Masses are volume-and-density estimates. Substitute real
          parameter values before releasing anything for manufacture. Everything outside
          stages 05 and 06 remains hand-authored vector drawing, which is why it carries
          tolerances and section cuts a render cannot.</p>
      </div>
    </details>
  </div>
</div>"""


def wrap_in_details(html, needle, open_tag, label, sub):
    """Demote a self-contained block into an expandable drawer. Nothing is deleted:
    the block is moved behind a summary so design reads before engineering."""
    i = html.find(needle)
    if i < 0:
        return html
    start = html.rfind(open_tag, 0, i)
    if start < 0:
        return html
    depth, j = 0, start
    while j < len(html):
        if html.startswith("<div", j):
            depth += 1
            j += 4
        elif html.startswith("</div>", j):
            depth -= 1
            j += 6
            if depth == 0:
                break
        else:
            j += 1
    if depth != 0:
        return html
    block = html[start:j]
    drawer = ('<details class="tech rv"><summary>'
              '<span class="lbl lbl-a">' + label + '</span>'
              '<span class="tech-sum">' + sub + "</span></summary>"
              '<div class="tech-body">' + block + "</div></details>")
    return html[:start] + drawer + html[j:]


def transform_head(head):
    import re as _re
    # finished product first, technical elevation after it
    nl = "\n\n"
    anchor = "</header>" + nl + '<div class="wrap">'
    head = head.replace(anchor,
                        "</header>" + nl + opener() + nl + '<div class="wrap">', 1)
    # the long scope note becomes a one-line claim with the detail behind a summary
    head = _re.sub(r'<div class="wrap" style="margin-top:clamp\(20px,3vw,34px\)">\s*<div class="note rv">.*?</div>\s*</div>',
                   credibility(), head, count=1, flags=_re.S)
    # design thinking first, visual quality second, technical depth third
    head = wrap_in_details(
        head, '<span class="lbl">Mesh audit</span>', '<div class="vp rv">',
        "Technical details — mesh audit",
        "Euler characteristic, the 28-shell derivation, subdivision arithmetic")
    head = wrap_in_details(
        head, "<h3>Values to enter, not to eyeball</h3>", '<div class="card rv">',
        "Technical details — shader parameters",
        "Linear ACEScg base colours, roughness, IOR and metallic per material")
    return head


# ---------------------------------------------------------------- page build
def build(mode):
    global MODE
    MODE = mode
    html = open(SRC, encoding="utf8").read()

    i5 = html.index('<section class="sec" id="s05">')
    i6 = html.index('<section class="sec" id="s06">')
    ift = html.index('<footer class="foot">')
    head, old5, old6, tail = html[:i5], html[i5:i6], html[i6:ift], html[ift:]
    head = transform_head(head)

    def inner_stack(block):
        b = block.split('<div class="stack">', 1)[1]
        b = b.rsplit("</section>", 1)[0].rstrip()
        for _ in range(2):
            assert b.endswith("</div>"), b[-80:]
            b = b[: b.rfind("</div>")].rstrip()
        return b

    tech5, body6 = inner_stack(old5), inner_stack(old6)

    s05 = f"""<section class="sec" id="s05">
  <div class="wrap bind">
    <span class="bind-n">05</span>
    <div class="sec-head rv">
      <span class="lbl">Stage 05</span>
      <h2>Photorealistic Visualization</h2>
      <p>Path-traced in Blender Cycles from geometry rebuilt to the dimensions recorded in
        this dossier. Physically based materials, global illumination, real depth of field
        and real contact shadows.</p>
    </div>
    <div class="stack">
      <div class="proj-head rv">
        <span class="lbl lbl-a">Project 01 &middot; Furniture</span>
        <h3 class="proj-name">COUCH</h3>
        <p class="proj-line">Hero, supporting views, material detail, then the room.</p>
      </div>
      {gallery(COUCH)}
      {before_after("couch_clay", "couch_studio", "The same model, twice",
                    "Left is the untextured geometry; right is the finished plate. "
                    "Identical build, identical camera, identical framing &mdash; only the "
                    "materials and the light differ. Drag the divider.")}
      <div class="proj-head proj-second rv">
        <span class="lbl">Project 02 &middot; Instrument &middot; secondary</span>
        <h3 class="proj-name">PARAMETER</h3>
        <p class="proj-line">A mains-metering enclosure, carried through the same pipeline
          to show the method holds at 1/14 the scale.</p>
      </div>
      {gallery(PARAM)}
      {before_after("param_clay", "param_hero", "Shell geometry to finished product",
                    "The enclosure carries no rear features because the source model has "
                    "none. Nothing was added to make the render more attractive.")}
      <details class="tech rv">
        <summary><span class="lbl lbl-a">Visualization setup</span>
          <span class="tech-sum">Lighting plan, camera sheets, sampling, colour pipeline,
            AOV list</span></summary>
        <div class="tech-body">
          <p class="tech-lead">The specification the plates above were shot to. It was
            originally written for V-Ray or Corona against <span class="mono">PhysCamera002</span>;
            these plates were rendered in Blender Cycles, so read the engine settings as the
            intent and the Cycles equivalents as what actually ran. Nothing here is presented
            as a V-Ray or Corona render.</p>
          {tech5}
        </div>
      </details>
    </div>
  </div>
</section>"""

    s07 = f"""<section class="sec" id="s07">
  <div class="wrap bind">
    <span class="bind-n">07</span>
    <div class="sec-head rv">
      <span class="lbl">Stage 07</span>
      <h2>Final Product</h2>
      <p>What the two objects look like made, finished and photographed &mdash; followed by
        the numbers, the materials and the drawings that got them there.</p>
    </div>
    <div class="stack">
      {product_block(PRODUCTS[0])}
      {product_block(PRODUCTS[1], secondary=True)}
      <div class="prog-wrap rv">
        <span class="lbl lbl-a">Progression</span>
        <h3 class="prog-title">Source geometry to finished plate</h3>
        {progression()}
      </div>
      <details class="tech rv">
        <summary><span class="lbl lbl-a">Full specification, bill of materials and handover</span>
          <span class="tech-sum">Every dimension, the as-assembled BOM, and what is still
            open before manufacture</span></summary>
        <div class="tech-body">{body6}</div>
      </details>
    </div>
  </div>
</section>"""

    out = head + s05 + "\n" + film_section() + "\n" + s07 + "\n" + tail
    out = out.replace("</style>", EXTRA_CSS + "\n</style>", 1)
    out = out.replace("</script>", EXTRA_JS + "\n</script>", 1)
    return out


EXTRA_CSS = open(os.path.join(HERE, "extra.css"), encoding="utf8").read()
EXTRA_JS = open(os.path.join(HERE, "extra.js"), encoding="utf8").read()

if __name__ == "__main__":
    a = build("artifact")
    open(os.path.join(HERE, "artifact.html"), "w", encoding="utf8").write(a)
    print(f"artifact.html  {len(a)/1048576:.2f} MB")
    r = build("repo")
    open(os.path.join(HERE, "repo_body.html"), "w", encoding="utf8").write(r)
    print(f"repo_body.html {len(r)/1024:.0f} KB")
