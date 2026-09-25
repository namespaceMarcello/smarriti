"""Phase B: predictive checks on numbers not used in the calibration.

    python -m sim.validate

B1 cats, mixture: indoor and outdoor cats mixed 164:150 (the found-alive sample sizes of
   Huang 2018) against the overall distances (p25/p50/p75 = 9/50/500 m, 75% within 500 m).
B2 cats, time: the model cannot return home or be picked up faster than Huang's cats were
   found alive (34% by day 7, 50% by day 30, 56% by day 61). Strict bound: P(HOME by t)
   <= found(t). Loose bound: P(HOME or HELD by t) <= found(t) (a held cat may never return).
B3 dogs, time: share of pickups within 5 days (Kremer 2021: over 90% of reunions).
B4 I-CAD: share of HELD among found animals at 30 days >= 4% (dogs), 0.5% (cats).
C1 map calibration: truths drawn from the same model (an independent run) must fall in the
   cells holding 50% / 90% of the map's mass about 50% / 90% of the time.

    python -m sim.validate --coverage
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from .calibrate import CAT_TARGETS, DOG_HORIZON_H, DOG_NAMES, HOD0, HUANG_FOUND, cat_readings
from .categories import BASE, MIXTURES, get
from .engine import HELD, HOME, LOOSE, Simulation
from .outputs import make_grid

HUANG_OVERALL = (9.0, 50.0, 500.0)
HUANG_WITHIN_500 = 0.75
FOUND_ALIVE_N = {"cat_indoor": 164, "cat_outdoor": 150}
KREMER_WITHIN_5D = 0.90
ICAD_SHELTER = {"dog": 0.04, "cat": 0.005}


def b1_cat_mixture(seed: int = 0, n: int = 20_000) -> dict:
    names = list(CAT_TARGETS)
    readings = cat_readings([get(nm) for nm in names], n, seed)
    rng = np.random.default_rng(seed + 3)
    total = sum(FOUND_ALIVE_N.values())
    parts = []
    for nm, (d, _) in zip(names, readings):
        d = d[~np.isnan(d)]
        parts.append(rng.choice(d, int(n * FOUND_ALIVE_N[nm] / total), replace=False))
    d = np.concatenate(parts)
    q = np.percentile(d, [25, 50, 75])
    return {"target_p25_p50_p75": HUANG_OVERALL, "got": [round(v, 1) for v in q],
            "rel_err": [round(abs(g - t) / t, 3) for g, t in zip(q, HUANG_OVERALL)],
            "within_500m": round(float(np.mean(d <= 500)), 3), "target_within_500m": HUANG_WITHIN_500}


def b2_cat_time(seed: int = 0, n: int = 20_000) -> dict:
    out = {}
    days = [d for d, _ in HUANG_FOUND[1:]]
    for mix_name, mix in [("cat_indoor", [(get("cat_indoor"), 1.0)]), ("cat_outdoor", [(get("cat_outdoor"), 1.0)]),
                          ("cat (28:46)", [(get(k), w) for k, w in MIXTURES["cat"].items()])]:
        sim = Simulation(mix, n, seed, hod0=HOD0)
        rows = []
        for day, found in HUANG_FOUND[1:]:
            sim.run(day * 24)
            home = float(np.mean(sim.state == HOME))
            held = float(np.mean(sim.state == HELD))
            rows.append({"day": day, "found_huang": found, "home": round(home, 3), "home_or_held": round(home + held, 3),
                         "strict_ok": home <= found, "loose_ok": home + held <= found})
        out[mix_name] = rows
    out["days"] = days
    return out


def b3_dog_time(seed: int = 0, n: int = 20_000) -> dict:
    sim = Simulation([(get(k), w) for k, w in MIXTURES["dog"].items()], n, seed, hod0=HOD0)
    sim.run(DOG_HORIZON_H)
    held = sim.state == HELD
    t = sim.t_end[held]
    by_cat = {nm: round(float(np.mean(t[sim.par.cat_idx[held] == i] <= 120)), 3) for i, nm in enumerate(DOG_NAMES)}
    home = sim.state == HOME
    return {"pickups_within_5d": round(float(np.mean(t <= 120)), 3), "target": KREMER_WITHIN_5D, "by_category": by_cat,
            "p_held_60d": round(float(held.mean()), 3), "p_home_60d": round(float(home.mean()), 3)}


def b4_icad(seed: int = 0, n: int = 20_000) -> dict:
    out = {}
    for species in ("dog", "cat"):
        sim = Simulation([(get(k), w) for k, w in MIXTURES[species].items()], n, seed, hod0=HOD0)
        sim.run(30 * 24)
        held, home = float(np.mean(sim.state == HELD)), float(np.mean(sim.state == HOME))
        share = held / max(held + home, 1e-9)
        out[species] = {"held_share_of_found": round(share, 3), "icad_shelter_share": ICAD_SHELTER[species],
                        "ok": share >= ICAD_SHELTER[species]}
    return out


def map_coverage(name: str, hours: int, n_map: int = 10_000, n_truth: int = 4_000, seed: int = 0) -> dict:
    """Share of truths (from an independent run of the same model) inside the map's HPD50/90."""
    mix = [(get(k), w) for k, w in MIXTURES[name].items()] if name in MIXTURES else [(get(name), 1.0)]
    sim = Simulation(mix, n_map, seed, hod0=HOD0)
    sim.run(hours)
    sim.condition_not_home()
    grid = make_grid(sim)
    truth = Simulation(mix, n_truth, seed + 1000, hod0=HOD0)
    truth.run(hours)
    loose = truth.state == LOOSE
    tx, ty = truth.x[loose], truth.y[loose]
    ny, nx = grid.mass.shape
    ix = np.floor((tx - grid.x0) / grid.cell).astype(int)
    iy = np.floor((ty - grid.y0) / grid.cell).astype(int)
    inside = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    m_truth = np.zeros(len(tx))
    m_truth[inside] = grid.mass[iy[inside], ix[inside]]
    flat = np.sort(grid.mass.ravel())[::-1]
    cum = np.cumsum(flat) / flat.sum()
    out = {"truths": int(loose.sum())}
    if not loose.any():
        return {**out, "cover50": None, "cover90": None}
    for q in (0.5, 0.9):
        thr = flat[int(np.searchsorted(cum, q))]
        out[f"cover{int(q * 100)}"] = round(float(np.mean((m_truth > 0) & (m_truth >= thr))), 3)
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m sim.validate")
    ap.add_argument("--coverage", action="store_true", help="only C1, the map calibration")
    args = ap.parse_args(argv)
    if args.coverage:
        print(json.dumps({f"{n} {h}h": map_coverage(n, h) for n in BASE for h in (48, 168)}, indent=2))
        return
    print(json.dumps({"B1": b1_cat_mixture(), "B2": b2_cat_time(), "B3": b3_dog_time(), "B4": b4_icad()}, indent=2))


if __name__ == "__main__":
    main()
