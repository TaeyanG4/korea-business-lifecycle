# Architecture

## Objective

Keep source evidence separate from semantic interpretation and allow only evidence-backed decisions to flow to later stages.

```text
official source evidence
  → ignored local raw storage (`data/local/`)
  → staging/profile
  → grain/identity/lifecycle audit
  → canonical schema freeze
      ↳ PERMIT parent: frozen
      ↳ PERMIT_STATUS_EPISODE: frozen
  → deterministic PERMIT parent transformation
      ↳ synthetic 39-column fixture: validated
      ↳ bounded real-snapshot compatibility: passed (256 rows/source)
      ↳ full-snapshot streaming dry run: passed (3,010,802 rows)
  → local PERMIT Parquet/ZSTD materialization
      ↳ production build: completed (3,010,802 rows)
      ↳ independent verifier: passed
  → geospatial source-field QA
      ↳ bounded axis probe: X=easting/Y=northing strongly preferred
      ↳ full-snapshot aggregate validator: passed/reviewed (2,811,767 coordinate pairs)
      ↳ local WGS84 derivation: approved for exact current-v1 artifacts
      ↳ frozen PERMIT parent mutation: prohibited; use separate enrichment
  → PERMIT_GEOSPATIAL_ENRICHMENT
      ↳ seven-column schema: frozen
      ↳ production build: completed/verified (3,010,802 rows)
  → privacy-minimized aggregate candidate
      ↳ direct/linkable row-level fields: excluded
      ↳ exact dates: year-only derivation
      ↳ minimum cell count: 10; smaller cells suppressed
      ↳ production scan: completed (3,010,802 rows)
      ↳ independent verifier: passed
      ↳ candidate cells: 67,267 released / 229,928 suppressed
      ↳ Kaggle aggregate publication: approved by final v1 release scope
      ↳ public serialization: same 67,267 cells as UTF-8 CSV + verified Parquet
      ↳ package metadata: source summary + release schema + data dictionary + manifest
  → approved canonical row-level Kaggle release
      ↳ PERMIT parent rows preserved: 3,010,802
      ↳ canonical columns preserved: 26
      ↳ public serialization: CSV + Parquet
      ↳ source EPSG:5174 coordinates included
      ↳ separately derived WGS84 sidecar excluded
  → bounded PERMIT_STATUS_EPISODE tooling
      ↳ sparse explicit observations only
      ↳ max 100,000 observations/call, in memory
      ↳ LEFT / INTERVAL / RIGHT censoring preserved
      ↳ nationwide production reconstruction: optional advanced workflow
  → nationwide history observation cost gate
      ↳ exact-244 pre-reform current-scale planning: 30,109..30,838 requests/as-of date
      ↳ post-reform current-244-only planning: 30,151..30,838 requests/as-of date
      ↳ approved monthly 10-date scenario: 301,258..308,380 requests
      ↳ daily comparison scenario: 7,499,997..7,678,662 requests
      ↳ latest current numeric authority domain: exact 244 ingested/validated
      ↳ exact deleted numeric change-reference codes: 32; current+deleted candidate union: 276
      ↳ current observed authority count: 230; all are a subset of current 244
      ↳ bounded semantics: deleted partitions freeze after reform while current partitions can keep evolving
      ↳ full 32-code count-only probe: completed, 384/384 requests; post-reform count freeze in 96/96 pairs
      ↳ post-reform policy: current 244 only, exclude deleted 32
      ↳ pre-reform policy: current 244 - new 32 + deleted 32 = exact 244
      ↳ no same-date old/new union
      ↳ approved cadence: MONTHLY_ANCHOR_PLUS_END, 10 dates, maximum gap 31 days
      ↳ optional acquisition reference: 7,320 snapshot tasks, resumable, 400,000 requests/run hard cap
      ↳ episode materializer/verifier: optional; still requires all 7,320 snapshots complete/unique if executed
  → v1 release scope
      ↳ core v1: current PERMIT + local WGS84 sidecar, COMPLETE
      ↳ Kaggle/public: consolidated around one canonical row-level PERMIT current snapshot
      ↳ historical privacy-minimized aggregate: separate Kaggle dataset retired to remove duplicate products; derivative/provenance retained
      ↳ source EPSG:5174 coordinates: included in canonical row release
      ↳ derived WGS84 sidecar: private
      ↳ written source-specific clarification: optional additional assurance
```

The v1 parent and WGS84 sidecar are both production-materialized and independently verified across 3,010,802 rows. **As of 2026-09-08, core v1 is complete around this current-snapshot product** and nationwide history/episode reconstruction is optional advanced analysis. The current Kaggle product is one canonical `PERMIT` current-snapshot dataset with **3,010,802 rows × 26 columns** in CSV and Parquet. The separate k=10 aggregate Kaggle dataset was retired after row-level publication to remove a duplicate product; the verified derivative and historical publication provenance remain available for audit. Source EPSG:5174 coordinates are included in the canonical release; the separately derived WGS84 sidecar remains unpublished. `provenance/v1_release_scope.json` is the current scope authority.

## Data storage rule

Runtime data lives under the Git-ignored `data/local/` tree by default. `KBL_DATA_ROOT` may override this location, but any repository-local override must remain under `data/local/`.
