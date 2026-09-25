"""Before / rings / now, side by side, for a person to see what the map does.

    python -m sim.compare [--out out/confronto-prima-dopo.png]

Two examples (house cat and fearful dog, 48 h after the loss). Three maps each: the old
histogram of particles, the ring model (phase C baseline), the smoothed map. On top, 40 true
animals from an independent run of the same model; the "typical area" in each title is the
geometric mean, over 2,000 true animals, of the area searched before reaching one
(docs/MISURE.md, C2 read without steps).
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

EXAMPLES = [("Gatto di casa", "cat_indoor", 700.0), ("Cane pauroso", "dog_fearful", 8000.0)]
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


def main(argv: list[str] | None = None) -> Path:
    ap = argparse.ArgumentParser(prog="python -m sim.compare")
    ap.add_argument("--out", default="out/confronto-prima-dopo.png")
    args = ap.parse_args(argv)
    fig, axes = plt.subplots(2, 3, figsize=(15, 11), dpi=100)
    for r, (title, name, half) in enumerate(EXAMPLES):
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
        vmax = (now.mass / now.cell**2).max()
        panels = [("PRIMA: particelle contate nelle celle", histogram(now, sim)),
                  ("CERCHI: il metodo classico", ring_grid(np.quantile(d, RING_Q), now.cell)),
                  ("ORA: la mappa lisciata", now)]
        for c, (label, g) in enumerate(panels):
            ax = axes[r, c]
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
            lines = [label, f"area tipica da cercare: {area_label(typical)}"]
            if hole.any():
                lines.append(f"{hole.sum()} animali su {SHOWN} dove la mappa dice «niente»")
            ax.set_title("\n".join(lines), fontsize=10, color="darkgreen" if c == 2 else "black")
            if c == 0:
                ax.set_ylabel(f"{title}, {HOURS} ore dopo\nmetri a nord di casa", fontsize=11)
    fig.suptitle("Dove cercare. Più scuro = più probabile. Stella verde = casa. Pallini = 40 animali veri "
                 "(simulati a parte).\nX rossa = animale finito dove la mappa dice «qui non c'è niente».",
                 fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print(out)
    return out


if __name__ == "__main__":
    main()
