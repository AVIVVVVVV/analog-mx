# Analog MX — Space Apps 2026 submission text

## Title
Analog MX: finding Moon and Mars test sites in northern Mexico

## Short summary (≤ 100 words)
Analog MX is an interactive map that scores every 0.5° cell of northern Mexico against the terrain and climate of a future landing site: the Mons Mouton Plateau at the lunar south pole (Artemis III candidate) or Gale Crater on Mars. Terrain is compared with the same method on Earth (Copernicus DEM), the Moon (LRO LOLA) and Mars (MGS MOLA); climate comes from NASA POWER. Users tune criterion weights, see the top candidates, check two known analogs (Cuatro Ciénegas ranks in the top 5 % for Gale) and read what each site can, and cannot, simulate.

## Project description

**What it does.** Analog MX answers one question: *where in northern Mexico should I test this technology before sending it to this site on the Moon or Mars?* Pick a target, and a heat map ranks 431 cells of northern Mexico from 0 to 100. Sliders change the weight of each criterion and the map updates instantly. Clicking a cell opens its score, a per-criterion breakdown, a confidence value, "What you could test here" (rover mobility, dust mitigation, thermal cycling, solar power) and "What Earth can't simulate" (gravity, vacuum or thin CO₂, radiation, polar lighting, global dust storms).

**How it works.** A Python pipeline runs once. It downloads NASA POWER climatology and Copernicus GLO-90 elevation tiles, computes slope and relief statistics per cell at ~460 m, and computes the *same* statistics for the target sites from NASA's LRO LOLA (Moon) and MGS MOLA (Mars) elevation models. Terrain criteria score by similarity to the target value. Climate criteria score by how extreme a cell is within the region, toward the Moon or Mars: driest, largest daily temperature swing, coldest, sunniest. Lunar and Martian climates are far outside Earth's range, so direct matching isn't possible. Scoring runs in the browser on a static website, so there is no backend.

**Validation.** Two places NASA has already used as analogs are checked automatically:
- Cuatro Ciénegas (gypsum dunes, a Gale Crater analog) ranks **#22 of 431 (top 5.1 %)** for the Mars target.
- El Pinacate (Apollo astronaut training, 1965–1970) ranks **#345 of 431** for the Mons Mouton target. We report this honestly instead of tuning weights. Pinacate is a low, gentle volcanic field (0.6° median slope) that suited Apollo-era volcanic geology training. The Artemis south-polar plateau is a rugged highland massif (5.9° median slope, ~1.5 km relief). The tool shows that the two kinds of lunar analog differ, and points instead to mountainous, hyper-arid cells such as the Sierra San Pedro Mártir area in Baja California.

**Benefits.** It gives mission planners, universities and Mexican research groups a transparent, source-linked shortlist of field-test sites, close to home and cheaper than far-off analogs. Every number in the UI links to its source or comes from open data.

**What we hope to achieve.** A starting point for a Mexican analog-site network and a reusable method: swap in another target profile or region and rerun the pipeline.

## Use of NASA data
- **NASA POWER** climatology API: annual temperature, daily temperature range, precipitation and surface solar irradiance for each cell.
- **NASA GIBS** (Blue Marble shaded relief, WMTS): map basemap.
- **LRO LOLA** global DEM (118 m; USGS Astrogeology mosaic of NASA PDS data): slope and relief profile of the Mons Mouton Plateau.
- **MGS MOLA** global DEM (463 m; USGS Astrogeology mosaic of NASA PDS data): slope and relief profile around Curiosity's Bradbury Landing in Gale Crater.
- NASA sources cited in the target cards: the Artemis III candidate regions announcement (Oct 2024), NSSDC Moon and Mars fact sheets, LRO Diviner cold-trap temperatures (Paige et al. 2010), Curiosity REMS temperatures at Gale, and NASA Earth Observatory articles on El Pinacate and on gypsum in Cuatro Ciénegas and Gale.

## Data from other agencies
- **Copernicus DEM GLO-90 (ESA)**, public Cloud-Optimized GeoTIFFs on AWS Open Data: terrain for every Earth cell. We used it because NASA Earthdata (needed for SRTM/NASADEM) was in maintenance during the hackathon. Attribution: *produced using Copernicus WorldDEM-90 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.*
- **Natural Earth** country boundaries to clip the grid to Mexico.

## Limitations and what Earth can't simulate
- 0.5° cells (~55 km) average out small features such as dune fields and individual craters; metre-scale rover hazards aren't captured at ~460 m.
- Target terrain comes from one 40 × 30 km box per site, and the result depends on where the box sits.
- Climate criteria are relative: no place on Earth reaches lunar or Martian temperatures or pressures.
- No mineralogy layer yet (e.g. gypsum/sulfates), which matters for Gale.
- Earth can't simulate: lunar 1/6 g and Martian ~3/8 g gravity, vacuum or a ~6 mbar CO₂ atmosphere, the space radiation environment, low-angle polar sunlight and permanently shadowed regions, and global dust storms.

## 30-second demo video script

| Time | On screen | Narration (English) | Subtitles |
|---|---|---|---|
| 0–5 s | Map of northern Mexico, cursor idle | "Before we send a rover to the Moon or Mars, where on Earth do we test it?" | Before we send a rover to the Moon or Mars, where on Earth do we test it? |
| 5–15 s | Click **Moon: Mons Mouton**, heat map updates; open the validation card for El Pinacate, then click the #1 cell in Baja California | "Pick the Artemis III Mons Mouton plateau. Analog MX compares lunar LOLA terrain with every cell in Mexico. El Pinacate trained Apollo crews, but the south-pole highlands point to the Baja mountains instead." | Mons Mouton (Artemis III) vs. every cell in Mexico. Apollo's El Pinacate ≠ south-pole highlands → Baja mountains rank #1. |
| 15–25 s | Click **Mars: Gale Crater**; Cuatro Ciénegas badge "TOP 10 %" (#22); click it, site card shows "What you could test here" and "What Earth can't simulate"; drag the aridity slider | "Switch to Gale Crater. Cuatro Ciénegas, a known gypsum analog, lands in the top 5 percent, and each site shows what you can test there and what Earth can't simulate." | Gale Crater: Cuatro Ciénegas lands in the top 5 %. What you can test, and what Earth can't simulate. |
| 25–30 s | Zoom out, title "Analog MX", footer with data sources | "Analog MX. Built on open NASA data." | Analog MX · Open NASA data |

## Use of AI
The code, data pipeline and documentation for Analog MX were written with the help of **Claude Code**, an AI coding assistant, directed and reviewed by the team. The AI also helped find and cite sources. All data values come from the cited datasets or are computed by the open-source pipeline in this repository. No AI-generated images or data are used. The project does not use NASA logos or imply NASA endorsement.
