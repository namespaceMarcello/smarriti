"""Phase A: calibrate the categories against the published distances.

    python -m sim.calibrate start        # measure the starting parameters, change nothing
    python -m sim.calibrate cat_indoor   # or cat_outdoor, dogs, all; writes calibrated.json

Cats (Huang 2018, cats found alive): p25/p50/p75 of the distance from the point of escape.
Competing risks (lessons.md #8): each cat leaves the loose state at the first of its events
and is read at that hour: HOME -> 0, HELD -> where it was picked up, DEAD -> excluded, and,
in the calibration only, FOUND by the searcher -> its position. The search hazard is the
same at every distance and constant between days 0-7-30-61; it is solved so that the
found-alive curve matches Huang, while h_home and h_pickup are scaled to Huang's shares.
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
from scipy.optimize import brentq

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


CAT_HORIZON_H = HUANG_FOUND[-1][0] * 24
SEARCH_KNOTS_H = np.array([d for d, _ in HUANG_FOUND], float) * 24  # search hazard constant in between
SEARCH_KEY = "_search"  # in calibrated.json: the search hazards that go with each cat's h_home, h_pickup
SEARCH_BY = ("h_home", "h_pickup", "h_dead", "home_from_h", "home_until_h", "home_late_mult")


def rel_err(got, target) -> float:
    got, target = np.asarray(got, float), np.asarray(target, float)
    return float(np.max(np.abs(got - target) / target))


# --- cats ----------------------------------------------------------------------------------


def search_cum(rates, t) -> np.ndarray:
    """Cumulative search hazard at hour t; rates per hour, constant between the knots."""
    t = np.asarray(t, float)
    return sum(r * np.clip(t - lo, 0.0, hi - lo) for r, lo, hi in zip(rates, SEARCH_KNOTS_H[:-1], SEARCH_KNOTS_H[1:]))


def search_hours(rates, n: int, rng: np.random.Generator) -> np.ndarray:
    """Hour at which the searcher finds each cat if it is still loose (horizon + 1: never)."""
    e = rng.exponential(1.0, n)
    cum = search_cum(np.maximum(rates, 1e-12), SEARCH_KNOTS_H)  # strictly increasing: invertible
    t = np.maximum(1, np.ceil(np.interp(e, cum, SEARCH_KNOTS_H)))
    return np.where(e > cum[-1], CAT_HORIZON_H + 1, t).astype(np.int64)


def cat_events(cat: Category, n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Final state and event hour (-1: none) of each cat after 61 days, without any search."""
    sim = Simulation([(cat, 1.0)], n, seed, hod0=HOD0)
    sim.run(CAT_HORIZON_H)
    return sim.state, sim.t_end


def found_by(state: np.ndarray, t_end: np.ndarray, rates, day: float) -> dict[str, float]:
    """Share of all cats found at home, held and outside by `day`. Exact given one engine run,
    because the search does not depend on the place: an engine event at hour e comes first
    with probability exp(-L(e - 1)); the searcher finds a cat at hour k <= e - 1."""
    ev = np.where(t_end > 0, t_end, np.inf)
    t = day * 24
    first = np.exp(-search_cum(rates, np.minimum(ev - 1, CAT_HORIZON_H)))
    return {"home": float(np.mean(np.where((state == HOME) & (ev <= t), first, 0.0))),
            "held": float(np.mean(np.where((state == HELD) & (ev <= t), first, 0.0))),
            "outside": float(np.mean(1 - np.exp(-search_cum(rates, np.minimum(t, ev - 1)))))}


def solve_search(state: np.ndarray, t_end: np.ndarray) -> list[float]:
    """The three search hazards that put the found-alive curve on Huang's, knot by knot."""
    rates = [0.0, 0.0, 0.0]
    for k, (day, target) in enumerate(HUANG_FOUND[1:]):
        def gap(r, k=k, day=day, target=target):
            return sum(found_by(state, t_end, rates[:k] + [r] + [0.0] * (2 - k), day).values()) - target
        if gap(0.0) >= 0:  # the engine alone finds enough: no search in this stretch
            continue
        if gap(1.0) < 0:
            raise ValueError(f"no search hazard reaches {target} found by day {day}: too many cats die")
        rates[k] = brentq(gap, 0.0, 1.0, xtol=1e-12)
    return rates


def shares(state: np.ndarray, t_end: np.ndarray, rates) -> dict[str, float]:
    f = found_by(state, t_end, rates, HUANG_FOUND[-1][0])
    total = sum(f.values())
    return {"found": total, "home": f["home"] / total, "held": f["held"] / total}


_SEARCH_CACHE: dict[tuple, list[float]] = {}


def search_key(cat: Category) -> tuple:
    return (cat.name, *(float(getattr(cat, k)) for k in SEARCH_BY))


def search_rates(cat: Category, seed: int = 0) -> list[float]:
    """The search hazards that go with this cat's hazards: saved by the calibration, or solved
    now from one engine run (cached: a grid that only moves the cat solves once)."""
    key = search_key(cat)
    if key not in _SEARCH_CACHE:
        saved = load_calibrated().get(SEARCH_KEY, {}).get(cat.name, {})
        if saved and all(np.isclose(saved.get(k, np.nan), getattr(cat, k)) for k in ("h_home", "h_pickup", "h_dead")):
            _SEARCH_CACHE[key] = saved["rates_per_h"]
        else:
            _SEARCH_CACHE[key] = solve_search(*cat_events(cat, 20_000, seed))
    return _SEARCH_CACHE[key]


