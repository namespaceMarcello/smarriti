"""The place in 3D prototype (proto/luogo3d): exact pieces on a synthetic place, no private data."""
import json
import zlib

import numpy as np
import pytest

from proto.luogo3d.cogread import _undo_predictor
from proto.luogo3d.fetch import tinitaly_tile
from proto.luogo3d.place3d import Params, Place, PlaceSimulation, World
from proto.luogo3d.utm import from_utm, to_utm
from sim.categories import mixture

from conftest import quantile_ci


def test_utm_round_trip_and_axes():
    lat = np.array([36.7, 40.85, 45.1, 47.0]); lon = np.array([8.1, 14.27, 12.3, 15.9])
    for zone in (32, 33):
        e, n = to_utm(lat, lon, zone)
        la, lo = from_utm(e, n, zone)
        assert np.max(np.abs(la - lat)) * 110_574 < 1e-3 and np.max(np.abs(lo - lon)) * 84_000 < 1e-3
    e, n = to_utm(40.0, 15.0, 33)  # on the central meridian: false easting exactly
    assert abs(e - 500_000) < 1e-6
    assert abs(to_utm(0.0, 12.0, 33)[1]) < 1e-6  # the equator is northing 0


def test_tinitaly_tile_name_from_south_west_edge():
    # lessons.md #30: w45090 holds E 900-950 km, N 4500-4550 km (tiepoint 900000, 4550000)
    assert tinitaly_tile(938_937.4, 4_537_855.7) == "w45090_s10"
    assert tinitaly_tile(900_000.0, 4_500_000.0) == "w45090_s10"
    assert tinitaly_tile(899_999.0, 4_549_999.0) == "w45085_s10"


def test_floating_point_predictor_round_trip():
    rng = np.random.default_rng(0)
    a = (rng.normal(200, 30, (8, 16))).astype(np.float32)
    be = a.astype(">f4").view(np.uint8).reshape(8, 16, 4).transpose(0, 2, 1).reshape(8, 64)  # byte planes
    diff = np.diff(be.astype(np.int16), axis=1, prepend=0).astype(np.uint8)
    out = _undo_predictor(zlib.decompress(zlib.compress(diff.tobytes())), 3, np.float32, 16, 8)
    assert np.array_equal(out, a)


def synthetic_world(tmp_path, n=200, cell=2.0, dense=False):
    half = n * cell / 2
    c = -half + (np.arange(n) + 0.5) * cell
    gx, gy = np.meshgrid(c, c)
    ground = 100 + 0.1 * gy  # 10% slope, uphill to the north
    bid = np.full((n, n), -1, np.int32); bh = np.zeros((n, n), np.float32)
    boxes = [(-10, 10, 2, 14, 9.0), (30, 60, -40, -10, 6.0), (-80, -40, 20, 70, 12.0), (-30, -20, -60, -30, 2.0)]
    if dense:  # a town: 12 m blocks every 20 m, a third of the ground built, like the test place within 100 m
        boxes += [(bx, bx + 12, by, by + 12, 7.0) for bx in range(-196, 190, 20) for by in range(-196, 190, 20)
                  if not (-30 < bx < 20 and -10 < by < 25)]
    for k, (x0, x1, y0, y1, h) in enumerate(boxes):
        m = (gx >= x0) & (gx < x1) & (gy >= y0) & (gy < y1)
        bid[m] = k; bh[m] = h
    road = np.zeros((n, n), np.uint8); road[np.abs(gy + 80) < 3] = 4
    cover = np.full((n, n), 50, np.uint8); cover[gx > 100] = 10; cover[(gx < -100) & (gy < 0)] = 30
    meta = dict(cell=cell, x0=-half, y0=-half, n=n, lat0=0.0, lon0=0.0)
    np.savez(tmp_path / "world.npz", meta=json.dumps(meta), ground=ground, dsm30=ground, bh=bh, bid=bid,
             bsrc=np.zeros((n, n), np.uint8), cover=cover, road=road, green=np.zeros((n, n), np.uint8),
             wall=np.zeros((n, n), np.uint8), bid_home=0)
    return World(tmp_path / "world.npz")


@pytest.mark.parametrize("variant", [2, 3])
def test_anchor_keeps_the_distance(tmp_path, variant):
    W = synthetic_world(tmp_path)
    P = Place(W, variant, floor=1)
    rng = np.random.default_rng(1)
    r = rng.uniform(1, 190, 20_000)
    ax, ay = P.sample_anchor(r, rng)
    ok = ~np.isnan(ax)
    assert ok.mean() > 0.95
    half = np.maximum(P.par.ring_min, P.par.ring_frac * r[ok]) / 2
    err = np.abs(np.hypot(ax[ok], ay[ok]) - r[ok])
    assert np.all(err <= half + W.cell * 0.71 + 1e-9)  # the ring plus half a cell diagonal
    iy, ix, _ = W.index(ax[ok], ay[ok])
    assert np.all(P.surface[iy, ix]) and np.all(P.weight[iy, ix] > 0)
    if variant == 2:
        assert not np.any(W.bid[iy, ix] >= 0)  # flat: never inside a building
    assert not np.any(W.bid[iy, ix] == W.bid_home)


def test_window_exits_obey_the_jumps(tmp_path):
    W = synthetic_world(tmp_path)
    P = Place(W, 3, floor=1)
    door, window = P.exits
    dz = P.z_floor - P.z[window]
    assert window.any() and np.all(dz <= P.par.h_down + 1e-9) and np.all(-dz <= P.par.h_up + 1e-9)
    assert not np.any(window & (W.bid == W.bid_home))


def test_place_changes_only_the_direction(tmp_path):
    """Same seed with and without the place: every anchor at the same distance from home."""
    W = synthetic_world(tmp_path)
    plain = PlaceSimulation(mixture("cat_indoor"), 5_000, 3, floor=1, place=None)
    placed = PlaceSimulation(mixture("cat_indoor"), 5_000, 3, floor=1, place=Place(W, 2, 1))
    r0, r1 = np.hypot(plain.ax, plain.ay), np.hypot(placed.ax, placed.ay)
    moved = (placed.ax != plain.ax) | (placed.ay != plain.ay)
    assert moved.mean() > 0.5
    half = np.maximum(Params().ring_min, Params().ring_frac * r0) / 2
    assert np.all(np.abs(r1 - r0)[moved] <= half[moved] + W.cell * 0.71 + 1e-9)


def test_place_keeps_the_walk_distances(tmp_path):
    """lessons.md #33: the place changes where the cat is, not how far (24 h, +-10%)."""
    W = synthetic_world(tmp_path, dense=True)
    kw = dict(floor=1, hod0=20)
    plain = PlaceSimulation(mixture("cat_indoor"), 20_000, 5, place=None, **kw)
    placed = PlaceSimulation(mixture("cat_indoor"), 20_000, 5, place=Place(W, 2, 1), **kw)
    plain.run(24); placed.run(24)
    r0, r1 = np.hypot(plain.x, plain.y), np.hypot(placed.x, placed.y)
    for q in (0.25, 0.5, 0.75):  # both 4-SE intervals: placed within +-10% of plain (lessons.md #28)
        lo0, hi0 = quantile_ci(r0, q)
        lo1, hi1 = quantile_ci(r1, q)
        assert 0.9 * lo0 <= lo1 and hi1 <= 1.1 * hi0, (q, lo0, hi0, lo1, hi1)
    iy, ix, ok = W.index(placed.x, placed.y)
    assert not np.any(ok & (W.bid[iy, ix] >= 0))  # nobody ends inside a building
