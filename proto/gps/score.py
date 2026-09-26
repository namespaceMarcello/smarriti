"""Does the place point where real cats are? The direction part of the model (the ring
density w = sel x reach of sim/place.py) scored on GPS fixes of pet cats, against the same
map rotated around home. The protocol was written before the data: docs/MISURE.md, L5.

    python -m proto.gps.score <data_dir> [--rot 999] [--perm 9999] [--seed 0]

<data_dir> holds index.csv and cats/<id>/{world.npz, fixes.csv} (proto/gps/build_cats.py).
Writes <data_dir>/score.json.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from sim.place import TYPES, Place, World

SIGMA_M = 10.0  # GPS error, estimate (L5)
FLOOR = 0.01  # share of the ring mean added everywhere: no fix scores -inf
R_MIN, R_MAX = 20.0, 280.0  # fixes used, metres from home
RING_M = 2.0
CLASSES = {"garden": ("garden", "open"), "anthropogenic": ("edge", "street", "roof"), "natural": ("veg",)}


def gain_map(place: Place) -> np.ndarray:
    """log(w_s / ring mean of w_s) per cell: the log score gain of the place map over the
    radial map at the same distance from home."""
    W = place.w
    w = ndimage.gaussian_filter(place.weight.astype(float), SIGMA_M / W.cell)
    k = (W.d / RING_M).astype(np.int64)
    ring = np.bincount(k.ravel(), w.ravel()) / np.maximum(np.bincount(k.ravel()), 1)
    w = w + FLOOR * ring[k]
    return np.log(np.maximum(w, 1e-300) / np.maximum(ring[k] * (1 + FLOOR), 1e-300))


def rotations(x, y, theta):
    c, s = np.cos(theta)[:, None], np.sin(theta)[:, None]
    return c * x - s * y, s * x + c * y


def score_cat(world: World, place: Place, x, y, rng, n_rot: int) -> dict:
    r = np.hypot(x, y)
    keep = (r > R_MIN) & (r <= R_MAX)
    x, y = x[keep], y[keep]
    G = gain_map(place)
    theta = np.concatenate([[0.0], rng.uniform(0.0, 2 * np.pi, n_rot)])
    xr, yr = rotations(x, y, theta)
    iy, ix, _ = world.index(xr, yr)
    S = G[iy, ix].mean(axis=1)
    t = place.type[iy, ix]
    shares = np.stack([np.isin(t, [TYPES.index(n) for n in names]).mean(axis=1) for names in CLASSES.values()], 1)
    return {"n_fixes": int(keep.sum()), "S": float(S[0]), "S_rot": S[1:],
            "u": float((1 + np.sum(S[1:] >= S[0])) / (1 + n_rot)),
            "shares": shares[0], "shares_rot": shares[1:].mean(axis=0)}


def combine(cats: list[dict], n_perm: int, rng) -> dict:
    """D = mean over cats of (S - mean S_rot); null: one random rotation per cat."""
    rot = np.stack([c["S_rot"] for c in cats])  # cats x rotations
    centre = rot.mean(axis=1)
    D = float(np.mean([c["S"] for c in cats] - centre))
    j = rng.integers(0, rot.shape[1], (n_perm, rot.shape[0]))
    Dp = (rot[np.arange(rot.shape[0]), j] - centre).mean(axis=1)
    sh = np.mean([c["shares"] for c in cats], axis=0)
    sr = np.mean([c["shares_rot"] for c in cats], axis=0)
    ratio = np.where(sr > 0, sh / np.maximum(sr, 1e-300), np.nan)
    delta = np.array([c["S"] for c in cats]) - centre
    sd = float(delta.std(ddof=1)) if len(cats) > 1 else float("nan")
    n_needed = int(np.ceil((3.09 * sd / D) ** 2)) if D > 0 and np.isfinite(sd) else None  # one-sided p < 0.001
    return {"n_cats": len(cats), "D_nats_per_fix": D, "p": float((1 + np.sum(Dp >= D)) / (1 + n_perm)),
            "sd_between_cats": sd, "n_needed_p001": n_needed,
            "share_cats_p_lt_0.05": float(np.mean([c["u"] < 0.05 for c in cats])),
            "shares": dict(zip(CLASSES, sh.round(4).tolist())), "shares_rotated": dict(zip(CLASSES, sr.round(4).tolist())),
            "vs_rotated_standardised": dict(zip(CLASSES, (ratio / np.nansum(ratio)).round(3).tolist()))}


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
    a = ap.parse_args()
    data = Path(a.data)
    rng = np.random.default_rng(a.seed)
    with open(data / "index.csv", newline="", encoding="utf-8") as f:
        index = [r for r in csv.DictReader(f) if not r.get("skipped_reason")]
    cats, per_cat = [], {}
    for row in index:
        d = data / "cats" / row["cat_id"]
        if not (d / "world.npz").exists():
            continue
        world = World(d / "world.npz")
        place = Place(world, floor=0)
        x, y = read_fixes(d / "fixes.csv")
        c = score_cat(world, place, x, y, rng, a.rot)
        if c["n_fixes"] < 20:
            continue
        cats.append(c)
        per_cat[row["cat_id"]] = {"n_fixes": c["n_fixes"], "S": round(c["S"], 4),
                                  "S_rot_mean": round(float(c["S_rot"].mean()), 4), "u": round(c["u"], 4)}
        print(row["cat_id"], per_cat[row["cat_id"]])
    out = {"protocol": "docs/MISURE.md L5", **combine(cats, a.perm, rng), "cats": per_cat}
    (data / "score.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "cats"}, indent=1))


if __name__ == "__main__":
    main()
