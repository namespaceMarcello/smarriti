"""Three maps side by side for one place: 1 today (circles), 2 buildings and gardens,
3 with heights and slopes. Plus the checks of docs/simulatore.md ("Come si prova").

    python -m proto.luogo3d.variants <place.json> <data_dir> [--hours 24] [--n 50000] [--no-step-selection]

Writes <data_dir>/varianti-<h>h.png (side by side), <data_dir>/variante-{1,2,3}-<h>h.png and
<data_dir>/varianti-<h>h.json. The images show the real place: they stay private.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource, ListedColormap

from sim.categories import mixture
from sim.engine import LOOSE, Simulation
from sim.outputs import _smooth, kernel_sigmas, make_place_grid
from sim.place import TYPES, Place, PlaceParams, World

CELL = 4.0  # map cells, m
VIEW = 300.0  # half-width of the picture, m
BANDS = (0.25, 0.5, 0.75)
TITLES = {1: "1 · Oggi: a cerchi", 2: "2 · Con edifici e giardini", 3: "3 · Con anche i dislivelli"}


def run(world, place, floor, hours, n, seed, hod0=20):
    sim = Simulation(mixture("cat_indoor"), n, seed, floor=floor, hod0=hod0, place=place, place_seed=seed + 7)
    anchors = (sim.ax.copy(), sim.ay.copy())
    sim.run(hours)
    sim.condition_not_home()
    return sim, anchors


def fine_map(world, place, sim):
    """P(loose in cell) on CELL m cells over the world square; masked where the cat cannot stand."""
    loose = (sim.state == LOOSE) & (sim.w > 0)
    if place is not None:
        return make_place_grid(sim, CELL).mass, float(sim.w[loose].sum())
    x, y, w = sim.x[loose], sim.y[loose], sim.w[loose]
    half = -world.x0
    m = int(2 * half / CELL)
    s = kernel_sigmas(x, y, CELL) / CELL
    gx, gy = (x + half) / CELL, (y + half) / CELL
    inside = (gx >= 0) & (gx < m) & (gy >= 0) & (gy < m)
    return _smooth((m, m), gx[inside], gy[inside], w[inside], s[inside]), float(w.sum())


def hdr_levels(mass, fracs, total):
    """Density thresholds whose superlevel sets hold each fraction of the total loose mass."""
    v = np.sort(mass.ravel())[::-1]
    c = np.cumsum(v) / total
    out = []
    for f in fracs:
        k = np.searchsorted(c, f)
        out.append((v[k] if k < len(v) else 0.0, int(k + 1) if k < len(v) else None))
    return out


def coverage(mass, total, truth_x, truth_y, world, fracs=(0.5, 0.75)):
    half = -world.x0
    m = mass.shape[0]
    ix, iy = ((truth_x + half) // CELL).astype(int), ((truth_y + half) // CELL).astype(int)
    ok = (ix >= 0) & (ix < m) & (iy >= 0) & (iy < m)
    out = {}
    for f, (lev, k) in zip(fracs, hdr_levels(mass, fracs, total)):
        if k is None:
            out[f] = None
            continue
        hit = np.zeros(len(truth_x), bool)
        hit[ok] = mass[iy[ok], ix[ok]] >= lev
        out[f] = float(hit.mean())
    return out


HANMER = {"garden": ("garden", "open"), "anthropogenic": ("edge", "street", "roof"), "natural": ("veg",)}
HANMER_RATIOS = {"garden": 0.553, "anthropogenic": 0.311, "natural": 0.136}


def class_shares(world, place3, x, y, w, radius=200.0):
    """Share of the weight on each of Hanmer's classes, positions on the ground within `radius`."""
    iy, ix, ok = world.index(x, y)
    ok &= np.isfinite(x) & (np.hypot(x, y) <= radius) & (world.bid[iy, ix] < 0)
    t, ww = place3.type[iy[ok], ix[ok]], w[ok]
    return {k: float((ww * np.isin(t, [TYPES.index(nm) for nm in names])).sum() / max(ww.sum(), 1e-300))
            for k, names in HANMER.items()}


def against_1(shares, shares1):
    """lessons.md #36: an effect of the place is read against the map without it, at the same
    distances: use in this variant / use in variant 1, standardised like Manly's ratios."""
    r = {k: shares[k] / shares1[k] if shares1[k] > 0 else np.nan for k in HANMER}
    s = sum(r.values())
    return {k: round(float(v / s), 3) for k, v in r.items()}


