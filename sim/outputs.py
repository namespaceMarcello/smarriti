"""What the simulation says: the map (grid, PNG, GeoJSON), the states, the advice."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import PowerNorm  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

from .categories import is_night  # noqa: E402
from .engine import HELD, HOME, LOOSE, Simulation  # noqa: E402
from .case import Case  # noqa: E402

CELL_M = 50.0
MAP_MASS = 0.99  # the map rectangle holds this share of the loose mass
MIN_HALF_EXTENT_M = 200.0
SPOTS = 5
SPOT_SEPARATION_M = 150.0
CALL_THRESHOLD = 0.3  # P(HELD) above which shelters and vets should be called (to calibrate)
CALL_EXTRA_M = 10_000.0  # people carry a found animal by car
FORECAST_H = 168


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q) -> np.ndarray:
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w)
    cw /= cw[-1]
    return np.interp(q, cw, v)


@dataclass
class Grid:
    x0: float  # west edge (m)
    y0: float  # south edge (m)
    cell: float
    mass: np.ndarray  # [ny, nx], probability that the animal is loose in the cell

    def centers(self):
        ny, nx = self.mass.shape
        return self.x0 + (np.arange(nx) + 0.5) * self.cell, self.y0 + (np.arange(ny) + 0.5) * self.cell

    def extent(self):
        ny, nx = self.mass.shape
        return (self.x0, self.x0 + nx * self.cell, self.y0, self.y0 + ny * self.cell)


def make_grid(sim: Simulation, cell: float = CELL_M) -> Grid:
    loose = sim.state == LOOSE
    x, y, w = sim.x[loose], sim.y[loose], sim.w[loose]
    if w.sum() <= 0:
        n = int(2 * MIN_HALF_EXTENT_M / cell)
        return Grid(-MIN_HALF_EXTENT_M, -MIN_HALF_EXTENT_M, cell, np.zeros((n, n)))
    tail = (1 - MAP_MASS) / 2
    xl, xh = weighted_quantile(x, w, [tail, 1 - tail])
    yl, yh = weighted_quantile(y, w, [tail, 1 - tail])
    xl, yl = min(xl, -MIN_HALF_EXTENT_M), min(yl, -MIN_HALF_EXTENT_M)
    xh, yh = max(xh, MIN_HALF_EXTENT_M), max(yh, MIN_HALF_EXTENT_M)
    # cells are centred on home: edges at (k + 1/2) * cell
    x0, y0 = (np.floor(xl / cell - 0.5) + 0.5) * cell, (np.floor(yl / cell - 0.5) + 0.5) * cell
    x1, y1 = (np.ceil(xh / cell - 0.5) + 0.5) * cell, (np.ceil(yh / cell - 0.5) + 0.5) * cell
    xe = np.arange(x0, x1 + cell / 2, cell)
    ye = np.arange(y0, y1 + cell / 2, cell)
    mass, _, _ = np.histogram2d(y, x, bins=[ye, xe], weights=w)
    return Grid(float(x0), float(y0), cell, mass)


def search_spots(grid: Grid, k: int = SPOTS) -> list[dict]:
    """Greedy peaks of the map, at least SPOT_SEPARATION_M apart; each takes the mass around it."""
    cx, cy = grid.centers()
    gx, gy = np.meshgrid(cx, cy)
    left = grid.mass.copy()
    spots = []
    for _ in range(k):
        i = np.unravel_index(np.argmax(left), left.shape)
        if left[i] <= 0:
            break
        sx, sy = gx[i], gy[i]
        near = (gx - sx) ** 2 + (gy - sy) ** 2 < SPOT_SEPARATION_M**2
        spots.append({"x": float(sx), "y": float(sy), "mass": float(left[near].sum())})
        left[near] = 0
    return spots


def next_window(now: datetime, species: str) -> tuple[datetime, str]:
    """When to go: cats at dusk and night, dogs by day (quiet early morning)."""
    if species == "cat":
        if is_night(now.hour):
            return now, "now: cats move at night"
        start = now.replace(hour=20, minute=0, second=0, microsecond=0)
        return start, "at dusk: cats hide by day and move at night"
    if not is_night(now.hour):
        return now, "now: dogs move by day"
    start = now.replace(hour=6, minute=0, second=0, microsecond=0)
    if start < now:
        start += timedelta(days=1)
    return start, "at first light: quiet streets, dogs start moving"


def distance_radii(sim: Simulation) -> dict:
    loose = sim.state == LOOSE
    w = sim.w[loose]
    if w.sum() <= 0:
        return {"r50_m": None, "r90_m": None}
    d = np.hypot(sim.x[loose], sim.y[loose])
    r50, r90 = weighted_quantile(d, w, [0.5, 0.9])
    return {"r50_m": round(float(r50)), "r90_m": round(float(r90))}


def call_advice(sim: Simulation, p_held: float) -> dict:
    held = sim.state == HELD
    out = {"call": bool(p_held > CALL_THRESHOLD), "p_held": round(p_held, 3), "threshold": CALL_THRESHOLD}
    if held.any() and sim.w[held].sum() > 0:
        d = np.hypot(sim.x[held], sim.y[held])
        p95 = float(weighted_quantile(d, sim.w[held], 0.95))
        out["radius_km"] = round((p95 + CALL_EXTRA_M) / 1000, 1)
        out["pickup_p95_m"] = round(p95)
    return out


def forecast_home(sim: Simulation, hours: int = FORECAST_H) -> float:
    """P(the animal comes home by itself within `hours`), from the current particles."""
    f = sim.fork()
    was_loose = f.state == LOOSE
    f.run(f.t + hours)
    return float(f.w[was_loose & (f.state == HOME)].sum())


def summarize(sim: Simulation, case: Case, now: datetime, grid: Grid) -> dict:
    proj = case.projection
    probs = sim.state_probs()
    species = sim.categories[0].species
    when, why = next_window(now, species)
    spots = []
    for s in search_spots(grid):
        lat, lon = proj.to_latlon(s["x"], s["y"])
        spots.append({
            "lat": round(float(lat), 6), "lon": round(float(lon), 6),
            "from_home_m": round(float(np.hypot(s["x"], s["y"]))),
            "p": round(s["mass"], 4),
            "when": when.isoformat(timespec="minutes"),
        })
    return {
        "category": case.category,
        "lost_at": case.lost_at.isoformat(timespec="minutes"),
        "now": now.isoformat(timespec="minutes"),
        "hours_lost": sim.t,
        "states": {k: round(v, 4) for k, v in probs.items()},
        "p_home_within_7d": round(forecast_home(sim), 4),
        "advice": {
            "search_here": {"why": why, "spots": spots},
            "radius": distance_radii(sim),
            "call_shelters": call_advice(sim, probs["held"]),
        },
    }


def write_png(grid: Grid, sim: Simulation, case: Case, summary: dict, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 8), dpi=110)
    m = np.ma.masked_less_equal(grid.mass, 0)
    vmax = float(grid.mass.max()) if grid.mass.max() > 0 else 1.0
    im = ax.imshow(m, origin="lower", extent=grid.extent(), cmap="magma_r", norm=PowerNorm(0.5, 0, vmax))
    fig.colorbar(im, ax=ax, shrink=0.75, label="P(animal is here, loose) per 50 m cell")
    for p in case.environment.patches:
        ax.add_patch(Circle((p.x, p.y), p.radius_m, fill=False, edgecolor="tab:olive", linewidth=1))
        ax.annotate(p.zone, (p.x, p.y), color="tab:olive", ha="center", fontsize=8)
    for i, s in enumerate(search_spots(grid), 1):
        ax.annotate(str(i), (s["x"], s["y"]), color="white", ha="center", va="center", fontsize=9,
                    fontweight="bold", bbox=dict(boxstyle="circle,pad=0.2", fc="tab:blue", ec="none"))
    ax.plot(0, 0, marker="*", color="tab:cyan", markersize=16, markeredgecolor="black")
    st = summary["states"]
    ax.set_title(
        f"{case.category} - {summary['hours_lost']} h after loss ({summary['now']})\n"
        f"loose {st['loose']:.0%} · held {st['held']:.0%} · dead {st['dead']:.0%} · "
        f"home within 7 d {summary['p_home_within_7d']:.0%}", fontsize=10)
    ax.set_xlabel("metres east of home")
    ax.set_ylabel("metres north of home")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def write_geojson(grid: Grid, case: Case, summary: dict, path: Path) -> None:
    proj = case.projection
    feats = []
    ny, nx = grid.mass.shape
    flat = grid.mass.ravel()
    order = np.argsort(-flat)
    total = flat.sum()
    kept = order[: int(np.searchsorted(np.cumsum(flat[order]), MAP_MASS * total) + 1)] if total > 0 else []
    for rank, k in enumerate(kept, 1):
        if flat[k] <= 0:
            break
        iy, ix = divmod(int(k), nx)
        x0, y0 = grid.x0 + ix * grid.cell, grid.y0 + iy * grid.cell
        xs = [x0, x0 + grid.cell, x0 + grid.cell, x0, x0]
        ys = [y0, y0, y0 + grid.cell, y0 + grid.cell, y0]
        lat, lon = proj.to_latlon(xs, ys)
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[round(float(a), 7), round(float(b), 7)] for a, b in zip(lon, lat)]]},
            "properties": {"kind": "cell", "p": float(flat[k]), "rank": rank},
        })
    points = [("home", case.home_lat, case.home_lon, {})]
    for i, s in enumerate(summary["advice"]["search_here"]["spots"], 1):
        points.append(("search_here", s["lat"], s["lon"], {"rank": i, "p": s["p"], "when": s["when"]}))
    for kind, lat, lon, props in points:
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(lon, 7), round(lat, 7)]},
            "properties": {"kind": kind, **props},
        })
    path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}), encoding="utf-8")
