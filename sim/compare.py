"""Before / rings / now, side by side, for a person to see what the map does.

    python -m sim.compare [--out out/confronto-prima-dopo.png]
    python -m sim.compare --readme docs/img/where-to-search.png

Two examples (house cat and fearful dog, 48 h after the loss). Three maps each: the old
histogram of particles, the ring model (phase C baseline), the smoothed map; with --readme,
the README's figure: the rings and the map only, in English. On top, 40 true animals from an
independent run of the same model; the "typical area" in each title is the geometric mean,
over 2,000 true animals, of the area searched before reaching one (docs/MISURE.md, C2 read
without steps).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402

from .baseline import RING_Q, grid_scores, ring_grid  # noqa: E402
from .calibrate import HOD0  # noqa: E402
from .categories import get  # noqa: E402
from .engine import LOOSE, Simulation  # noqa: E402
from .outputs import Grid, make_grid  # noqa: E402

EXAMPLES = [("Gatto di casa", "Indoor cat", "cat_indoor", 700.0),
            ("Cane pauroso", "Fearful dog", "dog_fearful", 8000.0)]
HOURS = 48
SHOWN = 40


def histogram(like: Grid, sim: Simulation) -> Grid:
    """The map as it was before the smoothing: particles counted in cells."""
    loose = sim.state == LOOSE
    ny, nx = like.mass.shape
    xe = like.x0 + np.arange(nx + 1) * like.cell
    ye = like.y0 + np.arange(ny + 1) * like.cell
    m, _, _ = np.histogram2d(sim.y[loose], sim.x[loose], bins=[ye, xe], weights=sim.w[loose])
    return Grid(like.x0, like.y0, like.cell, m)


def at(g: Grid, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    ny, nx = g.mass.shape
    ix = np.floor((x - g.x0) / g.cell).astype(int)
    iy = np.floor((y - g.y0) / g.cell).astype(int)
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    v = np.zeros(len(x))
    v[ok] = g.mass[iy[ok], ix[ok]]
    return v


def area_label(ha: float) -> str:
    return f"{ha:.1f} ettari".replace(".", ",") if ha < 100 else f"{ha / 100:.1f} km²".replace(".", ",")


def area_en(ha: float) -> str:
    return f"{ha:.1f} ha" if ha < 100 else f"{ha / 100:.1f} km²"


def example(name: str) -> tuple:
    """One example 48 h after the loss: the simulation, its map, the rings drawn from its own
    distances, 2,000 true animals from an independent run, and the radius for truths off the map."""
    sim = Simulation([(get(name), 1.0)], 5000, 1, hod0=HOD0)
    sim.run(HOURS)
    sim.condition_not_home()
    truth = Simulation([(get(name), 1.0)], 6000, 99, hod0=HOD0)
    truth.run(HOURS)
    loose = truth.state == LOOSE
    tx, ty = truth.x[loose][:2000], truth.y[loose][:2000]
    d = np.hypot(sim.x[sim.state == LOOSE], sim.y[sim.state == LOOSE])
    r_out = max(2 * np.quantile(d, 0.99), 1.1 * float(np.max(np.hypot(tx, ty))))
    now = make_grid(sim)
    return sim, now, ring_grid(np.quantile(d, RING_Q), now.cell), tx, ty, r_out


def draw(ax, g: Grid, vmax: float, tx: np.ndarray, ty: np.ndarray, r_out: float, half: float) -> tuple[float, int]:
    """One map with the first SHOWN true animals on top. Returns the typical area (ha) and how
    many of the shown animals are where the map says nothing (red crosses)."""
    ny, nx = g.mass.shape
    ext = (g.x0, g.x0 + nx * g.cell, g.y0, g.y0 + ny * g.cell)
    ax.imshow(np.ma.masked_less_equal(g.mass / g.cell**2, 0), origin="lower", extent=ext,
              cmap="magma_r", norm=LogNorm(vmax / 3e3, vmax), interpolation="nearest")
    typical = float(np.exp(np.mean(np.log(grid_scores(g, tx, ty, r_out)["area_ha"]))))
    sx, sy = tx[:SHOWN], ty[:SHOWN]
    hole = at(g, sx, sy) <= 0
    ax.scatter(sx[~hole], sy[~hole], s=28, c="deepskyblue", edgecolors="black", linewidths=0.6, zorder=3)
    ax.scatter(sx[hole], sy[hole], s=44, c="red", marker="X", edgecolors="black", linewidths=0.5, zorder=4)
    ax.plot(0, 0, marker="*", color="lime", markersize=15, markeredgecolor="black", zorder=5)
    ax.set_xlim(-half, half)
    ax.set_ylim(-half, half)
    ax.set_aspect("equal")
    ax.tick_params(labelsize=8)
    return typical, int(hole.sum())


def before_after(out: Path) -> None:
    """Marcello's picture, in Italian: before / rings / now."""
    fig, axes = plt.subplots(2, 3, figsize=(15, 11), dpi=100)
    for r, (title, _, name, half) in enumerate(EXAMPLES):
        sim, now, rings, tx, ty, r_out = example(name)
        vmax = (now.mass / now.cell**2).max()
        panels = [("PRIMA: particelle contate nelle celle", histogram(now, sim)),
                  ("CERCHI: il metodo classico", rings),
                  ("ORA: la mappa lisciata", now)]
        for c, (label, g) in enumerate(panels):
            ax = axes[r, c]
            typical, holes = draw(ax, g, vmax, tx, ty, r_out, half)
            lines = [label, f"area tipica da cercare: {area_label(typical)}"]
            if holes:
                lines.append(f"{holes} animali su {SHOWN} dove la mappa dice «niente»")
            ax.set_title("\n".join(lines), fontsize=10, color="darkgreen" if c == 2 else "black")
            if c == 0:
                ax.set_ylabel(f"{title}, {HOURS} ore dopo\nmetri a nord di casa", fontsize=11)
    fig.suptitle("Dove cercare. Più scuro = più probabile. Stella verde = casa. Pallini = 40 animali veri "
                 "(simulati a parte).\nX rossa = animale finito dove la mappa dice «qui non c'è niente».",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(out)
    plt.close(fig)


def readme(out: Path) -> None:
    """The README's figure, in English: the rings and the map, cat and dog."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 10.4), dpi=100, layout="constrained")
    for r, (_, label, name, half) in enumerate(EXAMPLES):
        _, now, rings, tx, ty, r_out = example(name)
        vmax = (now.mass / now.cell**2).max()
        for c, (model, g, color) in enumerate((("Rings, the classic method", rings, "black"),
                                               ("Smarriti", now, "darkgreen"))):
            typical, _ = draw(axes[r, c], g, vmax, tx, ty, r_out, half)
            axes[r, c].set_title(f"{model}\ntypical area to search: {area_en(typical)}", fontsize=11, color=color)
        axes[r, 0].set_ylabel(f"{label}, {HOURS} h after the loss\nmetres north of home", fontsize=11)
    for ax in axes[-1]:
        ax.set_xlabel("metres east of home", fontsize=9)
    fig.suptitle("Where to search. Darker = more likely. Green star = home.\n"
                 f"Dots = {SHOWN} true animals, simulated separately.", fontsize=11)
    fig.savefig(out, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


def main(argv: list[str] | None = None) -> Path:
    ap = argparse.ArgumentParser(prog="python -m sim.compare")
    ap.add_argument("--out", default="out/confronto-prima-dopo.png")
    ap.add_argument("--readme", metavar="PNG", help="write the README's figure here instead")
    args = ap.parse_args(argv)
    out = Path(args.readme or args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    (readme if args.readme else before_after)(out)
    print(out)
    return out


if __name__ == "__main__":
    main()
