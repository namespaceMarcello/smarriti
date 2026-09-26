"""A fingerprint of the engine without a place: 7 runs (the two example cases, the five
categories), each hashed. Run it before and after a change to the engine: the same lines mean
the same bits, so calibration and phases A-C do not move (docs/MISURE.md, L2a).

    python -m sim.fingerprint > before.txt   # ... change ...   python -m sim.fingerprint | diff before.txt -
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

from .case import load_case
from .categories import mixture
from .engine import Simulation, run_case

CASES = Path(__file__).resolve().parent.parent / "cases"


def digest(*arrays) -> str:
    return hashlib.sha256(np.concatenate([np.asarray(a, float) for a in arrays]).tobytes()).hexdigest()[:16]


def main() -> None:
    for name in ("esempio-gatto.json", "esempio-cane.json"):
        s = run_case(load_case(CASES / name), 72, n=3000, seed=0)
        print(f"cases/{name}", digest(s.x, s.y, s.w, s.state))
    for cat in ("cat_indoor", "cat_outdoor", "dog_friendly", "dog_wary", "dog_fearful"):
        s = Simulation(mixture(cat), 3000, 5, floor=1, hod0=20)
        s.run(100)
        print(cat, digest(s.x, s.y, s.state))


if __name__ == "__main__":
    main()
