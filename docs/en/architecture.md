# Architecture

## Objective

Keep source evidence separate from semantic interpretation and allow only evidence-backed decisions to flow to later stages.

```text
official source evidence
  → ignored local raw storage (`data/local/`)
  → staging/profile
  → grain/identity/lifecycle audit
  → canonical PERMIT parent
  → derived PERMIT_STATUS_EPISODE
  → canonical schema freeze
  → geospatial normalization
  → deterministic Parquet/ZSTD build
  → separate publication review
```

The v1 grain is frozen as a canonical `PERMIT` parent plus derived `PERMIT_STATUS_EPISODE`. Full-history ingestion, production episode reconstruction, and Kaggle publication are not implemented yet.

## Data storage rule

Runtime data lives under the Git-ignored `data/local/` tree by default. `KBL_DATA_ROOT` may override this location, but any repository-local override must remain under `data/local/`.
