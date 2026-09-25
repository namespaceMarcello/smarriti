"""Phases B and C1: the hypotheses the model makes, checked against numbers not used to
calibrate it. Known failures are strict xfails that cite docs/MISURE.md: if one starts
passing, the suite turns red so that the xfail is removed and the measure rewritten.

Reliability: every threshold is at least 4 standard errors away from the value measured,
so seeds cannot flip a verdict.
"""
import numpy as np
import pytest
from conftest import quantile_ci, within

from sim.calibrate import HOD0, HUANG_FOUND
from sim.categories import MIXTURES, get
from sim.engine import HELD, HOME, Simulation
from sim.validate import HUANG_OVERALL, b1_cat_mixture, b3_dog_time, b4_icad, map_coverage

B1 = {}


def b1():
    if not B1:
        B1.update(b1_cat_mixture(seed=31))
    return B1


def test_b1_cats_mixed_p25_p75_and_share_within_500m():
    r = b1()
    assert abs(r["got"][0] / HUANG_OVERALL[0] - 1) <= 0.2 and abs(r["got"][2] / HUANG_OVERALL[2] - 1) <= 0.2
    assert abs(r["within_500m"] - 0.75) <= 0.05  # SE 0.003


@pytest.mark.xfail(strict=True, reason="B: mixed median 72 m against 50 m (docs/MISURE.md)")
def test_b1_cats_mixed_median():
    assert abs(b1()["got"][1] / HUANG_OVERALL[1] - 1) <= 0.2


def cats_by_day(n=10_000):
    sim = Simulation([(get(k), w) for k, w in MIXTURES["cat"].items()], n, seed=32, hod0=HOD0)
    out = []
    for day, found in HUANG_FOUND[1:]:
        sim.run(day * 24)
        out.append((found, float(np.mean(sim.state == HOME)), float(np.mean(sim.state == HELD)), n))
    return out


def test_b2_cats_do_not_come_home_faster_than_they_are_found():
    for found, home, _, n in cats_by_day():
        assert home + 4 * np.sqrt(home * (1 - home) / n) <= found


@pytest.mark.xfail(strict=True, reason="B2: HOME+HELD 0.66 at 30 d vs 0.50 found; h_home 4-5x too high (lessons.md #8)")
def test_b2_cats_home_or_held_within_found():
    assert all(home + held <= found for found, home, held, _ in cats_by_day())


@pytest.mark.xfail(strict=True, reason="B3: 0.81 of dog pickups within 5 days vs > 0.90 (docs/MISURE.md)")
def test_b3_dogs_picked_up_within_five_days():
    assert b3_dog_time(seed=33, n=10_000)["pickups_within_5d"] >= 0.90


def test_b4_icad_shelter_share_is_a_lower_bound():
    assert all(v["ok"] for v in b4_icad(seed=34, n=5_000).values())


CALIBRATED_MAPS = [("cat_indoor", 48), ("cat_indoor", 168), ("dog_friendly", 48)]
SPARSE_MAPS = [("cat_outdoor", 48), ("dog_wary", 48), ("dog_fearful", 48)]


@pytest.mark.parametrize("name,hours", CALIBRATED_MAPS)
def test_c1_map_is_a_calibrated_probability(name, hours):
    r = map_coverage(name, hours, n_truth=20_000 if name == "dog_friendly" else 4_000, seed=35)
    assert r["truths"] > 1000
    assert 0.45 <= r["cover50"] <= 0.58 and 0.84 <= r["cover90"] <= 0.95


@pytest.mark.parametrize("name,hours", SPARSE_MAPS)
@pytest.mark.xfail(strict=True, reason="C1: histogram too sparse where particles spread (lessons.md #10)")
def test_c1_sparse_maps_are_not_yet_calibrated(name, hours):
    r = map_coverage(name, hours, seed=35)
    assert 0.84 <= r["cover90"] <= 0.95
