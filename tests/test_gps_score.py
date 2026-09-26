"""The GPS test of the place (proto/gps/score.py, docs/MISURE.md L5) on synthetic cats: it must
find a place that cats follow, and find nothing when their directions are random."""
import numpy as np

from proto.gps.score import combine, score_cat
from sim.place import Place

from test_place3d import synthetic_world


def test_rotation_test_sees_a_place_that_matters_and_not_one_that_does_not(tmp_path):
    W = synthetic_world(tmp_path, dense=True, gardens=True)
    P = Place(W, floor=1)
    rng = np.random.default_rng(0)
    follow, random_dir = [], []
    for _ in range(12):
        r = rng.uniform(25, 180, 300)
        ax, ay = P.sample_anchor(r, rng)  # positions drawn from the place map itself
        ok = ~np.isnan(ax)
        x, y = ax[ok] + rng.normal(0, 3, ok.sum()), ay[ok] + rng.normal(0, 3, ok.sum())
        follow.append(score_cat(W, P, x, y, rng, 199))
        a = rng.uniform(0, 2 * np.pi, len(r))  # same distances, direction at random
        random_dir.append(score_cat(W, P, r * np.cos(a), r * np.sin(a), rng, 199))
    sig, null = combine(follow, 1999, rng), combine(random_dir, 1999, rng)
    assert sig["D_nats_per_fix"] > 0 and sig["p"] < 0.001, sig
    assert null["p"] > 0.01, null
    assert sig["share_cats_p_lt_0.05"] > 0.5
