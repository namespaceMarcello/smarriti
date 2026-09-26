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
from scipy.ndimage import gaussian_filter  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

from .categories import is_night  # noqa: E402
from .engine import HELD, HOME, LOOSE, Simulation  # noqa: E402
from .case import Case  # noqa: E402

CELL_M = 50.0
PLACE_CELL_M = 4.0  # map cells when the case has a place in 3D (two world cells a side)
MAP_MASS = 0.99  # the map rectangle holds this share of the loose mass
MIN_HALF_EXTENT_M = 200.0
KDE_K = 10  # the bandwidth follows the distance to the k-th nearest loose particle
KDE_ALPHA = 1.0  # sigma = alpha * that distance (chosen with C1, docs/MISURE.md)
KDE_TRUNCATE = 4.0  # kernels are cut at 4 sigma
SIGMA_RATIO = 2 ** 0.25  # sigma classes: cell/2 * SIGMA_RATIO**j
MIN_COARSE_SIGMA = 4.0  # large sigmas are filtered on a coarser grid, at >= 4 coarse cells
GEO_LEAF_MASS = 1e-3  # a GeoJSON block is split in four while it holds more than this share
GEO_MAX_BLOCK = 64  # cells a side of the largest GeoJSON block (3.2 km)
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


def kernel_sigmas(x: np.ndarray, y: np.ndarray, cell: float = CELL_M, k: int = KDE_K,
                  alpha: float = KDE_ALPHA) -> np.ndarray:
    """Adaptive bandwidth: sigma_i = max(cell/2, alpha * distance to the k-th nearest particle)."""
    n = len(x)
    if n < 2:
        return np.full(n, cell / 2)
    pts = np.c_[x, y]
    d, _ = cKDTree(pts).query(pts, k=min(k, n - 1) + 1)
    return np.maximum(cell / 2, alpha * d[:, -1])


def _lerp_index(n_coarse: int, f: int, lo: int, hi: int, offset: int):
    """Fine cells lo..hi-1 as linear interpolation between coarse cells (f fine cells each)."""
    u = np.clip((np.arange(lo, hi) + 0.5) / f - 0.5 - offset, 0, n_coarse - 1)
    i0 = np.floor(u).astype(int)
    return i0, np.minimum(i0 + 1, n_coarse - 1), u - i0


def _level(s: float) -> int:
    """Pyramid level of a sigma (in fine cells): the coarsest grid where it spans >= MIN_COARSE_SIGMA cells."""
    return max(0, int(np.floor(np.log2(s / MIN_COARSE_SIGMA))))


