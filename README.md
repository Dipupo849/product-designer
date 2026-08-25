# Cage to Catalogue

A six-stage product design dossier covering two objects taken from working files to a
finished specification:

- **COUCH** — a 2.5-seat leather sofa, subdivision-modelled in 3ds Max
- **PARAMETER** — a mains-metering instrument enclosure, parametric assembly in Fusion 360

Open `index.html` in a browser, or serve the repo with GitHub Pages.

## What this is

A single self-contained HTML page. No build step, no dependencies, no bundler. All
drawings are hand-authored inline SVG; the only external request is Google Fonts.

The six stages are a real sequence, not decoration:

| Stage | Contents |
| --- | --- |
| 01 Design Concept | Design intent and the proportion ratios held during modelling |
| 02 CAD Development | Dimensioned enclosure drawings, internal layout, isolation architecture |
| 03 3D Modelling | Mesh audit, subdivision ladder, sofa elevations and plan, section details |
| 04 Materials & Finishes | Twelve materials specified for both workshop and renderer |
| 05 Photorealistic Visualization | Lighting plan and eleven fully parameterised camera sheets |
| 06 Final Product | Specifications, bill of materials, handover status |

## Two things to read before using it

**The plates are drawn, not rendered.** No renderer was run and no photograph was
used. Every view is vector geometry reconstructed from the source files and dimensioned,
which is why the drawings carry tolerances, section cuts and callouts that a render
cannot. Stage 05 is the render brief that was never executed — camera, lens, aperture,
light positions and sizes, HDRI, ACES pipeline and pass list, written to run against
`PhysCamera002`, the camera already in the scene.

**Dimensions are reconstructed, not measured.** They are proportionally derived from the
reference views and internally consistent, but they are not read off the original
parametric model. Substitute the real parameter values before releasing anything for
manufacture. Masses are volume-and-density estimates, not weighings.

Both caveats are stated on the page itself, and the open items are listed in full in the
handover panel at the end of stage 06.

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

A second reading is still open: `1,033,680 / 4³ = 16,151.25`, not an integer, so the
render mesh is not a single uniform three-iteration subdivision of one cage. At least one
shell group runs at a different iteration count. Worth confirming against the modifier
stack before the file is archived.

## Structure

```
index.html    the complete dossier — single file, self-contained
README.md     this file
```
