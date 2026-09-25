"""Integrity: every piece does exactly what docs/simulatore.md says.

Exact checks where the result is deterministic; statistical checks against closed-form
theory with a tolerance of at least 4 standard errors (stated in each test).
"""
from dataclasses import replace
from datetime import datetime

import numpy as np
import pytest

from sim.categories import get, is_night, mixture
from sim.engine import DEAD, HOME, LOOSE, NIGHT_ACTIVITY, Simulation, allocate
from sim.environment import ZONES, Environment, Patch
from sim.case import Projection, parse_case
from sim.outputs import weighted_quantile

STILL = dict(p_move_day=0.0, p_move_night=0.0, h_pickup=0.0, h_home=0.0, h_dead=0.0)


def still(name="dog_friendly", **kw):
    """A category that never moves and never changes state, unless told otherwise."""
    return replace(get(name), **{**STILL, **kw})


def case_json(**kw):
    base = {"category": "dog_friendly", "home": {"lat": 40.85, "lon": 14.27}, "lost_at": "2026-09-20T19:00"}
    return parse_case({**base, **kw})


# --- geometry and bookkeeping -------------------------------------------------------


def test_projection_round_trip_and_scale():
    p = Projection(40.85, 14.27)
    rng = np.random.default_rng(0)
    lat = 40.85 + rng.uniform(-0.2, 0.2, 1000)
    lon = 14.27 + rng.uniform(-0.2, 0.2, 1000)
    la, lo = p.to_latlon(*p.to_xy(lat, lon))
    assert np.max(np.abs(la - lat)) < 1e-12 and np.max(np.abs(lo - lon)) < 1e-12
    x, y = p.to_xy(40.85 + 0.001, 14.27)
    assert abs(float(y) - 110.574) < 1e-6 and abs(float(x)) < 1e-9


def test_allocate_is_exact_and_proportional():
    assert allocate([0.5, 0.3, 0.2], 10) == [5, 3, 2]
    rng = np.random.default_rng(1)
    for _ in range(200):
        w = rng.random(int(rng.integers(1, 8)))
        n = int(rng.integers(1, 5000))
        c = allocate(list(w), n)
        assert sum(c) == n
        assert np.all(np.abs(np.array(c) - w / w.sum() * n) < 1.0 + 1e-9)


def test_weighted_quantile_matches_repetition():
    v = np.arange(1000.0)
    assert abs(weighted_quantile(v, np.ones(1000), 0.5) - 499.5) <= 1.0
    counts = np.array([1, 3, 6])
    vals = np.array([10.0, 20.0, 30.0])
    for q in (0.05, 0.3, 0.6, 0.95):
        ref = np.quantile(np.repeat(vals, counts), q)
        assert abs(weighted_quantile(vals, counts.astype(float), q) - ref) <= 10.0


def test_night_boundaries():
    assert [h for h in range(24) if is_night(h)] == [0, 1, 2, 3, 4, 5, 20, 21, 22, 23]


# --- the case file ------------------------------------------------------------------


def test_hours_round_half_up():
    c = case_json()
    assert c.hour_of(datetime(2026, 9, 20, 21, 30)) == 3  # 2.5 h
    assert c.hour_of(datetime(2026, 9, 21, 6, 30)) == 12  # 11.5 h
    assert c.hour_of(datetime(2026, 9, 20, 19, 29)) == 0


@pytest.mark.parametrize("bad", [
    {"area": {"zone": "desert"}},
    {"area": {"patches": [{"zone": "lava", "center": {"lat": 40.85, "lon": 14.27}, "radius_m": 10}]}},
])
def test_unknown_names_are_rejected(bad):
    with pytest.raises(ValueError):
        case_json(**bad)


def test_unknown_category_is_rejected():
    with pytest.raises(ValueError):
        mixture("hamster")


# --- environment ---------------------------------------------------------------------


def test_environment_lookup_and_overlap():
    env = Environment("city_center", [Patch("park", 0.0, 0.0, 100.0), Patch("rural", 0.0, 0.0, 40.0)])
    x = np.array([0.0, 70.0, 5000.0])
    got = env.at(x, np.zeros(3))
    park, rural, city = ZONES["park"], ZONES["rural"], ZONES["city_center"]
    assert got[:, 0].tolist() == [rural.people, rural.traffic, rural.stay, rural.mobility]  # later patch wins
    assert got[:, 1].tolist() == [park.people, park.traffic, park.stay, park.mobility]
    assert got[:, 2].tolist() == [city.people, city.traffic, city.stay, city.mobility]
    assert Environment().uniform and Environment().at(x, x).tolist() == [1.0, 1.0, 1.0, 1.0]


# --- conditioning -----------------------------------------------------------------------


def placed(cat, xs, **kw):
    sim = Simulation([(cat, 1.0)], len(xs), seed=0, **kw)
    sim.x = np.asarray(xs, float)
    sim.y = np.zeros(len(xs))
    return sim


def test_not_home_zeroes_home_only():
    sim = placed(still(), [0.0, 0.0, 0.0])
    sim.state[:] = [LOOSE, HOME, DEAD]
    sim.condition_not_home()
    assert sim.w.tolist() == [0.5, 0.0, 0.5]


def test_all_home_raises():
    sim = placed(still(), [0.0])
    sim.state[0] = HOME
    with pytest.raises(ValueError):
        sim.condition_not_home()


