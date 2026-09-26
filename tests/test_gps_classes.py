"""The class maps of proto/gps/classes.py (docs/MISURE.md L13): the tables score as score.gain_map,
the fit at sigma 0 is the selection ratio (Gibbs), and the building tags are those of the world."""
import json

import numpy as np
import pytest

from proto.gps import classes as C
from proto.gps import score
from proto.gps.build_cats import build_world
from sim.place import Place, World

from test_place3d import synthetic_world


def test_the_class_tables_score_as_gain_map(tmp_path, monkeypatch):
    """S from the tables (blurred class indicators at the fixes, ring means) is the log score of
    score.gain_map with the same class map and no floor, at sigma 0 and 10."""
    W = synthetic_world(tmp_path, dense=True, gardens=True)
    blds = [({"building": ("shed", "house", "yes")[b % 3]}, (20.0, 150.0)[b % 2]) for b in range(W.bid.max() + 1)]
    rng = np.random.default_rng(3)
    r, a = rng.uniform(21, 180, 400), rng.uniform(0, 2 * np.pi, 400)
    x, y = r * np.cos(a), r * np.sin(a)
    t = C.cat_table(W, blds, x, y, sigmas=(0.0, 10.0))
    wc = np.exp(rng.normal(0, 0.5, len(C.FINE)))
    grid = wc[C.fine_labels(W, blds)]
    monkeypatch.setattr(score, "FLOOR", 0.0)
    iy, ix, _ = W.index(x, y)
    for j, s in enumerate((0.0, 10.0)):
        ref = score.gain_map(Place(W, floor=0), grid, s)[iy, ix]
        mine = np.log(t["phi"][j].astype(float) @ wc) - np.log(t["abar"][j][t["ring"]].astype(float) @ wc)
        assert np.allclose(mine, ref, atol=1e-5)


def test_the_fit_at_sigma_0_is_the_selection_ratio_and_gains_the_KL():
    """Gibbs (docs/matematica.md): with one ring, the weights that maximise S are u/a and S = KL(u||a)."""
    a = np.array([0.15, 0.35, 0.5])
    u = np.array([0.10, 0.40, 0.5])
    n = 1000
    lab = np.repeat(np.arange(3), (u * n).astype(int))
    Phi = np.eye(3)[lab]
    A = np.tile(a, (len(lab), 1))
    wfix = np.full(len(lab), 1 / len(lab))
    beta = C.fit(Phi, A, wfix, ridge=1e-12)
    w = np.exp(beta)
    assert np.allclose(w / w.sum(), (u / a) / (u / a).sum(), atol=1e-4)
    assert C.score_S(beta, Phi, A, wfix)[0] == pytest.approx(float(np.sum(u * np.log(u / a))), abs=1e-7)


def test_every_scheme_takes_every_fine_class_once():
    for groups, names in {**C.SCHEMES, **C.PIECES}.values():
        assert C.scheme_matrix(groups).shape == (len(names), len(C.FINE))
    with pytest.raises(ValueError):
        C.scheme_matrix([[0, 1]])


def test_the_tags_are_those_of_the_world(tmp_path):
    """buildings_of paints the OSM answer again: the tags come back in bid order, and an answer that
    paints other buildings than the world's is refused."""
    d = 10 / 110574  # 10 m of latitude, about 10 m of longitude at the equator
    def way(i, x0, tag):
        box = [(0, 0), (0, 1), (1, 1), (1, 0), (0, 0)]
        return {"type": "way", "id": i, "tags": {"building": tag},
                "geometry": [{"lat": (y + x0) * d, "lon": x * d} for x, y in box]}
    osm = {"elements": [way(1, 0, "house"), way(2, 3, "garage")]}
    layers, g, nb = build_world(0.0, 0.0, osm)
    meta = dict(cell=g.cell, x0=g.x0, y0=g.y0, n=g.n, lat0=0.0, lon0=0.0, osm_buildings=nb)
    np.savez(tmp_path / "world.npz", meta=json.dumps(meta), bid_home=np.array(0), **layers)
    W = World(tmp_path / "world.npz")
    blds = C.buildings_of(W, osm)
    assert [t["building"] for t, _ in blds] == ["house", "garage"]
    assert all(a == pytest.approx(100.0, rel=0.02) for _, a in blds)
    assert [C.GROUP_NAMES[C.group_of(t)] for t, _ in blds] == ["dwelling", "garage"]
    with pytest.raises(ValueError):
        C.buildings_of(W, {"elements": osm["elements"][:1]})
