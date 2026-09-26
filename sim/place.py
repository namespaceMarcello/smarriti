"""The place in 3D: the real shape of the place decides the direction, the studies decide
the distance (docs/simulatore.md, "Il luogo in 3D").

A World is a 2 m grid around home filled from open data (proto/luogo3d/world.py builds
it). A Place reads it for one case: the type of every cell, where the cat can stand, the
exits from home, how reachable every cell is, and the anchor weights. Without heights the
buildings are walls (the variant chosen on 2026-09-26); with heights the roofs are surfaces
reached by jumps.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import ndimage, sparse
from scipy.sparse.csgraph import dijkstra

TYPES = ("veg", "garden", "edge", "open", "street", "roof")
WATER = 80  # ESA WorldCover class: not a place where a cat can be (docs/MISURE.md L11)


@dataclass
class PlaceParams:
    """docs/simulatore.md, table of the place in 3D. Every value: a source or a declared estimate."""
    p_door: float = 272 / (272 + 42 + 19 + 21)  # Huang 2018 Table 4: door vs window/balcony/screen
    floor_m: float = 3.0  # estimate (Italian storey; Whitney & Mehlhaff 1987 use 3.66 m in New York)
    h_down: float = 4.0  # voluntary jump down, m: estimate - a first-floor window stays a way out (Huang Table 4: 16%)
    h_up: float = 1.5  # jump up, m: estimate (no study found)
    # Manly's standardised selection ratios, Hanmer et al. 2017 (cats next to large greenspace, n = 11):
    # garden 0.553, anthropogenic surfaces 0.311, natural 0.136 -> relative to anthropogenic = 1.
    # "open" (built-up ground away from buildings and roads: yards and paved courtyards, which a 10 m
    # land cover cannot tell apart) sits halfway (geometric mean): an estimate.
    sel: dict = field(default_factory=lambda: {"veg": 0.136 / 0.311, "garden": 0.553 / 0.311,
                                               "open": (0.553 / 0.311) ** 0.5, "edge": 1.0,
                                               "street": 1.0, "roof": 1.0})
    # what the anchors and the time spent weigh (docs/MISURE.md L14): "hanmer" = Hanmer's `sel` by
    # type, buildings as walls (the engine). "lost" = outside, the resident cats' selection by distance
    # from the nearest building (L13, 391 GPS cats, over its mean outside); inside a building other
    # than home, where a lost cat hides (Huang 2018: garages, sheds, under houses, others' houses),
    # `hide` against outside. Not the engine's yet: with `hide` in the step selection the cats outside
    # move 1.5-1.7 times more and the lower quartile of the distances rises 13-28% (L14). `sel` stays
    # Hanmer's either way: the GPS maps of L5-L7 read it.
    preference: str = "hanmer"
    band_edges: tuple = (3.0, 6.0, 12.0, 24.0)  # m from the nearest building: 0-3, 3-6, 6-12, 12-24, >24
    bands: tuple = (1.002, 1.045, 1.089, 1.003, 0.819)  # L13 bands6 at sigma 0, / 1.021 (its mean outside)
    hide: float = 3.58  # L14: (s/a)/((1-s)/(1-a)), s 0.268 of Huang's found cats in a footprint, a 0.093 (US, AU)
    c_road: tuple = (1.0, 1.0, 2.0, 3.0, 10.0, 10.0)  # by road class 0..5: estimate
    k_up: float = 5.0  # extra metres of path per metre climbed: estimate
    edge_m: float = 3.0  # estimate
    ring_frac: float = 0.05
    ring_min: float = 2.0
    slope_allow: float = 0.3  # a walk step may change height by 30% of its length (with heights)
    # the selection also in the step: a cat moves less often where it likes to stay, so the time
    # spent in a type of place goes with sel (docs/simulatore.md, "Il movimento attorno all'ancora")
    step_selection: bool = True
    # anchors weigh sel x reachability (L5) or sel alone on the free cells (after L7, where the
    # reachability was neutral on 391 real cats: docs/MISURE.md L6, L7)
    reach_weight: bool = False
    # a step that ends where the cat cannot be is drawn again up to `redraw` times, then it ends on
    # the nearest free cell; 0 = straight to the nearest free cell (L2: twice the mass against walls)
    redraw: int = 5


class World:
    def __init__(self, path: str | Path):
        W = np.load(path)
        self.meta = json.loads(str(W["meta"]))
        self.cell, self.x0, self.n = self.meta["cell"], self.meta["x0"], self.meta["n"]
        for k in ("ground", "bh", "bid", "cover", "road", "green", "wall"):
            setattr(self, k, W[k])
        self.bid_home = int(W["bid_home"])
        c = self.x0 + (np.arange(self.n) + 0.5) * self.cell
        self.gx, self.gy = np.meshgrid(c, c)
        self.d = np.hypot(self.gx, self.gy)  # from the door (home point)

    def index(self, x, y):
        ix = np.floor((np.asarray(x) - self.x0) / self.cell).astype(np.int64)
        iy = np.floor((np.asarray(y) - self.x0) / self.cell).astype(np.int64)
        ok = (ix >= 0) & (ix < self.n) & (iy >= 0) & (iy < self.n)
        return np.clip(iy, 0, self.n - 1), np.clip(ix, 0, self.n - 1), ok


class Place:
    """Surfaces, exits, reachability and anchor weights of one place, for a cat leaving `floor`."""

    def __init__(self, world: World, floor: int, heights: bool = False, par: PlaceParams | None = None):
        self.w, self.heights, self.floor = world, heights, floor
        self.par = par = par or PlaceParams()
        W = world
        bld = W.bid >= 0
        home = W.bid == W.bid_home
        water = (W.cover == WATER) & (W.road == 0)  # a road over the water is a bridge
        near_bld = ndimage.distance_transform_edt(~bld) * W.cell <= par.edge_m
        t = np.full(W.bid.shape, TYPES.index("open"), np.int8)
        t[np.isin(W.cover, (10, 20, 30, 40)) | (W.green == 2)] = TYPES.index("veg")  # Hanmer "natural"
        t[W.green == 1] = TYPES.index("garden")
        t[near_bld] = TYPES.index("edge")
        t[W.road >= 2] = TYPES.index("street")
        t[bld] = TYPES.index("roof")
        self.type = t
        self.z = W.ground + (W.bh if heights else 0.0)
        # where the cat can stand: flat, the ground outside buildings; with heights, ground and roofs but its own
        # house; never on the water
        self.surface = (~home if heights else ~bld) & ~water
        self.exits = self._exits(home)
        self.D = self._costs()
        with np.errstate(divide="ignore", invalid="ignore"):
            reach = [np.where(np.isfinite(D), np.minimum(1.0, np.where(D > 0, W.d / D, 1.0)), 0.0) for D in self.D]
        self.reach = par.p_door * reach[0] + (1 - par.p_door) * reach[1]
        free = self.surface & (self.reach > 0)
        self.sel = np.array([par.sel[k] for k in TYPES])[t]
        if par.preference == "hanmer":
            self.ok, self.pref, self.hide = free, self.sel, np.zeros_like(bld)
        elif par.preference == "lost":
            self.hide = self._hides(bld & ~home & ~water, free & ~bld)
            self.ok = free | self.hide  # where a cat can be
            d_bld = ndimage.distance_transform_edt(~bld) * W.cell
            band = np.array(par.bands)[np.searchsorted(par.band_edges, d_bld, "left")]
            self.pref = np.where(self.hide, par.hide, band)
        else:
            raise ValueError(f"preference: 'lost' or 'hanmer', not {par.preference!r}")
        self.weight = np.where(self.ok, self.pref * (self.reach if par.reach_weight else 1.0), 0.0)
        self._index_rings()
        _, self._near = ndimage.distance_transform_edt(~self.ok, return_indices=True)

    def _hides(self, others: np.ndarray, ground: np.ndarray) -> np.ndarray:
        """Every cell of the buildings in `others` that touch `ground` (free and reachable): where a
        lost cat can hide. The graph does not go through them: a cat gets in from the ground nearby."""
        touch = ndimage.binary_dilation(ground, np.ones((3, 3), bool)) & others
        return others & np.isin(self.w.bid, np.unique(self.w.bid[touch]))

    # --- exits ------------------------------------------------------------------------
    def _exits(self, home):
        W, par = self.w, self.par
        ring = ndimage.binary_dilation(home, np.ones((3, 3), bool)) & ~home & self.surface
        door = (W.d <= 3.0) & self.surface & ~home
        if not door.any():  # the nearest standable cell to the door point
            k = np.argmin(np.where(self.surface & ~home, W.d, np.inf))
            door = np.zeros_like(home); door.flat[k] = True
        self.z_floor = None
        if not self.heights:
            return door, ring
        z_door = float(np.median(W.ground[door]))
        self.z_floor = z_door + self.floor * par.floor_m
        dz = self.z_floor - self.z
        window = ring & (dz <= par.h_down) & (-dz <= par.h_up)
        if not window.any():  # nowhere to jump: the window route falls back to the door
            window = door
        return door, window

    # --- reachability -------------------------------------------------------------------
    def _costs(self):
        W, par, n = self.w, self.par, self.w.n
        idx = np.arange(n * n).reshape(n, n)
        mult = np.array(par.c_road)[W.road].astype(np.float64)
        mult[W.bid >= 0] = 1.0  # roofs are not roads
        rows, cols, vals = [], [], []
        for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)):
            ya, yb = slice(max(0, -dy), n - max(0, dy)), slice(max(0, dy), n - max(0, -dy))
            xa, xb = slice(max(0, -dx), n - max(0, dx)), slice(max(0, dx), n - max(0, -dx))
            ok = self.surface[ya, xa] & self.surface[yb, xb]
            step = W.cell * (1.4142135 if dx and dy else 1.0)
            cost = step * 0.5 * (mult[ya, xa] + mult[yb, xb])
            if self.heights:
                up = self.z[yb, xb] - self.z[ya, xa]
                slope_ok = np.abs(up) <= step * par.slope_allow  # ground slope, or roof to roof
                jump_ok = (up <= par.h_up) & (-up <= par.h_down)
                ok &= slope_ok | jump_ok
                cost = cost + par.k_up * np.maximum(up, 0.0)
            rows.append(idx[ya, xa][ok]); cols.append(idx[yb, xb][ok]); vals.append(cost[ok])
        G = sparse.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n * n, n * n))
        return [dijkstra(G, directed=True, indices=np.flatnonzero(ex), min_only=True).reshape(n, n) for ex in self.exits]

    # --- anchors -------------------------------------------------------------------------
    def _index_rings(self):
        d = self.w.d.ravel()
        order = np.argsort(d, kind="stable")
        self.sd = d[order]
        self.sidx = order
        self.cw = np.concatenate([[0.0], np.cumsum(self.weight.ravel()[order])])

    def sample_anchor(self, r: np.ndarray, rng: np.random.Generator):
        """A cell at distance ~r from home, chosen by weight; NaN where the ring has no weight."""
        par, W = self.par, self.w
        half = np.maximum(par.ring_min, par.ring_frac * r) / 2
        lo = np.searchsorted(self.sd, r - half, "left")
        hi = np.searchsorted(self.sd, r + half, "right")
        tot = self.cw[hi] - self.cw[lo]
        ok = (tot > 0) & (r + half < -W.x0)  # the ring must be whole inside the grid
        u = self.cw[lo] + rng.random(len(r)) * tot
        k = np.clip(np.searchsorted(self.cw, u, "right") - 1, 0, len(self.sidx) - 1)
        cell = self.sidx[k]
        jx, jy = rng.uniform(-0.5, 0.5, (2, len(r))) * W.cell
        ax = np.where(ok, W.gx.ravel()[cell] + jx, np.nan)
        ay = np.where(ok, W.gy.ravel()[cell] + jy, np.nan)
        return ax, ay

    # --- steps ---------------------------------------------------------------------------
    def standable(self, x, y):
        """True where a cat can be, and everywhere off the grid."""
        iy, ix, inside = self.w.index(x, y)
        return np.where(inside, self.ok[iy, ix], True)

    def snap(self, x, y):
        """The nearest cell where the cat can stand (lessons.md #33: an hourly step is a path,
        only its end counts)."""
        iy, ix, _ = self.w.index(x, y)
        jy, jx = self._near[0][iy, ix], self._near[1][iy, ix]
        return self.w.gx[jy, jx], self.w.gy[jy, jx]

    def sel_at(self, x, y):
        """The preference (`pref`) of the cell under each point, what the time spent there goes with;
        NaN off the grid or where a cat cannot be."""
        iy, ix, inside = self.w.index(x, y)
        return np.where(inside & self.ok[iy, ix], self.pref[iy, ix], np.nan)

    def start_point(self):
        door = self.exits[0]
        k = np.argmin(np.where(door, self.w.d, np.inf))
        return float(self.w.gx.flat[k]), float(self.w.gy.flat[k])


def load_place(path: str | Path, floor: int, heights: bool = False) -> Place:
    return Place(World(path), floor, heights)
