"""The surroundings: what kind of place each cell is, and how that changes the animal.

v0: the whole plane is the zone declared in the case, optionally with circular patches
("there is a park here"). v0.1 fills the same grid from OpenStreetMap.

Every multiplier here is an unsourced estimate (docs/simulatore.md, "L'ambiente"):
the reference zone is suburban_houses = 1, the kind of place the calibration studies
come from (Huang 2018: Australia/USA; Kremer 2021: Dallas).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Zone:
    people: float  # multiplies h_pickup: more people, more chances someone picks it up
    traffic: float  # multiplies h_dead
    stay: float  # multiplies p_move: < 1 where there is cover and the animal lingers
    mobility: float  # multiplies the step length


ZONES = {
    "suburban_houses": Zone(people=1.0, traffic=1.0, stay=1.0, mobility=1.0),
    "apartment_blocks": Zone(people=1.5, traffic=1.3, stay=1.0, mobility=0.8),
    "city_center": Zone(people=2.0, traffic=1.5, stay=1.1, mobility=0.7),
    "rural": Zone(people=0.3, traffic=0.7, stay=0.9, mobility=1.5),
    "park": Zone(people=0.8, traffic=0.2, stay=0.6, mobility=1.0),
}
REFERENCE_ZONE = "suburban_houses"

# Cats living from the second floor up: the anchor (hiding place) is closer to home,
# because the cat hides in the building or at its foot. Unsourced estimate.
UPPER_FLOOR = 2
UPPER_FLOOR_ANCHOR_MULT = 0.6


@dataclass(frozen=True)
class Patch:
    zone: str
    x: float
    y: float
    radius_m: float


class Environment:
    """Per-cell multipliers; a uniform zone unless patches are given."""

    def __init__(self, zone: str = REFERENCE_ZONE, patches: list[Patch] | tuple = (), cell_m: float = 50.0):
        if zone not in ZONES:
            raise ValueError(f"unknown zone {zone!r}; known: {sorted(ZONES)}")
        for p in patches:
            if p.zone not in ZONES:
                raise ValueError(f"unknown zone {p.zone!r}; known: {sorted(ZONES)}")
        self.zone = zone
        self.patches = list(patches)
        self.cell = cell_m
        base = ZONES[zone]
        self.base = np.array([base.people, base.traffic, base.stay, base.mobility])
        if not self.patches:
            self.layers = None
            return
        xs = [p.x - p.radius_m for p in self.patches] + [p.x + p.radius_m for p in self.patches]
        ys = [p.y - p.radius_m for p in self.patches] + [p.y + p.radius_m for p in self.patches]
        self.x0 = np.floor(min(xs) / cell_m) * cell_m
        self.y0 = np.floor(min(ys) / cell_m) * cell_m
        nx = int(np.ceil((max(xs) - self.x0) / cell_m)) + 1
        ny = int(np.ceil((max(ys) - self.y0) / cell_m)) + 1
        self.layers = np.broadcast_to(self.base[:, None, None], (4, ny, nx)).copy()
        cx = self.x0 + (np.arange(nx) + 0.5) * cell_m
        cy = self.y0 + (np.arange(ny) + 0.5) * cell_m
        gx, gy = np.meshgrid(cx, cy)
        for p in self.patches:  # later patches paint over earlier ones
            z = ZONES[p.zone]
            inside = (gx - p.x) ** 2 + (gy - p.y) ** 2 <= p.radius_m**2
            for k, v in enumerate((z.people, z.traffic, z.stay, z.mobility)):
                self.layers[k][inside] = v

    @property
    def uniform(self) -> bool:
        return self.layers is None

    def at(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Multipliers (people, traffic, stay, mobility) at each position: shape (4,) or (4, n)."""
        if self.layers is None:
            return self.base
        ny, nx = self.layers.shape[1:]
        ix = np.floor((x - self.x0) / self.cell).astype(np.int64)
        iy = np.floor((y - self.y0) / self.cell).astype(np.int64)
        ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
        out = np.repeat(self.base[:, None], x.shape[0], axis=1)
        out[:, ok] = self.layers[:, iy[ok], ix[ok]]
        return out
