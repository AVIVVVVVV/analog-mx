# Analog MX — NASA Space Apps 2026

Eres el único desarrollador de este proyecto de hackathon. El humano (Habib) solo te da credenciales, revisa y graba la demo. Toma decisiones razonables sin preguntar; detente a preguntar SOLO si necesitas credenciales o una cuenta.

**Meta:** tener el MVP publicado **esta misma noche** (sábado 14 de noviembre de 2026). Ve lo más rápido posible: los tiempos de la sección 7 son máximos, no un horario. Si algo se pasa de su tiempo, usa el plan B y sigue. Primero algo publicado que funcione; después, mejoras.

---

## 1. El reto

Reto oficial: **"Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars"**.
Usar datos abiertos de la Tierra, la Luna y Marte (NASA y otras agencias) para identificar y caracterizar lugares en la Tierra parecidos a futuros sitios de base lunares o marcianos, donde se pueda probar tecnología antes de volar.

## 2. Qué construimos

**Analog MX**: un sitio web estático que califica cada celda de 0.5° del norte de México contra el perfil de un sitio objetivo y responde: *"¿Dónde en el norte de México pruebo esta tecnología antes de mandarla a este sitio de la Luna o de Marte?"*

- Objetivo Luna: **Mons Mouton Plateau** (región candidata de Artemis III, polo sur lunar).
- Objetivo Marte: **cráter Gale** (sitio de Curiosity, rico en yeso).
- Validación con dos análogos conocidos:
  - **El Pinacate, Sonora** (~31.77°N, 113.49°W): campo volcánico donde la NASA entrenó astronautas Apolo (1965–1970). Debe salir alto para el objetivo Luna.
  - **Cuatro Ciénegas, Coahuila** (~26.9°N, 102.1°W; verifica las coordenadas): dunas de yeso, análogo del cráter Gale. Debe salir alto para el objetivo Marte.
- **Idioma:** todo lo que ve el usuario (UI, README, textos de envío) va en **inglés**. Los comentarios del código pueden ir en inglés o español.

### Flujo del usuario (MVP)
1. Elige el objetivo (Moon: Mons Mouton / Mars: Gale) y ve su ficha: valores de referencia, cada uno con enlace a su fuente.
2. Ve un mapa de calor del norte de México (celdas de 0.5°), puntuación de 0 a 100.
3. Mueve los pesos por criterio con sliders; el mapa y el ranking se recalculan en el navegador.
4. Ve el top 10 con el desglose por criterio.
5. Ve dónde quedan El Pinacate y Cuatro Ciénegas (rango y percentil). Es la validación; muéstrala de forma destacada.
6. Hace clic en una celda o candidato y ve la ficha del sitio: puntuación, desglose, **"What you could test here"** (derivado por reglas, ver §5) y **"What Earth can't simulate"** (gravedad, vacío/atmósfera de CO₂, radiación, luz rasante del polo sur lunar).

### Fuera del MVP (solo si sobra tiempo, en este orden)
1. Mapa del sitio objetivo con teselas WMTS de NASA Solar System Treks (Moon Trek / Mars Trek), que no piden login. **Es el extra más importante:** suma datos de la NASA a la parte de la Luna y Marte.
2. Relieve a 30 m (Copernicus GLO-30, mismo esquema en AWS) solo para las 10 mejores celdas.
3. (Solo si Earthdata vuelve a funcionar) bonificación por yeso o sulfatos con EMIT L2B para el objetivo Marte.

### Lo que NO haremos
Backend, base de datos, login, frameworks de frontend (nada de React ni bundlers), cobertura global.

---

## 3. Arquitectura

```
Python (corre una vez, local)            Web estática (GitHub Pages)
data/raw/  <- fetch_power.py             web/index.html
           <- fetch_dem.py               web/app.js    (Leaflet, UI, sliders, fichas)
features.py -> métricas por celda        web/score.js  (fórmulas de similitud)
build_cells.py + data/targets.json  ->   web/cells.json
```