def cat_readings(cats: list[Category], n_per: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """For each category: (distance where it was found alive, state then). A cat is read at the
    first of its events; nan when it died or was not found by day 61."""
    rng = np.random.default_rng(seed + 1)
    n = n_per * len(cats)
    sim = Simulation([(c, 1.0) for c in cats], n, seed, hod0=HOD0)
    idx = sim.par.cat_idx
    t_find = np.empty(n, np.int64)
    for i, c in enumerate(cats):
        t_find[idx == i] = search_hours(search_rates(c), int(np.sum(idx == i)), rng)
    rec = sim.run(CAT_HORIZON_H, record_at=np.minimum(t_find, CAT_HORIZON_H))
    d = np.hypot(rec["x"], rec["y"])
    d = np.where(rec["state"] == HOME, 0.0, d)
    lost = (rec["state"] == DEAD) | ((rec["state"] == LOOSE) & (t_find > CAT_HORIZON_H))
    d = np.where(lost, np.nan, d)
    return [(d[idx == i], rec["state"][idx == i]) for i in range(len(cats))]


def cat_shares(d: np.ndarray, state: np.ndarray) -> tuple[float, float]:
    """Shares found at home and held among the cats found alive, from the readings."""
    found = ~np.isnan(d)
    return float(np.mean(state[found] == HOME)), float(np.mean(state[found] == HELD))


def cat_quantiles(d: np.ndarray) -> np.ndarray:
    return np.nanpercentile(d, [25, 50, 75])


def solve_cat_hazards(cat: Category, seed: int = 0, n: int = 20_000) -> tuple[Category, list[float], dict]:
    """Scale h_home and h_pickup, solving the search again each time, until the shares found at
    home and held by day 61 match Huang. The hazards do not depend on how the cat moves in
    the reference zone, so this runs before the grid on the movement."""
    for _ in range(12):
        state, t_end = cat_events(cat, n, seed)
        rates = solve_search(state, t_end)
        s = shares(state, t_end, rates)
        on_curve = all(abs(sum(found_by(state, t_end, rates, day).values()) - f) < 1e-3 for day, f in HUANG_FOUND[1:])
        if on_curve and abs(s["home"] / CAT_SHARE_HOME - 1) < 0.01 and abs(s["held"] / CAT_SHARE_HELD - 1) < 0.01:
            break
        cat = replace(cat, h_home=cat.h_home * CAT_SHARE_HOME / max(s["home"], 1e-4),
                      h_pickup=cat.h_pickup * CAT_SHARE_HELD / max(s["held"], 1e-4))
    else:
        raise ValueError(f"{cat.name}: shares did not converge ({s})")
    return cat, rates, s


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
    cat, rates, solved = solve_cat_hazards(get(name, calibrated=False), seed)
    _SEARCH_CACHE[search_key(cat)] = rates
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
    home, held = cat_shares(d, state)
    return {
        "category": final,
        "search": rates,
        "report": {
            "target_p25_p50_p75": CAT_TARGETS[name], "got": [round(v, 1) for v in q], "max_rel_err": round(rel_err(q, CAT_TARGETS[name]), 3),
            "share_home": round(home, 3), "share_held": round(held, 3), "found_alive_by_61d": round(float(np.mean(~np.isnan(d))), 3),
            "search_rates_per_h": [float(f"{r:.4g}") for r in rates], "solved_found_home_held": [round(v, 3) for v in solved.values()],
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
        home, held = cat_shares(d, state)
        out[name] = {"got_p25_p50_p75": [round(v, 1) for v in cat_quantiles(d)], "target": CAT_TARGETS[name],
                     "share_home": round(home, 3), "share_held": round(held, 3)}
    m = dog_metrics(dog_run([[get(n, calibrated=False) for n in DOG_NAMES]], 20_000, seed), 0)
    out["dogs"] = {"got_q42_q70": [round(v, 1) for v in m["q"]], "target": [t for _, t in DOG_TARGETS],
                   "home_share": round(m["home_share"], 3)}
    return out


def save(cats: list[Category], search: list[float] | None = None) -> None:
    data = load_calibrated()
    for c in cats:
        data[c.name] = {k: round(float(getattr(c, k)), 6) for k in
                        ("anchor_med_m", "anchor_sigma", "step_flight", "step_settled", "h_home", "h_pickup")
                        if getattr(c, k) != getattr(BASE[c.name], k)}
    if search is not None:
        (c,) = cats
        data.setdefault(SEARCH_KEY, {})[c.name] = {**{k: data[c.name].get(k, float(getattr(c, k))) for k in ("h_home", "h_pickup")},
                                                   "h_dead": float(c.h_dead), "rates_per_h": [float(f"{r:.6g}") for r in search]}
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
            save([r["category"]], r["search"])
        print(what, json.dumps(r["report"], indent=2))


if __name__ == "__main__":
    main()
