# Korea Local Food-Service Permit Data

[한국어](README.md)

A reproducible public-data project built from Korean Ministry of the Interior and Safety local-government permit data. The repository keeps the name `korea-business-lifecycle`, but the **core v1 data product is a nationwide current permit snapshot**. Nationwide history acquisition and `PERMIT_STATUS_EPISODE` reconstruction are retained as an **optional advanced workflow** for analysts who need longitudinal inference.

## v1 status

**LOCAL V1 CORE: COMPLETE**

**Kaggle: PUBLISHED** — [South Korea Food-Service Permits - Snapshot](https://www.kaggle.com/datasets/taeyangg4/korea-food-service-permits)

**Quickstart Notebook** — [Korea Food-Service Permits: 3M-Row Quickstart](https://www.kaggle.com/code/taeyangg4/korea-food-service-permits-3m-row-quickstart)

**Regional Market Notebook** — [South Korea Food-Service Market Map](https://www.kaggle.com/code/taeyangg4/south-korea-food-service-market-map)

**Business ML Notebook** — [Korea F&B Permit Demand Forecasting with XGBoost](https://www.kaggle.com/code/taeyangg4/korea-f-b-permit-demand-forecasting-with-xgboost)

- Scope: general restaurants, rest cafes, and bakeries
- Raw current CSV: **3,010,802 rows / 926,587,446 bytes (~926.6 MB)** retrieved and verified
- Canonical `PERMIT`: **3,010,802 rows / 165,176,236 bytes (~165.2 MB)**, production materialized and independently verified
- WGS84 sidecar: **3,010,802 rows / 50,805,782 bytes (~50.8 MB)**, 2,811,767 coordinates transformed and independently verified
- Main Kaggle product: canonical `PERMIT` **3,010,802 rows × 26 columns**, **1,398,626,208-byte CSV + 165,170,021-byte Parquet**, `PUBLIC / READY`
- Kaggle usability maintenance: structured Overview, cover, tags, official source provenance, monthly update cadence, Quickstart v6, and Regional Market Map v1 are public and complete. All **8/8** Version 2 file descriptions and **56/56** Data Explorer column descriptions are live and exact-match the approved release metadata; the current web UI shows **10.00/10** Usability with no Pending Actions
- Business ML: public v1 walk-forward notebook forecasts next-3-month administrative permit counts by `authority_code × source_key`. Mean WAPE improves from **21.13% seasonal naive to 18.72% (11.4% relative)**; the top 10% of ranked markets capture **43.9%** of actual permit volume, and the 2026Q2 out-of-time Tweedie WAPE is **17.83%**. The 2026-08 bakery drop and partial 2026-09 month are excluded from evaluation as freshness anomalies
- Historical public aggregate: **67,267 cells** with k=10 suppression. The separate Kaggle dataset was retired after row-level publication to avoid duplicate products; the derived artifact and historical provenance remain preserved
- Nationwide history/episodes: **not required for v1 completion**; runner, schema, and verifier remain available as optional tooling

All real and derived runtime data stays under Git-ignored `data/local/`.

## Public release scope

The current Kaggle/public v1 product is a single **3,010,802-row canonical `PERMIT` release**. It preserves the canonical 26 columns, including business name, address, management number, and source EPSG:5174 coordinates. Telephone/homepage fields are not part of the canonical 26-column parent.

The separately derived WGS84 sidecar and incomplete history snapshots remain unpublished.

The historical privacy-minimized aggregate grouped by source, authority code, raw status/detail-status code, permit year, and closure year, suppressing cells below 10. **k=10 is a technical minimization threshold, not a legal privacy guarantee.** That derivative is no longer a separate Kaggle product.

### Public file formats

`korea_food_service_permits.csv` and `korea_food_service_permits.parquet` contain the same **3,010,802 rows × 26 columns**. CSV targets spreadsheets, broad tooling, and direct downloads; Parquet is the typed compact analytical representation. They are two serializations of the verified canonical `PERMIT`, not duplicated aggregate rows.

The package also includes `source_summary.csv`, `schema.json`, `DATA_DICTIONARY.md`, `README.md`, `SOURCES.md`, and `release-manifest.json`.

## Sources and permitted-use metadata

As rechecked on 2026-09-08, all three official Public Data Portal API pages display `이용허락범위 제한 없음` (no restriction on the permitted-use scope). The current v1 release scope permits the canonical row-level release, and the Kaggle product is now consolidated around that one 3,010,802-row current snapshot. Separate written clarification remains optional additional assurance rather than a release prerequisite.

- 15154916 — MOIS food/general restaurants API
- 15154921 — MOIS food/rest cafes API
- 15155252 — MOIS food/bakeries API

The machine-readable final release decision is `provenance/v1_release_scope.json`.
The initial aggregate publication and package v2 are preserved as **historical evidence** in `provenance/kaggle_release.json` and `provenance/kaggle_release_v2.json`. The initial 3,010,802-row canonical publication is in `provenance/kaggle_row_release_v1.json`.

## Lifecycle caveats

The current snapshot is not promoted into invented lifecycle events.

- `MNG_NO` is not declared an official primary key or establishment identity.
- Permit date is not treated as the physical opening date.
- Closure date is not assumed to be a permanent terminal event.
- Two observed `03→01` reversals prove that `03` is not irreversible terminal closure.
- Status code `05` remains unresolved.
- History is an as-of snapshot service, not a lossless event log.
- Optional sparse episodes preserve interval censoring and right censoring.

## Optional history workflow

Analysts who require longitudinal reconstruction can use the prepared monthly reference cadence and acquisition tooling. The reference plan is 10 dates × 3 sources × 244 date-effective authority codes = 7,320 snapshot tasks. This acquisition is **not required for core v1 or the current Kaggle snapshot release**.

Key docs:

- [v1 Grain Decision](docs/en/grain-decision.md)
- [History Observation Strategy](docs/en/history-observation-strategy.md)
- [Authority Domain Reference](docs/en/authority-domain-reference.md)
- [Architecture](docs/en/architecture.md)
- [Public Aggregate](docs/en/public-permit-aggregate.md)
- [Redistribution Clarification](docs/en/redistribution-clarification.md)

## Development and verification

```bash
python -m pip install -e ".[test]"
python -m compileall src scripts tests
pytest -v
python scripts/release_readiness.py
```

Tests block network access by default and use synthetic fixtures only. The roughly 4 KB under `tests/fixtures/` is minimal test data required to reproducibly validate transformers and verifiers; it is not source data for publication.

## Repository data policy

- Real source bulk files, credentials, runtime logs, partial history, local canonical builds, and Kaggle staging stay under `data/local/`; the approved release artifacts are distributed separately on Kaggle.
- `.env` and Kaggle/API credentials are never tracked.
- Schemas and aggregate/row-level release provenance are tracked.
- Older conservative gates/probes remain for audit history; `v1_release_scope.json` is the current product-scope authority.
