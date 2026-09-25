"""The simulation: thousands of virtual animals, stepped hour by hour (Monte Carlo).

Each particle has a position, a state (LOOSE, HELD, HOME, DEAD), a heading and an anchor
(its hiding place). Every request re-simulates from the moment of loss with a fixed seed:
fully deterministic.
"""
from __future__ import annotations

import copy

import numpy as np

from .categories import NUMERIC_FIELDS, Category, is_night, mixture
from .environment import UPPER_FLOOR, UPPER_FLOOR_ANCHOR_MULT, Environment
from .case import Case

LOOSE, HELD, HOME, DEAD = 0, 1, 2, 3
STATE_NAMES = ("loose", "held", "home", "dead")

COLLAR_PICKUP_MULT = 1.5  # people pick up an animal with a collar more readily
NIGHT_ACTIVITY = 0.2  # human activity at night, relative to day
HOME_DECAY_AFTER_H = 720  # the chance of returning alone fades after 30 days
HUNGER_FROM_DAY = 3
HUNGER_PER_DAY = 0.25
HUNGER_MAX = 3.0
CAT_NIGHT_HOME_MULT = 2.0


class Params:
    """Per-particle copies of the category parameters, so mixtures run in one pass."""

    def __init__(self, cats: list[Category], counts: list[int]):
        for f in NUMERIC_FIELDS:
            setattr(self, f, np.concatenate([np.full(c, getattr(cat, f), float) for cat, c in zip(cats, counts)]))
        self.is_cat = np.concatenate([np.full(c, cat.species == "cat") for cat, c in zip(cats, counts)])
        self.hunger = np.concatenate([np.full(c, cat.hunger) for cat, c in zip(cats, counts)])
        self.cat_idx = np.concatenate([np.full(c, i, np.int16) for i, c in enumerate(counts)])

def allocate(weights: list[float], n: int) -> list[int]:
    """Split n particles by weights (largest remainder), deterministically."""
    w = np.asarray(weights, float) / np.sum(weights)
    raw = w * n
    counts = np.floor(raw).astype(int)
    for i in np.argsort(-(raw - counts))[: n - counts.sum()]:
        counts[i] += 1
    return counts.tolist()