La puntuación se calcula en el navegador para que los sliders respondan al instante. Python solo prepara las métricas crudas por celda.

**Estructura del repo:**
```
analog-mx/
  CLAUDE.md
  README.md                 # en inglés
  requirements.txt
  .gitignore                # incluye data/raw/
  pipeline/
    fetch_power.py
    fetch_dem.py
    features.py
    build_cells.py
    validate.py             # imprime rango y percentil de los sitios conocidos
  data/
    raw/
    targets.json
    known_sites.json
  web/
    index.html
    app.js
    score.js
    style.css
    cells.json              # generado
  docs/
    submission.md           # textos para la página de Space Apps + guion de la demo
```

**Stack:** Python 3 (`requests`, `numpy`, `pandas`, `rasterio`, `shapely`). Sin `earthaccess`. JavaScript sin framework + Leaflet desde CDN. Publicación en GitHub Pages (servir desde `/web` o con una GitHub Action; elige lo más simple).

---

## 4. Datos

### Región
Rectángulo aproximado: latitud 22–33°N, longitud 117–98°W. **Recórtalo a territorio de México** con la frontera de Natural Earth (GeoJSON de países, filtra México, y prueba si cada centro de celda cae dentro con shapely). Descarta las celdas de océano.

### 4.1 Clima — NASA POWER (sin login)
- Docs: https://power.larc.nasa.gov/docs/services/api/temporal/climatology/
- Endpoint regional de climatología (rejilla de 0.5°):
  `https://power.larc.nasa.gov/api/temporal/climatology/regional?latitude-min=..&latitude-max=..&longitude-min=..&longitude-max=..&parameters=T2M&community=SB&format=JSON`
- Las peticiones regionales aceptan **un parámetro a la vez**. Pide por bloques (empieza en 4°×4°; si la API se queja del tamaño, reduce el bloque).
- Límite aproximado: **30 peticiones por minuto** en climatología. Espera ~2.5 s entre llamadas, guarda cada respuesta en `data/raw/power/` y no repitas lo que ya está en caché.
- Parámetros (usa el valor anual `ANN`): `T2M`, `T2M_MAX`, `T2M_MIN`, `T2M_RANGE`, `PRECTOTCORR`, `ALLSKY_SFC_SW_DWN`, `RH2M`. Si alguno no existe en la climatología, quítalo y anótalo en el README.
- Los centros de celda son las coordenadas que devuelve POWER.
- **Plan B:** si la regional falla, usa el endpoint `point` para cada celda de tierra (con caché y pausas).

### 4.2 Relieve — DEM
**Earthdata (NASA) está en mantenimiento: NO uses `earthaccess` ni nada que pida login.**

- **Fuente única:** Copernicus DEM GLO-90 (ESA), en COG públicos sin login en el bucket de AWS Open Data `copernicus-dem-90m` (HTTPS: `https://copernicus-dem-90m.s3.amazonaws.com/`). Teselas de 1°×1°; verifica el patrón exacto de nombres (algo como `Copernicus_DSM_COG_30_N31_00_W114_00_DEM/...tif`) con el listado o el readme del bucket antes de descargar en masa.
- Lee con `rasterio` directo por HTTPS usando los **overviews** del COG (o `out_shape` reducido): ~500 m de resolución basta para celdas de 0.5°, así descargas mucho menos.
- Las teselas que no existen (mar) devuelven 404: trátalo como "sin datos", no como error.
- **Atribución obligatoria:** busca el texto de atribución oficial que exige la licencia de Copernicus DEM y ponlo tal cual en el pie de la web y en el README.
- Por cada celda de 0.5° calcula sobre el DEM (submuestreado a ~250–500 m si hace falta por velocidad):
  - `slope_median_deg` y `slope_p90_deg` (pendiente en grados; corrige el tamaño de píxel en metros según la latitud)
  - `relief_m` = P95 − P5 de la elevación
  - `elev_mean_m`
- **Límite de tiempo:** si el DEM tarda más de 30 min en total, usa una resolución más gruesa o recorta la región a Sonora, Chihuahua y Coahuila.

