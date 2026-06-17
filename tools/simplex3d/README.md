# Simplex on a Convex Polytope in ℝ³

Visualization of the **decomposition / feasible-direction simplex method**
walking vertex-to-vertex across a 3-D polytope.
One verified dataset drives **both** outputs:

| Output | Path | Surface |
|---|---|---|
| Looping animation (GIF + MP4) | `assets/readme/simplex-polytope-3d.gif` | embedded inline in the profile `README.md` |
| Interactive page (Plotly + KaTeX) | `simplex3d/index.html` in the `mutingma123.github.io` repo | served at `https://mutingma123.github.io/simplex3d/` |

## The example LP (standard form, exact rational arithmetic)

```
max  z = 3x₁ + 2x₂ + x₃
s.t.   x₁ ≤ 4,  x₂ ≤ 4,  x₃ ≤ 4,   x₁ + x₂ + x₃ ≤ 9,   x ≥ 0
```

The feasible region is the cube `[0,4]³` with its far corner sliced off
(10 vertices, 7 faces, 15 edges). Dantzig's rule gives the 3-pivot walk

```
(0,0,0) → (4,0,0) → (4,4,0) → (4,4,1)*      z: 0 → 12 → 20 → 21
```

with dual `y* = (2,1,0,1)` and `b·y* = 21 = z*` (strong duality).

## Rebuild

```bash
cd tools/simplex3d
python3 core.py        # solve + enumerate geometry -> steps.json (single source of truth)
python3 make_gif.py    # -> simplex-polytope-3d.gif / .mp4   (add --quick for a fast preview)
python3 build_html.py  # -> index.html  (data embedded inline)
# then copy to the published locations:
cp simplex-polytope-3d.gif ../../assets/readme/                         # profile README
cp index.html simplex-polytope-3d.mp4 <mutingma123.github.io>/simplex3d/ # interactive page
```

Requires `numpy`, `scipy`, `matplotlib`, and (optional) `ffmpeg` for MP4 and
ImageMagick `convert` for GIF size optimization.

## Publishing the interactive page

The interactive page lives in the user-site repo `mutingma123/mutingma123.github.io`
at `simplex3d/index.html`, which GitHub Pages serves automatically at
`https://mutingma123.github.io/simplex3d/`. The file is fully self-contained
(libraries via CDN, step data embedded), so it also works by opening it directly
in a browser.
