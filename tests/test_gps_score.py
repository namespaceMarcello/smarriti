"""The GPS test of the place (proto/gps/score.py, docs/MISURE.md L5) on synthetic cats: it must
find a place that cats follow, and find nothing when their directions are random."""
import numpy as np
import pytest

from proto.gps.score import MAPS, built_cats, combine, households, score_cat
from sim.place import Place, PlaceParams

from test_place3d import synthetic_world


def test_cats_of_one_home_rotate_together():
    """lessons.md #48: cats whose homes are closer than 20 m are one household and share their
    rotation in the null: two identical cats of one home are one cat, not two independent ones
    (which would halve the variance of the null and make p far too small)."""
    homes = {"a": (51.0, -1.0), "b": (51.0 + 10 / 110574, -1.0), "c": (51.01, -1.0)}  # a-b 10 m, c 1.1 km
    hh = households(homes, 20.0)
    assert hh["a"] == hh["b"] != hh["c"]
    s_rot = np.random.default_rng(1).normal(0, 1, 999)
    cats = [{"S": 2.5, "S_rot": s_rot, "u": 0.0, "shares": np.ones(3), "shares_rot": np.ones(3)}] * 2
    apart = combine(cats, 20000, np.random.default_rng(2))
    together = combine(cats, 20000, np.random.default_rng(2), groups=np.array([0, 0]))
    one = combine(cats[:1], 20000, np.random.default_rng(2))
    assert together["n_households"] == 1
    assert apart["p"] < 0.002 < 0.003 < together["p"]  # N(0, 1/2) against N(0, 1) beyond 2.5
    assert abs(together["p"] - one["p"]) < 0.003


def test_built_cats_finds_names_with_spaces_and_refuses_missing_worlds(tmp_path):
    """lessons.md #45: a cat whose name has a space lives in a folder with an underscore; a cat
    marked as built without its world stops the score instead of vanishing from it."""
    (tmp_path / "cats" / "Lady_T").mkdir(parents=True)
    (tmp_path / "cats" / "Lady_T" / "world.npz").write_bytes(b"")
    index = "cat_id,dataset,n_fixes,home_lat,home_lon,home_source,n_buildings,skipped_reason\n"
    (tmp_path / "index.csv").write_text(index + "Lady T,UK,100,0,0,cell,5,\nTom,UK,100,0,0,cell,0,no building\n")
    assert built_cats(tmp_path) == {"Lady T": tmp_path / "cats" / "Lady_T"}
    (tmp_path / "index.csv").write_text(index + "Lady T,UK,100,0,0,cell,5,\nTom,UK,100,0,0,cell,3,\n")
    with pytest.raises(FileNotFoundError):
        built_cats(tmp_path)


def test_rotation_test_sees_a_place_that_matters_and_not_one_that_does_not(tmp_path):
    W = synthetic_world(tmp_path, dense=True, gardens=True)
    P = Place(W, floor=1, par=PlaceParams(preference="hanmer"))  # the map of L5, which score_cat scores
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


def test_full_stays_the_map_of_L5_and_engine_follows_the_engine(tmp_path):
    """L9 changed Place.weight: `full` must stay sel x reach (L5, the secondaries of L7), `engine` is the engine's."""
    P = Place(synthetic_world(tmp_path), floor=0)
    assert np.array_equal(MAPS["full"](P), np.where(P.surface, P.sel * P.reach, 0.0))
    assert MAPS["engine"](P) is P.weight


def test_a_map_can_rank_the_real_fixes_higher_and_still_forecast_worse():
    """L12: D (real above rotated) is not the forecast. Every cat puts 10% of its fixes where the map
    says the floor (-4.6 nat) and the rotations 15%: D > 0, yet the real fixes score below the radial map."""
    g_in, g_out = np.log(0.01 / 1.01), 0.17
    real = 0.10 * g_in + 0.90 * g_out
    rot = np.full(99, 0.15 * g_in + 0.85 * g_out)
    cats = [{"S": real, "S_rot": rot, "u": 0.01, "shares": np.ones(3), "shares_rot": np.ones(3)} for _ in range(5)]
    c = combine(cats, 99, np.random.default_rng(0))
    assert c["D_nats_per_fix"] > 0.2 and c["S_real_nats_per_fix"] < -0.3
    assert c["S_real_nats_per_fix"] == pytest.approx(real)
