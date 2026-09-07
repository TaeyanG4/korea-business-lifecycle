# Architecture

## Objective

Keep source evidence separate from semantic interpretation and allow only evidence-backed decisions to flow to later stages.

```text
official source evidence
  → ignored local raw storage (`data/local/`)
  → staging/profile
  → grain/identity/lifecycle audit
  → canonical schema
  → geospatial normalization
  → deterministic Parquet/ZSTD build
  → separate publication review
```

The repository currently implements only the first bounded execution milestone. Full-history ingestion, lifecycle reconstruction, and Kaggle publication are not implemented yet.

## Data storage rule

Runtime data lives under the Git-ignored `data/local/` tree by default. `KBL_DATA_ROOT` may override this location, but any repository-local override must remain under `data/local/`.
