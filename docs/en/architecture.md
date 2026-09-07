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
      ↳ full-snapshot streaming dry run: implemented / user execution pending
  → geospatial normalization
  → deterministic Parquet/ZSTD build
  → separate publication review
```

The v1 grain and both canonical schema contracts are frozen, and the current-snapshot → `PERMIT` transformer has passed both synthetic validation and bounded real compatibility on 256 rows per source. A progress-reporting full-snapshot dry-run validator is now implemented; the long local execution is pending user execution. Production canonical materialization, full-history ingestion, episode reconstruction, and Kaggle publication are not implemented yet.

## Data storage rule

Runtime data lives under the Git-ignored `data/local/` tree by default. `KBL_DATA_ROOT` may override this location, but any repository-local override must remain under `data/local/`.
