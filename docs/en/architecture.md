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
      ↳ nationwide production reconstruction: disabled until acquisition completes
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
      ↳ acquisition: 7,320 snapshot tasks, resumable, 400,000 requests/run hard cap, not executed
      ↳ episode materializer/verifier: prepared; blocked until all 7,320 snapshots are complete/unique
  → redistribution clarification gate
      ↳ source-use metadata: PASS
      ↳ written source-specific questions/contact routes: prepared
      ↳ raw/aggregate external redistribution: unresolved
```

The v1 parent and WGS84 sidecar are both production-materialized and independently verified across 3,010,802 rows. The authority code set is approved from the official change reference as pre-reform `current-new+deleted` 244 and post-reform current 244. This current-state membership policy is deliberately separate from which codes the API will answer for a historical `BASE_DATE`. A 10-date monthly cadence and a fail-closed 400,000-request budget are approved, but nationwide acquisition itself has not yet been executed. The runner reuses complete snapshots and the production episode materializer remains blocked until all 7,320 tasks are complete and unique. Source-use metadata is PASS, while external redistribution remains blocked until source-specific written clarification is archived.

## Data storage rule

Runtime data lives under the Git-ignored `data/local/` tree by default. `KBL_DATA_ROOT` may override this location, but any repository-local override must remain under `data/local/`.