def _add_class(canvas: np.ndarray, f: int, gx: np.ndarray, gy: np.ndarray, w: np.ndarray, s: float) -> None:
    """Add Gaussians of sigma s (fine cells) at fine-cell coordinates gx, gy into canvas, a
    grid f times coarser than the fine one. The filter runs only on the box that holds the
    particles plus the kernel's reach."""
    nyc, nxc = canvas.shape
    sc = s / f
    cx, cy = (gx // f).astype(int), (gy // f).astype(int)
    pad = int(KDE_TRUNCATE * sc + 0.5) + 1
    bx0, by0 = max(cx.min() - pad, 0), max(cy.min() - pad, 0)
    bx1, by1 = min(cx.max() + pad + 1, nxc), min(cy.max() + pad + 1, nyc)
    bw, bh = bx1 - bx0, by1 - by0
    hist = np.bincount((cy - by0) * bw + (cx - bx0), weights=w, minlength=bw * bh).reshape(bh, bw)
    canvas[by0:by1, bx0:bx1] += gaussian_filter(hist, sc, mode="constant", truncate=KDE_TRUNCATE)


def _upsample2(coarse: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Mass on a grid twice as fine (shape), by linear interpolation of the density."""
    x0i, x1i, tx = _lerp_index(coarse.shape[1], 2, 0, shape[1], 0)
    y0i, y1i, ty = _lerp_index(coarse.shape[0], 2, 0, shape[0], 0)
    a = coarse[:, x0i] * (1 - tx) + coarse[:, x1i] * tx
    return (a[y0i] * (1 - ty)[:, None] + a[y1i] * ty[:, None]) / 4


def _smooth(shape: tuple[int, int], gx: np.ndarray, gy: np.ndarray, w: np.ndarray, s: np.ndarray) -> np.ndarray:
    """Mass on a grid of `shape` from Gaussians of sigma s (cells) at fine-cell coordinates
    gx, gy. Each weight is split between the two classes around its sigma, keeping its variance."""
    ny, nx = shape
    if len(w) == 0:
        return np.zeros(shape)
    j = np.floor(np.log(s / 0.5) / np.log(SIGMA_RATIO) + 1e-9).astype(int)
    sa = 0.5 * SIGMA_RATIO**j
    up = np.clip((s**2 - sa**2) / (sa**2 * (SIGMA_RATIO**2 - 1)), 0.0, 1.0)
    classes = np.unique(np.concatenate([j, j + 1]))
    top = _level(0.5 * SIGMA_RATIO ** classes.max())
    shapes = [(-(-ny // 2**lv), -(-nx // 2**lv)) for lv in range(top + 1)]
    canvases = [np.zeros(sh) for sh in shapes]
    for c in classes:
        lo, hi = j == c, (j == c - 1) & (up > 0)
        cw = np.concatenate([w[lo] * (1 - up[lo]), w[hi] * up[hi]])
        if cw.sum() <= 0:
            continue
        sc = 0.5 * SIGMA_RATIO**c
        lv = _level(sc)
        _add_class(canvases[lv], 2**lv, np.concatenate([gx[lo], gx[hi]]), np.concatenate([gy[lo], gy[hi]]), cw, sc)
    for lv in range(top, 0, -1):
        canvases[lv - 1] += _upsample2(canvases[lv], shapes[lv - 1])
    return np.maximum(canvases[0], 0.0)


def make_grid(sim: Simulation, cell: float = CELL_M, alpha: float = KDE_ALPHA, k: int = KDE_K) -> Grid:
    """The map: an adaptive kernel density of the loose particles, integrated on cells.

    Every particle spreads as a Gaussian of its own sigma (kernel_sigmas), so where particles
    are sparse the mass covers the space between them instead of leaving empty cells
    (lessons.md #10). Sigmas are binned in classes SIGMA_RATIO apart; a particle's weight is
    split between the two classes around its sigma so that its variance is kept. Large
    sigmas are filtered on grids 2, 4, 8... times coarser and interpolated back, level by
    level. The rectangle holds MAP_MASS of the particles, widened by twice the median sigma;
    the kernels' mass beyond it is dropped."""
    loose = (sim.state == LOOSE) & (sim.w > 0)
    x, y, w = sim.x[loose], sim.y[loose], sim.w[loose]
    if w.sum() <= 0:
        n = int(2 * MIN_HALF_EXTENT_M / cell)
        return Grid(-MIN_HALF_EXTENT_M, -MIN_HALF_EXTENT_M, cell, np.zeros((n, n)))
    sig = kernel_sigmas(x, y, cell, k, alpha)
    tail = (1 - MAP_MASS) / 2
    margin = 2 * float(weighted_quantile(sig, w, 0.5))
    xl, xh = weighted_quantile(x, w, [tail, 1 - tail]) + [-margin, margin]
    yl, yh = weighted_quantile(y, w, [tail, 1 - tail]) + [-margin, margin]
    xl, yl = min(xl, -MIN_HALF_EXTENT_M), min(yl, -MIN_HALF_EXTENT_M)
    xh, yh = max(xh, MIN_HALF_EXTENT_M), max(yh, MIN_HALF_EXTENT_M)
    # cells are centred on home: edges at (k + 1/2) * cell
    x0, y0 = (np.floor(xl / cell - 0.5) + 0.5) * cell, (np.floor(yl / cell - 0.5) + 0.5) * cell
    x1, y1 = (np.ceil(xh / cell - 0.5) + 0.5) * cell, (np.ceil(yh / cell - 0.5) + 0.5) * cell
    nx, ny = int(round((x1 - x0) / cell)), int(round((y1 - y0) / cell))
    gx, gy = (x - x0) / cell, (y - y0) / cell
    inside = (gx >= 0) & (gx < nx) & (gy >= 0) & (gy < ny)
    return Grid(float(x0), float(y0), cell, _smooth((ny, nx), gx[inside], gy[inside], w[inside], sig[inside] / cell))


def make_place_grid(sim: Simulation, cell: float = PLACE_CELL_M) -> Grid:
    """The fine map of a case with a place: the same adaptive kernels on `cell` m cells over
    the place's square, then set to zero where the animal cannot be and rescaled to keep the
    mass the square held. The mass beyond the square is dropped (map_share_in_place)."""
    world, place = sim.place.w, sim.place
    loose = (sim.state == LOOSE) & (sim.w > 0)
    x, y, w = sim.x[loose], sim.y[loose], sim.w[loose]
    half = -world.x0
    m = int(round(2 * half / cell))
    if w.sum() <= 0:
        return Grid(-half, -half, cell, np.zeros((m, m)))
    s = kernel_sigmas(x, y, cell) / cell
    gx, gy = (x + half) / cell, (y + half) / cell
    inside = (gx >= 0) & (gx < m) & (gy >= 0) & (gy < m)
    mass = _smooth((m, m), gx[inside], gy[inside], w[inside], s[inside])
    f = int(round(cell / world.cell))
    frac = place.ok.astype(float).reshape(m, f, m, f).mean(axis=(1, 3))
    before = mass.sum()
    mass = mass * frac
    mass *= before / max(mass.sum(), 1e-300)
    return Grid(-half, -half, cell, mass)


def search_spots(grid: Grid, k: int = SPOTS) -> list[dict]:
    """Greedy peaks of the map, at least SPOT_SEPARATION_M apart; each takes the mass around it."""
    cx, cy = grid.centers()
    left = grid.mass.copy()
    r = int(np.ceil(SPOT_SEPARATION_M / grid.cell))
    spots = []
    for _ in range(k):
        iy, ix = np.unravel_index(np.argmax(left), left.shape)
        if left[iy, ix] <= 0:
            break
        ys, xs = slice(max(iy - r, 0), iy + r + 1), slice(max(ix - r, 0), ix + r + 1)
        near = (cx[xs][None, :] - cx[ix]) ** 2 + (cy[ys][:, None] - cy[iy]) ** 2 < SPOT_SEPARATION_M**2
        window = left[ys, xs]
        spots.append({"x": float(cx[ix]), "y": float(cy[iy]), "mass": float(window[near].sum())})
        window[near] = 0
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
    loose_mass = float(sim.w[sim.state == LOOSE].sum())
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
        "map_cell_m": grid.cell,
        **({"map_share_in_place": round(float(grid.mass.sum()) / loose_mass, 4) if loose_mass > 0 else None}
           if sim.place is not None else {}),
    }


def write_png(grid: Grid, sim: Simulation, case: Case, summary: dict, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 8), dpi=110)
    if sim.place is not None:  # the buildings under the map
        W = sim.place.w
        ax.imshow(np.where(W.bid >= 0, 0.8, np.nan), origin="lower", cmap="gray", vmin=0, vmax=1,
                  extent=(W.x0, -W.x0, W.x0, -W.x0), interpolation="nearest")
    m = np.ma.masked_less_equal(grid.mass, 0)
    vmax = float(grid.mass.max()) if grid.mass.max() > 0 else 1.0
    im = ax.imshow(m, origin="lower", extent=grid.extent(), cmap="magma_r", norm=PowerNorm(0.5, 0, vmax))
    fig.colorbar(im, ax=ax, shrink=0.75, label=f"P(animal is here, loose) per {grid.cell:g} m cell")
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


def map_blocks(grid: Grid, leaf_mass: float = GEO_LEAF_MASS, max_size: int = GEO_MAX_BLOCK):
    """The map as a quadtree, so that the GeoJSON stays small where the mass is spread thin:
    square blocks of 1..max_size cells a side, each split in four while it holds more than
    leaf_mass of the total. Returns iy, ix, size (in cells, clipped to the grid) and mass."""
    ny, nx = grid.mass.shape
    top = int(np.log2(max_size))
    py, px = -(-ny // max_size) * max_size, -(-nx // max_size) * max_size
    pyr = [np.zeros((py, px))]
    pyr[0][:ny, :nx] = grid.mass
    for _ in range(top):
        p = pyr[-1]
        pyr.append(p.reshape(p.shape[0] // 2, 2, p.shape[1] // 2, 2).sum(axis=(1, 3)))
    limit = leaf_mass * grid.mass.sum()
    iy, ix = [a.ravel() for a in np.indices(pyr[top].shape)]
    out = []
    for lv in range(top, -1, -1):
        m = pyr[lv][iy, ix]
        iy, ix, m = iy[m > 0], ix[m > 0], m[m > 0]
        leaf = (m <= limit) | (lv == 0)
        out.append((iy[leaf] << lv, ix[leaf] << lv, np.full(leaf.sum(), 1 << lv), m[leaf]))
        iy = (2 * iy[~leaf][:, None] + [0, 0, 1, 1]).ravel()
        ix = (2 * ix[~leaf][:, None] + [0, 1, 0, 1]).ravel()
    iy, ix, size, m = (np.concatenate(a) for a in zip(*out))
    return iy, ix, size, m


def write_geojson(grid: Grid, case: Case, summary: dict, path: Path) -> None:
    """Blocks of the quadtree (map_blocks) from the densest down, until they hold MAP_MASS of
    the mass; every block has its mass p and its side in metres."""
    proj = case.projection
    feats = []
    ny, nx = grid.mass.shape
    iy, ix, size, m = map_blocks(grid)
    h, w = np.minimum(iy + size, ny) - iy, np.minimum(ix + size, nx) - ix
    order = np.argsort(-m / (h * w))
    total = m.sum()
    kept = order[: int(np.searchsorted(np.cumsum(m[order]), MAP_MASS * total) + 1)] if total > 0 else []
    for rank, k in enumerate(kept, 1):
        x0, y0 = grid.x0 + ix[k] * grid.cell, grid.y0 + iy[k] * grid.cell
        x1, y1 = x0 + w[k] * grid.cell, y0 + h[k] * grid.cell
        lat, lon = proj.to_latlon([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0])
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[round(float(a), 7), round(float(b), 7)] for a, b in zip(lon, lat)]]},
            "properties": {"kind": "cell", "p": float(m[k]), "size_m": int(size[k] * grid.cell), "rank": rank},
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
