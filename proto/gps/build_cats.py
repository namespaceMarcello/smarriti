"""Per-cat GPS validation inputs from the Movebank Cat Tracker dataset (Kays et al. 2020, CC0).

    python -m proto.gps.build_cats [max_cats]

Downloads the UK Cat Tracker dataset (handle 10255/move.882, fallback US 10255/move.885)
from the Movebank Data Repository (DSpace 7 REST API), keeps cats with >=100 fixes (up to
max_cats, default 40, ordered by fix count), builds one world.npz + fixes.csv per cat from
OSM (Overpass), and privato/dati/cattracker/index.csv. Raw data: privato/dati/cattracker/
(gitignored).
"""
from __future__ import annotations

import csv
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from proto.luogo3d.world import GARDEN, NATURAL, ROAD_CLASS, Grid  # noqa: E402

API = "https://datarepository.movebank.org/server/api"
OVERPASS = "https://overpass-api.de/api/interpreter"
UA = {"User-Agent": "smarriti-research/0.1 (open-source lost-pet simulator, contact: marcello.costagliola1@gmail.com)"}
DATA = ROOT / "privato" / "dati" / "cattracker"
CATS_DIR = DATA / "cats"
OSM_CACHE = DATA / "osm_cache"
CELL = 2.0
HALF = 300.0  # world grid half-size, m (n = 300)
OSM_HALF = 320.0  # Overpass query box half-size, m
MIN_FIXES = 100
MAX_CATS = int(sys.argv[1]) if len(sys.argv) > 1 else 40

COVER_TREE = {("natural", "wood"), ("landuse", "forest")}
COVER_SHRUB = {("natural", "scrub")}
COVER_GRASS = {("landuse", "grass"), ("landuse", "meadow"), ("natural", "grassland")}


def safe_name(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in str(s))