def manly(world, place3, x, y, w, radius=200.0, buildings=True):
    """Manly's standardised selection ratios over Hanmer et al. 2017's three classes, within
    `radius` of home: use = weighted positions, availability = ground cells and roofs there.
    Hanmer (cats next to large greenspace): garden 0.553, anthropogenic 0.311, natural 0.136."""
    t = place3.type
    avail_mask = (world.d <= radius) & (world.bid != world.bid_home)
    if not buildings:  # lessons.md #34: available = where the cat can stand in variant 2
        avail_mask &= world.bid < 0
    iy, ix, ok = world.index(x, y)
    ok &= np.hypot(x, y) <= radius
    ok &= np.isfinite(x)
    ratio = {}
    for k, names in HANMER.items():
        codes = [TYPES.index(nm) for nm in names]
        a = np.isin(t, codes)[avail_mask].mean()
        u = (w[ok] * np.isin(t[iy[ok], ix[ok]], codes)).sum() / max(w[ok].sum(), 1e-300)
        ratio[k] = u / a if a > 0 else np.nan
    s = sum(ratio.values())
    return {k: round(float(v / s), 3) for k, v in ratio.items()}


def basemap(world, place3):
    W = world
    rgb = np.empty(W.bid.shape + (3,))
    rgb[:] = (0.95, 0.94, 0.91)
    t = place3.type
    rgb[t == TYPES.index("garden")] = (0.88, 0.93, 0.80)
    rgb[t == TYPES.index("veg")] = (0.80, 0.89, 0.76)
    rgb[W.road >= 1] = (1.0, 1.0, 1.0)
    rgb[W.road >= 4] = (1.0, 0.95, 0.82)
    bld = W.bid >= 0
    shade = np.clip(0.80 - W.bh / 60.0, 0.5, 0.8)
    rgb[bld] = np.stack([shade, shade, shade * 0.98], -1)[bld]
    hs = LightSource(azdeg=315, altdeg=40).hillshade(W.ground + W.bh, vert_exag=1.0, dx=W.cell, dy=W.cell)
    return np.clip(rgb * (0.78 + 0.22 * hs[..., None]), 0, 1)