### 4.3 Perfiles de los objetivos — `data/targets.json`
**Investígalos tú** con búsqueda web en fuentes primarias (NASA, LPI, PDS, artículos revisados por pares, datos de LRO LOLA/Diviner, MOLA, Curiosity REMS). Regla dura: **cada valor lleva `source_url` y `source_note`. Si no encuentras fuente, pon `null` y ese criterio queda fuera de ese objetivo. Nunca inventes números.**

Formato:
```json
{
  "moon_mons_mouton": {
    "name": "Mons Mouton Plateau (Lunar South Pole, Artemis III candidate)",
    "body": "Moon",
    "center": {"lat": null, "lon": null, "source_url": "..."},
    "criteria": {
      "slope_median_deg": {"value": null, "type": "match", "source_url": "", "source_note": ""},
      "slope_p90_deg":    {"value": null, "type": "match", "source_url": "", "source_note": ""},
      "relief_m":         {"value": null, "type": "match", "source_url": "", "source_note": ""},
      "aridity":          {"type": "extreme", "direction": "dry"},
      "thermal_range":    {"type": "extreme", "direction": "high"},
      "cold":             {"type": "extreme", "direction": "low_temp"},
      "solar":            {"type": "extreme", "direction": "high"}
    },
    "real_values_for_display": [
      {"label": "Surface temperature range", "value": "...", "source_url": "..."}
    ],
    "earth_cannot_simulate": ["1/6 g gravity", "Vacuum", "Radiation environment", "Low-angle polar sunlight and permanently shadowed regions"]
  },
  "mars_gale": { "...": "misma estructura; earth_cannot_simulate: ~3/8 g, thin CO2 atmosphere, radiation, global dust storms" }
}
```
Los criterios `extreme` no necesitan valor numérico (ver §5). `real_values_for_display` es solo informativo (p. ej. temperaturas reales de la Luna/Marte con fuente) para que el usuario vea la diferencia.

Fuentes de partida:
- Regiones candidatas de Artemis III (nueve, oct 2024): https://www.nasa.gov/news-release/nasa-identifies-candidate-regions-for-landing-next-americans-on-moon/ y noticias de oct 2024 sobre las nueve regiones
- Diviner (temperaturas lunares): https://www.diviner.ucla.edu/data
- Cuatro Ciénegas y Gale: https://science.nasa.gov/earth/earth-observatory/gypsum-on-earth-and-mars-80502/ y https://pmc.ncbi.nlm.nih.gov/articles/PMC3426888
- El Pinacate: https://science.nasa.gov/earth/earth-observatory/pinacate-biosphere-reserve-3923 y https://eol.jsc.nasa.gov/Collections/EarthObservatory/articles/PinacatesBiosphereReservehtm.htm

### 4.4 `data/known_sites.json`
El Pinacate y Cuatro Ciénegas con nombre, coordenadas, objetivo esperado (`moon` / `mars`), una línea de por qué es un análogo y la URL de la fuente.

### 4.5 Mapa base
NASA GIBS en WMTS (EPSG:3857), por ejemplo la capa `BlueMarble_ShadedRelief_Bathymetry` o un mosaico de MODIS. Verifica la URL de la plantilla de teselas en la documentación de GIBS antes de usarla. Pon la atribución en el mapa.

---

## 5. Modelo de puntuación (`web/score.js`)

Puntuación de la celda: `S = 100 * Σ(w_i * s_i) / Σ(w_i)` sobre los criterios disponibles (`s_i` entre 0 y 1).

**Criterios `match`** (terreno; misma unidad en los tres mundos):
`s_i = exp(-0.5 * ((x_i - t_i) / σ_i)^2)`, con `σ_i` = rango intercuartílico de `x_i` en todas las celdas de la región / 1.349 (calcúlalo en Python y guárdalo en `cells.json`).

