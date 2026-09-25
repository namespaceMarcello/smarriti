"""The case: which animal, where it lives, what the place is like, when it was lost.

Coordinates: a local plane centred on home (x east, y north, metres), equirectangular.
Time: hour 0 is the moment the animal was lost; hour t is t hours later.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import numpy as np

from .environment import REFERENCE_ZONE, Environment, Patch

M_PER_DEG_LAT = 110_574.0
M_PER_DEG_LON_EQ = 111_320.0


class Projection:
    def __init__(self, lat0: float, lon0: float):
        self.lat0, self.lon0 = lat0, lon0
        self.kx = M_PER_DEG_LON_EQ * math.cos(math.radians(lat0))

    def to_xy(self, lat, lon):
        return (np.asarray(lon) - self.lon0) * self.kx, (np.asarray(lat) - self.lat0) * M_PER_DEG_LAT

    def to_latlon(self, x, y):
        return self.lat0 + np.asarray(y) / M_PER_DEG_LAT, self.lon0 + np.asarray(x) / self.kx


@dataclass
class Case:
    category: str
    home_lat: float
    home_lon: float
    lost_at: datetime
    collar: bool = False
    floor: int = 0
    environment: Environment = field(default_factory=Environment)

    @property
    def projection(self) -> Projection:
        return Projection(self.home_lat, self.home_lon)

    def hour_of(self, when: datetime) -> int:
        # half hours round up (Python's round() would send 2.5 to 2 and 3.5 to 4)
        return math.floor((when - self.lost_at).total_seconds() / 3600 + 0.5)

    def hour_of_day(self, hour: int) -> int:
        return (self.lost_at.hour + hour + (1 if self.lost_at.minute >= 30 else 0)) % 24


def parse_case(data: dict) -> Case:
    home = data["home"]
    proj = Projection(home["lat"], home["lon"])
    area = data.get("area", {})
    patches = []
    for p in area.get("patches", []):
        px, py = proj.to_xy(p["center"]["lat"], p["center"]["lon"])
        patches.append(Patch(p["zone"], float(px), float(py), float(p["radius_m"])))
    return Case(
        category=data["category"],
        home_lat=home["lat"],
        home_lon=home["lon"],
        lost_at=datetime.fromisoformat(data["lost_at"]),
        collar=bool(data.get("collar", False)),
        floor=int(area.get("floor", 0)),
        environment=Environment(area.get("zone", REFERENCE_ZONE), patches),
    )


def load_case(path: str | Path) -> Case:
    return parse_case(json.loads(Path(path).read_text(encoding="utf-8")))
