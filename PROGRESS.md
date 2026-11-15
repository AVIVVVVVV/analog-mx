# PROGRESS

**Current phase:** 6 (publish), blocked on GitHub credentials. Phases 0–5 and 7 are done.

## Done
- Phase 0: repo, deps (`requirements.txt`), `.gitignore` (excludes `data/raw/`).
- Phase 1: `fetch_power.py` (105 cached files, all OK) and `fetch_dem.py` (224 tiles OK, 49 ocean). Both complete.
- Phase 2: web (`index.html`, `app.js`, `score.js`, `style.css`). No fake dataset was ever needed: real data arrived first.
- Phase 3: `data/targets.json` and `data/known_sites.json`. Target terrain computed from LOLA/MOLA by `pipeline/target_terrain.py` (`data/target_terrain.json`).
- Phase 4: `features.py`, `build_cells.py`, `validate.py` → `web/cells.json` (431 cells, 0 missing values).
  - Cuatro Ciénegas → Gale: #22/431 (top 5.1 %) ✅
  - El Pinacate → Mons Mouton: #345/431 ❌, explained in the README (terrain mismatch; weights not tuned).
- Phase 5: tested in headless Chrome via `python -m http.server`; desktop and mobile OK.
- Phase 7: `README.md`, `docs/submission.md`, screenshots in `docs/img/`.
- `.github/workflows/pages.yml` deploys `web/` to GitHub Pages on push to `main`.

## Pending
- **Publish:** needs the GitHub CLI (`winget install GitHub.cli`, then `gh auth login`) or an empty repo created by Habib. Then:
  `gh repo create analog-mx --public --source . --push` → enable Pages with "GitHub Actions" as source
  (`gh api -X POST repos/{owner}/analog-mx/pages -f build_type=workflow`) → check the URL in a private window
  → put the URL in the README and in the footer "Source code" link.
- Extras (only if Habib asks): Solar System Treks WMTS target map, GLO-30 for the top 10, EMIT gypsum.

## Re-running
Everything is cached. `python pipeline/build_cells.py && python pipeline/validate.py` rebuilds in about 10 s.
Fetch scripts skip cached files. The local server is `python -m http.server 8765 --directory web`.
