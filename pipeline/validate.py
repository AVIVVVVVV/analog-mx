"""Print rank and percentile of the known analog sites with default weights.

Runs web/score.js under Node so validation uses exactly the same scoring code as the web UI.
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

JS = r"""
const S = require(process.argv[1] + '/web/score.js');
const fs = require('fs');
const root = process.argv[1];
const data = JSON.parse(fs.readFileSync(root + '/web/cells.json'));
const targets = JSON.parse(fs.readFileSync(root + '/data/targets.json'));
const sites = JSON.parse(fs.readFileSync(root + '/data/known_sites.json'));
const out = [];
const pf = S.percentileFns(data.cells);
for (const site of sites.sites) {
  for (const [tk, t] of Object.entries(targets)) {
    const res = S.scoreAll(data.cells, t, S.DEFAULT_WEIGHTS, data.meta, pf);
    const i = S.nearestCell(data.cells, site.lat, site.lon);
    const r = S.rankOf(res, i);
    out.push({site: site.name, expected: site.expected_target, target: tk, cell: [data.cells[i].lat, data.cells[i].lon],
      score: res[i].score, confidence: res[i].confidence, rank: r.rank, n: r.n, top_pct: r.topPct, parts: res[i].parts});
  }
}
console.log(JSON.stringify(out));
"""


def main():
    res = subprocess.run(["node", "-e", JS, str(ROOT).replace("\\", "/")], capture_output=True, text=True, check=True)
    rows = json.loads(res.stdout)
    for r in rows:
        star = "  <== expected" if r["target"].startswith(r["expected"]) else ""
        print(f"{r['site']:<28} vs {r['target']:<18} cell {r['cell']}  score {r['score']:.1f}  "
              f"rank {r['rank']}/{r['n']}  top {r['top_pct']:.1f}%  conf {r['confidence']:.2f}{star}")
        if star:
            print("    parts:", {k: (round(v, 2) if v is not None else None) for k, v in r["parts"].items()})
    (ROOT / "data" / "validation.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