def get(url, data=None, timeout=120) -> bytes:
    req = urllib.request.Request(url, data=data, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_json(url):
    return json.loads(get(url))


# ---------------------------------------------------------------- Movebank download (DSpace 7 REST)
def resolve_item(handle: str) -> dict:
    for pid in (handle, f"hdl:{handle}", f"https://hdl.handle.net/{handle}"):
        try:
            j = get_json(f"{API}/pid/find?id={urllib.parse.quote(pid, safe='/:')}")
            if j and j.get("uuid"):
                return j
        except Exception as ex:
            print("  pid find", pid, "->", ex)
    raise RuntimeError(f"cannot resolve handle {handle}")


def download_dataset(handle: str) -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    item = resolve_item(handle)
    uuid = item["uuid"]
    print("  item uuid", uuid, item.get("name"))
    bundles = get_json(f"{API}/core/items/{uuid}/bundles")
    result = {}
    for b in bundles.get("_embedded", {}).get("bundles", []):
        if b.get("name") != "ORIGINAL":
            continue
        href = b["_links"]["bitstreams"]["href"]
        bits = get_json(href if href.startswith("http") else API + href)
        for bs in bits.get("_embedded", {}).get("bitstreams", []):
            name = bs["name"]
            if not name.lower().endswith(".csv"):
                continue
            content_href = bs["_links"]["content"]["href"]
            path = DATA / name
            if not path.exists():
                path.write_bytes(get(content_href if content_href.startswith("http") else API + content_href))
            key = "reference" if "reference" in name.lower() else "locations"
            result[key] = path
            print("  got", name, path.stat().st_size, "bytes ->", key)
    return result


# ---------------------------------------------------------------- CSV parsing
def load_fixes(loc_path: Path):
    cats, n_total, n_kept = {}, 0, 0
    with open(loc_path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        cols = r.fieldnames or []
        id_col = "individual-local-identifier" if "individual-local-identifier" in cols else "tag-local-identifier"
        err_cols = [c for c in cols if any(k in c.lower() for k in ("error", "hdop", "accuracy", "dop", "satellite"))]
        for row in r:
            n_total += 1
            if row.get("visible", "true").strip().lower() == "false":
                continue
            if row.get("manually-marked-outlier", "false").strip().lower() == "true":
                continue
            cid = row.get(id_col) or row.get("tag-local-identifier")
            if not cid:
                continue
            try:
                lat, lon = float(row["location-lat"]), float(row["location-long"])
            except (KeyError, ValueError, TypeError):
                continue
            cats.setdefault(cid, []).append((row.get("timestamp", ""), lat, lon))
            n_kept += 1
    print(f"  fixes kept {n_kept}/{n_total}, {len(cats)} individuals, id_col={id_col}, error-like cols={err_cols}")
    return cats, id_col, err_cols


def load_reference(ref_path: Path | None):
    home = {}
    if not ref_path or not ref_path.exists():
        return home
    with open(ref_path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        cols = r.fieldnames or []
        cand = [c for c in ("animal-id", "individual-local-identifier", "tag-local-identifier", "tag-id") if c in cols]
        for row in r:
            lat, lon = row.get("deploy-on-latitude"), row.get("deploy-on-longitude")
            if not lat or not lon:
                continue
            for c in cand:
                cid = row.get(c)
                if cid:
                    home[cid] = (float(lat), float(lon))
    print(f"  reference deploy-on points: {len(home)} (matched via {cand})")
    return home


def home_from_fixes(fixes):
    lats = np.array([f[1] for f in fixes]); lons = np.array([f[2] for f in fixes])
    lat0, lon0 = float(lats.mean()), float(lons.mean())
    kx = 111320.0 * math.cos(math.radians(lat0))
    x = (lons - lon0) * kx; y = (lats - lat0) * 110574.0
    ix = np.floor(x / 10.0).astype(int); iy = np.floor(y / 10.0).astype(int)
    (bx, by), _ = Counter(zip(ix.tolist(), iy.tolist())).most_common(1)[0]
    home_lat = lat0 + (by + 0.5) * 10.0 / 110574.0
    home_lon = lon0 + (bx + 0.5) * 10.0 / kx
    return home_lat, home_lon


# ---------------------------------------------------------------- OSM (Overpass, cached)
def fetch_osm_cached(lat, lon, cache_key):
    OSM_CACHE.mkdir(parents=True, exist_ok=True)
    path = OSM_CACHE / f"{safe_name(cache_key)}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    dlat = OSM_HALF / 110574.0
    dlon = OSM_HALF / (111320.0 * math.cos(math.radians(lat)))
    bb = f"{lat - dlat},{lon - dlon},{lat + dlat},{lon + dlon}"
    q = (f"[out:json][timeout:20];(way[building]({bb});relation[building]({bb});"
         f"way[highway]({bb});way[barrier]({bb});way[railway]({bb});"
         f"way[landuse]({bb});way[leisure]({bb});way[natural]({bb}););out geom tags;")
    body = urllib.parse.urlencode({"data": q}).encode()
    last = None
    for attempt in range(4):  # overpass-api.de 504s under load but recovers within seconds; the
        try:                  # other public mirrors are unreachable from this network (always time out)
            data = get(OVERPASS, body, timeout=15)
            path.write_bytes(data)
            return json.loads(data)
        except Exception as ex:
            last = ex
            print("  overpass attempt", attempt, "->", ex, flush=True)
            time.sleep(3)
    raise last


# ---------------------------------------------------------------- world build
def build_world(lat0, lon0, osm):
    g = Grid(lat0, lon0, cell=CELL, half=HALF)
    n = g.n
    bh = np.zeros((n, n), np.float32)
    ground = np.zeros((n, n), np.float32)
    bid = np.full((n, n), -1, np.int32)
    cover = np.full((n, n), 50, np.uint8)
    road = np.zeros((n, n), np.uint8)
    green = np.zeros((n, n), np.uint8)
    wall = np.zeros((n, n), np.uint8)
    nb = 0
    for el in osm.get("elements", []):
        tags, geom = el.get("tags", {}), el.get("geometry")
        if not tags or not geom or any(p is None for p in geom):
            continue
        try:
            xy = np.column_stack(g.xy([p["lat"] for p in geom], [p["lon"] for p in geom]))
        except (KeyError, TypeError):
            continue
        kv = set(tags.items())
        if "building" in tags and el["type"] == "way":
            if g.fill_polygon(bid, [xy], nb):
                nb += 1
            continue
        if "highway" in tags and tags["highway"] in ROAD_CLASS:
            cls, width = ROAD_CLASS[tags["highway"]]
            try:
                width = float(tags.get("width", width))
            except (TypeError, ValueError):
                pass
            g.paint_line(road, xy, width, cls)
        elif "railway" in tags and tags["railway"] in ("rail", "light_rail", "subway", "tram") \
                and tags.get("tunnel") != "yes":
            g.paint_line(road, xy, 4.0, 5)
        elif tags.get("barrier") in ("wall", "retaining_wall", "fence", "city_wall"):
            g.paint_line(wall, xy, 0.5, 1)
        elif kv & GARDEN and len(xy) > 3:
            g.fill_polygon(green, [xy], 1)
        elif kv & NATURAL and len(xy) > 3:
            g.fill_polygon(green, [xy], 2)
        if kv & COVER_TREE and len(xy) > 3:
            g.fill_polygon(cover, [xy], 10)
        elif kv & COVER_SHRUB and len(xy) > 3:
            g.fill_polygon(cover, [xy], 20)
        elif kv & COVER_GRASS and len(xy) > 3:
            g.fill_polygon(cover, [xy], 30)
    road[bid >= 0] = 0
    return dict(bh=bh, ground=ground, bid=bid, cover=cover, road=road, green=green, wall=wall), g, nb


def find_bid_home(bid, g):
    iy0, ix0 = int(np.argmin(np.abs(g.cy))), int(np.argmin(np.abs(g.cx)))
    if bid[iy0, ix0] >= 0:
        return int(bid[iy0, ix0]), "containing"
    mask = bid >= 0
    if not mask.any():
        return -1, "none"
    d = np.hypot(g.gx, g.gy)
    dm = np.where(mask, d, np.inf)
    k = int(np.argmin(dm))
    if dm.flat[k] <= 30.0:
        return int(bid.flat[k]), "nearest"
    return -1, "none"


# ---------------------------------------------------------------- main
def main():
    t0 = time.time()
    dataset = "UK 10255/move.882"
    try:
        print("downloading UK dataset (10255/move.882)...")
        files = download_dataset("10255/move.882")
    except Exception as ex:
        print("UK dataset failed:", ex, "-> falling back to US 10255/move.885")
        dataset = "US 10255/move.885"
        files = download_dataset("10255/move.885")
    if "locations" not in files:
        raise RuntimeError(f"no locations CSV found in {files}")
    print(f"[{time.time() - t0:.0f}s] downloaded, parsing CSV...")

    cats, id_col, err_cols = load_fixes(files["locations"])
    ref_home = load_reference(files.get("reference"))

    counts = sorted(((cid, len(fx)) for cid, fx in cats.items() if len(fx) >= MIN_FIXES),
                     key=lambda t: -t[1])[:MAX_CATS]
    print(f"[{time.time() - t0:.0f}s] {len(counts)} cats selected (>= {MIN_FIXES} fixes), dataset={dataset}")

    CATS_DIR.mkdir(parents=True, exist_ok=True)
    index_path = DATA / "index.csv"
    with open(index_path, "w", newline="", encoding="utf-8") as idxf:
        w = csv.writer(idxf)
        w.writerow(["cat_id", "dataset", "n_fixes", "home_lat", "home_lon", "home_source",
                    "n_buildings", "skipped_reason"])
        idxf.flush()

        built = skipped = 0
        for cat_id, n_fixes in counts:
            fixes = cats[cat_id]
            if cat_id in ref_home:
                home_lat, home_lon = ref_home[cat_id]
                home_source = "reference"
            else:
                home_lat, home_lon = home_from_fixes(fixes)
                home_source = "cell"

            cat_dir = CATS_DIR / safe_name(cat_id)
            cat_dir.mkdir(parents=True, exist_ok=True)

            kx = 111320.0 * math.cos(math.radians(home_lat))
            with open(cat_dir / "fixes.csv", "w", newline="", encoding="utf-8") as ff:
                fw = csv.writer(ff)
                fw.writerow(["t", "lat", "lon", "x", "y"])
                for t, lat, lon in fixes:
                    x = (lon - home_lon) * kx
                    y = (lat - home_lat) * 110574.0
                    fw.writerow([t, lat, lon, f"{x:.2f}", f"{y:.2f}"])

            reason = ""
            n_buildings = 0
            try:
                osm = fetch_osm_cached(home_lat, home_lon, cat_id)
                time.sleep(1.0)
                layers, g, nb = build_world(home_lat, home_lon, osm)
                n_buildings = nb
                bid_home, bid_src = find_bid_home(layers["bid"], g)
                if bid_home < 0:
                    reason = "no building within 30 m of home"
                    skipped += 1
                else:
                    meta = dict(cell=g.cell, x0=g.x0, y0=g.y0, n=g.n, lat0=home_lat, lon0=home_lon,
                                bid_home_source=bid_src, osm_buildings=nb)
                    np.savez_compressed(cat_dir / "world.npz", meta=json.dumps(meta),
                                        bid_home=np.array(bid_home), **layers)
                    built += 1
            except Exception as ex:
                reason = f"error: {ex}"
                skipped += 1
                print("  !!", cat_id, reason)

            w.writerow([cat_id, dataset, n_fixes, f"{home_lat:.6f}", f"{home_lon:.6f}", home_source,
                        n_buildings, reason])
            idxf.flush()
            print(f"[{time.time() - t0:.0f}s] {cat_id}: n={n_fixes} home_src={home_source} "
                  f"buildings={n_buildings} {'OK' if not reason else reason}")

    print(f"done in {time.time() - t0:.0f}s: built={built} skipped={skipped} -> {index_path}")


if __name__ == "__main__":
    main()