**Criterios `extreme`** (clima; la Luna y Marte se salen del rango terrestre):
`s_i` = rango percentil de la celda en la dirección indicada, dentro de la región.
- `aridity` / `dry` → menos `PRECTOTCORR` = más alto
- `thermal_range` / `high` → más `T2M_RANGE` (o `T2M_MAX − T2M_MIN`) = más alto
- `cold` / `low_temp` → menos `T2M` = más alto
- `solar` / `high` → más `ALLSKY_SFC_SW_DWN` = más alto

**Confianza** = fracción de criterios con datos en esa celda. Muéstrala junto a la puntuación.

**Pesos por defecto** (el usuario los ajusta con sliders): terreno 1.0 cada uno, aridez 1.0, amplitud térmica 0.75, frío 0.5, sol 0.5. Botón "Reset weights".

**"What you could test here"** (reglas; muestra las que apliquen con su `s_i ≥ 0.7`):
- pendiente/relieve → "Rover mobility and navigation on comparable slopes"
- aridez → "Dust mitigation and equipment durability in hyper-arid conditions"
- amplitud térmica → "Thermal cycling of hardware and habitats"
- sol → "Solar power systems"
- (opcional, Marte + yeso de EMIT) → "Mineral spectrometers and biosignature detection"

**Validación (`pipeline/validate.py` y la UI):** para cada sitio conocido, toma la celda más cercana y reporta su rango y percentil con los pesos por defecto, contra su objetivo esperado. Meta: top 10 %. Si no lo logra, revisa que cada criterio tenga la dirección correcta; ajusta los pesos **una vez** como máximo y documenta el cambio en el README. No fuerces el resultado: si queda bajo, la UI y el README lo dicen con honestidad y explican por qué.

---

## 6. UI (`web/`)

- Diseño limpio, oscuro o claro, legible en celular. Layout: barra lateral (selector de objetivo, sliders, validación, top 10) + mapa.
- Celdas como rectángulos de 0.5° con escala de color secuencial (bajo → alto) y leyenda.
- Marcadores para los dos sitios conocidos.
- Ficha del sitio en un panel: puntuación, confianza, tabla de criterios (valor de la Tierra, valor objetivo o "toward extreme", similitud), "What you could test here", "What Earth can't simulate".
- Pie de página: lista de datasets con enlaces y la frase "Built for NASA Space Apps Challenge 2026".
- Si hay más de ~2,000 celdas y el mapa va lento, dibuja en canvas (`L.canvas()`).

---

## 7. Fases — modo rápido (haz commit al terminar cada una)

Principio: **nunca esperes sin hacer nada.** Las descargas corren en segundo plano mientras avanzas otra cosa. Los tiempos son máximos; si terminas antes, sigue de inmediato.

| # | Fase | Tiempo máx. | Qué hacer | Terminado cuando |
|---|---|---|---|---|
| 0 | Setup | 10 min | Repo, carpetas, `requirements.txt`, `.gitignore`, `git init`. Verifica el login de GitHub (`gh auth status`) **al inicio**; si falta, pídeselo a Habib en ese primer mensaje | dependencias instaladas |
| 1 | Lanzar descargas | 15 min | Escribe `fetch_power.py` (NASA POWER) y `fetch_dem.py` (Copernicus GLO-90) y **lánzalos en segundo plano** (con caché y log a archivo) | ambos scripts corriendo sin error en los primeros minutos |
| 2 | Web con datos de ejemplo | 45 min | Mientras descargan: `index.html`, `app.js`, `score.js`, `style.css` completos, usando un `cells.json` de ejemplo generado con valores aleatorios **marcado como FAKE** (nunca se publica) | mapa, sliders, top 10 y fichas funcionan en local |
| 3 | Objetivos | 20 min | Investiga y llena `targets.json` y `known_sites.json` (cada valor con fuente o `null`). Revisa de vez en cuando el log de las descargas | archivos completos y válidos |
| 4 | Datos reales | 30 min | `features.py`, `build_cells.py`, `validate.py` → `web/cells.json` real. **Borra el archivo FAKE** | `validate.py` imprime rango y percentil de El Pinacate y Cuatro Ciénegas |
| 5 | Conectar y probar | 20 min | La web con datos reales; revisa en `python -m http.server` que no haya errores en la consola | todo funciona con datos reales |
| 6 | Publicar | 15 min | GitHub Pages (`gh repo create` + Pages, o GitHub Action) | URL pública que abre en una ventana privada |
| 7 | Textos | 20 min | `README.md` y `docs/submission.md` (ver §8), con capturas del sitio publicado | textos listos para copiar y pegar |
| ✔ | **MVP listo** | — | Avisa a Habib con la URL, los resultados de la validación y lo que quedó pendiente | — |
| 8 | Extras (opcional) | lo que quede | Solo si Habib lo pide, en el orden de §2 "Fuera del MVP", con commit por cada extra | — |

