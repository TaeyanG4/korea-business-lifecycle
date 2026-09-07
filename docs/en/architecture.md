# Architecture

## Objective

Keep source evidence separate from semantic interpretation and allow only evidence-backed decisions to flow to later stages.

```text
official source evidence
  → external raw storage
  → staging/profile
  → grain/identity/lifecycle audit
  → canonical schema
  → geospatial normalization
  → deterministic Parquet/ZSTD build
  → separate publication review
```

The repository currently implements only the first bounded execution milestone. Full-history ingestion, lifecycle reconstruction, and Kaggle publication are not implemented yet.

## Data storage rule

`data/raw`, `data/staging`, `data/processed`, and `data/logs` are structural placeholders. Real files must live outside Git under `KBL_DATA_ROOT`.
