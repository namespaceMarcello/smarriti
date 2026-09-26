"""The simulation: thousands of virtual animals, stepped hour by hour (Monte Carlo).

Each particle has a position, a state (LOOSE, HELD, HOME, DEAD), a heading and an anchor
(its hiding place). Every request re-simulates from the moment of loss with a fixed seed:
fully deterministic. With a place (sim/place.py) the cats' anchors take their direction from
it, no step ends where an animal cannot stand, and cats stay longer where they like to be;
without one, nothing changes.
"""
from __future__ import annotations

import copy

import numpy as np

from .categories import NUMERIC_FIELDS, Category, is_night, mixture
from .environment import UPPER_FLOOR, UPPER_FLOOR_ANCHOR_MULT, Environment
from .case import Case
from .place import Place, World

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
        place: Place | None = None,
        place_seed: int | None = None,
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
        self.place, self.sel_ref = None, None
        if place is not None:
            self._attach(place, seed + 7 if place_seed is None else place_seed)

    def _attach(self, place: Place, place_seed: int) -> None:
        """The place picks the direction of each cat's anchor at the distance already drawn;
        everyone starts at the door. A separate stream: the engine's draws stay paired."""
        self.place = place
        rng = np.random.default_rng(place_seed)
        rand = self.par.is_cat & self.has_anchor & ((self.ax != 0) | (self.ay != 0))
        if place.par.step_selection:
            # the mean sel where cats would be without the place (anchors in a random direction):
            # dividing by it keeps the mean p_move, so the distances stay A5's
            s = place.sel_at(self.ax[rand], self.ay[rand])
            self.sel_ref = float(np.nanmean(s)) if np.isfinite(s).any() else None
        ax, ay = place.sample_anchor(np.hypot(self.ax, self.ay)[rand], rng)
        keep = np.isnan(ax)  # ring without weight or off the grid: the random direction stays
        self.ax[rand] = np.where(keep, self.ax[rand], ax)
        self.ay[rand] = np.where(keep, self.ay[rand], ay)
        self.fallback = float(keep.mean()) if len(keep) else 0.0
        self.x[:], self.y[:] = place.start_point()
        self.left = np.zeros(self.n, bool)  # the door is where it fled from, not a place it chose
        self.place_rng = rng  # redrawn steps use it, so the engine's draws stay paired

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
        if self.sel_ref is not None:  # time spent in a type of place goes with its sel
            s = self.place.sel_at(self.x, self.y)
            chose = p.is_cat & self.left & np.isfinite(s)
            p_move = np.minimum(1.0, p_move * np.where(chose, self.sel_ref / s, 1.0))
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
        x0, y0, h0 = self.x, self.y, self.heading
        self.x = np.where(moving, nx, self.x)
        self.y = np.where(moving, ny, self.y)
        self.heading = heading
        if self.place is not None:
            self.left |= moving
            self._fit_steps(moving, x0, y0, h0, np.broadcast_to(mobility, n))

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

    def _fit_steps(self, moving, x0, y0, h0, mobility) -> None:
        """An hourly step is a path, only its end counts: a step that ends where the animal
        cannot be is drawn again from the same point (the place's own stream, up to `redraw`
        times, the same rule as the first draw); one still inside ends on the nearest free
        cell (lessons.md #33)."""
        p, place = self.par, self.place
        bad = moving & ~place.standable(self.x, self.y)
        for _ in range(place.par.redraw):
            k = np.flatnonzero(bad)
            if len(k) == 0:
                return
            s, rng = self.settled[k], self.place_rng
            length = np.where(s, p.step_settled[k], p.step_flight[k]) * mobility[k] * np.exp(p.step_sigma[k] * rng.standard_normal(len(k)))
            heading = h0[k] + rng.vonmises(0.0, np.where(s, p.kappa_settled[k], p.kappa_flight[k]))
            nx = x0[k] + length * np.cos(heading)
            ny = y0[k] + length * np.sin(heading)
            pull = np.where(s, p.pull_settled[k], p.pull_flight[k]) * self.has_anchor[k]
            self.x[k] = nx + pull * (self.ax[k] - nx)
            self.y[k] = ny + pull * (self.ay[k] - ny)
            self.heading[k] = heading
            bad[k] = ~place.standable(self.x[k], self.y[k])
        if bad.any():
            self.x[bad], self.y[bad] = place.snap(self.x[bad], self.y[bad])

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
        place, self.place = self.place, None  # the place is read-only: shared, not copied
        try:
            twin = copy.deepcopy(self)
        finally:
            self.place = place
        twin.place = place
        return twin

    # --- summaries ------------------------------------------------------------------------------

    def state_probs(self) -> dict[str, float]:
        return {name: float(self.w[self.state == k].sum()) for k, name in enumerate(STATE_NAMES)}


def run_case(case: Case, until: int, n: int = 10_000, seed: int = 0, calibrated: bool = True) -> Simulation:
    """Simulate a case from the moment of loss to hour `until`."""
    sim = Simulation(
        mixture(case.category, calibrated), n, seed,
        env=case.environment, collar=case.collar, floor=case.floor, hod0=case.hour_of_day(0),
        place=load_case_place(case),
    )
    sim.run(until)
    sim.condition_not_home()
    return sim


def load_case_place(case: Case) -> Place | None:
    """The case's place, if it has one; its world must be centred on the case's home."""
    if case.place is None:
        return None
    world = World(case.place)
    lat0, lon0 = world.meta["lat0"], world.meta["lon0"]
    dx, dy = case.projection.to_xy(lat0, lon0)
    if np.hypot(dx, dy) > 1.0:
        raise ValueError(f"the place {case.place} is not centred on the case's home ({np.hypot(dx, dy):.0f} m off)")
    return Place(world, case.floor, case.place_heights)
