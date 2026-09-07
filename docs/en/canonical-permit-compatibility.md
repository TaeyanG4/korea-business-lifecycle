# Canonical PERMIT Bounded Real-Data Compatibility

Checked: **2026-09-07**

The `PERMIT` transformer previously validated on synthetic fixtures has now been applied for the first time to the real current snapshots under Git-ignored `data/local/`. This milestone performs **compatibility validation only** and does not create a production canonical dataset.

## Scope

- Sources: `general_restaurants`, `rest_cafes`, `bakeries`
- Selection: latest immutable retrieval manifest for each source
- Sample: first 256 data rows after the CSV header
- Total rows validated: 768
- Row-level values printed or recorded: none
- Full-snapshot scan: not performed
- Parquet/ZSTD materialization: not performed

## Result

All three sources passed.

| source | rows | encoding | source → canonical columns | duplicate linkage |
| --- | ---: | --- | --- | ---: |
| general restaurants | 256 | CP949 | 39 → 26 | 0 |
| rest cafes | 256 | CP949 | 39 → 26 | 0 |
| bakeries | 256 | CP949 | 39 → 26 | 0 |

All 768 rows passed the frozen transformer. `permit_date_quality` was `VALID` for every bounded row; closure dates were `VALID` for 485 rows and `MISSING` for 283. X/Y were null in 68 rows each; coordinate values themselves are not stored in provenance.

## What this does not establish

The first 256 rows are not a statistically representative sample. This `PASS` therefore does not prove:

- that every row in the nationwide artifacts satisfies the transformer contract;
- a new full-snapshot proof of linkage-candidate uniqueness;
- absence of the invalid permit-date anomalies already observed during full profiling;
- geospatial axis/CRS transformation semantics; or
- approval to create a production canonical dataset.

In particular, the absence of `INVALID` permit dates in this bounded sample does not supersede the previous full-snapshot profiling evidence.

## Privacy/publication boundary

Management numbers, business names, addresses, telephone numbers, and coordinate values are not written to Git provenance. `provenance/permit_parent_compatibility.json` contains only source identifiers, artifact hashes, counts, and aggregate quality results.

## Next gate

The full-snapshot streaming dry run has also completed with all 3,010,802 rows passing. The next gate is the local-only Parquet/ZSTD production build described in `canonical-permit-materialization.md`.
