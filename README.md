# Sri Lanka COVID-19 Interactive Geo Dashboard

Coursework 1 (Individual) — HNDDSFT-M0104 Data Visualization
Pool 2: Geospatial Visualization with Bokeh

## What this is

A Bokeh Server application styled after a Ministry-of-Health style
COVID-19 status dashboard:

- 4 top stat cards (Total confirmed / Active / Recovered / Deaths)
- An interactive bubble map of Sri Lanka's 25 districts on a dark
  CARTO basemap (hover tooltips, size = case count, colour = risk band)
- A district search box + risk-level filter (Low / Medium / High)
- A daily case trend chart (new + cumulative) with a time slider that
  "replays" the outbreak day by day
- A vaccination progress line chart (1st dose / 2nd dose / booster)
- Two donut charts for 1st/2nd dose coverage that update live as you
  move the time slider

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

(Tested against Bokeh 3.x. If your grader's machine has an older/newer
Bokeh, `pip install --upgrade bokeh` first.)

## 2. Regenerate the data (optional)

The three CSVs in `data/` are already generated. To regenerate them
(e.g. after editing `generate_data.py`, or after swapping in a real
dataset):

```bash
python generate_data.py
```

> **Important — read before you submit:** the data shipped here is
> **synthetic** (fixed random seed, see the docstring in
> `generate_data.py`), created so the app runs out-of-the-box. For a
> real submission, replace `data/districts.csv`, `data/daily_trends.csv`
> and `data/vaccination.csv` with a real published dataset (Sri Lanka
> Ministry of Health situation reports, HDX, or Our World in Data
> filtered to Sri Lanka) and describe the preprocessing you did in the
> report. The dashboard code does not need to change — it only cares
> about the column names.

## 3. Run locally

From the **parent** folder of `covid_dashboard/`:

```bash
bokeh serve --show covid_dashboard
```

This opens `http://localhost:5006/covid_dashboard` in your browser.
Use this for your live demo / screenshots.

## 4. Deploy to a free host

### Option A — Render.com
1. Push this folder to a GitHub repo.
2. New "Web Service" on Render, connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command:
   ```
   bokeh serve covid_dashboard --port $PORT --address 0.0.0.0 --allow-websocket-origin=*
   ```
5. Deploy — Render gives you a public URL.

### Option B — Railway.app
1. New project → Deploy from GitHub repo.
2. Add a `Procfile` (or set the start command in Railway settings) to:
   ```
   web: bokeh serve covid_dashboard --port $PORT --address 0.0.0.0 --allow-websocket-origin=*
   ```
3. Railway auto-detects Python from `requirements.txt`.

### Option C — PythonAnywhere
Bokeh Server needs a persistent websocket process, which the free
PythonAnywhere web-app tier does not support well. If you're on the
free plan, prefer Render/Railway or the local-hosting demo instead and
say so in the report (this is a legitimate, examinable trade-off to
discuss under "Challenges").

### Option D — Local hosting for the live demo
```bash
bokeh serve --show covid_dashboard
```
Take a screen recording or screenshots of `localhost:5006` for the
report.

## Project structure

```
covid_dashboard/
├── main.py              # Bokeh server app (layout + callbacks)
├── generate_data.py      # builds the synthetic CSVs (swap for real data)
├── requirements.txt
├── templates/
│   └── index.html        # dark page background / favicon
└── data/
    ├── districts.csv      # 25 districts: lat/lon, cases, risk level
    ├── daily_trends.csv   # island-wide daily new/cumulative cases
    └── vaccination.csv    # island-wide daily dose coverage %
```

## Mapping to the coursework rubric

| Criterion | Where it's covered |
|---|---|
| Data integration (20%) | CSV lat/lon geodata reprojected to Web Mercator in `main.py`; `generate_data.py` documents preprocessing |
| Advanced plotting (30%) | Hover tooltips, district search `Select`, risk `CheckboxButtonGroup` filter, time `Slider` replay, linked donut updates |
| Hosting & accessibility (20%) | See deployment section above; designed to run with `bokeh serve` |
| Report quality (20%) | Use `README.md` + this table as a starting outline for your report |
| Creativity (10%) | Dark "Ministry of Health"-style theme, animated vaccination replay, stat cards |
