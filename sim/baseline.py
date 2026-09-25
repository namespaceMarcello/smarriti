"""Phase C: the simulator against the ring model (Koester, Lost Person Behavior).

    python -m sim.baseline [--per-category 40] [--truths 50] [--seed 0]

Synthetic cases: for each case the true animals move with parameters perturbed by +-30%
from the calibrated ones (so the simulator does not grade itself), from a random clock hour,
and are read at a random hour between 12 h and 10 days while still loose. Two maps:

- rings: concentric rings around home at the 25/50/75/95/99% quantiles of the distance
  the category has reached at that hour (a ring model that knows the elapsed time),
  drawn on the same 50 m grid so that resolution favours neither;
- sim: the simulator's map.

Score, per true animal: the area searched, cell by cell from the most probable, before
reaching it (ties: half the tied area); and whether it falls in the cells holding 50% / 90%
of the mass. Truth outside a map's support: the support plus half of the rest of the disk
of radius R_OUT_FACTOR x r99.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace

import numpy as np

from .categories import BASE, NUMERIC_FIELDS, Category, get
from .engine import LOOSE, Simulation
from .outputs import CELL_M, Grid, make_grid

CATEGORIES = list(BASE)
PERTURB = 0.30
NOW_RANGE_H = (12, 240)
N_PARTICLES = 5_000
R_OUT_FACTOR = 2.0
RING_Q = (0.25, 0.50, 0.75, 0.95, 0.99)
STRUCTURAL = {"home_from_h", "home_until_h", "home_late_mult"}


def perturb(cat: Category, rng: np.random.Generator) -> Category:
    kw = {f: getattr(cat, f) * rng.uniform(1 - PERTURB, 1 + PERTURB) for f in NUMERIC_FIELDS if f not in STRUCTURAL}
    for f in ("p_move_day", "p_move_night"):
        kw[f] = min(kw[f], 1.0)
    for f in ("pull_flight", "pull_settled"):
        kw[f] = min(kw[f], 0.95)
    return replace(cat, **kw)


def ring_grid(radii: np.ndarray, cell: float) -> Grid:
    """The ring model on the simulator's grid: rings hold 25/25/25/20/4% of the mass
    (1% beyond r99), uniform inside each ring, cells centred on home."""
    half = int(np.ceil(radii[-1] / cell - 0.5))
    c = np.arange(-half, half + 1) * cell
    gx, gy = np.meshgrid(c, c)
    d = np.hypot(gx, gy)
    edges = np.concatenate([[0.0], radii])
    mass = np.diff(np.concatenate([[0.0], RING_Q]))
    dens = mass / np.maximum(np.pi * (edges[1:] ** 2 - edges[:-1] ** 2), 1e-9)
    k = np.searchsorted(edges[1:], d)
    m = np.where(k < len(radii), dens[np.minimum(k, len(radii) - 1)], 0.0) * cell**2
    return Grid(float(c[0] - cell / 2), float(c[0] - cell / 2), cell, m / m.sum() * RING_Q[-1])


def grid_scores(grid: Grid, tx: np.ndarray, ty: np.ndarray, r_out: float) -> dict:
    """Per truth: area (ha) searched before reaching it, and membership of HPD50/90."""
    cell_ha = grid.cell**2 / 1e4
    ny, nx = grid.mass.shape
    ix = np.floor((tx - grid.x0) / grid.cell).astype(int)
    iy = np.floor((ty - grid.y0) / grid.cell).astype(int)
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    p = np.zeros(len(tx))
    p[ok] = grid.mass[iy[ok], ix[ok]]
    asc = np.sort(grid.mass.ravel())
    right = np.searchsorted(asc, p, "right")
    left = np.searchsorted(asc, p, "left")
    support = np.count_nonzero(asc) * cell_ha
    outside = support + 0.5 * max(0.0, np.pi * r_out**2 / 1e4 - support)
    area = np.where(p > 0, ((len(asc) - right) + 0.5 * (right - left)) * cell_ha, outside)
    desc = asc[::-1]
    cum = np.cumsum(desc) / max(desc.sum(), 1e-12)
    out = {"area_ha": area}
    for q in (0.5, 0.9):
        thr = desc[int(np.searchsorted(cum, q))]
        out[f"in_hpd{int(q * 100)}"] = (p > 0) & (p >= thr)
    return out


MIN_LOOSE = 20  # below this the simulator has no map to score (both models skip the case)


def run_case(name: str, rng: np.random.Generator, seed: int, n_truths: int, now: int | None = None) -> dict | str | None:
    """Scores for one case; None if no true animal is loose, "no_map" if the simulator has
    fewer than MIN_LOOSE loose particles (it predicts the animal is not loose)."""
    hod0 = int(rng.integers(0, 24))
    now = int(rng.integers(*NOW_RANGE_H)) if now is None else now
    truth = Simulation([(perturb(get(name), rng), 1.0)], 4 * n_truths, seed, hod0=hod0)
    truth.run(now)
    loose = np.flatnonzero(truth.state == LOOSE)[:n_truths]
    if len(loose) == 0:
        return None
    tx, ty = truth.x[loose], truth.y[loose]
    sim = Simulation([(get(name), 1.0)], N_PARTICLES, seed + 1, hod0=hod0)
    sim.run(now)
    if np.count_nonzero(sim.state == LOOSE) < MIN_LOOSE:
        return "no_map"
    sim.condition_not_home()
    d = np.hypot(sim.x[sim.state == LOOSE], sim.y[sim.state == LOOSE])
    radii = np.quantile(d, RING_Q)
    r_out = max(R_OUT_FACTOR * radii[-1], 1.1 * float(np.max(np.hypot(tx, ty))))
    return {"rings": grid_scores(ring_grid(radii, CELL_M), tx, ty, r_out),
            "sim": grid_scores(make_grid(sim), tx, ty, r_out)}


def summarize(rows: list[dict]) -> dict:
    out = {"cases": len(rows), "truths": int(sum(len(r["sim"]["area_ha"]) for r in rows))}
    for model in ("rings", "sim"):
        a = np.concatenate([r[model]["area_ha"] for r in rows])
        out[model] = {
            "area_ha_p50": round(float(np.median(a)), 2), "area_ha_p90": round(float(np.quantile(a, 0.9)), 2),
            "cover50": round(float(np.mean(np.concatenate([r[model]["in_hpd50"] for r in rows]))), 3),
            "cover90": round(float(np.mean(np.concatenate([r[model]["in_hpd90"] for r in rows]))), 3),
        }
    rs = np.concatenate([r["rings"]["area_ha"] for r in rows])
    ss = np.concatenate([r["sim"]["area_ha"] for r in rows])
    out["sim_over_rings_p50"] = round(out["sim"]["area_ha_p50"] / max(out["rings"]["area_ha_p50"], 1e-9), 3)
    out["sim_over_rings_p90"] = round(out["sim"]["area_ha_p90"] / max(out["rings"]["area_ha_p90"], 1e-9), 3)
    out["sim_smaller_share"] = round(float(np.mean(ss < rs)), 3)
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m sim.baseline")
    ap.add_argument("--per-category", type=int, default=40)
    ap.add_argument("--truths", type=int, default=50, help="true animals per case")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    rng = np.random.default_rng(args.seed)
    by_cat: dict[str, list] = {}
    no_map: dict[str, int] = {}
    for name in CATEGORIES:
        rows, attempt, no_map[name] = [], 0, 0
        while len(rows) < args.per_category:
            attempt += 1
            r = run_case(name, rng, args.seed * 100_000 + attempt * 2, args.truths)
            if r == "no_map":
                no_map[name] += 1
            elif r is not None:
                rows.append(r)
        by_cat[name] = rows
    report = {"all": summarize([r for rows in by_cat.values() for r in rows])}
    report.update({name: {**summarize(rows), "skipped_no_map": no_map[name]} for name, rows in by_cat.items()})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
