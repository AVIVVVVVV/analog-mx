"""Terrain metrics for the target sites, computed from NASA altimetry with the SAME method as Earth cells.

- Moon: LRO LOLA global DEM 118 m (USGS Astrogeology mosaic, from PDS LOLA data)
- Mars: MGS MOLA global DEM 463 m (USGS Astrogeology mosaic, from PDS MOLA MEGDR)

A 40 km N-S x 30 km E-W box centred on the target site (Moon: centre of the flat summit plateau
as seen in LOLA; Mars: Bradbury Landing) is read,
block-averaged to ~460 m pixels, and slope/relief stats computed exactly as in features.py.
Writes data/target_terrain.json.
"""
import json
import math
import os
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
ROOT = Path(__file__).resolve().parents[1]
BOX_NS_KM, BOX_EW_KM, PIX_M = 40.0, 30.0, 460.0

TARGETS = {
    "moon_mons_mouton": {
        "url": "https://planetarymaps.usgs.gov/mosaic/Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif",
        "dataset_page": "https://astrogeology.usgs.gov/search/map/moon_lro_lola_dem_118m",
        "radius": 1737400.0, "lat": -84.5, "lon": 28.0,
    },
    "mars_gale": {
        "url": "https://planetarymaps.usgs.gov/mosaic/Mars_MGS_MOLA_DEM_mosaic_global_463m.tif",
        "dataset_page": "https://astrogeology.usgs.gov/search/map/mars_mgs_mola_dem_463m",
        "radius": 3396190.0, "lat": -4.5895, "lon": 137.4417,
    },
}


def metrics(key, cfg):
    R = cfg["radius"]
    dlat = math.degrees(BOX_NS_KM * 1000 / R)
    dlon = math.degrees(BOX_EW_KM * 1000 / (R * math.cos(math.radians(cfg["lat"]))))
    with rasterio.open("/vsicurl/" + cfg["url"]) as src:
        def xy(lat, lon):
            return math.radians(lon) * R, math.radians(lat) * R
        x0, y1 = xy(cfg["lat"] + dlat / 2, cfg["lon"] - dlon / 2)
        x1, y0 = xy(cfg["lat"] - dlat / 2, cfg["lon"] + dlon / 2)
        r0, c0 = src.index(x0, y1)
        r1, c1 = src.index(x1, y0)
        win = Window(c0, r0, c1 - c0, r1 - r0)
        z = src.read(1, window=win).astype("float64") * src.scales[0] + src.offsets[0]
        res = src.res[0]
    # pixel ground size: y = res; x = res * cos(lat) (simple cylindrical)
    lat_rows = cfg["lat"] + dlat / 2 - (np.arange(z.shape[0]) + 0.5) * (dlat / z.shape[0])
    fy = max(1, round(PIX_M / res))
    fx = max(1, round(PIX_M / (res * math.cos(math.radians(cfg["lat"])))))
    h, w = (z.shape[0] // fy) * fy, (z.shape[1] // fx) * fx
    zb = z[:h, :w].reshape(h // fy, fy, w // fx, fx).mean(axis=(1, 3))
    lat_b = lat_rows[:h].reshape(-1, fy).mean(axis=1)
    dy = res * fy
    dx = (res * fx * np.cos(np.radians(lat_b)))[:, None]
    gy, gx = np.gradient(zb)
    slope = np.degrees(np.arctan(np.hypot(gx / dx, gy / dy)))
    p5, p95 = np.percentile(zb, [5, 95])
    return {
        "slope_median_deg": round(float(np.median(slope)), 2),
        "slope_p90_deg": round(float(np.percentile(slope, 90)), 2),
        "relief_m": round(float(p95 - p5), 1),
        "elev_mean_m": round(float(zb.mean()), 1),
        "pixels": int(zb.size),
        "pixel_size_m": [round(float(dy), 1), round(float(dx.mean()), 1)],
        "box_km": [BOX_NS_KM, BOX_EW_KM], "center": [cfg["lat"], cfg["lon"]],
        "source_file": cfg["url"], "dataset_page": cfg["dataset_page"],
    }


def main():
    out = {k: metrics(k, v) for k, v in TARGETS.items()}
    (ROOT / "data" / "target_terrain.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
