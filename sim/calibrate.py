"""Phase A: calibrate the categories against the published distances.

    python -m sim.calibrate start        # measure the starting parameters, change nothing
    python -m sim.calibrate cat_indoor   # or cat_outdoor, dogs, all; writes calibrated.json

Cats (Huang 2018, cats found alive): p25/p50/p75 of the distance from the point of escape.
Each particle gets a find hour drawn from Huang's recovery curve and is read at that hour:
LOOSE or HELD -> its distance (HELD: where it was picked up), HOME -> 0, DEAD -> excluded.
Dogs (Kremer 2021, strays returned to owner): distance of the pickup point, all three dog
categories pooled with the 50/30/20 prior: 42% within 120 m, 70% within 1,609 m.
Search: a coarse grid, then a finer grid around the best; a parameter set is accepted
(ABC) when every quantile is within +-20% of its target.
"""
from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import replace

import numpy as np

from .categories import BASE, CALIBRATED_PATH, MIXTURES, Category, get, load_calibrated
from .engine import DEAD, HELD, HOME, LOOSE, Simulation

# Huang 2018: cumulative share of missing cats found alive by day 7, 30, 61.
HUANG_FOUND = ((0, 0.0), (7, 0.34), (30, 0.50), (61, 0.56))
CAT_TARGETS = {"cat_indoor": (9.0, 39.0, 137.0), "cat_outdoor": (14.0, 300.0, 1609.0)}
# Huang 2018, where the 602 cats found alive were: 4% inside my house, 83% outside of which
# 19% "waiting outside home" (taken as 19% of the 83%), 11% inside someone else's house.
CAT_SHARE_HOME = 0.04 + 0.19 * 0.83
CAT_SHARE_HELD = 0.11
# Kremer 2021: quantiles of the pickup distance of stray dogs.
DOG_TARGETS = ((0.42, 120.0), (0.70, 1609.0))
# Lord 2007 (dogs): 8% came home on their own, 71% were recovered.
DOG_HOME_SHARE = 0.08 / 0.71
DOG_HORIZON_H = 60 * 24
TOL = 0.20
HOD0 = 18  # losses start in the evening (unsourced)
DOG_NAMES = list(MIXTURES["dog"])


def found_hours(n: int, rng: np.random.Generator) -> np.ndarray:
    """Find hours drawn from Huang's curve, conditioned on being found alive by day 61."""
    days, cum = zip(*HUANG_FOUND)
    u = rng.uniform(0, cum[-1], n)
    return np.maximum(1, np.ceil(np.interp(u, cum, days) * 24)).astype(np.int64)


def rel_err(got, target) -> float:
    got, target = np.asarray(got, float), np.asarray(target, float)
    return float(np.max(np.abs(got - target) / target))


# --- cats ----------------------------------------------------------------------------------


