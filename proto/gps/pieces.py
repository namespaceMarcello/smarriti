"""Which piece of the place carries the signal on real cats? Exploratory, not a confirmation
(docs/MISURE.md, L6): the L5 score (proto/gps/score.py) with one piece of the map at a time, on
the same cats, the same rotations and the same permutation draws, so the pieces are paired.

    python -m proto.gps.pieces <data_dir> [--households 0] [--rot 999] [--perm 9999] [--seed 0]

The maps (w before the smoothing for the GPS error):
  walls          1 outside buildings, 0 inside
  sel            Hanmer's selection of the type of place everywhere (a building counts as roof, 1)
  walls_sel      walls x sel
  reach          reachability from the exits (a building is unreachable: walls included)
  reach_noroads  the same with every road costing its length (only the detours round buildings)
  full_noroads   sel x reach_noroads
  full           sel x reach, the map of L5 (the engine's up to L9)
  engine         sel on the cells a cat can stand on, the engine's since L9 (walls_sel less the
                 free cells the graph cannot reach)
each smoothed with sigma 0, 5, 10, 20 m. With the same seed and --households, every map is
score.py's to the bit (full at 10 m: L5; walls_sel at 0 m: L7). Also the share of the fixes per
type of place and per distance from the nearest building against the rotated fixes (also per
dataset), the share on free cells the graph cannot reach, and D per dataset (country). Writes <data_dir>/pieces.json.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy import ndimage

from proto.gps import score
from proto.gps.score import R_MAX, R_MIN, combine, gain_map, read_fixes, rotations
from sim.place import TYPES, Place, PlaceParams, World

SIGMAS = (0.0, 5.0, 10.0, 20.0)
MAPS = ("walls", "sel", "walls_sel", "reach", "reach_noroads", "full_noroads", "full", "engine")
DIST_BINS = (0.0, 3.0, 6.0, 12.0, 24.0)  # m from the nearest building; 0 = inside one
DIST_NAMES = ("inside", "0-3", "3-6", "6-12", "12-24", ">24")


def maps_of(place: Place, noroads: Place) -> dict:
    out = {m: f(place) for m, f in score.MAPS.items()}
    out.update(reach_noroads=noroads.reach, full_noroads=score.MAPS["full"](noroads))
    return {m: out[m] for m in MAPS}


def dist_class(world: World) -> np.ndarray:
    bld = world.bid >= 0
    d = ndimage.distance_transform_edt(~bld) * world.cell  # 0 inside a building
    return np.where(bld, 0, 1 + np.searchsorted(DIST_BINS[1:], d, "left")).astype(np.int8)


def shares(labels: np.ndarray, n: int):
    """Share of each label among the real fixes (row 0) and among all the rotated ones."""
    real = np.bincount(labels[0], minlength=n) / labels.shape[1]
    rot = np.bincount(labels[1:].ravel(), minlength=n) / labels[1:].size
    return real, rot


def paired(real: np.ndarray, rot: np.ndarray, names) -> dict:
    """Mean over cats of the real and rotated shares, their ratio, and the paired difference."""
    d = real - rot
    se = d.std(axis=0, ddof=1) / np.sqrt(len(d))
    return {k: {"real": round(float(real[:, i].mean()), 4), "rotated": round(float(rot[:, i].mean()), 4),
                "ratio": round(float(real[:, i].mean() / max(rot[:, i].mean(), 1e-12)), 3),
                "diff": round(float(d[:, i].mean()), 4), "se": round(float(se[i]), 4)}
            for i, k in enumerate(names)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--rot", type=int, default=999)
    ap.add_argument("--perm", type=int, default=9999)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--households", type=float, default=0.0, help="as in score.py (L7: 20)")
    a = ap.parse_args()
    data = Path(a.data)
    rng = np.random.default_rng(a.seed)
    dirs = score.built_cats(data)
    with open(data / "index.csv", newline="", encoding="utf-8") as f:
        dataset_of = {r["cat_id"]: r["dataset"].split()[0] for r in csv.DictReader(f)}
    hh = score.households(score.read_homes(data, dirs), a.households) if a.households > 0 else None
    S = {(m, s): [] for m in MAPS for s in SIGMAS}  # per cat: scores of the real and rotated fixes
    types_real, types_rot, dist_real, dist_rot, per_cat, angles = [], [], [], [], {}, {}
    for cid, d in dirs.items():
        world = World(d / "world.npz")
        x, y = read_fixes(d / "fixes.csv")
        r = np.hypot(x, y)
        keep = (r > R_MIN) & (r <= R_MAX)
        if hh is None:
            theta = score.draw_angles(rng, a.rot)  # the draws of score.py, in the same order
        else:
            if hh[cid] not in angles:
                angles[hh[cid]] = score.draw_angles(rng, a.rot)
            theta = angles[hh[cid]]
        if keep.sum() < 20:
            continue
        place = Place(world, floor=0)
        noroads = Place(world, floor=0, par=PlaceParams(c_road=(1.0,) * 6))
        iy, ix, _ = world.index(*rotations(x[keep], y[keep], theta))
        for m, w in maps_of(place, noroads).items():
            for s in SIGMAS:
                S[m, s].append(gain_map(place, w, s)[iy, ix].mean(axis=1))
        tr, tt = shares(place.type[iy, ix], len(TYPES))
        dr, dt = shares(dist_class(world)[iy, ix], len(DIST_NAMES))
        types_real.append(tr); types_rot.append(tt); dist_real.append(dr); dist_rot.append(dt)
        unreachable = ((world.bid < 0) & (place.reach == 0))[iy, ix]  # free cells the graph cannot reach
        per_cat[cid] = {"n_fixes": int(keep.sum()), "inside_real": round(float(dr[0]), 4),
                        "inside_rotated": round(float(dt[0]), 4),
                        "unreachable_real": round(float(unreachable[0].mean()), 4),
                        "unreachable_rotated": round(float(unreachable[1:].mean()), 4)}
        print(cid, per_cat[cid], flush=True)
    n = len(per_cat)
    if hh is None:  # the draws of score.py's combine: the same null for every map
        j = rng.integers(0, a.rot, (a.perm, n))
    else:  # one rotation per household, as score.py
        ids = {h: k for k, h in enumerate(dict.fromkeys(hh[c] for c in per_cat))}
        j = rng.integers(0, a.rot, (a.perm, len(ids)))[:, [ids[hh[c]] for c in per_cat]]
    out = {"protocol": "docs/MISURE.md L6 (exploratory)", "n_cats": n, "households_m": a.households,
           "inputs_sha1": score.inputs_sha1({k: dirs[k] for k in per_cat}), "maps": {}}
    delta = {k: np.array([v[0] - v[1:].mean() for v in S[k]]) for k in S}  # per cat, S - mean S_rot
    ref = delta["full", 10.0]
    for m in MAPS:
        out["maps"][m] = {}
        for s in SIGMAS:
            cats = [{"S": float(v[0]), "S_rot": v[1:], "u": float((1 + np.sum(v[1:] >= v[0])) / len(v)),
                     "shares": np.ones(3), "shares_rot": np.ones(3)} for v in S[m, s]]  # shares: see "types"
            c = combine(cats, a.perm, rng, j)
            dd = delta[m, s] - ref  # paired with the L5 map (full, 10 m) on the same cats
            out["maps"][m][f"{s:g}"] = {"D": round(c["D_nats_per_fix"], 5), "se": round(c["sd_between_cats"] / np.sqrt(n), 5),
                                        "p": c["p"], "sd": round(c["sd_between_cats"], 4),
                                        "S_real": round(c["S_real_nats_per_fix"], 5), "S_real_se": round(c["S_real_se"], 5),
                                        "n_needed_p001": c["n_needed_p001"],
                                        "share_cats_p_lt_0.05": round(c["share_cats_p_lt_0.05"], 3),
                                        "vs_full10": round(float(dd.mean()), 5),
                                        "vs_full10_se": round(float(dd.std(ddof=1) / np.sqrt(n)), 5)}
    out["types"] = paired(np.array(types_real), np.array(types_rot), TYPES)
    out["dist_to_building"] = paired(np.array(dist_real), np.array(dist_rot), DIST_NAMES)
    for i, cid in enumerate(per_cat):  # S - mean S_rot of every map: any two maps can be paired later
        per_cat[cid]["delta"] = {f"{m} {s:g}": round(float(delta[m, s][i]), 5) for m in MAPS for s in SIGMAS}
    ds = np.array([dataset_of[c] for c in per_cat])  # D per dataset (country), descriptive
    out["by_dataset"] = {}
    for name in sorted(set(ds)):
        k = ds == name
        out["by_dataset"][name] = {
            f"{m} {s:g}": {"n": int(k.sum()), "D": round(float(delta[m, s][k].mean()), 5),
                           "se": round(float(delta[m, s][k].std(ddof=1) / np.sqrt(k.sum())), 5) if k.sum() > 1 else None}
            for m, s in (("walls_sel", 0.0), ("full", 10.0), ("engine", 0.0))}
        out["by_dataset"][name]["dist_to_building"] = paired(np.array(dist_real)[k], np.array(dist_rot)[k], DIST_NAMES)
    out["cats"] = per_cat
    (data / "pieces.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\n{n} cats. D nats/fix (p) [minus full 10 m, in paired se] {{S of the real fixes: > 0 beats the radial map}}"
          " by sigma: " + "  ".join(f"{s:g} m" for s in SIGMAS))
    for m in MAPS:
        print(f"{m:14s}" + "".join(f"  {v['D']:+.4f} ({v['p']:.3f}) [{v['vs_full10'] / max(v['vs_full10_se'], 1e-12):+.1f}]"
                                   f" {{{v['S_real']:+.4f}}}" for v in out["maps"][m].values()))
    for k in ("types", "dist_to_building"):
        print(k, {t: (v["real"], v["rotated"], v["ratio"]) for t, v in out[k].items()})


if __name__ == "__main__":
    main()
