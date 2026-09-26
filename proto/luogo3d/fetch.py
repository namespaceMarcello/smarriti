"""Download the open data for one place: the prototype of the place in 3D.

    python -m proto.luogo3d.fetch <place.json> <out_dir>

place.json: {"lat": .., "lon": ..}. Only a coarse box leaves the machine (rounded to
0.01 degrees, a few km wide): never the address, never the exact point.

Sources (docs/riferimenti.md section B):
- OpenStreetMap via Overpass (ODbL): roads, footprints, walls, gardens, woods.
- 3D-GloBFP (Che et al. 2024, CC BY 4.0): building footprints with heights.
- TINITALY/1.1 (INGV, CC BY 4.0): bare-ground elevation, 10 m, UTM 32N.
- Copernicus DEM GLO-30 (ESA): surface elevation (buildings and trees included), 30 m.
- ESA WorldCover 2021 v200 (CC BY 4.0): land cover, 10 m.
"""
from __future__ import annotations

import io
import json
import math
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

from .cogread import read_window
from .utm import to_utm

UA = {"User-Agent": "smarriti-research/0.1 (open-source lost-pet simulator)"}
HALF_M = 700.0  # the grid is +-600 m; a margin for roads and footprints crossing the edge


def coarse_box(lat: float, lon: float, half_m: float = HALF_M) -> tuple[float, float, float, float]:
    """(south, west, north, east) containing the square, snapped outwards to 0.01 degrees."""
    dlat = half_m / 110_574.0
    dlon = half_m / (111_320.0 * math.cos(math.radians(lat)))
    s, n = math.floor((lat - dlat) * 100) / 100, math.ceil((lat + dlat) * 100) / 100
    w, e = math.floor((lon - dlon) * 100) / 100, math.ceil((lon + dlon) * 100) / 100
    return s, w, n, e


