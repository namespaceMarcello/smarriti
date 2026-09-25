"""Pressure: long horizons, extreme inputs, many particles, random cases.

Every run must end with finite, non-negative weights summing to 1 and within its time budget
(budgets are about 3x the times measured on the development laptop).
"""
import json
import time

import numpy as np
import pytest

from sim.categories import BASE, MIXTURES, get, mixture
from sim.engine import HOME, LOOSE, Simulation, run_case
from sim.environment import ZONES
from sim.case import parse_case
from sim.outputs import make_grid, summarize, write_geojson

HOME_LL = {"lat": 40.85, "lon": 14.27}


def healthy(sim):
    assert np.all(np.isfinite(sim.w)) and np.all(sim.w >= 0)
    assert abs(sim.w.sum() - 1) < 1e-9
    assert abs(sum(sim.state_probs().values()) - 1) < 1e-9


def test_ninety_days_ten_thousand_particles_is_fast():
    case = parse_case({"category": "dog", "home": HOME_LL, "lost_at": "2026-06-01T08:00"})
    t = time.perf_counter()
    sim = run_case(case, 90 * 24, n=10_000)
    assert time.perf_counter() - t < 8
    healthy(sim)


def test_now_equals_the_moment_of_loss():
    case = parse_case({"category": "cat", "home": HOME_LL, "lost_at": "2026-09-20T19:00"})
    sim = run_case(case, 0, n=1000)
    healthy(sim)
    assert np.all(sim.state == LOOSE) and np.all(sim.x == 0)
    summarize(sim, case, case.lost_at, make_grid(sim))


def test_scaling_to_a_hundred_thousand_particles():
    sim = Simulation([(get("cat_outdoor"), 1.0)], 100_000, seed=7)
    t = time.perf_counter()
    sim.run(24)
    assert time.perf_counter() - t < 6
    healthy(sim)


def test_one_particle():
    sim = Simulation([(get("dog_friendly"), 1.0)], 1, seed=5)
    sim.run(30)
    assert abs(sim.w.sum() - 1) < 1e-12


def random_case(rng):
    def ll(scale):
        return {"lat": 40.85 + float(rng.normal(0, scale)), "lon": 14.27 + float(rng.normal(0, scale))}

    data = {
        "category": str(rng.choice(list(BASE) + list(MIXTURES))), "home": HOME_LL, "lost_at": "2026-09-20T19:00",
        "collar": bool(rng.random() < 0.5),
        "area": {"zone": str(rng.choice(list(ZONES))), "floor": int(rng.integers(0, 10)),
                 "patches": [{"zone": str(rng.choice(list(ZONES))), "center": ll(0.01), "radius_m": float(rng.uniform(10, 800))}
                             for _ in range(int(rng.integers(0, 4)))]},
    }
    return data, int(rng.integers(0, 300))


def test_forty_random_cases_keep_every_invariant(tmp_path):
    rng = np.random.default_rng(2026)
    t = time.perf_counter()
    for i in range(40):
        data, now_h = random_case(rng)
        case = parse_case(data)
        sim = run_case(case, now_h, n=400, seed=i)
        healthy(sim)
        assert sim.w[sim.state == HOME].sum() == 0
        grid = make_grid(sim)
        assert grid.mass.sum() <= sim.state_probs()["loose"] + 1e-9
        now = case.lost_at + np.timedelta64(now_h, "h").astype(object)
        summary = summarize(sim, case, now, grid)
        json.dumps(summary)
        write_geojson(grid, case, summary, tmp_path / f"{i}.geojson")
    assert time.perf_counter() - t < 20


@pytest.mark.parametrize("name", list(BASE) + list(MIXTURES))
def test_every_category_runs_a_week(name):
    sim = Simulation(mixture(name), 2000, seed=8)
    sim.run(168)
    healthy(sim)


def test_baseline_survives_a_model_with_no_loose_animal():
    """lessons.md #19: at 10 days the calibrated friendly dog may have no loose particle."""
    from sim.baseline import run_case as score

    rng = np.random.default_rng(0)
    for k in range(5):
        r = score("dog_friendly", rng, 100 + k, 10, now=239)
        assert r in (None, "no_map") or set(r) == {"rings", "sim"}
