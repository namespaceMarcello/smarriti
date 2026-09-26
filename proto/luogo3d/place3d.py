"""The place in 3D decides the direction; the calibrated distance stays (docs/simulatore.md,
"Il luogo in 3D - progetto"). A prototype outside the engine: PlaceSimulation subclasses
sim.engine.Simulation and changes only the anchor direction and the refused steps.

Variants: 1 = today (uniform plane), 2 = buildings and gardens (flat), 3 = with heights
and slopes (ground and roofs as surfaces, jumps).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import ndimage, sparse
from scipy.sparse.csgraph import dijkstra

from sim.engine import Simulation

TYPES = ("veg", "garden", "edge", "open", "street", "roof")


@dataclass
class Params:
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
    c_road: tuple = (1.0, 1.0, 2.0, 3.0, 10.0, 10.0)  # by road class 0..5: estimate
    k_up: float = 5.0  # extra metres of path per metre climbed: estimate
    edge_m: float = 3.0  # estimate
    ring_frac: float = 0.05
    ring_min: float = 2.0
    slope_allow: float = 0.3  # a walk step may change height by 30% of its length (v3)


class World:
    def __init__(self, path: Path):
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
    """Surfaces, exits, reachability and anchor weights for one variant (2 or 3)."""

    def __init__(self, world: World, variant: int, floor: int, par: Params = Params()):
        assert variant in (2, 3)
        self.w, self.v, self.par, self.floor = world, variant, par, floor
        W = world
        bld = W.bid >= 0
        home = W.bid == W.bid_home
        near_bld = ndimage.distance_transform_edt(~bld) * W.cell <= par.edge_m
        t = np.full(W.bid.shape, TYPES.index("open"), np.int8)
        t[np.isin(W.cover, (10, 20, 30, 40)) | (W.green == 2)] = TYPES.index("veg")  # Hanmer "natural"
        t[W.green == 1] = TYPES.index("garden")
        t[near_bld] = TYPES.index("edge")
        t[W.road >= 2] = TYPES.index("street")
        t[bld] = TYPES.index("roof")
        self.type = t
        self.z = W.ground + (W.bh if variant == 3 else 0.0)
        # where the cat can stand: v2 the ground outside buildings; v3 ground and roofs, not its own house
        self.surface = ~bld if variant == 2 else ~home
        self.exits = self._exits(home)
        self.D = self._costs()
        with np.errstate(divide="ignore", invalid="ignore"):
            reach = [np.where(np.isfinite(D), np.minimum(1.0, np.where(D > 0, W.d / D, 1.0)), 0.0) for D in self.D]
        self.reach = par.p_door * reach[0] + (1 - par.p_door) * reach[1]
        sel = np.array([par.sel[k] for k in TYPES])
        self.weight = np.where(self.surface, sel[t] * self.reach, 0.0)
        self._index_rings()

    # --- exits ------------------------------------------------------------------------
    def _exits(self, home):
        W, par = self.w, self.par
        ring = ndimage.binary_dilation(home, np.ones((3, 3), bool)) & ~home & self.surface
        door = (W.d <= 3.0) & self.surface & ~home
        if not door.any():  # the nearest standable cell to the door point
            k = np.argmin(np.where(self.surface & ~home, W.d, np.inf))
            door = np.zeros_like(home); door.flat[k] = True
        if self.v == 2:
            window = ring
        else:
            z_door = float(np.median(W.ground[door]))
            z_floor = z_door + self.floor * par.floor_m
            dz = z_floor - self.z
            window = ring & (dz <= par.h_down) & (-dz <= par.h_up)
            if not window.any():  # nowhere to jump: the window route falls back to the door
                window = door
        self.z_floor = None if self.v == 2 else z_floor
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
            if self.v == 3:
                up = self.z[yb, xb] - self.z[ya, xa]
                slope_ok = np.abs(up) <= step * par.slope_allow  # ground slope, or roof to roof
                jump_ok = (up <= par.h_up) & (-up <= par.h_down)
                ok &= slope_ok | jump_ok
                cost = cost + par.k_up * np.maximum(up, 0.0)
            rows.append(idx[ya, xa][ok]); cols.append(idx[yb, xb][ok]); vals.append(cost[ok])
        G = sparse.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n * n, n * n))
        out = []
        for ex in self.exits:
            D = dijkstra(G, directed=True, indices=np.flatnonzero(ex), min_only=True)
            out.append(D.reshape(n, n))
        return out

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

    def standable(self, x, y):
        iy, ix, inside = self.w.index(x, y)
        s = self.surface[iy, ix] & (self.reach[iy, ix] > 0)
        return np.where(inside, s, True)

    def snap(self, x, y):
        """The nearest cell where the cat can stand (lessons.md #33: an hourly step is a path,
        only its end counts)."""
        if not hasattr(self, "_near"):
            ok = self.surface & (self.reach > 0)
            _, (ny, nx) = ndimage.distance_transform_edt(~ok, return_indices=True)
            self._near = (ny, nx)
        iy, ix, _ = self.w.index(x, y)
        jy, jx = self._near[0][iy, ix], self._near[1][iy, ix]
        return self.w.gx[jy, jx], self.w.gy[jy, jx]

    def z_at(self, x, y):
        iy, ix, _ = self.w.index(x, y)
        return self.z[iy, ix]

    def start_point(self):
        door = self.exits[0]
        k = np.argmin(np.where(door, self.w.d, np.inf))
        return float(self.w.gx.flat[k]), float(self.w.gy.flat[k])


class PlaceSimulation(Simulation):
    """Simulation whose anchor direction and steps follow a Place; distances stay A5's."""

    def __init__(self, *args, place: Place | None = None, dir_seed: int = 1, **kw):
        super().__init__(*args, **kw)
        self.place = place
        if place is None:
            return
        rng = np.random.default_rng(dir_seed)  # a separate stream: the engine's draws stay paired
        rand = self.has_anchor & ((self.ax != 0) | (self.ay != 0))
        r = np.hypot(self.ax, self.ay)[rand]
        ax, ay = place.sample_anchor(r, rng)
        keep = np.isnan(ax)  # ring without weight or off the grid: today's random direction
        self.ax[rand] = np.where(keep, self.ax[rand], ax)
        self.ay[rand] = np.where(keep, self.ay[rand], ay)
        self.fallback = float(keep.mean()) if len(keep) else 0.0
        sx, sy = place.start_point()
        self.x[:], self.y[:] = sx, sy

    def step(self) -> None:
        if self.place is None:
            return super().step()
        ox, oy = self.x.copy(), self.y.copy()
        super().step()
        moved = (self.x != ox) | (self.y != oy)
        bad = moved & ~self.place.standable(self.x, self.y)
        if bad.any():
            sx, sy = self.place.snap(self.x[bad], self.y[bad])
            self.x[bad], self.y[bad] = sx, sy