def get(url: str, data: bytes | None = None, timeout: int = 300) -> bytes:
    req = urllib.request.Request(url, data=data, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()


def fetch_osm(box, out: Path) -> None:
    s, w, n, e = box
    bb = f"{s},{w},{n},{e}"
    q = f"""[out:json][timeout:180];
(way[building]({bb}); relation[building]({bb});
 way[highway]({bb}); way[barrier]({bb}); way[railway]({bb});
 way[landuse]({bb}); way[leisure]({bb}); way[natural]({bb}); way[amenity=parking]({bb}););
out geom tags;"""
    for url in ("https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
                "https://overpass.kumi.systems/api/interpreter"):
        try:
            (out / "osm.json").write_bytes(get(url, urllib.parse.urlencode({"data": q}).encode()))
            return
        except Exception as ex:  # try the next mirror
            print("overpass", url, ex)
            time.sleep(3)
    raise RuntimeError("all Overpass mirrors failed")


def fetch_gbfp(box, out: Path, cache: Path) -> None:
    """3D-GloBFP: find the grid cell, download its shapefile once, keep the box."""
    import shapefile  # pyshp

    s, w, n, e = box
    lat, lon = (s + n) / 2, (w + e) / 2
    grid_zip = cache / "gbfp_world_grid.zip"
    if not grid_zip.exists():
        grid_zip.write_bytes(get("https://zenodo.org/api/records/15487037/files/world_grid.zip/content"))
    zf = zipfile.ZipFile(grid_zip)
    shp = shapefile.Reader(shp=io.BytesIO(zf.read("world_grid.shp")), dbf=io.BytesIO(zf.read("world_grid.dbf")))
    gid = next(sr.record[0] for sr in shp.iterShapeRecords()
               if sr.shape.bbox[0] <= lon <= sr.shape.bbox[2] and sr.shape.bbox[1] <= lat <= sr.shape.bbox[3])
    local = sorted(cache.glob(f"gbfp_{gid}/*.shp"))
    if not local:
        parts = [line for line in get("https://zenodo.org/api/records/15487037/files/data_links.txt/content")
                 .decode().splitlines() if line.startswith("https://figshare.com/")]
        for link in parts:
            art = link.rstrip("/").split("/")[-1]
            files = json.loads(get(f"https://api.figshare.com/v2/articles/{art}/files?page_size=1000"))
            hit = [f for f in files if f["name"].split("_")[0] == str(gid)]
            if hit:
                z = zipfile.ZipFile(io.BytesIO(get(hit[0]["download_url"], timeout=1800)))
                z.extractall(cache / f"gbfp_{gid}")
                break
        local = sorted(cache.glob(f"gbfp_{gid}/*.shp"))
    r = shapefile.Reader(str(local[0]))
    blds = [{"h": float(sr.record[0]), "parts": list(sr.shape.parts), "pts": [list(p) for p in sr.shape.points]}
            for sr in r.iterShapeRecords(bbox=(w, s, e, n))]
    (out / "gbfp.json").write_text(json.dumps({"grid": gid, "box": box, "buildings": blds}))


def tinitaly_tile(x: float, y: float) -> str:
    """Name of the 50 km TINITALY tile holding UTM 32N point (x, y): w{south km/10:03d}{west km/10 % 100:02d}_s10
    (lessons.md #30: the name comes from the south edge; the file's tiepoint is its north-west corner)."""
    return f"w{int(y // 50_000) * 5:03d}{int(x // 50_000) * 5 % 100:02d}_s10"


def fetch_tinitaly(box, out: Path, cache: Path) -> None:
    """TINITALY/1.1: 50 km tiles in UTM 32N named w{south_km/10:03d}{west_km/10 % 100:02d}."""
    import tifffile

    s, w, n, e = box
    xs, ys = to_utm([s, s, n, n], [w, e, w, e], 32)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    names = {tinitaly_tile(xx, yy) for xx in (x0, x1) for yy in (y0, y1)}
    if len(names) != 1:
        raise NotImplementedError(f"box spans several TINITALY tiles: {names}")
    name, = names
    tif = cache / name / f"{name}.tif"
    if not tif.exists():
        zipfile.ZipFile(io.BytesIO(get(f"https://tinitaly.pi.ingv.it/data_1.1/{name}/{name}.zip", timeout=1800))).extractall(cache)
    with tifffile.TiffFile(tif) as t:
        g = t.geotiff_metadata
    assert g["ModelPixelScale"][:2] == [10.0, 10.0] and int(g["ProjectedCSTypeGeoKey"]) == 32632, g
    left, top = g["ModelTiepoint"][3:5]
    r0, r1 = int((top - y1) // 10) - 1, int((top - y0) // 10) + 2
    c0, c1 = int((x0 - left) // 10) - 1, int((x1 - left) // 10) + 2
    z, _ = read_window(tif, r0, r1, c0, c1)
    np.savez(out / "tinitaly.npz", z=z.astype(np.float32), top=top - r0 * 10.0, left=left + c0 * 10.0, res=10.0, zone=32)


def _latlon_window(url_or_path, box, tile_lat_top, tile_lon_left, res):
    s, w, n, e = box
    r0, r1 = int((tile_lat_top - n) / res) - 1, int((tile_lat_top - s) / res) + 2
    c0, c1 = int((w - tile_lon_left) / res) - 1, int((e - tile_lon_left) / res) + 2
    a, _ = read_window(url_or_path, r0, r1, c0, c1)
    return a, tile_lat_top - r0 * res, tile_lon_left + c0 * res


def fetch_worldcover(box, out: Path) -> None:
    s, w, n, e = box
    la, lo = int(math.floor(s / 3) * 3), int(math.floor(w / 3) * 3)
    url = (f"https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
           f"ESA_WorldCover_10m_2021_v200_N{la:02d}E{lo:03d}_Map.tif")
    c, top, left = _latlon_window(url, box, la + 3, lo, 1 / 12000)
    np.savez(out / "worldcover.npz", c=c, lat_top=top, lon_left=left, res=1 / 12000)


def fetch_cop30(box, out: Path) -> None:
    s, w, n, e = box
    la, lo = int(math.floor(s)), int(math.floor(w))
    url = (f"https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N{la:02d}_00_E{lo:03d}_00_DEM/"
           f"Copernicus_DSM_COG_10_N{la:02d}_00_E{lo:03d}_00_DEM.tif")
    z, top, left = _latlon_window(url, box, la + 1, lo, 1 / 3600)
    np.savez(out / "cop30.npz", z=z, lat_top=top, lon_left=left, res=1 / 3600)


def main(argv: list[str]) -> None:
    place = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    out = Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
    cache = out / "cache"; cache.mkdir(exist_ok=True)
    box = coarse_box(place["lat"], place["lon"])
    print("box", box)
    for name, fn in (("osm", lambda: fetch_osm(box, out)), ("gbfp", lambda: fetch_gbfp(box, out, cache)),
                     ("tinitaly", lambda: fetch_tinitaly(box, out, cache)),
                     ("worldcover", lambda: fetch_worldcover(box, out)), ("cop30", lambda: fetch_cop30(box, out))):
        t = time.time(); fn(); print(name, f"{time.time() - t:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1:])