def draw(ax, world, base, mass, total, title, home_mask, stats):
    W = world
    half = -W.x0
    ax.imshow(base, origin="lower", extent=(-half, half, -half, half), interpolation="nearest")
    levels = [lev for lev, _ in hdr_levels(mass, BANDS, total)]
    cmap = ListedColormap([(0.99, 0.80, 0.25), (0.93, 0.42, 0.13), (0.70, 0.05, 0.10)])
    band = np.full(mass.shape, np.nan)
    for i, lev in enumerate(sorted(levels)):  # 75% band first, 25% band last
        band[mass >= lev] = i
    ax.imshow(np.ma.masked_invalid(band), origin="lower", extent=(-half, half, -half, half), cmap=cmap,
              vmin=-0.5, vmax=2.5, alpha=0.62, interpolation="nearest")
    ax.contour(W.gx, W.gy, home_mask.astype(float), levels=[0.5], colors="#1a1a1a", linewidths=1.2)
    ax.plot(0, 0, marker="o", ms=6, mfc="white", mec="black", mew=1.4)
    ax.set_xlim(-VIEW, VIEW); ax.set_ylim(-VIEW, VIEW)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=15, loc="left", fontweight="bold")
    a50, a75 = stats["area_ha"]["0.5"], stats["area_ha"]["0.75"]
    it = lambda v: f"{v:.1f}".replace(".", ",")
    ax.text(0.01, -0.025, f"metà delle probabilità in {it(a50)} ettari · tre su quattro in {it(a75)} ettari",
            transform=ax.transAxes, fontsize=11.5, va="top")
    ax.plot([VIEW - 130, VIEW - 30], [-VIEW + 22] * 2, color="black", lw=3)
    ax.text(VIEW - 80, -VIEW + 30, "100 m", ha="center", fontsize=10)
    ax.annotate("N", xy=(-VIEW + 25, VIEW - 20), xytext=(-VIEW + 25, VIEW - 62), ha="center", fontsize=11,
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("place"); ap.add_argument("data")
    ap.add_argument("--hours", type=int, default=24); ap.add_argument("--n", type=int, default=50_000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-step-selection", action="store_true", help="the place picks the anchors only (L1b)")
    a = ap.parse_args()
    place_cfg = json.loads(Path(a.place).read_text(encoding="utf-8"))
    data = Path(a.data)
    floor = int(place_cfg.get("floor", 1))
    t0 = time.time()
    world = World(data / "world.npz")
    par = PlaceParams(step_selection=not a.no_step_selection)
    places = {1: None, 2: Place(world, floor, par=par), 3: Place(world, floor, heights=True, par=par)}
    t_place = time.time() - t0
    home_mask = world.bid == world.bid_home
    base = basemap(world, places[3])
    out, maps = {"hours": a.hours, "n": a.n, "floor": floor, "t_place_s": round(t_place, 2),
                 "step_selection": par.step_selection}, {}
    for v, place in places.items():
        t = time.time()
        sim, (ax_, ay_) = run(world, place, floor, a.hours, a.n, a.seed)
        mass, total = fine_map(world, place, sim)
        twin, _ = run(world, place, floor, a.hours, a.n, a.seed + 1000)  # independent truths for C1
        tl = twin.state == LOOSE
        cov = coverage(mass, total, twin.x[tl], twin.y[tl], world)
        loose = sim.state == LOOSE
        r = np.hypot(sim.x[loose], sim.y[loose])
        ra = np.hypot(ax_, ay_)
        ra = ra[np.isfinite(ra) & (ra > 0)]
        st = {"p_loose": float(sim.w[loose].sum()), "mass_in_grid": total and float(mass.sum() / total),
              "dist_loose_q25_50_75": np.percentile(r, [25, 50, 75]).round(1).tolist(),
              "dist_anchor_q25_50_75_90": np.percentile(ra, [25, 50, 75, 90]).round(1).tolist(),
              "coverage": {str(k): v_ for k, v_ in cov.items()},
              "area_ha": {str(f): (k * CELL * CELL / 1e4 if k else None) for f, (_, k) in zip(BANDS, hdr_levels(mass, BANDS, total))},
              "fallback_share": getattr(sim, "fallback", 1.0),
              "centre_of_mass_m": [float(np.average(sim.x[loose], weights=sim.w[loose])),
                                   float(np.average(sim.y[loose], weights=sim.w[loose]))],
              "seconds": round(time.time() - t, 2)}
        # place type of the anchors within the grid (every variant read on the same type map)
        iy, ix, ok = world.index(ax_, ay_)
        tt = places[3].type[iy, ix]
        grounded = ok & (world.bid[iy, ix] < 0) & (np.hypot(ax_, ay_) > 0)
        st["anchor_type_share"] = {k: float(((tt == i) & grounded).sum() / max(grounded.sum(), 1)) for i, k in enumerate(TYPES)}
        st["anchor_in_building"] = float((ok & (world.bid[iy, ix] >= 0)).sum() / max(ok.sum(), 1))
        st["manly_anchor"] = manly(world, places[3], ax_, ay_, np.ones(len(ax_)))
        st["manly_loose"] = manly(world, places[3], sim.x[loose], sim.y[loose], sim.w[loose])
        st["manly_anchor_ground"] = manly(world, places[3], ax_, ay_, np.ones(len(ax_)), buildings=False)
        st["manly_loose_ground"] = manly(world, places[3], sim.x[loose], sim.y[loose], sim.w[loose], buildings=False)
        st["shares_anchor"] = class_shares(world, places[3], ax_, ay_, np.ones(len(ax_)))
        st["shares_loose"] = class_shares(world, places[3], sim.x[loose], sim.y[loose], sim.w[loose])
        if v > 1:
            st["vs1_anchor"] = against_1(st["shares_anchor"], out["1"]["shares_anchor"])
            st["vs1_loose"] = against_1(st["shares_loose"], out["1"]["shares_loose"])
        st["sel_ref"] = sim.sel_ref
        if v == 3:
            st["z_floor"] = places[3].z_floor
            st["window_exit_cells"] = int(places[3].exits[1].sum())
        out[str(v)] = st
        maps[v] = (mass, total)
        print(v, json.dumps(st))
    h = a.hours
    tag = "" if par.step_selection else "-ancore"
    fig, axs = plt.subplots(1, 3, figsize=(21, 7.9))
    for v, ax in zip((1, 2, 3), axs):
        draw(ax, world, base, *maps[v], TITLES[v], home_mask, out[str(v)])
    fig.suptitle(f"Gatto di casa scappato dal primo piano: dove può essere dopo {h} ore", fontsize=17, x=0.01, ha="left")
    fig.text(0.01, 0.012, "rosso scuro: il 25% più probabile · rosso: 50% · giallo: 75%  —  cerchio bianco: il portone; "
             "contorno nero: la casa", fontsize=11)
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.savefig(data / f"varianti-{h}h{tag}.png", dpi=110)
    plt.close(fig)
    for v in (1, 2, 3):
        f, ax = plt.subplots(figsize=(8, 8.4))
        draw(ax, world, base, *maps[v], TITLES[v], home_mask, out[str(v)])
        f.tight_layout(); f.savefig(data / f"variante-{v}-{h}h{tag}.png", dpi=110); plt.close(f)
    tv = lambda a, b: 0.5 * float(np.abs(maps[a][0] / maps[a][1] - maps[b][0] / maps[b][1]).sum())
    out["tv_distance"] = {"2_vs_1": tv(2, 1), "3_vs_1": tv(3, 1), "3_vs_2": tv(3, 2)}
    print("tv", out["tv_distance"])
    (data / f"varianti-{h}h{tag}.json").write_text(json.dumps(out, indent=1))
    print(f"total {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
