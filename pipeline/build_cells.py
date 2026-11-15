"""Build web/cells.json from raw metrics, and copy targets/known sites into web/."""
import json
import shutil
from datetime import date
from pathlib import Path

import numpy as np

from features import DLAT, DLON, build_features

ROOT = Path(__file__).resolve().parents[1]
MATCH_FIELDS = ["slope_median_deg", "slope_p90_deg", "relief_m"]


def main():
    cells, present = build_features()
    sigma = {}
    for f in MATCH_FIELDS:
        x = np.array([c[f] for c in cells if c[f] is not None], dtype=float)
        q1, q3 = np.percentile(x, [25, 75])
        sigma[f] = round(float((q3 - q1) / 1.349), 4)
    meta = {
        "generated": date.today().isoformat(),
        "grid": {"dlat": DLAT, "dlon": DLON, "note": "Regular 0.5 deg grid; NASA POWER values from nearest POWER grid point"},
        "sigma": sigma,
        "power_params": present,
        "units": {
            "slope_median_deg": "deg", "slope_p90_deg": "deg", "relief_m": "m", "elev_mean_m": "m",
            "T2M": "°C", "T2M_MAX": "°C", "T2M_MIN": "°C", "T2M_RANGE": "°C",
            "PRECTOTCORR": "mm/day", "ALLSKY_SFC_SW_DWN": "kWh/m²/day", "RH2M": "%",
        },
        "n_cells": len(cells),
    }
    out = ROOT / "web" / "cells.json"
    out.write_text(json.dumps({"meta": meta, "cells": cells}, separators=(",", ":")))
    for name in ["targets.json", "known_sites.json"]:
        src = ROOT / "data" / name
        if src.exists():
            shutil.copy(src, ROOT / "web" / name)
    print(f"wrote {out} with {len(cells)} cells; params={present}; sigma={sigma}")
    missing = {f: sum(c.get(f) is None for c in cells) for f in MATCH_FIELDS + present}
    print("missing values per field:", missing)


if __name__ == "__main__":
    main()
