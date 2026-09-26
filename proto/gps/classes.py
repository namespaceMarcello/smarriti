"""The map as a forecast (docs/MISURE.md L13): the proper log score S of the real fixes against
the radial map (docs/matematica.md, Gibbs) for maps constant on classes of cells. The map lives
in the true position and is blurred by the GPS error (a Gaussian of sigma m) before the fixes
are scored, so the error sits inside the score, not in the map. The classes join the buildings,
by OSM type and footprint (the tags of the OSM answer each world was built from), to the
distance from the nearest building and the surface outside.

    python -m proto.gps.classes build <data_dir>    # <data_dir>/classes.npz; prints what is available, no real fix
    python -m proto.gps.classes inside <data_dir>   # real / available by building type and area, by country
    python -m proto.gps.classes fit <data_dir>      # S in sample and one country out (the rule of L13)
    python -m proto.gps.classes pieces <data_dir>   # the same for the candidate taken apart, sigma to 40 m
    python -m proto.gps.classes test <data_dir> --test <data_dir2> [--scheme inside11+bands5] [--sigma 20]

<data_dir> as proto/gps/score.py: index.csv, cats/<id>/{world.npz, fixes.csv}, osm_cache/.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import ndimage, optimize

from proto.gps import score
from proto.gps.build_cats import build_world, safe_name
from proto.gps.pieces import dist_class
from proto.gps.score import R_MAX, R_MIN, RING_M, read_fixes
from sim.place import World

GROUPS = {  # OSM building=* -> group; any other value is "other"
    "dwelling": ("house", "detached", "semidetached_house", "semi", "terrace", "residential", "apartments",
                 "bungalow", "dormitory", "static_caravan", "cabin", "farm", "townhouse"),
    "garage": ("garage", "garages", "carport"),
    "shed": ("shed", "hut", "barn", "farm_auxiliary", "greenhouse", "glasshouse", "outbuilding", "stable",
             "boathouse", "kennel", "allotment_house", "sty", "cowshed", "summer_house"),
    "yes": ("yes",),
}
GROUP_NAMES = (*GROUPS, "other")
SMALL_M2 = 40.0  # footprint, m2
BANDS = ("0-3", "3-6", "6-12", "12-24", ">24")  # m from the nearest building (pieces.DIST_BINS)
SURFACES = ("street", "garden", "veg", "open")
FINE = (("home",) + tuple(f"{g} {s}" for g in GROUP_NAMES for s in ("<40", ">=40"))
        + tuple(f"{b} {s}" for b in BANDS for s in SURFACES))
N_IN = 1 + 2 * len(GROUP_NAMES)  # fine classes 0..N_IN-1 are inside a building
SOURCES = ("outside", "home", "microsoft", "named source", "no source")  # where the footprint comes from
SIGNED = ("in >8", "in 4-8", "in 2-4", "in <=2", "out <=2", "out 2-4", "out 4-8", "out 8-16", "out 16-32", "out >32")
PER_CAT = ("lab", "ring", "phi", "abar", "signed", "signed_abar", "source", "source_abar")
K_MAX = int(R_MAX / RING_M) + 2  # rings kept: the cell of every kept fix is in one of them
SIGMAS = (0.0, 5.0, 10.0, 15.0, 20.0, 30.0, 40.0)  # the rule of L13 chooses among the first five


def group_of(tags: dict) -> int:
    v = str(tags.get("building", "")).strip().lower()
    return next((i for i, g in enumerate(GROUPS.values()) if v in g), len(GROUPS))


def polygon_area(xy: np.ndarray) -> float:
    x, y = xy[:, 0], xy[:, 1]
    return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2)


def buildings_of(world: World, osm: dict) -> list:
    """(tags, footprint m2) of every building of the world, in bid order: the OSM answer painted
    again as build_cats.build_world painted it, and the bid grid must come out identical."""
    blds = []
    layers, _, nb = build_world(world.meta["lat0"], world.meta["lon0"], osm, blds)
    if nb != world.meta["osm_buildings"] or not np.array_equal(layers["bid"], world.bid):
        raise ValueError("the OSM answer does not paint the world's buildings again")
    return [(tags, polygon_area(xy)) for tags, xy in blds]


def fine_labels(world: World, blds: list) -> np.ndarray:
    """The class of FINE of every cell."""
    bld = world.bid >= 0
    lab = np.zeros(world.bid.shape, np.int16)
    if blds:
        per_bld = 1 + 2 * np.array([group_of(t) for t, _ in blds]) + np.array([a >= SMALL_M2 for _, a in blds])
        lab[bld] = per_bld[world.bid[bld]]
    lab[world.bid == world.bid_home] = 0
    surf = np.full(world.bid.shape, SURFACES.index("open"), np.int16)
    surf[np.isin(world.cover, (10, 20, 30, 40)) | (world.green == 2)] = SURFACES.index("veg")
    surf[world.green == 1] = SURFACES.index("garden")
    surf[world.road >= 2] = SURFACES.index("street")
    band = dist_class(world).astype(np.int16)  # 0 inside, 1..5 outside
    out = ~bld
    lab[out] = N_IN + len(SURFACES) * (band[out] - 1) + surf[out]
    return lab


def source_labels(world: World, blds: list) -> np.ndarray:
    """SOURCES of every cell: the OSM source tag of the building it is in."""
    lab = np.zeros(world.bid.shape, np.int16)
    bld = world.bid >= 0
    if blds:
        s = [str(t.get("source", "")).lower() for t, _ in blds]
        per_bld = np.array([2 if "microsoft" in v else (3 if v else 4) for v in s], np.int16)
        lab[bld] = per_bld[world.bid[bld]]
    lab[world.bid == world.bid_home] = 1
    return lab


def signed_labels(world: World) -> np.ndarray:
    """Distance to the nearest wall, inside and outside (SIGNED), for the profile across the walls."""
    bld = world.bid >= 0
    din = ndimage.distance_transform_edt(bld) * world.cell
    dout = ndimage.distance_transform_edt(~bld) * world.cell
    lab_in = 3 - np.searchsorted((2.0, 4.0, 8.0), din, "left")  # <=2 -> 3, 2-4 -> 2, 4-8 -> 1, >8 -> 0
    lab_out = 4 + np.searchsorted((2.0, 4.0, 8.0, 16.0, 32.0), dout, "left")
    return np.where(bld, np.clip(lab_in, 0, 3), lab_out).astype(np.int16)


def ring_means(k: np.ndarray, layers: np.ndarray) -> np.ndarray:
    """Mean of every layer (C x n x n) over the cells of every ring 0..K_MAX: (K_MAX + 1) x C."""
    kk = np.minimum(k.ravel(), K_MAX + 1)
    cnt = np.bincount(kk, minlength=K_MAX + 2)[:K_MAX + 1]
    return np.stack([np.bincount(kk, L.ravel(), minlength=K_MAX + 2)[:K_MAX + 1] for L in layers], 1) / np.maximum(cnt, 1)[:, None]


def cat_table(world: World, blds: list, x: np.ndarray, y: np.ndarray, sigmas=SIGMAS) -> dict:
    """For the real fixes (x, y), already kept: the fine class and ring of the fix cell, the
    blurred class indicators there (per sigma), and the ring means of the same (per sigma)."""
    lab = fine_labels(world, blds)
    iy, ix, _ = world.index(x, y)
    k_cell = (world.d / RING_M).astype(np.int64)
    ind = np.stack([(lab == c).astype(np.float64) for c in range(len(FINE))])
    phi, abar = [], []
    for s in sigmas:
        L = ind if s == 0 else np.stack([ndimage.gaussian_filter(I, s / world.cell) for I in ind])
        phi.append(L[:, iy, ix].T.astype(np.float32))
        abar.append(ring_means(k_cell, L).astype(np.float32))
    sl = signed_labels(world)
    sind = np.stack([(sl == c).astype(np.float64) for c in range(len(SIGNED))])
    so = source_labels(world, blds)
    soind = np.stack([(so == c).astype(np.float64) for c in range(len(SOURCES))])
    return {"lab": lab[iy, ix], "ring": k_cell[iy, ix].astype(np.int16), "phi": np.stack(phi), "abar": np.stack(abar),
            "signed": sl[iy, ix], "signed_abar": ring_means(k_cell, sind).astype(np.float32),
            "source": so[iy, ix], "source_abar": ring_means(k_cell, soind).astype(np.float32)}


def build(data: Path, households_m: float) -> None:
    dirs = score.built_cats(data)
    with open(data / "index.csv", newline="", encoding="utf-8") as f:
        dataset_of = {r["cat_id"]: r["dataset"].split()[0] for r in csv.DictReader(f)}
    hh = score.households(score.read_homes(data, dirs), households_m)
    out = {k: [] for k in ("cat", *PER_CAT)}
    meta, tags_by_country, source_by_country = [], {}, {}
    for cid, d in dirs.items():
        world = World(d / "world.npz")
        x, y = read_fixes(d / "fixes.csv")
        r = np.hypot(x, y)
        keep = (r > R_MIN) & (r <= R_MAX)
        if keep.sum() < 20:
            continue
        osm = json.loads((data / "osm_cache" / f"{safe_name(cid)}.json").read_text(encoding="utf-8"))
        blds = buildings_of(world, osm)
        t = cat_table(world, blds, x[keep], y[keep])
        i = len(meta)
        for k in PER_CAT:
            out[k].append(t[k])
        out["cat"].append(np.full(int(keep.sum()), i, np.int32))
        country = dataset_of[cid]
        meta.append({"cat_id": cid, "country": country, "household": hh[cid], "n_fixes": int(keep.sum())})
        near = world.d <= R_MAX  # what the cat had around it, not where it went
        seen = set(np.unique(world.bid[near & (world.bid >= 0)]).tolist())
        for b in seen:
            tags, area = blds[b]
            tags_by_country.setdefault(country, Counter())[(GROUP_NAMES[group_of(tags)], area >= SMALL_M2)] += 1
            source_by_country.setdefault(country, Counter())[str(tags.get("source", "-"))[:40]] += 1
        print(cid, country, int(keep.sum()), len(blds), flush=True)
    np.savez_compressed(
        data / "classes.npz", meta=json.dumps({"fine": FINE, "signed": SIGNED, "sources": SOURCES, "sigmas": SIGMAS, "cats": meta,
                                              "households_m": households_m, "k_max": K_MAX}),
        cat=np.concatenate(out["cat"]), lab=np.concatenate(out["lab"]), ring=np.concatenate(out["ring"]),
        phi=np.concatenate(out["phi"], axis=1), abar=np.stack(out["abar"]),
        signed=np.concatenate(out["signed"]), signed_abar=np.stack(out["signed_abar"]),
        source=np.concatenate(out["source"]), source_abar=np.stack(out["source_abar"]))
    print(f"\n{len(meta)} cats, {sum(m['n_fixes'] for m in meta)} fixes -> {data / 'classes.npz'}")
    for c in sorted(tags_by_country):
        n = sum(tags_by_country[c].values())
        print(f"\n{c}: {n} buildings within {R_MAX:g} m of the homes (a building near two homes counts twice)")
        print("  ", {f"{g} {'>=' if big else '<'}40": round(v / n, 3) for (g, big), v in sorted(tags_by_country[c].items())})
        print("   source:", {k: round(v / n, 3) for k, v in source_by_country[c].most_common(6)})
    available(Table(data))


def available(T: "Table") -> None:
    """The available share of every fine class, per country, at the rings of the real fixes: where
    the fixes fell is not read."""
    s0 = T.sigmas.index(0.0)
    for country in sorted(set(T.country)):
        idx = np.flatnonzero(T.country == country)
        a = np.mean([T.abar[i, s0][T.ring[T.cat == i]].mean(axis=0) for i in idx], axis=0)
        print(f"\n{country} available:", {FINE[c]: round(float(a[c]), 4) for c in range(len(FINE)) if a[c] > 0})


class Table:
    """classes.npz read back: per fix the fine class, the ring, the blurred indicators; per cat the
    ring means of the same."""

    def __init__(self, data: Path):
        Z = np.load(data / "classes.npz")
        self.meta = json.loads(str(Z["meta"]))
        self.cats = self.meta["cats"]
        self.sigmas = tuple(self.meta["sigmas"])
        for k in ("cat", *PER_CAT):
            setattr(self, k, Z[k])
        self.country = np.array([c["country"] for c in self.cats])
        self.household = np.array([c["household"] for c in self.cats])

    def fixes(self, cats: np.ndarray, sigma: float):
        """phi (N x FINE), abar at each fix's ring (N x FINE), cat of each fix (0..len(cats)-1), weight
        of each fix (1 / (cats x fixes of its cat)) for the cats selected by the boolean `cats`."""
        s = self.sigmas.index(sigma)
        m = cats[self.cat]
        cat = self.cat[m]
        new = np.cumsum(cats) - 1
        phi = self.phi[s][m].astype(np.float64)
        abar = self.abar[cat, s, self.ring[m]].astype(np.float64)
        n = np.bincount(new[cat], minlength=int(cats.sum()))
        return phi, abar, new[cat], 1.0 / (cats.sum() * n[new[cat]])


def scheme_matrix(groups: list[list[int]]) -> np.ndarray:
    """0/1 matrix, coarse x fine, from the fine classes of each coarse class (every fine one once)."""
    P = np.zeros((len(groups), len(FINE)))
    for i, g in enumerate(groups):
        P[i, g] = 1
    if not np.array_equal(P.sum(0), np.ones(len(FINE))):
        raise ValueError("a scheme must take every fine class once")
    return P


def band_of(f: int) -> int:
    return 0 if f < N_IN else 1 + (f - N_IN) // len(SURFACES)


SCHEMES = {  # coarse classes as lists of fine ones, and their names (docs/MISURE.md L13)
    "bands6": ([[f for f in range(len(FINE)) if band_of(f) == b] for b in range(len(BANDS) + 1)], ("inside", *BANDS)),
    "inside11+bands5": ([[f] for f in range(N_IN)] + [[f for f in range(N_IN, len(FINE)) if band_of(f) == b]
                                                      for b in range(1, len(BANDS) + 1)], (*FINE[:N_IN], *BANDS)),
    "fine31": ([[f] for f in range(len(FINE))], FINE),
}
SMALL = [f for f in range(1, N_IN) if f % 2 == 1]  # inside, under 40 m2 (home excluded)
BIG = [f for f in range(1, N_IN) if f % 2 == 0]
OUT_BANDS = [[f for f in range(N_IN, len(FINE)) if band_of(f) == b] for b in range(1, len(BANDS) + 1)]
PIECES = {  # the candidate of L13 taken apart (exploratory): home, small buildings, the rest
    "home+bands6": ([[0], SMALL + BIG] + OUT_BANDS, ("home", "inside", *BANDS)),
    "small+bands6": ([SMALL, [0] + BIG] + OUT_BANDS, ("small", "inside", *BANDS)),
    "home+small+bands6": ([[0], SMALL, BIG] + OUT_BANDS, ("home", "small", "inside", *BANDS)),
}


def score_S(beta: np.ndarray, Phi: np.ndarray, A: np.ndarray, wfix: np.ndarray, ridge: float = 0.0):
    """S (the weighted mean of log(Phi.w) - log(A.w), w = exp(beta)) and its gradient in beta."""
    w = np.exp(beta)
    num, den = Phi @ w, A @ w
    S = float(wfix @ (np.log(num) - np.log(den))) - ridge * float(beta @ beta)
    g = w * ((wfix / num) @ Phi - (wfix / den) @ A) - 2 * ridge * beta
    return S, g


def fit(Phi: np.ndarray, A: np.ndarray, wfix: np.ndarray, ridge: float = 1e-6) -> np.ndarray:
    """Class log-weights maximising S. The ridge (in nats per fix) only pins the classes no training
    fix can see, and the free constant, toward the radial map."""
    res = optimize.minimize(lambda b: tuple(-v for v in score_S(b, Phi, A, wfix, ridge)), np.zeros(Phi.shape[1]),
                            jac=True, method="L-BFGS-B")
    return res.x - np.average(res.x, weights=A.T @ wfix)  # log w, 0 at the mean availability


def per_cat_S(beta, Phi, A, cat, n_cats) -> np.ndarray:
    w = np.exp(beta)
    v = np.log(Phi @ w) - np.log(A @ w)
    return np.bincount(cat, v, minlength=n_cats) / np.bincount(cat, minlength=n_cats)


def mean_se(v: np.ndarray, groups: np.ndarray | None = None) -> tuple[float, float]:
    """Mean over cats and its standard error, with the households as units when given."""
    m = float(v.mean())
    if groups is None:
        return m, float(v.std(ddof=1) / np.sqrt(len(v)))
    _, g = np.unique(groups, return_inverse=True)
    tot = np.bincount(g, v - m)
    return m, float(np.sqrt(np.sum(tot ** 2)) / len(v))


def shares(T: Table, sel: np.ndarray, labels_fix: np.ndarray, abar_ring: np.ndarray, n_cls: int, groups=None):
    """Per class: mean over cats of the share of real fixes and of the available share at the rings
    of the fixes (the rotated fixes of pieces.py without the Monte Carlo), their ratio and the paired se."""
    idx = np.flatnonzero(sel)
    real, avail = [], []
    for i in idx:
        m = T.cat == i
        real.append(np.bincount(labels_fix[m], minlength=n_cls) / m.sum())
        avail.append(abar_ring[i][T.ring[m]].mean(axis=0))
    real, avail = np.array(real), np.array(avail)
    out = {}
    for c in range(n_cls):
        d = real[:, c] - avail[:, c]
        _, se = mean_se(d, None if groups is None else groups[idx])
        out[c] = {"real": float(real[:, c].mean()), "avail": float(avail[:, c].mean()),
                  "ratio": float(real[:, c].mean() / max(avail[:, c].mean(), 1e-12)), "diff": float(d.mean()), "se": se}
    return out


def inside(data: Path) -> None:
    T = Table(data)
    res = {}
    s0 = T.sigmas.index(0.0)
    for country in (*sorted(set(T.country)), "all"):
        sel = np.ones(len(T.cats), bool) if country == "all" else T.country == country
        fine = shares(T, sel, T.lab, T.abar[:, s0], len(FINE), T.household)
        signed = shares(T, sel, T.signed, T.signed_abar, len(SIGNED), T.household)
        source = shares(T, sel, T.source, T.source_abar, len(SOURCES), T.household)
        res[country] = {"n_cats": int(sel.sum()), "fine": {FINE[c]: v for c, v in fine.items()},
                        "signed": {SIGNED[c]: v for c, v in signed.items()},
                        "source": {SOURCES[c]: v for c, v in source.items()}}
        print(f"\n{country}: {int(sel.sum())} cats. real / available (ratio, diff +- se in households)")
        for name, v in res[country]["fine"].items():
            if FINE.index(name) < N_IN:
                print(f"  {name:16s} {v['real']:.4f} / {v['avail']:.4f}  ({v['ratio']:.2f}, {v['diff']:+.4f} +- {v['se']:.4f})")
        for k in ("signed", "source"):
            print(f"  {k}:", {n: (round(v["real"], 4), round(v["avail"], 4), round(v["ratio"], 2)) for n, v in res[country][k].items()})
    (data / "classes-inside.json").write_text(json.dumps(res, indent=1), encoding="utf-8")


def fit_report(data: Path, schemes: dict, rule_sigmas: tuple, out_name: str) -> dict:
    """S of the class maps (`schemes`) for every sigma: in sample on all the cats (the most a family
    can give), in sample per country (where each country puts its sigma), and one country out (fitted
    on the other two, scored on it; sigma chosen by the training S among `rule_sigmas`)."""
    T = Table(data)
    countries = sorted(set(T.country))
    everyone = np.ones(len(T.cats), bool)
    res = {"in_sample": {}, "by_country": {}, "one_out": {}}
    for name, (groups, names) in schemes.items():
        P = scheme_matrix(groups)
        for s in T.sigmas:
            phi, abar, cat, wfix = T.fixes(everyone, s)
            beta = fit(phi @ P.T, abar @ P.T, wfix, ridge=1e-9)
            m, se = mean_se(per_cat_S(beta, phi @ P.T, abar @ P.T, cat, len(T.cats)), T.household)
            res["in_sample"][f"{name} {s:g}"] = {"S": m, "se": se, "w": dict(zip(names, np.exp(beta).round(3).tolist()))}
            for c in countries:
                sel = T.country == c
                phi, abar, cat, wfix = T.fixes(sel, s)
                beta = fit(phi @ P.T, abar @ P.T, wfix, ridge=1e-9)
                m, se = mean_se(per_cat_S(beta, phi @ P.T, abar @ P.T, cat, int(sel.sum())), T.household[sel])
                res["by_country"][f"{name} {s:g} {c}"] = {"S": m, "se": se}
        held = {}  # per cat: S with the sigma of the training rule
        for c in countries:
            train, test = T.country != c, T.country == c
            best = None
            for s in T.sigmas:
                phi, abar, cat, wfix = T.fixes(train, s)
                beta = fit(phi @ P.T, abar @ P.T, wfix)
                S_train = score_S(beta, phi @ P.T, abar @ P.T, wfix)[0]
                phi, abar, cat, _ = T.fixes(test, s)
                v = per_cat_S(beta, phi @ P.T, abar @ P.T, cat, int(test.sum()))
                m, se = mean_se(v, T.household[test])
                res["one_out"][f"{name} {s:g} {c}"] = {"S_train": S_train, "S": m, "se": se}
                if s in rule_sigmas and (best is None or S_train > best[0]):
                    best = (S_train, s, v)
            held[c] = best
            res["one_out"][f"{name} rule {c}"] = {"sigma": best[1], "S": float(best[2].mean()),
                                                  "se": mean_se(best[2], T.household[test])[1]}
        v = np.zeros(len(T.cats))
        for c in countries:
            v[T.country == c] = held[c][2]
        m, se = mean_se(v, T.household)
        res["one_out"][f"{name} rule all"] = {"S": m, "se": se, "positive_everywhere": all(held[c][2].mean() > 0 for c in countries)}
        print(f"{name}: in sample " + "  ".join(f"{s:g} m {res['in_sample'][f'{name} {s:g}']['S']:+.5f}" for s in T.sigmas))
        print(f"   one out (sigma by training): " + "  ".join(
            f"{c} {res['one_out'][f'{name} rule {c}']['S']:+.5f} +- {res['one_out'][f'{name} rule {c}']['se']:.5f}"
            f" ({res['one_out'][f'{name} rule {c}']['sigma']:g} m)" for c in countries)
              + f"  all {m:+.5f} +- {se:.5f}", flush=True)
    (data / out_name).write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


def test(train: Path, test_dir: Path, scheme: str, sigma: float) -> dict:
    """A class map fitted on every cat of `train`, scored on every cat of `test_dir` (S, se with the
    households of the test set as units). Writes <test_dir>/classes-test.json."""
    groups, names = {**SCHEMES, **PIECES}[scheme]
    P = scheme_matrix(groups)
    A_, B_ = Table(train), Table(test_dir)
    phi, abar, _, wfix = A_.fixes(np.ones(len(A_.cats), bool), sigma)
    beta = fit(phi @ P.T, abar @ P.T, wfix)
    phi, abar, cat, _ = B_.fixes(np.ones(len(B_.cats), bool), sigma)
    v = per_cat_S(beta, phi @ P.T, abar @ P.T, cat, len(B_.cats))
    m, se = mean_se(v, B_.household)
    out = {"train": str(train), "scheme": scheme, "sigma_m": sigma, "n_cats": len(B_.cats),
           "n_households": int(len(set(B_.household))), "S": m, "se": se,
           "w": dict(zip(names, np.exp(beta).round(4).tolist())),
           "cats": {c["cat_id"]: round(float(x), 5) for c, x in zip(B_.cats, v)}}
    path = test_dir / "classes-test.json"
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    old[f"{scheme} {sigma:g}"] = out
    path.write_text(json.dumps(old, indent=1), encoding="utf-8")
    print(f"{scheme} at {sigma:g} m, fitted on {len(A_.cats)} cats: S on {len(B_.cats)} cats "
          f"({out['n_households']} households) {m:+.5f} +- {se:.5f}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("build", "inside", "fit", "pieces", "test"))
    ap.add_argument("data")
    ap.add_argument("--test", help="test: the data set to score")
    ap.add_argument("--scheme", default="inside11+bands5")
    ap.add_argument("--sigma", type=float, default=20.0)
    ap.add_argument("--households", type=float, default=20.0, help="as score.py (L7: 20)")
    a = ap.parse_args()
    data = Path(a.data)
    if a.cmd == "build":
        build(data, a.households)
    elif a.cmd == "inside":
        inside(data)
    elif a.cmd == "fit":  # L13, the rule: sigma among 0-20 m
        fit_report(data, SCHEMES, SIGMAS[:5], "classes-fit.json")
    elif a.cmd == "pieces":  # the candidate taken apart, every sigma (exploratory)
        fit_report(data, {**SCHEMES, **PIECES}, SIGMAS, "classes-pieces.json")
    elif a.cmd == "test":
        test(data, Path(a.test), a.scheme, a.sigma)


if __name__ == "__main__":
    main()
