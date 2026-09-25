"""python -m sim <case.json> --now <iso> --out <dir>"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from .engine import run_case
from .case import load_case
from .outputs import make_grid, summarize, write_geojson, write_png


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(prog="python -m sim", description="Where to look for a lost animal, now.")
    ap.add_argument("case", help="case JSON (see cases/)")
    ap.add_argument("--now", required=True, help="ISO local time, e.g. 2026-09-22T08:00")
    ap.add_argument("--out", default="out", help="output directory")
    ap.add_argument("--n", type=int, default=10_000, help="particles")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    t_start = time.perf_counter()
    case = load_case(args.case)
    now = datetime.fromisoformat(args.now)
    until = case.hour_of(now)
    if until < 0:
        ap.error("--now is before the moment of loss")
    sim = run_case(case, until, args.n, args.seed)
    grid = make_grid(sim)
    summary = summarize(sim, case, now, grid)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(args.case).stem
    write_png(grid, sim, case, summary, out / f"{stem}.png")
    write_geojson(grid, case, summary, out / f"{stem}.geojson")
    summary["seconds"] = round(time.perf_counter() - t_start, 2)
    (out / f"{stem}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary
