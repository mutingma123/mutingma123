"""
core.py -- OM 600 decomposition-method Simplex, in EXACT rational arithmetic.

This is the single source of mathematical truth for both outputs
(the README GIF and the interactive HTML page).  Every quantity shown to the
viewer is computed here with Python's `fractions.Fraction`, so nothing is a
floating-point approximation.

Method (exactly as taught in OM 600, Exam 3 "SimplexAlgorithm" notes):

    standard form        max c^T x  s.t.  A x = b,  x >= 0
    basis                B = m linearly independent columns of A
    current BFS          x_B = B^{-1} b,  x_N = 0          (an extreme point)
    feasible direction   v^j = [ -B^{-1} A_j ; e_j ]       for each j in N
    reduced cost         c_bar_j = <c, v^j> = c_j - c_B^T B^{-1} A_j
    optimality (max)     c_bar_j <= 0  for all j in N
    entering variable    s = argmax_{j in N} { c_bar_j : c_bar_j > 0 }   (Dantzig)
    min-ratio test       lambda* = min_{i : a_bar_is > 0} ( b_bar_i / a_bar_is )
    update               x_new = x_old + lambda* v^s   (one extreme point -> adjacent one)
"""

from __future__ import annotations

import json
from fractions import Fraction as F
from itertools import combinations

import numpy as np
from scipy.spatial import ConvexHull


# --------------------------------------------------------------------------- #
#  The linear program (OM 600 standard form data)                             #
# --------------------------------------------------------------------------- #
#   max  3 x1 + 2 x2 + 1 x3
#   s.t.   x1                      <= 4      (-> slack s1)
#               x2                 <= 4      (-> slack s2)
#                    x3            <= 4      (-> slack s3)
#          x1 +  x2 +  x3          <= 9      (-> slack s4)
#          x1, x2, x3 >= 0
#
# Feasible region in (x1,x2,x3) space: the cube [0,4]^3 with its far corner
# (4,4,4) sliced off by x1+x2+x3 <= 9  -> a clean 10-vertex polytope.

N_DEC = 3  # decision variables x1,x2,x3
A_LE = [  # constraint matrix for the "<=" rows (decision columns only)
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
    [1, 1, 1],
]
B_RHS = [4, 4, 4, 9]
C_DEC = [3, 2, 1]

VAR_TEX = ["x_1", "x_2", "x_3", "s_1", "s_2", "s_3", "s_4"]
VAR_TXT = ["x1", "x2", "x3", "s1", "s2", "s3", "s4"]


# --------------------------------------------------------------------------- #
#  Exact rational linear algebra (small m x m systems)                        #
# --------------------------------------------------------------------------- #
def mat_inverse(M):
    """Inverse of a square Fraction matrix via Gauss-Jordan (exact)."""
    n = len(M)
    A = [[F(M[i][j]) for j in range(n)] + [F(int(i == j)) for j in range(n)]
         for i in range(n)]
    for col in range(n):
        piv = next((r for r in range(col, n) if A[r][col] != 0), None)
        if piv is None:
            raise ValueError("singular basis matrix")
        A[col], A[piv] = A[piv], A[col]
        pv = A[col][col]
        A[col] = [v / pv for v in A[col]]
        for r in range(n):
            if r != col and A[r][col] != 0:
                f = A[r][col]
                A[r] = [a - f * b for a, b in zip(A[r], A[col])]
    return [[A[i][j + n] for j in range(n)] for i in range(n)]


def matvec(M, v):
    return [sum(M[i][j] * v[j] for j in range(len(v))) for i in range(len(M))]


def matcol(M, j):
    return [M[i][j] for i in range(len(M))]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


# --------------------------------------------------------------------------- #
#  Build A, b, c in standard form (decision vars + slacks)                    #
# --------------------------------------------------------------------------- #
def build_standard_form():
    m = len(A_LE)
    n = N_DEC + m
    A = [[F(0)] * n for _ in range(m)]
    for i in range(m):
        for j in range(N_DEC):
            A[i][j] = F(A_LE[i][j])
        A[i][N_DEC + i] = F(1)  # slack identity
    b = [F(v) for v in B_RHS]
    c = [F(v) for v in C_DEC] + [F(0)] * m
    return A, b, c, m, n


