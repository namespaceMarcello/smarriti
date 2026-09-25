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
from sim.categories import BASE, MIXTURES, get
from sim.engine import HELD, HOME, Simulation
from sim.validate import HUANG_OVERALL, b1_distances, b3_dog_time, b4_icad, map_coverage

B1 = []


def b1():
    if not B1:
        B1.append(b1_distances(seed=31))  # about 21,600 cats found alive
    return B1[0]


def test_b1_cats_mixed_p75_and_share_within_500m():
    d = b1()
    assert within(quantile_ci(d, 0.75), HUANG_OVERALL[2], 0.2)
    p = np.mean(d <= 500)
    assert abs(p - 0.75) + 4 * np.sqrt(p * (1 - p) / len(d)) <= 0.05


@pytest.mark.xfail(strict=True, reason="B1 (A5): mixed p25 10.5-11.0 m vs 9, limit 10.8: on the edge, "
                   "not provable at 4 SE (docs/MISURE.md)")
def test_b1_cats_mixed_p25():
    assert within(quantile_ci(b1(), 0.25), HUANG_OVERALL[0], 0.2)


@pytest.mark.xfail(strict=True, reason="B: mixed median 72 m against 50 m (docs/MISURE.md)")
def test_b1_cats_mixed_median():
    assert within(quantile_ci(b1(), 0.5), HUANG_OVERALL[1], 0.2)


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


def test_b2_cats_home_or_held_within_found():
    """Weak since A5: Huang's curve is now a calibration target (lessons.md #9)."""
    for found, home, held, n in cats_by_day():
        p = home + held
        assert p + 4 * np.sqrt(p * (1 - p) / n) <= found


@pytest.mark.xfail(strict=True, reason="B3: 0.81 of dog pickups within 5 days vs > 0.90 (docs/MISURE.md)")
def test_b3_dogs_picked_up_within_five_days():
    assert b3_dog_time(seed=33, n=10_000)["pickups_within_5d"] >= 0.90


def test_b4_icad_shelter_share_is_a_lower_bound():
    assert all(v["ok"] for v in b4_icad(seed=34, n=5_000).values())


# C1: every category, at 48 h and (where animals are still loose) at 7 days. Truths per map
# so that the 4-SE interval of each coverage fits the tolerance. The HPD regions are taken on
# the grid's mass, ~98% of the loose mass (the rest is beyond the rectangle), so the 90%
# region holds ~88%: hence the band 0.84-0.95 (docs/MISURE.md, C1 with the smoothed map).
CALIBRATED_MAPS = [(n, 48) for n in BASE] + [(n, 168) for n in ("cat_indoor", "cat_outdoor", "dog_wary", "dog_fearful")]
C1_TRUTHS = {("dog_friendly", 48): 40_000, ("dog_wary", 168): 60_000, ("dog_fearful", 168): 80_000}


@pytest.mark.parametrize("name,hours", CALIBRATED_MAPS)
def test_c1_map_is_a_calibrated_probability(name, hours):
    r = map_coverage(name, hours, n_truth=C1_TRUTHS.get((name, hours), 20_000), seed=35)
    n = r["truths"]
    assert n > 2000
    for q, lo, hi in ((50, 0.45, 0.58), (90, 0.84, 0.95)):
        c = r[f"cover{q}"]
        se = np.sqrt(c * (1 - c) / n)
        assert lo <= c - 4 * se and c + 4 * se <= hi