def test_pickup_hazard_matches_the_product_formula():
    """P(still loose) = prod (1 - h * activity(hour)); n = 40k, SE <= 0.0025: tolerance 4 SE."""
    h = 0.01
    cat = still(h_pickup=h)
    sim = Simulation([(cat, 1.0)], 40_000, seed=4, hod0=7)
    sim.run(72)
    p = np.prod([1 - h * (NIGHT_ACTIVITY if is_night((7 + t) % 24) else 1.0) for t in range(72)])
    assert abs(np.mean(sim.state == LOOSE) - p) < 4 * np.sqrt(p * (1 - p) / sim.n)


def test_home_hazard_waits_for_home_from_and_doubles_at_night_for_cats():
    cat = still("cat_indoor", h_home=0.01)  # home_from_h = 24
    sim = Simulation([(cat, 1.0)], 40_000, seed=5, hod0=0)
    sim.run(24)
    assert np.all(sim.state != HOME)
    sim.run(72)
    p = np.prod([1 - 0.01 * (2.0 if is_night(t % 24) else 1.0) for t in range(24, 72)])
    assert abs(np.mean(sim.state == LOOSE) - p) < 4 * np.sqrt(p * (1 - p) / sim.n)


def test_death_hazard_scales_with_traffic():
    h = 0.005
    sim = Simulation([(still(h_dead=h), 1.0)], 40_000, seed=6, env=Environment("city_center"))
    sim.run(48)
    p = (1 - h * ZONES["city_center"].traffic) ** 48
    assert abs(np.mean(sim.state == LOOSE) - p) < 4 * np.sqrt(p * (1 - p) / sim.n)
    assert np.all(sim.t_end[sim.state == DEAD] > 0)


def test_one_step_is_lognormal_with_the_given_median():
    """n = 40k: SE of log-median ~ 1.25 sigma / sqrt(n) = 0.6%: tolerance 3%."""
    cat = replace(get("dog_wary"), p_move_day=1.0, p_move_night=1.0, t_settle_mean_h=0.0, h_pickup=0, h_home=0, h_dead=0)
    sim = Simulation([(cat, 1.0)], 40_000, seed=7, hod0=10)
    sim.run(1)
    r = np.hypot(sim.x, sim.y)
    assert abs(np.median(r) / cat.step_flight - 1) < 0.03
    assert abs(np.std(np.log(r)) / cat.step_sigma - 1) < 0.03


def test_ou_stationary_spread_matches_theory():
    """E r^2 = (1-p)^2 E L^2 / (1 - (1-p)^2) around the anchor. n = 40k: SE of the mean
    r^2 ~ 1%: tolerance 6%."""
    p, step, sig = 0.3, 50.0, 0.5
    cat = replace(get("dog_friendly"), p_move_day=1.0, p_move_night=1.0, kappa_flight=0.0, kappa_settled=0.0,
                  pull_flight=p, pull_settled=p, step_flight=step, step_settled=step, step_sigma=sig,
                  h_pickup=0, h_home=0, h_dead=0)
    sim = Simulation([(cat, 1.0)], 40_000, seed=8)
    sim.run(200)
    expected = (1 - p) ** 2 * step**2 * np.exp(2 * sig**2) / (1 - (1 - p) ** 2)
    assert abs(np.mean(sim.x**2 + sim.y**2) / expected - 1) < 0.06


def test_initial_anchor_median_and_upper_floor():
    cat = get("cat_outdoor")
    for floor, mult in ((0, 1.0), (3, 0.6)):
        sim = Simulation([(cat, 1.0)], 40_000, seed=9, floor=floor)
        # SE of the log-median = 1.25 * 2.2 / sqrt(40k) = 1.4%: tolerance 6%
        assert abs(np.median(np.hypot(sim.ax, sim.ay)) / (cat.anchor_med_m * mult) - 1) < 0.06


def test_settling_time_is_exponential():
    """Settling is checked at the start of each hour, so after 12 steps the particles with
    t_settle <= 11 have settled: 1 - e^(-11/12) for mean 12 h; n = 40k, SE 0.0024: 4 SE."""
    cat = replace(get("dog_wary"), h_pickup=0, h_home=0, h_dead=0)
    sim = Simulation([(cat, 1.0)], 40_000, seed=10)
    sim.run(12)
    p = 1 - np.exp(-11 / 12)
    assert abs(np.mean(sim.settled) - p) < 4 * np.sqrt(p * (1 - p) / sim.n)


def test_stay_multiplies_the_chance_of_moving():
    cat = replace(get("dog_friendly"), p_move_day=0.5, p_move_night=0.5, h_pickup=0, h_home=0, h_dead=0)
    sim = Simulation([(cat, 1.0)], 40_000, seed=11, env=Environment("park"))
    x0 = sim.x.copy()
    sim.run(1)
    p = 0.5 * ZONES["park"].stay
    assert abs(np.mean(sim.x != x0) - p) < 4 * np.sqrt(p * (1 - p) / sim.n)


def test_determinism_and_seed_sensitivity():
    a = Simulation(mixture("cat"), 3000, seed=1)
    b = Simulation(mixture("cat"), 3000, seed=1)
    c = Simulation(mixture("cat"), 3000, seed=2)
    for s in (a, b, c):
        s.run(48)
    assert np.array_equal(a.x, b.x) and not np.array_equal(a.x, c.x)