# --------------------------------------------------------------------------- #
#  LaTeX helpers                                                              #
# --------------------------------------------------------------------------- #
def fmt(x: F) -> str:
    """Fraction -> compact LaTeX (\\tfrac for non-integers)."""
    x = F(x)
    if x.denominator == 1:
        return str(x.numerator)
    sign = "-" if x < 0 else ""
    a = abs(x)
    return f"{sign}\\tfrac{{{a.numerator}}}{{{a.denominator}}}"


def fmt_plain(x: F) -> str:
    x = F(x)
    if x.denominator == 1:
        return str(x.numerator)
    return f"{x.numerator}/{x.denominator}"


def vec_tex(vals):
    return "(" + ",\\,".join(fmt(v) for v in vals) + ")"


def colvec_tex(vals):
    return "\\begin{bmatrix}" + "\\\\".join(fmt(v) for v in vals) + "\\end{bmatrix}"


# --------------------------------------------------------------------------- #
#  The simplex algorithm -- records every OM 600 step                         #
# --------------------------------------------------------------------------- #
def solve_and_record():
    A, b, c, m, n = build_standard_form()
    basis = [N_DEC + i for i in range(m)]   # start at the all-slack BFS (origin)
    steps = []
    it = 0
    MAXIT = 50

    while it < MAXIT:
        it += 1
        Bcols = [matcol(A, j) for j in basis]
        Bmat = [[Bcols[j][i] for j in range(m)] for i in range(m)]
        Binv = mat_inverse(Bmat)

        xB = matvec(Binv, b)                       # x_B = B^{-1} b
        x = [F(0)] * n
        for i, bi in enumerate(basis):
            x[bi] = xB[i]
        point = [x[0], x[1], x[2]]
        cB = [c[j] for j in basis]
        y = matvec([[Binv[j][i] for j in range(m)] for i in range(m)], cB)  # y = c_B^T B^{-1}
        z = dot(c, x)

        nonbasis = [j for j in range(n) if j not in basis]

        # reduced costs c_bar_j = c_j - c_B^T B^{-1} A_j  for non-basic j
        rcs = {}
        for j in nonbasis:
            Aj = matcol(A, j)
            cbar = c[j] - dot(cB, matvec(Binv, Aj))
            rcs[j] = cbar

        improving = [j for j in nonbasis if rcs[j] > 0]

        # ---- assemble the human-readable record for this iteration --------- #
        # x_B is in CURRENT basis order; show a labelled column so the variable
        # names row-align with their values (avoids any ordering ambiguity).
        basis_labels = "\\begin{bmatrix}" + "\\\\".join(VAR_TEX[j] for j in basis) + "\\end{bmatrix}"
        xB_labeled = f"x_B={basis_labels}=B^{{-1}}b={colvec_tex(xB)}"
        rec = {
            "iter": it,
            "point": [fmt_plain(p) for p in point],
            "point_f": [float(p) for p in point],
            "z": fmt(z),
            "z_f": float(z),
            "basis": [VAR_TXT[j] for j in basis],
            "basis_tex": "\\{" + ",".join(VAR_TEX[j] for j in basis) + "\\}",
            "nonbasis_tex": "\\{" + ",".join(VAR_TEX[j] for j in sorted(nonbasis)) + "\\}",
            "xB_labeled_tex": xB_labeled,
            "y_tex": vec_tex(y),
            "rc_tex": ",\\quad ".join(
                f"\\bar c_{{{VAR_TEX[j]}}}={fmt(rcs[j])}" for j in sorted(nonbasis)
            ),
        }

        if not improving:
            # optimal
            rec["status"] = "optimal"
            rec["rc_pairs"] = [[VAR_TEX[j], fmt_plain(rcs[j])] for j in sorted(nonbasis)]
            rec["title"] = f"Optimal vertex \\;x^\\ast={vec_tex(point)}"
            rec["blocks"] = [
                {"label": "Basis &amp; BFS",
                 "tex": f"B={rec['basis_tex']},\\quad {rec['xB_labeled_tex']},"
                        f"\\quad z={fmt(z)}"},
                {"label": "Optimality test (maximization)",
                 "tex": f"{rec['rc_tex']}"},
                {"label": "Certificate",
                 "tex": "\\bar c_j=\\langle c,v^j\\rangle\\le 0\\ \\ \\forall j\\in N"
                        "\\;\\Longrightarrow\\; \\textbf{optimal.}"},
                {"label": "Dual solution (shadow prices)",
                 "tex": f"y^\\ast=c_B^\\top B^{{-1}}={rec['y_tex']},\\qquad "
                        f"c^\\top x^\\ast=b^\\top y^\\ast={fmt(z)}"},
            ]
            rec["narrative"] = ("All reduced costs are non-positive, so no feasible "
                                "direction improves the objective. This extreme point "
                                "is optimal.")
            steps.append(rec)
            break

        # entering variable: Dantzig (largest reduced cost), tie -> smallest index
        s = max(improving, key=lambda j: (rcs[j], -j))
        Abar_s = matvec(Binv, matcol(A, s))        # = B^{-1} A_s

        # direction v^s = [-B^{-1}A_s ; e_s] expressed over ALL n variables
        v = [F(0)] * n
        v[s] = F(1)
        for i, bi in enumerate(basis):
            v[bi] = -Abar_s[i]

        # min-ratio test over rows with a_bar_is > 0
        ratios = []
        for i in range(m):
            if Abar_s[i] > 0:
                ratios.append((i, xB[i] / Abar_s[i]))
        if not ratios:
            rec["status"] = "unbounded"
            rec["title"] = "Unbounded"
            steps.append(rec)
            break
        lam = min(r for _, r in ratios)
        r_idx = min((i for i, r in ratios if r == lam), key=lambda i: basis[i])
        leaving = basis[r_idx]

        new_point = [point[k] + lam * v[k] for k in range(3)]

        ratio_rows = []
        for i in range(m):
            if Abar_s[i] > 0:
                ratio_rows.append(
                    f"\\tfrac{{{fmt(xB[i])}}}{{{fmt(Abar_s[i])}}}={fmt(xB[i] / Abar_s[i])}"
                )

        rec["status"] = "pivot"
        rec["entering"] = VAR_TXT[s]
        rec["leaving"] = VAR_TXT[leaving]
        rec["entering_tex"] = VAR_TEX[s]
        rec["leaving_tex"] = VAR_TEX[leaving]
        rec["lambda"] = fmt(lam)
        rec["lambda_plain"] = fmt_plain(lam)
        # mathtext-safe reduced-cost pairs for the GIF captions
        rec["rc_pairs"] = [[VAR_TEX[j], fmt_plain(rcs[j])] for j in sorted(nonbasis)]
        # 3D edge direction actually travelled (decision-space components of v^s)
        rec["dir3"] = [float(v[0]), float(v[1]), float(v[2])]
        rec["next_point_f"] = [float(p) for p in new_point]
        rec["title"] = (f"Iteration {it}: vertex \\;x^{{({it - 1})}}={vec_tex(point)}"
                        f",\\; z={fmt(z)}")
        rec["blocks"] = [
            {"label": "Decompose current BFS",
             "tex": f"B={rec['basis_tex']},\\;\\; N={rec['nonbasis_tex']},\\;\\; "
                    f"{rec['xB_labeled_tex']}"},
            {"label": "Reduced costs &nbsp;$\\bar c_j=c_j-c_B^\\top B^{-1}A_j=\\langle c,v^j\\rangle$",
             "tex": f"{rec['rc_tex']}"},
            {"label": "Entering variable (Dantzig rule)",
             "tex": f"s=\\arg\\max_{{j\\in N}}\\{{\\bar c_j:\\bar c_j>0\\}}"
                    f"\\;\\Rightarrow\\; {VAR_TEX[s]}\\ \\text{{enters}}"},
            {"label": "Feasible direction &nbsp;$v^s=\\big[-B^{-1}A_s;\\,e_s\\big]$",
             "tex": f"v^{{{VAR_TEX[s]}}}={colvec_tex(v)}"
                    f"\\;\\text{{(order }}{','.join(VAR_TEX)}\\text{{)}}"},
            {"label": "Minimum-ratio test &nbsp;$\\lambda^\\ast=\\min_{i:\\,\\bar a_{is}>0}\\bar b_i/\\bar a_{is}$",
             "tex": "\\lambda^\\ast=\\min\\{" + ",\\;".join(ratio_rows) + "\\}="
                    f"{fmt(lam)}\\;\\Rightarrow\\;{VAR_TEX[leaving]}\\ \\text{{leaves}}"},
            {"label": "Pivot (move to adjacent extreme point)",
             "tex": f"x^{{({it})}}=x^{{({it - 1})}}+\\lambda^\\ast v^{{{VAR_TEX[s]}}}"
                    f"={vec_tex(new_point)}"},
        ]
        rec["narrative"] = (
            f"Reduced cost of {VAR_TXT[s]} is the steepest positive ascent, so it "
            f"enters; the ratio test stops at λ*={fmt_plain(lam)} where {VAR_TXT[leaving]} "
            f"hits zero and leaves. We slide along that edge to the next vertex.")
        steps.append(rec)

        # update basis
        basis[r_idx] = s

    return steps


