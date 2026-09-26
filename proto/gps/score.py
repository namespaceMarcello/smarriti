"""Does the place point where real cats are? The direction part of the model (the ring
density w = sel x reach of sim/place.py, the engine's map up to L9) scored on GPS fixes of pet cats, against the same
map rotated around home. The protocols were written before the data: docs/MISURE.md, L5
(the engine's map, sigma 10 m) and L7 (--map walls_sel --sigma 0, chosen in L6, --households 20:
cats of the same home rotate together).

    python -m proto.gps.score <data_dir> [--map full] [--sigma 10] [--households 0] [--rot 999] [--perm 9999] [--seed 0]

<data_dir> holds index.csv and cats/<id>/{world.npz, fixes.csv} (proto/gps/build_cats.py).
Writes <data_dir>/score.json.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from proto.gps.build_cats import safe_name
from sim.place import TYPES, Place, World

SIGMA_M = 10.0  # GPS error, estimate (L5)
FLOOR = 0.01  # share of the ring mean added everywhere: no fix scores -inf
R_MIN, R_MAX = 20.0, 280.0  # fixes used, metres from home
RING_M = 2.0
CLASSES = {"garden": ("garden", "open"), "anthropogenic": ("edge", "street", "roof"), "natural": ("veg",)}
MAPS = {  # w before the smoothing (docs/MISURE.md L6, proto/gps/pieces.py)
    "walls": lambda p: p.surface.astype(float),
    "sel": lambda p: p.sel,
    "walls_sel": lambda p: p.surface * p.sel,
    "reach": lambda p: p.reach,
    "full": lambda p: np.where(p.ok, p.sel * p.reach, 0.0),  # the engine's up to L9 (the map of L5)
    "engine": lambda p: p.weight,  # the engine's since L9: sel on the cells a cat can stand on
}


def gain_map(place: Place, w: np.ndarray | None = None, sigma: float = SIGMA_M) -> np.ndarray:
    """log(w_s / ring mean of w_s) per cell: the log score gain of the place map (`w`, by
    default the engine's place.weight, smoothed with `sigma` m) over the radial map at the same distance."""
    W = place.w
    w = (place.weight if w is None else w).astype(float)
    if sigma > 0:
        w = ndimage.gaussian_filter(w, sigma / W.cell)
    k = (W.d / RING_M).astype(np.int64)
    ring = np.bincount(k.ravel(), w.ravel()) / np.maximum(np.bincount(k.ravel()), 1)
    w = w + FLOOR * ring[k]
    return np.log(np.maximum(w, 1e-300) / np.maximum(ring[k] * (1 + FLOOR), 1e-300))


def rotations(x, y, theta):
    c, s = np.cos(theta)[:, None], np.sin(theta)[:, None]
    return c * x - s * y, s * x + c * y


def draw_angles(rng, n_rot: int) -> np.ndarray:
    """Angle 0 (the real map) and n_rot random rotations."""
    return np.concatenate([[0.0], rng.uniform(0.0, 2 * np.pi, n_rot)])


def households(homes: dict[str, tuple[float, float]], limit_m: float) -> dict[str, int]:
    """cat_id -> household: cats whose homes are closer than limit_m (single linkage). Cats of a
    household walk the same gardens, so they rotate together, one angle per household, in the
    score and in the null (docs/MISURE.md L7; lessons.md #48)."""
    ids = list(homes)
    lat = np.array([homes[i][0] for i in ids]); lon = np.array([homes[i][1] for i in ids])
    y = (lat - lat.mean()) * 110574.0
    x = (lon - lon.mean()) * 111320.0 * np.cos(np.radians(lat.mean()))
    parent = list(range(len(ids)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(ids)):
        for j in np.flatnonzero(np.hypot(x[i + 1:] - x[i], y[i + 1:] - y[i]) < limit_m) + i + 1:
            parent[root(i)] = root(int(j))
    roots = {r: k for k, r in enumerate(dict.fromkeys(root(i) for i in range(len(ids))))}
    return {c: roots[root(i)] for i, c in enumerate(ids)}


def score_cat(world: World, place: Place, x, y, rng, n_rot: int, map_name: str = "full",
              sigma: float = SIGMA_M, theta: np.ndarray | None = None) -> dict:
    r = np.hypot(x, y)
    keep = (r > R_MIN) & (r <= R_MAX)
    x, y = x[keep], y[keep]
    G = gain_map(place, MAPS[map_name](place), sigma)
    if theta is None:  # given: the angles of the cat's household
        theta = draw_angles(rng, n_rot)
    xr, yr = rotations(x, y, theta)
    iy, ix, _ = world.index(xr, yr)
    S = G[iy, ix].mean(axis=1)
    t = place.type[iy, ix]
    shares = np.stack([np.isin(t, [TYPES.index(n) for n in names]).mean(axis=1) for names in CLASSES.values()], 1)
    return {"n_fixes": int(keep.sum()), "S": float(S[0]), "S_rot": S[1:],
            "u": float((1 + np.sum(S[1:] >= S[0])) / (1 + n_rot)),
            "shares": shares[0], "shares_rot": shares[1:].mean(axis=0)}


def combine(cats: list[dict], n_perm: int, rng, j: np.ndarray | None = None,
            groups: np.ndarray | None = None) -> dict:
    """D = mean over cats of (S - mean S_rot); null: one random rotation per cat, or per household
    when `groups` (household index of each cat, 0..G-1) is given: its cats share their angles, so
    the same index is the same rotation. The draws `j` (perm x cats) can be given to pair several
    maps on the same null. D tests an association (the real fixes above the rotated ones); whether
    the map is a better forecast than the radial one is S_real > 0, the proper log score of the real
    fixes alone (docs/MISURE.md L12: the engine's map has D > 0 and S_real < 0)."""
    rot = np.stack([c["S_rot"] for c in cats])  # cats x rotations
    centre = rot.mean(axis=1)
    D = float(np.mean([c["S"] for c in cats] - centre))
    if j is None:
        if groups is None:
            j = rng.integers(0, rot.shape[1], (n_perm, rot.shape[0]))
        else:
            j = rng.integers(0, rot.shape[1], (n_perm, int(groups.max()) + 1))[:, groups]
    Dp = (rot[np.arange(rot.shape[0]), j] - centre).mean(axis=1)
    sh = np.mean([c["shares"] for c in cats], axis=0)
    sr = np.mean([c["shares_rot"] for c in cats], axis=0)
    ratio = np.where(sr > 0, sh / np.maximum(sr, 1e-300), np.nan)
    delta = np.array([c["S"] for c in cats]) - centre
    sd = float(delta.std(ddof=1)) if len(cats) > 1 else float("nan")
    n_needed = int(np.ceil((3.09 * sd / D) ** 2)) if D > 0 and np.isfinite(sd) else None  # one-sided p < 0.001
    out = {}
    if groups is not None:  # the standard error of D with the households as units (cluster-robust)
        tot = np.bincount(groups, delta - D)
        out = {"n_households": int(groups.max()) + 1, "se_households": float(np.sqrt(np.sum(tot ** 2)) / len(cats))}
    s_real = np.array([c["S"] for c in cats])
    return {"n_cats": len(cats), **out, "D_nats_per_fix": D, "p": float((1 + np.sum(Dp >= D)) / (1 + n_perm)),
            "S_real_nats_per_fix": float(s_real.mean()),
            "S_real_se": float(s_real.std(ddof=1) / np.sqrt(len(cats))) if len(cats) > 1 else float("nan"),
            "sd_between_cats": sd, "se": sd / np.sqrt(len(cats)) if len(cats) > 1 else float("nan"),
            "n_needed_p001": n_needed,
            "share_cats_p_lt_0.05": float(np.mean([c["u"] < 0.05 for c in cats])),
            "shares": dict(zip(CLASSES, sh.round(4).tolist())), "shares_rotated": dict(zip(CLASSES, sr.round(4).tolist())),
            "vs_rotated_standardised": dict(zip(CLASSES, (ratio / np.nansum(ratio)).round(3).tolist()))}


def built_cats(data: Path) -> dict[str, Path]:
    """cat_id -> folder of every cat index.csv marks as built. The folder is named as build_cats
    names it (safe_name); a built cat without its world is an error, not a skip (lessons.md #45)."""
    with open(data / "index.csv", newline="", encoding="utf-8") as f:
        index = [r for r in csv.DictReader(f) if not r.get("skipped_reason")]
    out = {}
    for r in index:
        d = data / "cats" / safe_name(r["cat_id"])
        if not (d / "world.npz").exists():
            raise FileNotFoundError(f"{r['cat_id']}: built in index.csv, but no {d / 'world.npz'}")
        out[r["cat_id"]] = d
    return out


def read_homes(data: Path, dirs: dict[str, Path]) -> dict[str, tuple[float, float]]:
    """(lat, lon) of the home of every built cat, from index.csv."""
    with open(data / "index.csv", newline="", encoding="utf-8") as f:
        return {r["cat_id"]: (float(r["home_lat"]), float(r["home_lon"])) for r in csv.DictReader(f) if r["cat_id"] in dirs}


def inputs_sha1(dirs: dict[str, Path]) -> str:
    """Fingerprint of the data a score read: the arrays of every world.npz (not the zip bytes,
    which carry the build time) and every fixes.csv. A rerun on other data shows (lessons.md #44)."""
    h = hashlib.sha1()
    for cid, d in sorted(dirs.items()):
        h.update(cid.encode())
        with np.load(d / "world.npz") as W:
            for k in sorted(W.files):
                h.update(k.encode()); h.update(W[k].tobytes())
        h.update((d / "fixes.csv").read_bytes())
    return h.hexdigest()


def read_fixes(path: Path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return np.array([float(r["x"]) for r in rows]), np.array([float(r["y"]) for r in rows])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--rot", type=int, default=999)
    ap.add_argument("--perm", type=int, default=9999)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--map", choices=tuple(MAPS), default="full")
    ap.add_argument("--sigma", type=float, default=SIGMA_M, help="GPS error smoothing, m (0 = none)")
    ap.add_argument("--households", type=float, default=0.0,
                    help="cats with homes closer than this many m rotate together (0 = one angle per cat, L5)")
    a = ap.parse_args()
    data = Path(a.data)
    rng = np.random.default_rng(a.seed)
    dirs = built_cats(data)
    hh = households(read_homes(data, dirs), a.households) if a.households > 0 else None
    cats, per_cat, angles = [], {}, {}
    for cid, d in dirs.items():
        world = World(d / "world.npz")
        place = Place(world, floor=0)
        x, y = read_fixes(d / "fixes.csv")
        if hh is not None and hh[cid] not in angles:  # the first cat of a household draws its angles
            angles[hh[cid]] = draw_angles(rng, a.rot)
        c = score_cat(world, place, x, y, rng, a.rot, a.map, a.sigma, angles[hh[cid]] if hh is not None else None)
        if c["n_fixes"] < 20:
            continue
        cats.append(c)
        per_cat[cid] = {"n_fixes": c["n_fixes"], "S": round(c["S"], 4),
                        "S_rot_mean": round(float(c["S_rot"].mean()), 4), "u": round(c["u"], 4)}
        print(cid, per_cat[cid])
    groups = None
    if hh is not None:
        ids = {h: k for k, h in enumerate(dict.fromkeys(hh[c] for c in per_cat))}
        groups = np.array([ids[hh[c]] for c in per_cat])
    out = {"protocol": "docs/MISURE.md L5" if (a.map, a.sigma) == ("full", SIGMA_M) else "docs/MISURE.md L7",
           "map": a.map, "sigma_m": a.sigma, "households_m": a.households,
           "inputs_sha1": inputs_sha1({k: dirs[k] for k in per_cat}),
           **combine(cats, a.perm, rng, groups=groups), "cats": per_cat}
    (data / "score.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "cats"}, indent=1))


if __name__ == "__main__":
    main()
