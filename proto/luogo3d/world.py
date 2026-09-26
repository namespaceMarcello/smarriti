"""The place as layers on a metre grid centred on home (x east, y north, as sim/case.py).

    python -m proto.luogo3d.world <place.json> <data_dir>     # writes <data_dir>/world.npz

Layers (row 0 = south edge):
  ground   bare-ground elevation (TINITALY 10 m, bilinear), m
  dsm30    surface elevation (Copernicus GLO-30, bilinear), m: a cross-check only
  bh       building height (3D-GloBFP, else OSM levels x 3 m, else the local median), m; 0 = no building
  bid      building index (-1 = none); bid_home = the building of the home door
  cover    ESA WorldCover class (10 tree, 20 shrub, 30 grass, 40 crop, 50 built, 60 bare, 80 water)
  road     0 none, 1 footway/path/steps, 2 service, 3 residential/unclassified, 4 tertiary+, 5 railway
  green    OSM: 1 garden or park, 2 grass, wood, forest, orchard, scrub, farmland
  wall     OSM barrier=wall/retaining_wall/fence (1)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from matplotlib.path import Path as MplPath

from .utm import to_utm

CELL = 2.0
HALF = 600.0
M_PER_DEG_LAT = 110_574.0  # the same equirectangular plane as sim/case.py
M_PER_DEG_LON_EQ = 111_320.0
FLOOR_M = 3.0  # storey height for OSM building:levels; an estimate

ROAD_CLASS = {  # class, carriageway width in m (estimates; OSM here has no width tags)
    "footway": (1, 1.5), "path": (1, 1.5), "steps": (1, 1.5), "pedestrian": (1, 3.0), "track": (1, 3.0),
    "service": (2, 3.5), "living_street": (3, 5.0), "residential": (3, 5.0), "unclassified": (3, 5.0),
    "tertiary": (4, 7.0), "secondary": (4, 8.0), "primary": (4, 10.0), "trunk": (4, 12.0),
    "tertiary_link": (4, 6.0), "secondary_link": (4, 6.0), "primary_link": (4, 6.0),
}
GARDEN = {("leisure", "garden"), ("leisure", "park")}  # Hanmer 2017 "private gardens"
NATURAL = {("landuse", "grass"), ("landuse", "forest"), ("natural", "wood"), ("landuse", "orchard"),
           ("natural", "scrub"), ("landuse", "meadow"), ("landuse", "vineyard"), ("natural", "grassland"),
           ("landuse", "allotments"), ("landuse", "farmland")}  # Hanmer 2017 "natural": grassland, trees, scrub


class Grid:
    def __init__(self, lat0: float, lon0: float, cell: float = CELL, half: float = HALF):
        self.lat0, self.lon0, self.cell = lat0, lon0, cell
        self.kx = M_PER_DEG_LON_EQ * np.cos(np.radians(lat0))
        self.n = int(round(2 * half / cell))
        self.x0 = self.y0 = -half
        c = self.x0 + (np.arange(self.n) + 0.5) * cell
        self.cx, self.cy = c, c  # cell centres
        self.gx, self.gy = np.meshgrid(c, c)

    def xy(self, lat, lon):
        return (np.asarray(lon) - self.lon0) * self.kx, (np.asarray(lat) - self.lat0) * M_PER_DEG_LAT

    def latlon(self, x, y):
        return self.lat0 + np.asarray(y) / M_PER_DEG_LAT, self.lon0 + np.asarray(x) / self.kx

    def fill_polygon(self, layer, xy_rings, value) -> int:
        """Paint cells whose centre is inside the polygon (first ring outer, others holes)."""
        outer = np.asarray(xy_rings[0])
        i0 = max(0, int((outer[:, 0].min() - self.x0) // self.cell))
        i1 = min(self.n, int((outer[:, 0].max() - self.x0) // self.cell) + 1)
        j0 = max(0, int((outer[:, 1].min() - self.y0) // self.cell))
        j1 = min(self.n, int((outer[:, 1].max() - self.y0) // self.cell) + 1)
        if i0 >= i1 or j0 >= j1:
            return 0
        pts = np.column_stack([self.gx[j0:j1, i0:i1].ravel(), self.gy[j0:j1, i0:i1].ravel()])
        inside = MplPath(outer).contains_points(pts)
        for hole in xy_rings[1:]:
            inside &= ~MplPath(np.asarray(hole)).contains_points(pts)
        sub = layer[j0:j1, i0:i1]
        sub[inside.reshape(sub.shape)] = value
        return int(inside.sum())

    def paint_line(self, layer, xy, width, value, keep_max=True) -> None:
        xy = np.asarray(xy)
        r = max(width / 2, self.cell * 0.71)
        for (xa, ya), (xb, yb) in zip(xy[:-1], xy[1:]):
            i0 = max(0, int((min(xa, xb) - r - self.x0) // self.cell))
            i1 = min(self.n, int((max(xa, xb) + r - self.x0) // self.cell) + 1)
            j0 = max(0, int((min(ya, yb) - r - self.y0) // self.cell))
            j1 = min(self.n, int((max(ya, yb) + r - self.y0) // self.cell) + 1)
            if i0 >= i1 or j0 >= j1:
                continue
            px, py = self.gx[j0:j1, i0:i1], self.gy[j0:j1, i0:i1]
            dx, dy = xb - xa, yb - ya
            t = np.clip(((px - xa) * dx + (py - ya) * dy) / max(dx * dx + dy * dy, 1e-9), 0, 1)
            near = (px - xa - t * dx) ** 2 + (py - ya - t * dy) ** 2 <= r * r
            sub = layer[j0:j1, i0:i1]
            sub[near] = np.maximum(sub[near], value) if keep_max else value


def bilinear(img, fr, fc):
    """img sampled at fractional (row, col) of pixel centres; NaN outside."""
    r0, c0 = np.floor(fr).astype(int), np.floor(fc).astype(int)
    ok = (r0 >= 0) & (c0 >= 0) & (r0 + 1 < img.shape[0]) & (c0 + 1 < img.shape[1])
    r0c, c0c = np.clip(r0, 0, img.shape[0] - 2), np.clip(c0, 0, img.shape[1] - 2)
    a, b = fr - r0c, fc - c0c
    v = (img[r0c, c0c] * (1 - a) * (1 - b) + img[r0c, c0c + 1] * (1 - a) * b
         + img[r0c + 1, c0c] * a * (1 - b) + img[r0c + 1, c0c + 1] * a * b)
    return np.where(ok, v, np.nan)


def build(place: dict, data: Path) -> dict:
    g = Grid(place["lat"], place["lon"])
    lat, lon = g.latlon(g.gx, g.gy)
    L = {}

    t = np.load(data / "tinitaly.npz")
    e, n = to_utm(lat, lon, int(t["zone"]))
    L["ground"] = bilinear(t["z"].astype(np.float64), (float(t["top"]) - n) / 10 - 0.5, (e - float(t["left"])) / 10 - 0.5)

    c = np.load(data / "cop30.npz")
    L["dsm30"] = bilinear(c["z"].astype(np.float64), (float(c["lat_top"]) - lat) / float(c["res"]),
                          (lon - float(c["lon_left"])) / float(c["res"]))

    w = np.load(data / "worldcover.npz")
    r = np.floor((float(w["lat_top"]) - lat) / float(w["res"])).astype(int)
    q = np.floor((lon - float(w["lon_left"])) / float(w["res"])).astype(int)
    L["cover"] = w["c"][np.clip(r, 0, w["c"].shape[0] - 1), np.clip(q, 0, w["c"].shape[1] - 1)].astype(np.uint8)

    # buildings: 3D-GloBFP footprints with heights, then OSM footprints it misses
    bh = np.zeros((g.n, g.n)); bid = np.full((g.n, g.n), -1, np.int32); src = np.zeros((g.n, g.n), np.uint8)
    blds = json.loads((data / "gbfp.json").read_text())["buildings"]
    heights = []
    for k, b in enumerate(blds):
        pts, parts = np.asarray(b["pts"]), b["parts"] + [len(b["pts"])]
        rings = [np.column_stack(g.xy(pts[a:z, 1], pts[a:z, 0])) for a, z in zip(parts[:-1], parts[1:])]
        if g.fill_polygon(bid, rings, k):
            heights.append(b["h"])
            g.fill_polygon(bh, rings, b["h"]); g.fill_polygon(src, rings, 1)
    nb = len(blds)
    med_h = float(np.median(heights)) if heights else 6.0
    osm = json.loads((data / "osm.json").read_text(encoding="utf-8"))["elements"]
    road = np.zeros((g.n, g.n), np.uint8); green = np.zeros((g.n, g.n), np.uint8); wall = np.zeros((g.n, g.n), np.uint8)
    osm_b = osm_b_new = 0
    for el in osm:
        tags, geom = el.get("tags", {}), el.get("geometry")
        if not geom:
            continue
        xy = np.column_stack(g.xy([p["lat"] for p in geom], [p["lon"] for p in geom]))
        if "building" in tags and el["type"] == "way":
            osm_b += 1
            tmp = np.zeros((g.n, g.n), np.uint8)
            if not g.fill_polygon(tmp, [xy], 1):
                continue
            new = (tmp == 1) & (bid < 0)
            if new.sum() > 0.5 * (tmp == 1).sum():  # a building 3D-GloBFP does not have
                osm_b_new += 1
                lv = tags.get("building:levels")
                h = float(tags["height"]) if "height" in tags else float(lv) * FLOOR_M if lv else med_h
                bid[new] = nb; bh[new] = h; src[new] = 2; nb += 1
        elif "highway" in tags and tags["highway"] in ROAD_CLASS:
            cls, width = ROAD_CLASS[tags["highway"]]
            g.paint_line(road, xy, float(tags.get("width", width)), cls)
        elif "railway" in tags and tags["railway"] in ("rail", "light_rail", "subway", "tram") \
                and tags.get("tunnel") != "yes" and tags.get("layer", "0") in ("0", "1"):
            g.paint_line(road, xy, 4.0, 5)
        elif tags.get("barrier") in ("wall", "retaining_wall", "fence", "city_wall"):
            g.paint_line(wall, xy, 0.5, 1)
        elif any((k, v) in GARDEN for k, v in tags.items()) and len(xy) > 3:
            g.fill_polygon(green, [xy], 1)
        elif any((k, v) in NATURAL for k, v in tags.items()) and len(xy) > 3:
            g.fill_polygon(green, [xy], 2)
    road[bid >= 0] = 0  # a footprint over a road is a bridge or a data error: the building wins

    # home: the building whose edge is nearest to the door point (the grid centre)
    d = np.hypot(g.gx, g.gy)
    near = (bid >= 0) & (d < 25)
    L["bid_home"] = int(bid[near][np.argmin(d[near])]) if near.any() else -1
    L.update(bh=bh.astype(np.float32), bid=bid, bsrc=src, road=road, green=green, wall=wall)
    L["meta"] = dict(cell=g.cell, x0=g.x0, y0=g.y0, n=g.n, lat0=g.lat0, lon0=g.lon0, gbfp=len(heights),
                     osm_buildings=osm_b, osm_added=osm_b_new, median_h=med_h)
    return L


def main(argv):
    place = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    data = Path(argv[1])
    L = build(place, data)
    meta = L.pop("meta")
    np.savez_compressed(data / "world.npz", meta=json.dumps(meta), **L)
    print(json.dumps(meta))


if __name__ == "__main__":
    main(sys.argv[1:])