# --------------------------------------------------------------------------- #
#  Enumerate every extreme point (BFS) and the polytope geometry              #
# --------------------------------------------------------------------------- #
def enumerate_geometry():
    A, b, c, m, n = build_standard_form()
    pts = []
    seen = set()
    for combo in combinations(range(n), m):
        Bmat = [[matcol(A, j)[i] for j in combo] for i in range(m)]
        try:
            Binv = mat_inverse(Bmat)
        except ValueError:
            continue
        xB = matvec(Binv, b)
        if all(v >= 0 for v in xB):                      # basic FEASIBLE solution
            x = [F(0)] * n
            for k, j in enumerate(combo):
                x[j] = xB[k]
            key = (x[0], x[1], x[2])
            if key not in seen:
                seen.add(key)
                pts.append([float(x[0]), float(x[1]), float(x[2])])
    P = np.array(pts, dtype=float)
    hull = ConvexHull(P)

    # merge co-planar triangles into clean polygon faces
    groups = {}
    for eq, simp in zip(hull.equations, hull.simplices):
        key = tuple(np.round(eq, 6))
        groups.setdefault(key, set()).update(int(i) for i in simp)

    faces, edges = [], set()
    for key, idxs in groups.items():
        idxs = list(idxs)
        normal = np.array(key[:3], dtype=float)
        sub = P[idxs]
        centroid = sub.mean(axis=0)
        ref = sub[0] - centroid
        nref = np.linalg.norm(ref)
        if nref < 1e-9:
            ref = sub[1] - centroid
            nref = np.linalg.norm(ref)
        u = ref / nref
        w = np.cross(normal, u)
        w /= (np.linalg.norm(w) + 1e-12)
        ang = np.arctan2((sub - centroid) @ w, (sub - centroid) @ u)
        order = [idxs[i] for i in np.argsort(ang)]
        faces.append(order)
        for a, bb in zip(order, order[1:] + order[:1]):
            edges.add((min(a, bb), max(a, bb)))

    return {
        "vertices": P.tolist(),
        "faces": faces,
        "edges": sorted(edges),
        "objective": [float(v) for v in C_DEC],
    }


