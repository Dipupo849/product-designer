# Cage to Catalogue

A six-stage product design dossier covering two objects taken from working files to a
finished, rendered product:

- **COUCH** — a 2.5-seat leather sofa, subdivision-modelled in 3ds Max
- **PARAMETER** — a mains-metering instrument enclosure, parametric assembly in Fusion 360

Open `index.html` in a browser, or serve the repo with GitHub Pages.

## What this is

A single self-contained HTML page plus an `img/` folder. No build step, no dependencies,
no bundler. The technical drawings are hand-authored inline SVG; the product plates are
rendered images served at two widths with `srcset` and lazy loading.

| Stage | Contents |
| --- | --- |
| 01 Design Concept | Design intent and the proportion ratios held during modelling |
| 02 CAD Development | Dimensioned enclosure drawings, internal layout, isolation architecture |
| 03 3D Modelling | Mesh audit, subdivision ladder, sofa elevations and plan, section details |
| 04 Materials & Finishes | Twelve materials specified for both workshop and renderer |
| 05 Photorealistic Visualization | The rendered plates, with camera data in a collapsed drawer |
| 06 Final Product | Hero plates, progression strip, specifications, bill of materials |

## What every image actually is

**The product plates are real renders.** They were path-traced in **Blender Cycles** —
physically based materials, global illumination, real depth of field, real contact
shadows. They are not photographs, and **no image on this page is AI-generated.**

**The geometry behind them is a reconstruction.** It was rebuilt from the 3ds Max and
Fusion 360 references to the dimensions recorded in the dossier. It is *not* the original
1.03 M-quad asset or the original parametric solid. Silhouette, proportion, component
placement and every feature are carried across from the source; nothing was added to make
a render look better. The enclosure has no rear features because the source model has
none.

The two clay comparisons in stage 05 show the same model with its materials stripped, at
the same camera — that is the evidence the renders came from the geometry.

**The engine is not the one in the brief.** Stage 05's specification was written for V-Ray
or Corona against `PhysCamera002`. The plates were rendered in Cycles, so read those
settings as intent and the result as the Cycles equivalent.

**Dimensions are reconstructed, not measured** — proportionally derived and internally
consistent, but not read off the original parametric model. Masses are volume-and-density
estimates. Substitute real parameter values before releasing anything for manufacture.

There is no product video. The motion panel is a labelled specification, not a still
image presented as footage.

## One finding worth keeping

The 3ds Max statistics overlay reports **1,033,680 polygons and 1,033,736 vertices**.

For a closed all-quad surface every face carries four edges and every edge is shared by
two faces, so `E = 2F` and Euler's relation `V - E + F = 2` collapses to `V = F + 2` per
shell. The difference is 56, so:

```
56 / 2 = 28 closed shells
```

The counters are consistent with exactly 28 separate closed shells — all quads, no open
borders, no triangles, no n-gons anywhere in a million-polygon model. A single stray hole
or triangulated cap would break the arithmetic. It is the cheapest watertightness check
available and it costs one subtraction.

Still open: `1,033,680 / 4³ = 16,151.25`, not an integer, so the render mesh is not a
single uniform three-iteration subdivision of one cage. At least one shell group runs at
a different iteration count.

## Reproducing the renders

The scene is built entirely from script — there is no `.blend` file to lose.

```
couch.py         sofa geometry: lofted rail, per-vertex tufting, welts, splayed legs
enclosure.py     shell booleans, knurled knob, 5x7 dot-matrix display geometry
studio.py        materials, lighting rigs, cameras, Cycles render settings
render_couch.py  blender -b -P render_couch.py -- <shot>
render_param.py  blender -b -P render_param.py -- <shot>
```

They are included under `scene/`, so the claim on this page is checkable: install
Blender, run a shot, compare. Renders in this repo were made with Blender 5.2.1 at
1240 x 780, 110 samples (190 for interiors), adaptive sampling with OpenImageDenoise.

## Structure

```
index.html    the complete dossier — one file
img/          product plates, 1400 px and 700 px JPEG
scene/        Blender scene generators (see above)
README.md     this file
```
