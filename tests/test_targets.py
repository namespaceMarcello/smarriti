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


def cat_ok(name):
    d, _ = cat_readings([get(name)], 20_000, seed=21)[0]
    return [within(quantile_ci(d, q), t, TOL) for q, t in zip((0.25, 0.5, 0.75), CAT_TARGETS[name])]


def test_cat_indoor_hits_huang():
    assert all(cat_ok("cat_indoor"))


@pytest.mark.xfail(strict=True, reason="A2/A3: best fit stays 0.22-0.23 from Huang (docs/MISURE.md)")
def test_cat_outdoor_hits_huang():
    assert all(cat_ok("cat_outdoor"))


def test_dogs_hit_kremer():
    sim = dog_run([[get(n) for n in DOG_NAMES]], 20_000, seed=21)
    held = sim.state == HELD
    d = np.hypot(sim.x[held], sim.y[held])
    assert all(within(quantile_ci(d, q), t, TOL) for q, t in DOG_TARGETS)