def match_vertex(vertices, pt, tol=1e-6):
    for i, v in enumerate(vertices):
        if all(abs(v[k] - pt[k]) < tol for k in range(3)):
            return i
    return None


def build_dataset():
    steps = solve_and_record()
    geo = enumerate_geometry()
    # path through the polytope vertices, as indices into geo["vertices"]
    path_pts = [s["point_f"] for s in steps]
    path_idx = [match_vertex(geo["vertices"], p) for p in path_pts]
    return {
        "lp": {
            "objective_tex": "\\max\\; z = 3x_1 + 2x_2 + x_3",
            "constraints_tex": [
                "x_1 \\le 4", "x_2 \\le 4", "x_3 \\le 4",
                "x_1 + x_2 + x_3 \\le 9", "x_1,x_2,x_3 \\ge 0",
            ],
        },
        "geometry": geo,
        "steps": steps,
        "path_idx": path_idx,
        "path_pts": path_pts,
    }


if __name__ == "__main__":
    data = build_dataset()
    out = __file__.replace("core.py", "steps.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {out}")
    print("vertices:", len(data["geometry"]["vertices"]),
          "faces:", len(data["geometry"]["faces"]),
          "edges:", len(data["geometry"]["edges"]))
    print("path:", " -> ".join("(" + ",".join(s["point"]) + ")" for s in data["steps"]),
          "| z:", [s["z"] for s in data["steps"]])
    print("path_idx:", data["path_idx"])
    for s in data["steps"]:
        print(f"  it{s['iter']} {s['status']:9s} z={s['z']}",
              ("enter=" + s.get("entering", "-") + " leave=" + s.get("leaving", "-")
               + " lambda=" + s.get("lambda", "-")) if s["status"] == "pivot" else "")
