"""Per-cell raw metrics: terrain (Copernicus GLO-90, ~460 m) + climate (NASA POWER climatology).

Cells are a regular 0.5 x 0.5 deg grid (centres at x.25 / x.75). Each NASA POWER parameter is
taken from the nearest POWER grid point (meteorology: 0.5 x 0.625 deg MERRA-2 grid; solar: 1 x 1 deg
CERES/FLASHFlux grid). Only cells whose centre lies inside Mexico are kept.
"""
import json
from pathlib import Path

import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_origin
from shapely.geometry import Point, shape
from shapely.prepared import prep

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
POWER_PARAMS = ["T2M", "T2M_MAX", "T2M_MIN", "T2M_RANGE", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "RH2M"]
DLAT, DLON = 0.5, 0.5

# DEM mosaic grid (matches fetch_dem.py: 240 px per 1-degree tile)
PX = 240
M_LAT0, M_LAT1, M_LON0, M_LON1 = 21, 34, -118, -97


def mexico_geom():
    return shape(json.load(open(ROOT / "data" / "mexico.geojson"))["geometry"])


def load_power():
    """Return {param: (coords[N,2] as (lat, lon), values[N])} for params present."""
    out = {}
    for p in POWER_PARAMS:
        # exact param match (T2M_* would also match T2M_MAX_*)
        files = sorted(f for f in (RAW / "power").glob(f"{p}_*.json") if f.stem.rsplit("_", 2)[0] == p)
        if not files:
            continue
        pts = {}
        for f in files:
            for feat in json.loads(f.read_text())["features"]:
                lon, lat = feat["geometry"]["coordinates"][:2]
                v = feat["properties"]["parameter"][p].get("ANN")
                if v is None or v <= -998:
                    v = None
                pts[(round(lat, 4), round(lon, 4))] = v
        keys = list(pts)
        out[p] = (np.array(keys, dtype=float), np.array([np.nan if pts[k] is None else pts[k] for k in keys]))
    return out


def nearest(param_data, lat, lon, max_deg=0.75):
    coords, vals = param_data
    d = np.hypot(coords[:, 0] - lat, (coords[:, 1] - lon) * np.cos(np.radians(lat)))
    i = int(np.argmin(d))
    if d[i] > max_deg or not np.isfinite(vals[i]):
        return None
    return round(float(vals[i]), 3)


def dem_mosaic(mex):
    h, w = (M_LAT1 - M_LAT0) * PX, (M_LON1 - M_LON0) * PX
    mos = np.full((h, w), np.nan, dtype="float32")
    for f in (RAW / "dem").glob("*.npz"):
        d = np.load(f)
        left, bottom = d["bounds"][0], d["bounds"][1]
        lat, lon = int(round(bottom)), int(round(left))
        if not (M_LAT0 <= lat < M_LAT1 and M_LON0 <= lon < M_LON1):
            continue
        r0, c0 = (M_LAT1 - lat - 1) * PX, (lon - M_LON0) * PX
        mos[r0:r0 + PX, c0:c0 + PX] = d["elev"]
    # keep only pixels inside Mexico (drops US terrain and sea in border/coastal cells)
    tr = from_origin(M_LON0, M_LAT1, 1 / PX, 1 / PX)
    mask = rasterize([(mex, 1)], out_shape=(h, w), transform=tr, fill=0, dtype="uint8").astype(bool)
    # slope in degrees, pixel size corrected for latitude
    dy = 111320.0 / PX
    lats = M_LAT1 - (np.arange(h) + 0.5) / PX
    dx = (dy * np.cos(np.radians(lats)))[:, None]
    gy, gx = np.gradient(mos)
    slope = np.degrees(np.arctan(np.hypot(gx / dx, gy / dy)))
    mos[~mask] = np.nan
    slope[~mask] = np.nan
    return mos, slope


def terrain_metrics(mos, slope, lat, lon):
    r0 = int(round((M_LAT1 - (lat + DLAT / 2)) * PX))
    r1 = int(round((M_LAT1 - (lat - DLAT / 2)) * PX))
    c0 = int(round((lon - DLON / 2 - M_LON0) * PX))
    c1 = int(round((lon + DLON / 2 - M_LON0) * PX))
    e = mos[max(r0, 0):r1, max(c0, 0):c1]
    s = slope[max(r0, 0):r1, max(c0, 0):c1]
    e, s = e[np.isfinite(e)], s[np.isfinite(s)]
    if e.size < 50 or s.size < 50:
        return {"slope_median_deg": None, "slope_p90_deg": None, "relief_m": None, "elev_mean_m": None}
    p5, p95 = np.percentile(e, [5, 95])
    return {
        "slope_median_deg": round(float(np.median(s)), 2),
        "slope_p90_deg": round(float(np.percentile(s, 90)), 2),
        "relief_m": round(float(p95 - p5), 1),
        "elev_mean_m": round(float(e.mean()), 1),
    }


def build_features():
    mex = mexico_geom()
    pm = prep(mex)
    power = load_power()
    present = list(power)
    mos, slope = dem_mosaic(mex)
    cells = []
    for lat in np.arange(22.25, 33.0, DLAT):
        for lon in np.arange(-116.75, -98.0, DLON):
            lat, lon = round(float(lat), 3), round(float(lon), 3)
            if not pm.contains(Point(lon, lat)):
                continue
            c = {"lat": lat, "lon": lon}
            c.update(terrain_metrics(mos, slope, lat, lon))
            for p in present:
                c[p] = nearest(power[p], lat, lon)
            cells.append(c)
    return cells, present
