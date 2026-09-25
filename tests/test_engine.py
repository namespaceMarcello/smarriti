import json
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from sim.categories import get
from sim.cli import main as cli_main
from sim.engine import HOME, LOOSE, Simulation, run_case
from sim.environment import Environment, Patch
from sim.case import load_case

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "cases" / "esempio-gatto.json"
DOG = ROOT / "cases" / "esempio-cane.json"


def loose_mass_within(sim, x, y, r):
    loose = sim.state == LOOSE
    return float(sim.w[loose & ((sim.x - x) ** 2 + (sim.y - y) ** 2 <= r**2)].sum())


def test_deterministic():
    case = load_case(DOG)
    a, b = run_case(case, 48, n=2000, seed=3), run_case(case, 48, n=2000, seed=3)
    assert np.array_equal(a.x, b.x) and np.array_equal(a.w, b.w) and np.array_equal(a.state, b.state)


def test_weights_sum_to_one_and_home_ruled_out():
    sim = run_case(load_case(CAT), 37, n=3000)
    assert abs(sim.w.sum() - 1) < 1e-9
    assert sim.w[sim.state == HOME].sum() == 0


def test_park_patch_holds_animals():
    """Where the animal lingers (stay < 1) mass accumulates."""
    dog = replace(get("dog_friendly"), h_pickup=0.0, h_home=0.0, h_dead=0.0)
    plain = Simulation([(dog, 1.0)], 4000, seed=5)
    plain.run(72)
    park = Simulation([(dog, 1.0)], 4000, seed=5, env=Environment(patches=[Patch("park", 150.0, 0.0, 150.0)]))
    park.run(72)
    assert loose_mass_within(park, 150, 0, 150) > 1.2 * loose_mass_within(plain, 150, 0, 150)


def test_cli_under_ten_seconds(tmp_path):
    t = time.perf_counter()
    summary = cli_main([str(CAT), "--now", "2026-09-22T08:00", "--out", str(tmp_path)])
    assert time.perf_counter() - t < 10
    for ext in ("png", "geojson", "json"):
        assert (tmp_path / f"esempio-gatto.{ext}").stat().st_size > 0
    assert set(summary["states"]) == {"loose", "held", "home", "dead"}
    assert set(summary["advice"]) == {"search_here", "radius", "call_shelters"}
    geo = json.loads((tmp_path / "esempio-gatto.geojson").read_text(encoding="utf-8"))
    assert any(f["properties"]["kind"] == "cell" for f in geo["features"])


def test_grid_cells_centred_on_home():
    """lessons.md #11: home sits at the centre of a cell, not on a corner."""
    from sim.outputs import make_grid

    sim = run_case(load_case(CAT), 37, n=3000)
    g = make_grid(sim)
    cx, cy = g.centers()
    assert np.min(np.abs(cx)) < 1e-6 and np.min(np.abs(cy)) < 1e-6


def test_search_spots_do_not_share_mass():
    """lessons.md #12: every cell belongs to one spot only, so spot masses add up to <= P(loose)."""
    from sim.outputs import make_grid, search_spots

    sim = run_case(load_case(DOG), 40, n=5000)
    g = make_grid(sim)
    assert sum(s["mass"] for s in search_spots(g)) <= g.mass.sum() + 1e-9
