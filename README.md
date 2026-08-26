# EcoDrift

**Environmental signals, with uncertainty attached.**

EcoDrift is a browser-only environmental signal explorer built during the **GIBC V2** build window for **Track 03: Open (General Technical Invention)**. It turns a small, auditable public time series into an explainable workflow:

`PUBLIC DATA → SCHEMA/PROVENANCE → TREND → ANOMALY → CHANGE-POINT → UNCERTAINTY → VISUALIZATION`

## Problem
Environmental dashboards often show a line and leave the user to over-interpret it. A trend can be noisy, an extreme year can dominate intuition, and a possible structural break can look more certain than it is.

EcoDrift keeps those ideas separate. It shows a directional trend, a robust outlier layer, a CUSUM change-point candidate, and a bootstrap confidence interval — then explicitly labels unresolved evidence as uncertain.

## Default public dataset
- Upstream source: **NASA POWER** precipitation.
- Location: Budapest, Hungary — 47.4979 N, 19.0402 E.
- Period: 2000–2024.
- Derived SPI table retrieved through DMAP-AI production backend with `data_origin=real_dmap_ai_backend`, `data_source=nasa_power`, 12-month SPI, baseline 2000–2024, yearly method `jan_dec_totals`.
- NASA POWER Daily API docs: https://power.larc.nasa.gov/docs/services/api/temporal/daily/

The bundled file preserves the 25 yearly precipitation totals and SPI values used by the demo.

## Analytics
- OLS slope and R².
- 95% pair-bootstrap slope interval with deterministic seed.
- Median/MAD robust anomaly score, threshold `|z| >= 2.5`.
- Mean-centered CUSUM maximum as a **candidate** change-point.
- Fail-closed uncertainty label when the bootstrap interval includes zero.

## Claim ceiling
EcoDrift is descriptive and educational. It does **not** attribute climate change, forecast weather or drought, measure drought impact, or establish causality. DMAP-AI categories are SPI categories, not direct measurements of real-world impacts.

## Run
Any static web server works:

```bash
python -m http.server 8080
```

Open `http://localhost:8080`.

## Test

```bash
node tests.mjs
```

## Custom data
Upload CSV with:

```csv
year,value
2010,123
2011,118
...
```

At least 8 valid rows are required.

## Built with
Vanilla HTML, CSS, JavaScript, Canvas 2D, NASA POWER public environmental data, and a DMAP-AI-derived SPI-12 table. No external AI API, cloud inference, CDN, paid model, or runtime dependency.

## AI assistance disclosure
ChatGPT was used as an AI coding assistant for implementation, documentation, test generation, and presentation preparation. The project owner is responsible for the submitted code, source disclosures, tests, and claims.

## GIBC V2 originality statement
EcoDrift was created during the GIBC V2 official build period. It is a separate project from the earlier ProofPath / Earth Evidence submissions: it uses a new environmental time-series architecture, new analytics modules, new public-data provenance flow, new visualization, and a different claim ceiling.