class Simulation:
    def __init__(
        self,
        mix: list[tuple[Category, float]],
        n: int = 10_000,
        seed: int = 0,
        env: Environment | None = None,
        collar: bool = False,
        floor: int = 0,
        hod0: int = 0,
    ):
        self.rng = np.random.default_rng(seed)
        self.n = n
        self.env = env or Environment()
        self.collar_mult = COLLAR_PICKUP_MULT if collar else 1.0
        self.hod0 = hod0
        self.categories = [c for c, _ in mix]
        counts = allocate([w for _, w in mix], n)
        self.par = p = Params(self.categories, counts)
        rng = self.rng

        self.t = 0
        self.x = np.zeros(n)
        self.y = np.zeros(n)
        self.state = np.zeros(n, np.int8)
        self.w = np.full(n, 1.0 / n)
        self.t_end = np.full(n, -1, np.int32)
        self.heading = rng.uniform(-np.pi, np.pi, n)

        # anchors: "random" = lognormal distance from home, "home" = home, "none" = set on settling
        kinds = np.concatenate([np.full(c, cat.anchor) for cat, c in zip(self.categories, counts)])
        med = p.anchor_med_m * np.where(p.is_cat & (floor >= UPPER_FLOOR), UPPER_FLOOR_ANCHOR_MULT, 1.0)
        r = med * np.exp(p.anchor_sigma * rng.standard_normal(n))
        a = rng.uniform(-np.pi, np.pi, n)
        rand = kinds == "random"
        self.ax = np.where(rand, r * np.cos(a), 0.0)
        self.ay = np.where(rand, r * np.sin(a), 0.0)
        self.has_anchor = kinds != "none"
        self.t_settle = np.where(p.t_settle_mean_h > 0, rng.exponential(np.maximum(p.t_settle_mean_h, 1e-9)), 0.0)
        self.settled = self.t_settle <= 0

    def hour_of_day(self, t: int) -> int:
        return (self.hod0 + t) % 24

    def normalize(self) -> None:
        s = self.w.sum()
        if not np.isfinite(s) or s <= 0:
            raise ValueError("all particle weights are zero")
        self.w /= s

    # --- one hour ------------------------------------------------------------------

    def step(self) -> None:
        p, rng, n = self.par, self.rng, self.n
        h = self.t  # every time-dependent factor uses the hour being lived: [h, h+1)
        night = is_night(self.hour_of_day(h))
        loose = self.state == LOOSE

        newly = loose & ~self.settled & (h >= self.t_settle)
        if newly.any():
            self.ax = np.where(newly, self.x, self.ax)
            self.ay = np.where(newly, self.y, self.ay)
            self.has_anchor = self.has_anchor | newly
            self.settled = self.settled | newly

        people, traffic, stay, mobility = self.env.at(self.x, self.y)

        # movement: correlated random walk with pauses and a pull towards the anchor
        p_move = (p.p_move_night if night else p.p_move_day) * stay
        moving = loose & (rng.random(n) < p_move)
        s = self.settled
        length = np.where(s, p.step_settled, p.step_flight) * mobility * np.exp(p.step_sigma * rng.standard_normal(n))
        turn = rng.vonmises(0.0, np.where(s, p.kappa_settled, p.kappa_flight), size=n)
        heading = np.where(moving, self.heading + turn, self.heading)
        nx = self.x + length * np.cos(heading)
        ny = self.y + length * np.sin(heading)
        pull = np.where(s, p.pull_settled, p.pull_flight) * self.has_anchor
        nx += pull * (self.ax - nx)
        ny += pull * (self.ay - ny)
        self.x = np.where(moving, nx, self.x)
        self.y = np.where(moving, ny, self.y)
        self.heading = heading

        # state transitions: independent hourly hazards, one draw decides
        hp = p.h_pickup * people * (NIGHT_ACTIVITY if night else 1.0) * self.collar_mult
        hunger = min(HUNGER_MAX, 1.0 + HUNGER_PER_DAY * max(0.0, h / 24 - HUNGER_FROM_DAY))
        hp = np.where(p.hunger, hp * hunger, hp)
        window = np.where(h < p.home_from_h, 0.0, np.where(h >= p.home_until_h, p.home_late_mult, 1.0))
        if h > HOME_DECAY_AFTER_H:
            window = window * np.exp(-(h - HOME_DECAY_AFTER_H) / HOME_DECAY_AFTER_H)
        hh = p.h_home * window * np.where(p.is_cat & night, CAT_NIGHT_HOME_MULT, 1.0)
        hd = p.h_dead * traffic
        u = rng.random(n)
        to_held = loose & (u < hp)
        to_home = loose & ~to_held & (u < hp + hh)
        to_dead = loose & ~to_held & ~to_home & (u < hp + hh + hd)
        self.state = self.state.copy()
        self.state[to_held] = HELD
        self.state[to_home] = HOME
        self.state[to_dead] = DEAD
        self.t = h + 1
        self.t_end = np.where(to_held | to_home | to_dead, self.t, self.t_end)

    def condition_not_home(self) -> None:
        """The owner is asking, so the animal has not come home: HOME is ruled out."""
        self.w = np.where(self.state == HOME, 0.0, self.w)
        self.normalize()

    # --- the run ---------------------------------------------------------------------------

    def run(self, until: int, record_at: np.ndarray | None = None) -> dict | None:
        """Step to hour `until`. With record_at (one hour per particle), return the
        (x, y, state) each particle had at its own hour."""
        rec = None
        if record_at is not None:
            rec = {"x": np.zeros(self.n), "y": np.zeros(self.n), "state": np.full(self.n, -1, np.int8)}
            self._record(rec, record_at)
        while self.t < until:
            self.step()
            if rec is not None:
                self._record(rec, record_at)
        return rec

    def _record(self, rec: dict, record_at: np.ndarray) -> None:
        m = record_at == self.t
        if m.any():
            rec["x"][m] = self.x[m]
            rec["y"][m] = self.y[m]
            rec["state"][m] = self.state[m]

    def fork(self) -> "Simulation":
        return copy.deepcopy(self)

    # --- summaries ------------------------------------------------------------------------------

    def state_probs(self) -> dict[str, float]:
        return {name: float(self.w[self.state == k].sum()) for k, name in enumerate(STATE_NAMES)}


def run_case(case: Case, until: int, n: int = 10_000, seed: int = 0, calibrated: bool = True) -> Simulation:
    """Simulate a case from the moment of loss to hour `until`."""
    sim = Simulation(
        mixture(case.category, calibrated), n, seed,
        env=case.environment, collar=case.collar, floor=case.floor, hod0=case.hour_of_day(0),
    )
    sim.run(until)
    sim.condition_not_home()
    return sim
