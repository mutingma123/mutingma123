"""
make_gif.py -- render the looping README animation of the simplex walk.

Reads steps.json (produced by core.py) and renders a 3D matplotlib animation:
the truncated-cube feasible polytope, every extreme point, and the simplex
sliding vertex-to-vertex along edges, with per-step LaTeX captions that appear
and disappear in sync with the pivots.  Saves both a GIF (for the profile
README) and an MP4.

Usage:  python3 make_gif.py [--quick]
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "steps.json")))
QUICK = "--quick" in sys.argv

# ----------------------------- palette ------------------------------------- #
BG        = "#0d1326"
FACE      = "#3b6fb6"
EDGE      = "#9fb6d6"
VERT      = "#7f93b8"
PATH      = "#ffd23f"
PATH_GLOW = "#ff8c42"
CURRENT   = "#ff3b6b"
OBJ       = "#36e0a4"
TXT       = "#e8eef9"
MUTE      = "#8fa2c4"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "mathtext.fontset": "cm",
    "figure.facecolor": BG,
    "savefig.facecolor": BG,
})

V    = np.array(DATA["geometry"]["vertices"])
FACES = DATA["geometry"]["faces"]
EDGES = DATA["geometry"]["edges"]
CVEC = np.array(DATA["geometry"]["objective"], float)
STEPS = DATA["steps"]
PATH_PTS = np.array(DATA["path_pts"], float)

# ----------------------------- timeline ------------------------------------ #
# Phases: an intro hold, then for each pivot a (hold, move) pair, then a final
# hold on the optimum.  Each phase carries a caption that fades in.
HOLD0   = 8 if QUICK else 16
HOLD     = 8 if QUICK else 20
MOVE     = 10 if QUICK else 26
HOLD_OPT = 12 if QUICK else 34

pivots = [s for s in STEPS if s["status"] == "pivot"]
opt    = STEPS[-1]


def cap_pivot_hold(s):
    rc = ",\\ ".join(f"\\bar c_{{{v}}}={val}" for v, val in s["rc_pairs"])
    return (f"$\\mathbf{{Iteration\\ {s['iter']}}}$  at  $x=({','.join(s['point'])})$,  $z={s['z']}$\n"
            f"${rc}$   $\\Rightarrow$  enter $\\mathbf{{{s['entering_tex']}}}$ "
            f"(steepest ascent),   $\\lambda^*={s['lambda_plain']}$,   "
            f"${s['leaving_tex']}$ leaves")


def cap_pivot_move(s, zfrom, zto):
    return (f"slide along edge  $x^{{({s['iter']})}}=x^{{({s['iter']-1})}}"
            f"+\\lambda^*\\,v^{{{s['entering_tex']}}}$,   "
            f"objective  $z:\\ {zfrom}\\ \\rightarrow\\ {zto}$")


def cap_opt(s):
    rc = ",\\ ".join(f"\\bar c_{{{v}}}={val}" for v, val in s["rc_pairs"])
    return (f"${rc}\\ \\leq 0\\ \\ \\Rightarrow$  $\\mathbf{{optimal}}$\n"
            f"$x^*=({','.join(s['point'])})$,   $z^*={s['z']}$,   "
            f"dual  $y^*=c_B^{{\\top}}B^{{-1}}$")


# Build the frame list: each entry = (caption, fade_t in [0,1], seg_idx or None, alpha_along)
frames = []
# intro hold at vertex 0
for f in range(HOLD0):
    frames.append((cap_pivot_hold(pivots[0]), min(1, f / 5), 0, 0.0))
# each pivot
for k, s in enumerate(pivots):
    for f in range(HOLD):
        frames.append((cap_pivot_hold(s), min(1, f / 5), k, 0.0))
    zfrom = STEPS[k]["z"]
    zto = STEPS[k + 1]["z"]
    for f in range(MOVE):
        t = (f + 1) / MOVE
        frames.append((cap_pivot_move(s, zfrom, zto), 1.0, k, t))
# final hold
for f in range(HOLD_OPT):
    frames.append((cap_opt(opt), min(1, f / 6), len(pivots) - 1, 1.0))

N_FRAMES = len(frames)

# ----------------------------- figure -------------------------------------- #
fig = plt.figure(figsize=(8.8, 6.6), dpi=110)
ax = fig.add_subplot(111, projection="3d")
ax.set_box_aspect((1, 1, 1))

cap_text = fig.text(0.5, 0.075, "", ha="center", va="center", color=TXT,
                    fontsize=11.5, linespacing=1.7,
                    bbox=dict(boxstyle="round,pad=0.6", fc="#16203d",
                              ec="#2e4a72", lw=1.2, alpha=0.96))
title = fig.text(0.5, 0.955, r"Simplex Algorithm on a Convex Polytope in $\mathbb{R}^3$",
                 ha="center", va="center", color=TXT, fontsize=15, fontweight="bold")
subtitle = fig.text(0.5, 0.915,
                    r"Decomposition (feasible-direction) method:  $\max\ 3x_1+2x_2+x_3$  "
                    r"s.t.  $x_i\leq 4,\ \ x_1+x_2+x_3\leq 9,\ \ x\geq 0$",
                    ha="center", va="center", color=MUTE, fontsize=10)


def style_axes():
    ax.set_facecolor(BG)
    ax.set_xlabel("$x_1$", color=TXT, labelpad=-6, fontsize=12)
    ax.set_ylabel("$x_2$", color=TXT, labelpad=-6, fontsize=12)
    ax.set_zlabel("$x_3$", color=TXT, labelpad=-6, fontsize=12)
    ax.set_xlim(0, 4.4); ax.set_ylim(0, 4.4); ax.set_zlim(0, 4.4)
    ax.set_xticks([0, 2, 4]); ax.set_yticks([0, 2, 4]); ax.set_zticks([0, 2, 4])
    ax.tick_params(colors=MUTE, labelsize=8)
    for pane in (ax.xaxis, ax.yaxis, ax.zaxis):
        pane.set_pane_color((1, 1, 1, 0.02))
        pane.line.set_color((1, 1, 1, 0.18))
        pane._axinfo["grid"]["color"] = (1, 1, 1, 0.06)


def draw():
    """Static scene: faces, edges, vertices, objective arrow."""
    polys = [[V[i] for i in face] for face in FACES]
    pc = Poly3DCollection(polys, facecolor=FACE, edgecolor="none", alpha=0.13)
    ax.add_collection3d(pc)
    lc = Line3DCollection([[V[a], V[b]] for a, b in EDGES], colors=EDGE, lw=1.1, alpha=0.55)
    ax.add_collection3d(lc)
    ax.scatter(V[:, 0], V[:, 1], V[:, 2], s=26, c=VERT, depthshade=False,
               edgecolors="white", linewidths=0.4, alpha=0.9, zorder=3)
    # objective direction arrow (uphill), anchored near the polytope centre
    base = np.array([2.0, 2.0, 2.0])
    d = CVEC / np.linalg.norm(CVEC) * 2.1
    ax.quiver(*base, *d, color=OBJ, lw=2.4, arrow_length_ratio=0.18, zorder=6)
    ax.text(*(base + d * 1.06), r"$\nabla z=c$", color=OBJ, fontsize=11, zorder=7)


def init():
    ax.cla()
    style_axes()
    draw()
    return []


def update(fi):
    caption, fade, seg, along = frames[fi]
    ax.cla()
    style_axes()
    draw()

    # slow orbit
    ax.view_init(elev=22 + 6 * np.sin(fi / N_FRAMES * 2 * np.pi),
                 azim=-58 + 360 * fi / N_FRAMES * 0.45)

    # completed path (vertices 0..seg) drawn boldly
    done = PATH_PTS[:seg + 1]
    if len(done) >= 2:
        ax.plot(done[:, 0], done[:, 1], done[:, 2], color=PATH_GLOW, lw=7, alpha=0.30, zorder=8)
        ax.plot(done[:, 0], done[:, 1], done[:, 2], color=PATH, lw=3.2, alpha=0.95, zorder=9)
    # current moving point (interpolated along the active edge)
    p0 = PATH_PTS[seg]
    p1 = PATH_PTS[min(seg + 1, len(PATH_PTS) - 1)]
    cur = p0 + (p1 - p0) * along
    if along > 0:
        ax.plot([p0[0], cur[0]], [p0[1], cur[1]], [p0[2], cur[2]],
                color=PATH, lw=3.2, zorder=9)
    # visited vertices so far
    vis = PATH_PTS[:seg + 1]
    ax.scatter(vis[:, 0], vis[:, 1], vis[:, 2], s=70, c=PATH, depthshade=False,
               edgecolors="white", linewidths=0.8, zorder=10)
    # the live cursor
    ax.scatter([cur[0]], [cur[1]], [cur[2]], s=220, c=CURRENT, depthshade=False,
               edgecolors="white", linewidths=1.4, zorder=12)

    cap_text.set_text(caption)
    cap_text.set_alpha(0.25 + 0.75 * fade)
    return []


def _main():
    anim = FuncAnimation(fig, update, init_func=init, frames=N_FRAMES,
                         interval=55, blit=False)

    gif_path = os.path.join(HERE, "simplex-polytope-3d.gif")
    mp4_path = os.path.join(HERE, "simplex-polytope-3d.mp4")

    print(f"rendering {N_FRAMES} frames ...")
    anim.save(gif_path, writer=PillowWriter(fps=18))
    print("wrote", gif_path, f"({os.path.getsize(gif_path) / 1e6:.2f} MB)")

    try:
        anim.save(mp4_path, writer=FFMpegWriter(fps=24, bitrate=2400))
        print("wrote", mp4_path, f"({os.path.getsize(mp4_path) / 1e6:.2f} MB)")
    except Exception as e:
        print("mp4 skipped:", e)

    # optimise the GIF with ImageMagick if available (palette + layer optimise)
    opt_gif = os.path.join(HERE, "simplex-polytope-3d.opt.gif")
    try:
        subprocess.run(
            ["convert", gif_path, "-coalesce", "-fuzz", "3%",
             "-layers", "OptimizePlus", "-colors", "128", opt_gif],
            check=True, capture_output=True)
        if os.path.getsize(opt_gif) < os.path.getsize(gif_path):
            os.replace(opt_gif, gif_path)
            print("optimised GIF ->", f"{os.path.getsize(gif_path) / 1e6:.2f} MB")
        else:
            os.remove(opt_gif)
    except Exception as e:
        print("gif optimise skipped:", e)


if __name__ == "__main__":
    _main()