**Recortes por si se alarga** (aplícalos en este orden sin preguntar):
1. Región recortada a Sonora, Chihuahua y Coahuila.
2. DEM más grueso (~1 km).
3. Quitar los criterios `solar` y `cold` y quedarse con terreno, aridez y amplitud térmica.
4. Ficha del sitio simplificada: puntuación, desglose y "What you could test here".

## 8. Textos de entrega (inglés)

**`README.md`:** qué es, captura de pantalla, cómo correr el pipeline y la web, datasets usados (con enlaces), método de puntuación, resultados de la validación, limitaciones, créditos.

**`docs/submission.md`** (para copiar y pegar en la página de Space Apps):
- Título y resumen corto (≤ 100 palabras).
- Descripción del proyecto: qué hace, cómo funciona, beneficios, qué se espera lograr.
- Uso de datos de la NASA: cada dataset y para qué se usó (POWER para el clima, GIBS para el mapa base, Solar System Treks si se hizo ese extra, y las fuentes de NASA/LRO/Curiosity citadas en `targets.json`).
- Datos de otras agencias: Copernicus DEM GLO-90 (ESA) para el relieve, con su atribución. Explica que se usó porque Earthdata estaba en mantenimiento durante el hackathon.
- Limitaciones y lo que la Tierra no puede simular.
- **Guion del video de 30 segundos** con marcas de tiempo, qué se ve en pantalla en cada momento, la narración y los subtítulos en inglés (la demo debe durar ≤ 30 s y llevar subtítulos en inglés si se narra en otro idioma). Estructura: 0–5 s el problema; 5–15 s objetivo Luna, sale El Pinacate; 15–25 s objetivo Marte, sale Cuatro Ciénegas y un candidato nuevo con su ficha; 25–30 s nombre del proyecto y "Open NASA data".
- Declaración de uso de IA: indica que el código se escribió con ayuda de Claude Code (revisa las reglas de Space Apps 2026 sobre herramientas de IA y cúmplelas).

## 9. Reglas de trabajo

- Avanza por fases; no pases a la siguiente sin cumplir el criterio de terminado de la actual (o sin aplicar su plan B). La excepción son las descargas de la fase 1, que siguen corriendo mientras haces las fases 2 y 3.
- Agrupa las preguntas a Habib en un solo mensaje y hazlas al principio; cada pregunta lo deja esperando.
- **Mantén `PROGRESS.md` siempre al día** (actualízalo y haz commit al terminar cada fase y antes de cualquier tarea larga): fase actual, qué está hecho, qué falta, procesos en segundo plano y cómo volver a lanzarlos, y el siguiente paso exacto. Si la sesión se corta (por ejemplo, por el límite de uso), la siguiente sesión empieza leyendo `PROGRESS.md` y `git log`, verifica qué descargas quedaron completas (la caché dice qué falta) y continúa desde ahí sin rehacer nada.
- Caché en todo lo que se descarga; los scripts deben poder volver a correrse sin descargar todo de nuevo.
- Nunca inventes datos ni cifras. Si un número aparece en la UI o en los textos, debe salir de los datos o de una fuente citada.
- Prueba la web en un servidor local (`python -m http.server`) antes de publicar.
- Al final de cada fase, escribe 2–3 líneas: qué funciona, qué falta y si usaste un plan B.
