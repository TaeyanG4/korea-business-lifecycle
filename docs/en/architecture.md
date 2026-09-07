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
      ↳ builder: implemented/tested
      ↳ production execution: pending user run
  → separate geospatial QA / derived normalization
  → separate publication review
```

The v1 grain and both canonical schema contracts are frozen, and the current-snapshot → `PERMIT` transformer has passed synthetic validation, bounded real compatibility on 256 rows per source, and the complete 3,010,802-row full dry run. A local-only production Parquet/ZSTD builder restricted to the exact approved input SHA-256 values is also implemented and tested. The long production materialization remains pending user execution; public row-level release, WGS84 generation, full-history ingestion, episode reconstruction, and Kaggle publication remain disabled.

## Data storage rule

Runtime data lives under the Git-ignored `data/local/` tree by default. `KBL_DATA_ROOT` may override this location, but any repository-local override must remain under `data/local/`.
