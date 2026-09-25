"""The five animal categories and their parameters.

Starting values are the estimates in docs/simulatore.md. Phase A (calibrate.py) writes
the calibrated values to calibrated.json, which overrides them when present.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, fields, replace
from pathlib import Path

CALIBRATED_PATH = Path(__file__).with_name("calibrated.json")

# Local clock hours counted as night: 20:00-05:59.
NIGHT_HOURS = frozenset([20, 21, 22, 23, 0, 1, 2, 3, 4, 5])


def is_night(hour_of_day: int) -> bool:
    return hour_of_day % 24 in NIGHT_HOURS


@dataclass(frozen=True)
class Category:
    name: str
    species: str  # "cat" or "dog"
    # movement: probability of moving in a given hour
    p_move_day: float
    p_move_night: float
    # step length: lognormal with this median (m) and dispersion
    step_sigma: float
    step_flight: float  # before settling
    step_settled: float  # after settling
    # turning: von Mises concentration around the previous heading
    kappa_flight: float
    kappa_settled: float
    # fraction of the distance to the anchor recovered at each move (discrete OU)
    pull_flight: float
    pull_settled: float
    # mean of the exponential settling time (h); 0 = settled from the start
    t_settle_mean_h: float
    # initial anchor: "random" (lognormal distance from home), "home", or "none"
    anchor: str
    anchor_med_m: float
    anchor_sigma: float
    # hourly hazards
    h_pickup: float
    h_home: float
    home_from_h: float  # h_home is zero before this hour
    home_until_h: float  # after this hour h_home is multiplied by home_late_mult
    home_late_mult: float
    h_dead: float
    hunger: bool  # pickup hazard grows after day 3 (wary animals approach people when hungry)


BASE = {
    "cat_indoor": Category(
        name="cat_indoor", species="cat",
        p_move_day=0.05, p_move_night=0.30,
        step_sigma=1.0, step_flight=15, step_settled=15,
        kappa_flight=0.5, kappa_settled=0.5,
        pull_flight=0.5, pull_settled=0.5,
        t_settle_mean_h=0, anchor="random", anchor_med_m=40, anchor_sigma=0.5,
        h_pickup=0.002, h_home=0.004, home_from_h=24, home_until_h=float("inf"),
        home_late_mult=1.0, h_dead=0.0002, hunger=False,
    ),
    "cat_outdoor": Category(
        name="cat_outdoor", species="cat",
        p_move_day=0.15, p_move_night=0.40,
        step_sigma=1.2, step_flight=40, step_settled=40,
        kappa_flight=0.5, kappa_settled=0.5,
        pull_flight=0.2, pull_settled=0.2,
        t_settle_mean_h=0, anchor="random", anchor_med_m=200, anchor_sigma=0.5,
        h_pickup=0.003, h_home=0.010, home_from_h=0, home_until_h=float("inf"),
        home_late_mult=1.0, h_dead=0.0003, hunger=False,
    ),
    "dog_friendly": Category(
        name="dog_friendly", species="dog",
        p_move_day=0.60, p_move_night=0.20,
        step_sigma=0.8, step_flight=150, step_settled=150,
        kappa_flight=1.0, kappa_settled=1.0,
        pull_flight=0.1, pull_settled=0.1,
        t_settle_mean_h=0, anchor="home", anchor_med_m=0, anchor_sigma=0,
        h_pickup=0.08, h_home=0.020, home_from_h=0, home_until_h=12,
        home_late_mult=0.1, h_dead=0.0003, hunger=False,
    ),
    "dog_wary": Category(
        name="dog_wary", species="dog",
        p_move_day=0.50, p_move_night=0.30,
        step_sigma=1.0, step_flight=250, step_settled=250,
        kappa_flight=2.0, kappa_settled=2.0,
        pull_flight=0.0, pull_settled=0.3,
        t_settle_mean_h=12, anchor="none", anchor_med_m=0, anchor_sigma=0,
        h_pickup=0.01, h_home=0.010, home_from_h=0, home_until_h=float("inf"),
        home_late_mult=1.0, h_dead=0.0005, hunger=True,
    ),
    "dog_fearful": Category(
        name="dog_fearful", species="dog",
        p_move_day=0.40, p_move_night=0.50,
        step_sigma=1.0, step_flight=500, step_settled=100,
        kappa_flight=4.0, kappa_settled=0.5,
        pull_flight=0.0, pull_settled=0.4,
        t_settle_mean_h=6, anchor="none", anchor_med_m=0, anchor_sigma=0,
        h_pickup=0.003, h_home=0.002, home_from_h=0, home_until_h=float("inf"),
        home_late_mult=1.0, h_dead=0.0010, hunger=False,
    ),
}

# Mixtures used when the owner does not know the temperament / outdoor habits.
# Cats: indoor-only vs indoor-outdoor in Huang 2018 (28% vs 46% of 1,210 cats).
# Dogs: 50/30/20 is an unsourced guess (docs/simulatore.md, "buchi dichiarati").
MIXTURES = {
    "cat": {"cat_indoor": 28 / 74, "cat_outdoor": 46 / 74},
    "dog": {"dog_friendly": 0.5, "dog_wary": 0.3, "dog_fearful": 0.2},
}

NUMERIC_FIELDS = [f.name for f in fields(Category) if f.name not in ("name", "species", "anchor", "hunger")]


def load_calibrated() -> dict[str, dict[str, float]]:
    if CALIBRATED_PATH.exists():
        return json.loads(CALIBRATED_PATH.read_text(encoding="utf-8"))
    return {}


def get(name: str, calibrated: bool = True) -> Category:
    """A category with its calibrated overrides applied (if any)."""
    cat = BASE[name]
    if calibrated:
        overrides = load_calibrated().get(name, {})
        cat = replace(cat, **{k: v for k, v in overrides.items() if k in NUMERIC_FIELDS})
    return cat


def mixture(name: str, calibrated: bool = True) -> list[tuple[Category, float]]:
    """A single category or a named mixture, as (category, prior weight) pairs."""
    if name in MIXTURES:
        return [(get(n, calibrated), w) for n, w in MIXTURES[name].items()]
    if name not in BASE:
        raise ValueError(f"unknown category {name!r}; known: {sorted(BASE) + sorted(MIXTURES)}")
    return [(get(name, calibrated), 1.0)]
