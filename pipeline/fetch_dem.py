"""Download Copernicus DEM GLO-90 tiles (public AWS COGs, no login), downsampled to ~460 m.

Each 1x1 degree tile is read over HTTPS using the COG overviews (out_shape 240x240)
and cached as data/raw/dem/<tile>.npz (elev + bounds). Missing tiles (ocean) -> <tile>.none
"""
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "dem"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://copernicus-dem-90m.s3.amazonaws.com"
SIZE = 240  # pixels per 1 deg tile -> ~460 m


def tile_name(lat, lon):
    ns = "N" if lat >= 0 else "S"
    ew = "W" if lon < 0 else "E"
    return f"Copernicus_DSM_COG_30_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"


def fetch(lat, lon):
    name = tile_name(lat, lon)
    npz, none = OUT / f"{name}.npz", OUT / f"{name}.none"
    if npz.exists() or none.exists():
        return "cached"
    url = f"/vsicurl/{BASE}/{name}/{name}.tif"
    try:
        with rasterio.open(url) as src:
            arr = src.read(1, out_shape=(SIZE, SIZE), resampling=Resampling.average).astype("float32")
            nod = src.nodata
            if nod is not None:
                arr[arr == nod] = np.nan
            b = src.bounds
        np.savez_compressed(npz, elev=arr, bounds=np.array([b.left, b.bottom, b.right, b.top]))
        return "ok"
    except Exception as e:
        msg = str(e)
        if "404" in msg or "No such file" in msg or "does not exist" in msg or "not recognized" in msg:
            none.write_text("no tile (ocean)")
            return "none"
        return f"err {msg[:150]}"


def main():
    jobs = [(la, lo) for la in range(21, 34) for lo in range(-118, -97)]
    with ThreadPoolExecutor(8) as ex:
        for (la, lo), res in zip(jobs, ex.map(lambda j: fetch(*j), jobs)):
            print(tile_name(la, lo), res, flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