def cat_readings(cats: list[Category], n_per: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """For each category: (distance at the find hour, state at the find hour); DEAD -> nan."""
    rng = np.random.default_rng(seed + 1)
    n = n_per * len(cats)
    sim = Simulation([(c, 1.0) for c in cats], n, seed, hod0=HOD0)
    t_find = found_hours(n, rng)
    rec = sim.run(int(t_find.max()), record_at=t_find)
    d = np.hypot(rec["x"], rec["y"])
    d = np.where(rec["state"] == HOME, 0.0, d)
    d = np.where(rec["state"] == DEAD, np.nan, d)
    idx = sim.par.cat_idx
    return [(d[idx == i], rec["state"][idx == i]) for i in range(len(cats))]


def cat_shares(state: np.ndarray) -> tuple[float, float]:
    alive = state != DEAD
    return float(np.mean(state[alive] == HOME)), float(np.mean(state[alive] == HELD))


def cat_quantiles(d: np.ndarray) -> np.ndarray:
    return np.nanpercentile(d, [25, 50, 75])


def solve_cat_hazards(cat: Category, seed: int = 0, n: int = 20_000) -> Category:
    """Scale h_home and h_pickup until the found-at-home and found-held shares match Huang."""
    for _ in range(8):
        _, state = cat_readings([cat], n, seed)[0]
        home, held = cat_shares(state)
        if abs(home / CAT_SHARE_HOME - 1) < 0.02 and abs(held / CAT_SHARE_HELD - 1) < 0.02:
            break
        cat = replace(cat, h_home=cat.h_home * CAT_SHARE_HOME / max(home, 1e-4),
                      h_pickup=cat.h_pickup * CAT_SHARE_HELD / max(held, 1e-4))
    return cat


CAT_GRID = {
    "cat_indoor": {"anchor_med_m": [10, 20, 30, 45, 65, 90], "anchor_sigma": [0.5, 1.0, 1.5, 2.0], "step": [5, 10, 15, 25]},
    "cat_outdoor": {"anchor_med_m": [300, 450, 600, 800, 1100], "anchor_sigma": [1.8, 2.1, 2.4, 2.7, 3.0], "step": [3, 5, 10, 20]},
}


def with_move(cat: Category, med: float, sigma: float, step: float) -> Category:
    return replace(cat, anchor_med_m=float(med), anchor_sigma=float(sigma), step_flight=float(step), step_settled=float(step))


def search_cat(cat: Category, grid: dict, n_per: int, seed: int) -> list[dict]:
    points = list(itertools.product(grid["anchor_med_m"], grid["anchor_sigma"], grid["step"]))
    cats = [with_move(cat, *p) for p in points]
    out = []
    for p, (d, _) in zip(points, cat_readings(cats, n_per, seed)):
        q = cat_quantiles(d)
        out.append({"anchor_med_m": p[0], "anchor_sigma": p[1], "step": p[2], "q": q.tolist(),
                    "err": rel_err(q, CAT_TARGETS[cat.name])})
    return sorted(out, key=lambda r: r["err"])


def calibrate_cat(name: str, seed: int = 0) -> dict:
    cat = solve_cat_hazards(get(name, calibrated=False), seed)
    coarse = search_cat(cat, CAT_GRID[name], 800, seed)
    b = coarse[0]
    fine_grid = {
        "anchor_med_m": [b["anchor_med_m"] * f for f in (0.8, 0.9, 1.0, 1.1, 1.2)],
        "anchor_sigma": [max(0.1, b["anchor_sigma"] + s) for s in (-0.2, -0.1, 0.0, 0.1, 0.2)],
        "step": [b["step"] * f for f in (0.6, 1.0, 1.6)],
    }
    fine = search_cat(cat, fine_grid, 2500, seed + 7)
    # the winner of a small sample is optimistic: validate the top five on a large one
    top = [with_move(cat, r["anchor_med_m"], r["anchor_sigma"], r["step"]) for r in fine[:5]]
    checked = [(rel_err(cat_quantiles(d), CAT_TARGETS[name]), c, d, st)
               for c, (d, st) in zip(top, cat_readings(top, 20_000, seed + 13))]
    _, final, d, state = min(checked, key=lambda r: r[0])
    q = cat_quantiles(d)
    home, held = cat_shares(state)
    return {
        "category": final,
        "report": {
            "target_p25_p50_p75": CAT_TARGETS[name], "got": [round(v, 1) for v in q], "max_rel_err": round(rel_err(q, CAT_TARGETS[name]), 3),
            "share_home": round(home, 3), "share_held": round(held, 3),
            "accepted_coarse": sum(r["err"] <= TOL for r in coarse), "coarse_points": len(coarse),
            "accepted_fine": sum(r["err"] <= TOL for r in fine), "fine_points": len(fine),
            "params": {k: round(getattr(final, k), 5) for k in ("anchor_med_m", "anchor_sigma", "step_settled", "h_home", "h_pickup")},
        },
    }


# --- dogs ------------------------------------------------------------------------------------


def dog_set(near: float, far: float, pickup_scale: float, home_scale: float, base: dict[str, Category]) -> list[Category]:
    """Friendly dogs scale their steps by `near`, wary and fearful dogs by `far`."""
    out = []
    for n in DOG_NAMES:
        k = near if n == "dog_friendly" else far
        out.append(replace(base[n], step_flight=base[n].step_flight * k, step_settled=base[n].step_settled * k,
                           h_pickup=base[n].h_pickup * pickup_scale, h_home=base[n].h_home * home_scale))
    return out


def dog_run(sets: list[list[Category]], n_per_set: int, seed: int) -> Simulation:
    """One simulation holding every parameter set (3 categories each, 50/30/20)."""
    prior = MIXTURES["dog"]
    mix = [(c, prior[c.name]) for s in sets for c in s]
    sim = Simulation(mix, n_per_set * len(sets), seed, hod0=HOD0)
    sim.run(DOG_HORIZON_H)
    return sim


def dog_metrics(sim: Simulation, set_index: int) -> dict:
    sel = (sim.par.cat_idx // 3) == set_index
    st = sim.state[sel]
    held = st == HELD
    d = np.hypot(sim.x[sel][held], sim.y[sel][held])
    q = np.quantile(d, [p for p, _ in DOG_TARGETS]) if held.any() else np.array([np.nan, np.nan])
    n_home, n_held = np.sum(st == HOME), np.sum(held)
    return {"q": q, "home_share": float(n_home / max(n_home + n_held, 1)), "t_end": sim.t_end[sel][held]}


def solve_dog_home(base: dict[str, Category], seed: int) -> float:
    home_scale = 1.0
    for _ in range(8):
        m = dog_metrics(dog_run([dog_set(1.0, 1.0, 1.0, home_scale, base)], 12_000, seed), 0)
        if abs(m["home_share"] / DOG_HOME_SHARE - 1) < 0.02:
            break
        home_scale *= DOG_HOME_SHARE / max(m["home_share"], 1e-4)
    return home_scale


def calibrate_dogs(seed: int = 0) -> dict:
    """Two step scales (friendly; wary + fearful); pickup hazards stay at their starting values,
    h_home is scaled so that the share of dogs coming home on their own matches Lord 2007."""
    base = {n: get(n, calibrated=False) for n in DOG_NAMES}
    targets = np.array([t for _, t in DOG_TARGETS])
    home = solve_dog_home(base, seed)

    def search(nears, fars, n_per, s):
        points = list(itertools.product(nears, fars))
        sim = dog_run([dog_set(a, b, 1.0, home, base) for a, b in points], n_per, s)
        out = []
        for i, (a, b) in enumerate(points):
            m = dog_metrics(sim, i)
            out.append({"near": a, "far": b, "q": m["q"].tolist(), "err": rel_err(m["q"], targets)})
        return sorted(out, key=lambda r: r["err"])

    coarse = search([0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0], [0.5, 0.7, 1.0, 1.4, 2.0, 2.8, 4.0], 1500, seed)
    b = coarse[0]
    fine = search([b["near"] * f for f in (0.7, 0.85, 1.0, 1.2, 1.4)],
                  [b["far"] * f for f in (0.7, 0.85, 1.0, 1.2, 1.4)], 2500, seed + 7)
    best = fine[0]
    final = dog_set(best["near"], best["far"], 1.0, home, base)
    m = dog_metrics(dog_run([final], 20_000, seed + 13), 0)
    return {
        "categories": final,
        "report": {
            "target_q42_q70_m": targets.tolist(), "got": [round(v, 1) for v in m["q"]], "max_rel_err": round(rel_err(m["q"], targets), 3),
            "home_share": round(m["home_share"], 3),
            "accepted_coarse": sum(r["err"] <= TOL for r in coarse), "coarse_points": len(coarse),
            "accepted_fine": sum(r["err"] <= TOL for r in fine), "fine_points": len(fine),
            "scales": {"near": round(best["near"], 4), "far": round(best["far"], 4), "home": round(home, 4)},
        },
    }


# --- starting parameters ------------------------------------------------------------------------


def measure_start(seed: int = 0) -> dict:
    out = {}
    for name in CAT_TARGETS:
        d, state = cat_readings([get(name, calibrated=False)], 20_000, seed)[0]
        home, held = cat_shares(state)
        out[name] = {"got_p25_p50_p75": [round(v, 1) for v in cat_quantiles(d)], "target": CAT_TARGETS[name],
                     "share_home": round(home, 3), "share_held": round(held, 3)}
    m = dog_metrics(dog_run([[get(n, calibrated=False) for n in DOG_NAMES]], 20_000, seed), 0)
    out["dogs"] = {"got_q42_q70": [round(v, 1) for v in m["q"]], "target": [t for _, t in DOG_TARGETS],
                   "home_share": round(m["home_share"], 3)}
    return out


def save(cats: list[Category]) -> None:
    data = load_calibrated()
    for c in cats:
        data[c.name] = {k: round(float(getattr(c, k)), 6) for k in
                        ("anchor_med_m", "anchor_sigma", "step_flight", "step_settled", "h_home", "h_pickup")
                        if getattr(c, k) != getattr(BASE[c.name], k)}
    CALIBRATED_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m sim.calibrate")
    ap.add_argument("what", choices=["start", "cat_indoor", "cat_outdoor", "dogs", "all"])
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    if args.what == "start":
        print(json.dumps(measure_start(args.seed), indent=2))
        return
    todo = ["cat_indoor", "cat_outdoor", "dogs"] if args.what == "all" else [args.what]
    for what in todo:
        if what == "dogs":
            r = calibrate_dogs(args.seed)
            save(r["categories"])
        else:
            r = calibrate_cat(what, args.seed)
            save([r["category"]])
        print(what, json.dumps(r["report"], indent=2))


if __name__ == "__main__":
    main()
