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
  → geospatial source-field QA
      ↳ bounded axis probe: X=easting/Y=northing strongly preferred
      ↳ full-snapshot aggregate validator: implemented / user execution pending
      ↳ WGS84 generation: blocked
  → separate publication review
```

The v1 grain and both canonical schema contracts are frozen, and the current-snapshot → `PERMIT` transformer passed synthetic validation, bounded real compatibility, and the complete 3,010,802-row full dry run. A local-only Parquet/ZSTD builder restricted to exact approved SHA-256 inputs is implemented and tested. Bounded geospatial QA strongly supports source X=easting/Y=northing and a full-snapshot aggregate validator is implemented, but it has not run yet, so the schema axis-validation flag and WGS84 generation remain disabled. Production materialization and full geospatial validation await long user execution; publication and episode reconstruction remain blocked.

## Data storage rule

Runtime data lives under the Git-ignored `data/local/` tree by default. `KBL_DATA_ROOT` may override this location, but any repository-local override must remain under `data/local/`.
