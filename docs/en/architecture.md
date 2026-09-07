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
      ↳ builder + independent verifier: implemented/tested
      ↳ production execution: pending user run
  → separate publication review
```

The v1 parent/lifecycle contracts remain frozen. The current-snapshot → `PERMIT` transformer and production Parquet/ZSTD build are complete and verified at 3,010,802 rows. Full geospatial QA inspected all 2,811,767 coordinate pairs and adopted source X=easting/Y=northing for the approved current-v1 artifacts. The frozen `PERMIT` schema hash and parent build remain unchanged; a separate seven-column `PERMIT_GEOSPATIAL_ENRICHMENT` schema plus deterministic builder/verifier are now implemented. Only the long production WGS84 sidecar execution remains user-run. Publication and episode reconstruction remain blocked.

## Data storage rule

Runtime data lives under the Git-ignored `data/local/` tree by default. `KBL_DATA_ROOT` may override this location, but any repository-local override must remain under `data/local/`.
