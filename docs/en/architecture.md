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
      ↳ publication/redistribution: still blocked
  → bounded PERMIT_STATUS_EPISODE tooling
      ↳ sparse explicit observations only
      ↳ max 100,000 observations/call, in memory
      ↳ LEFT / INTERVAL / RIGHT censoring preserved
      ↳ nationwide production reconstruction: disabled
  → nationwide history observation cost gate
      ↳ current-scale 276-code candidate-union planning: 30,247..30,934 requests/as-of date
      ↳ daily 249-date scenario: 7,531,503..7,702,566 requests
      ↳ latest current numeric authority domain: exact 244 ingested/validated
      ↳ exact deleted numeric change-reference codes: 32; current+deleted candidate union: 276
      ↳ current observed authority count: 230; all are a subset of current 244
      ↳ bounded semantics: deleted partitions freeze after reform while current partitions can keep evolving
      ↳ full 32-code count-only probe: prepared, 384 requests, not executed
      ↳ frozen legacy-partition inclusion policy: unresolved
      ↳ approved cadence: none
  → redistribution clarification gate
      ↳ source-use metadata: PASS
      ↳ written source-specific questions/contact routes: prepared
      ↳ raw/aggregate external redistribution: unresolved
```

The v1 parent and WGS84 sidecar are both production-materialized and independently verified across 3,010,802 rows. The publication-safety local aggregate candidate is also fully scanned and independently verified. The exact 244 current numeric authority codes and 32 deleted numeric codes are ingested, hashed, and validated, and authenticated bounded history execution is now available. Direct execution evidence shows deleted partitions evolving before the reform and then remaining queryable as frozen legacy state, while current partitions can continue evolving. The 276-code union therefore remains a cost-planning candidate rather than a current-state equivalent. Production enumeration stays blocked pending the full 32-code count probe, a legacy-partition inclusion policy, and cadence approval. Source-use metadata is PASS, but external redistribution remains blocked until source-specific written clarification is archived.

## Data storage rule

Runtime data lives under the Git-ignored `data/local/` tree by default. `KBL_DATA_ROOT` may override this location, but any repository-local override must remain under `data/local/`.
