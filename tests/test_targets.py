"""Phase A: the calibrated categories against the published quantiles (docs/MISURE.md).

A target passes only if the whole 4-SE interval of the simulated quantile lies within
+-20% of it, so a pass or a fail cannot hinge on the seed.
"""
import numpy as np
import pytest
from conftest import quantile_ci, within

from sim.calibrate import CAT_TARGETS, DOG_NAMES, DOG_TARGETS, TOL, cat_readings, dog_run
from sim.categories import get
from sim.engine import HELD


def cat_ok(name, n=20_000, qs=(0.25, 0.5, 0.75)):
    """Only the cats found alive by day 61 count: about 56% of n."""
    d, _ = cat_readings([get(name)], n, seed=21)[0]
    return [within(quantile_ci(d, q), t, TOL) for q, t in zip((0.25, 0.5, 0.75), CAT_TARGETS[name]) if q in qs]


def test_cat_indoor_hits_huang_p50_p75():
    assert all(cat_ok("cat_indoor", qs=(0.5, 0.75)))


@pytest.mark.slow
def test_cat_indoor_hits_huang_p25():
    """p25 = 9 m sits just above the ~21% found at home (distance 0), where the distribution is
    steep: the 4-SE interval needs about 55,000 cats found alive (lessons.md #25, #28)."""
    assert all(cat_ok("cat_indoor", n=100_000, qs=(0.25,)))


@pytest.mark.xfail(strict=True, reason="A2-A5: best fit stays 0.22-0.28 from Huang (docs/MISURE.md)")
def test_cat_outdoor_hits_huang():
    assert all(cat_ok("cat_outdoor"))


def test_dogs_hit_kremer():
    sim = dog_run([[get(n) for n in DOG_NAMES]], 20_000, seed=21)
    held = sim.state == HELD
    d = np.hypot(sim.x[held], sim.y[held])
    assert all(within(quantile_ci(d, q), t, TOL) for q, t in DOG_TARGETS)
