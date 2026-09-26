"""What the LiDAR at 1 m adds to the place (docs/MISURE.md, L8), within R of home: the terrain
against TINITALY at 10 m, the height of things above the ground outside buildings, and how much
of the place a cat reaches when the heights count (variant 3) with the terrain at 1 m.

    python -m proto.luogo3d.metre <place.json> <data_dir>    # world.npz with dtm1 (fetch ... lidar, then world)

Writes <data_dir>/metre.json. The engine does not read the LiDAR layers: nothing here changes it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

from sim.place import Place, World

R = 200.0  # m from home
H_BINS = (0.3, 1.5, 4.0)  # above the ground: bare or grass, low (bushes, hedges, cars, low walls), mid, trees
H_NAMES = ("<0.3", "0.3-1.5", "1.5-4", ">=4")


def steps(z, free, h: float) -> float:
    """Share of pairs of side-by-side free cells whose ground differs by more than h."""
    d = []
    for a, b in ((np.s_[:, :-1], np.s_[:, 1:]), (np.s_[:-1, :], np.s_[1:, :])):
        ok = free[a] & free[b]
        d.append(np.abs(z[a] - z[b])[ok])
    return float((np.concatenate(d) > h).mean())


def reach_stats(P: Place, near, bld, home) -> dict:
    roofs, ground = near & bld & ~home, near & ~bld
    return {"roofs_reachable": round(float((P.reach[roofs] > 0).mean()), 4),
            "ground_reachable": round(float((P.reach[ground] > 0).mean()), 4),
            "reach_mean_ground": round(float(P.reach[ground].mean()), 4)}


def main(argv):
    floor = int(json.loads(Path(argv[0]).read_text(encoding="utf-8")).get("floor", 1))
    data = Path(argv[1])
    Z = np.load(data / "world.npz")
    W = World(data / "world.npz")
    near, bld, home = W.d <= R, W.bid >= 0, W.bid == W.bid_home
    free = near & ~bld
    dtm1, dsm1, hmax = Z["dtm1"].astype(float), Z["dsm1"].astype(float), Z["hmax1"].astype(float)
    d = (dtm1 - W.ground)[free]
    out = {"R_m": R, "terrain": {
        "median_abs_m": round(float(np.median(np.abs(d))), 2), "p95_abs_m": round(float(np.percentile(np.abs(d), 95)), 2),
        "median_m": round(float(np.median(d)), 2),
        "steps_over_1.5m_lidar": round(steps(dtm1, free, 1.5), 4), "steps_over_1.5m_tinitaly": round(steps(W.ground, free, 1.5), 4)}}
    c = np.digitize(hmax[free], H_BINS)
    out["height_above_ground_free"] = dict(zip(H_NAMES, np.round(np.bincount(c, minlength=4) / c.size, 4).tolist()))
    out["building_height_m"] = {"globfp_osm_median": round(float(np.median(W.bh[near & bld])), 2),
                                "lidar_median": round(float(np.median((dsm1 - dtm1)[near & bld])), 2)}
    # per building, on the cells inside the footprint shrunk by one cell (no mixed edges): L8b
    inner = ndimage.binary_erosion(bld, np.ones((3, 3), bool)) & near & ~home
    ids = np.unique(W.bid[inner])
    n_in = ndimage.sum(inner, labels=W.bid, index=ids)
    h_lidar = ndimage.median(dsm1 - dtm1, labels=np.where(inner, W.bid, -1), index=ids)
    h_world = ndimage.maximum(W.bh, labels=W.bid, index=ids)
    src = ndimage.maximum(Z["bsrc"], labels=W.bid, index=ids)
    out["building_height_per_building"] = {}
    for name, s in (("globfp", 1), ("osm_added", 2)):
        k = (n_in >= 4) & (src == s)
        dh = h_world[k] - h_lidar[k]
        out["building_height_per_building"][name] = {
            "n": int(k.sum()), "median_world_minus_lidar_m": round(float(np.median(dh)), 2) if k.any() else None,
            "iqr_m": [round(float(v), 2) for v in np.percentile(dh, [25, 75])] if k.any() else None,
            "corr": round(float(np.corrcoef(h_world[k], h_lidar[k])[0, 1]), 3)
            if k.sum() > 2 and np.ptp(h_world[k]) > 0 else None}  # OSM-added: one height for all, no correlation
    out["reach"] = {"variant2": reach_stats(Place(W, floor, heights=False), near, bld, home),
                    "variant3_tinitaly": reach_stats(Place(W, floor, heights=True), near, bld, home)}
    W.ground = dtm1  # the terrain at 1 m, and every roof at its surface from the LiDAR
    W.bh = np.where(bld, np.maximum(dsm1 - dtm1, 0.0), 0.0)
    out["reach"]["variant3_lidar"] = reach_stats(Place(W, floor, heights=True), near, bld, home)
    # the same with each roof flat at the median surface of its building: a 2 m cell on the edge of
    # a footprint mixes roof and ground and makes steps a cat could climb that are not there (L8)
    med = ndimage.median(dsm1, labels=W.bid + 1, index=np.arange(W.bid.max() + 2))
    W.bh = np.where(bld, np.maximum(med[W.bid + 1] - dtm1, 0.0), 0.0)
    P = Place(W, floor, heights=True)
    out["reach"]["variant3_lidar_flat_roofs"] = reach_stats(P, near, bld, home)
    roofs = near & bld & ~home
    out["reach"]["variant3_lidar_flat_roofs"]["buildings_reachable"] = \
        f"{len(np.unique(W.bid[roofs & (P.reach > 0)]))} of {len(np.unique(W.bid[roofs]))}"
    (data / "metre.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
