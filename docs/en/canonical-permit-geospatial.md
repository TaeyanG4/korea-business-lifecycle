# Canonical PERMIT Geospatial Enrichment

Checked: **2026-09-07**

A separately versioned **one-to-one sidecar** is implemented to provide WGS84 coordinates without modifying the verified immutable `PERMIT` parent. The output is local private runtime data and does not imply approval for public/Kaggle distribution.

## Parent gate

- parent build: `permit-v1-9908225df465e2ff`
- parent rows: 3,010,802
- parent independent verifier: PASS
- parent schema: frozen at 26 columns and unchanged
- axis evidence: `provenance/geospatial_full_axis.json`
- source X: easting
- source Y: northing
- source CRS: `EPSG:5174`
- target CRS: `EPSG:4326`

Full geospatial QA inspected all 2,811,767 coordinate pairs. Of 2,631,605 pairs eligible for coarse address-region comparison, X=easting/Y=northing matched 2,630,497 (99.958%) and there were zero candidate-B-only matches. The approval is scoped **only to the current SHA-256-pinned v1 artifacts**; future snapshots require revalidation.

## Sidecar grain/schema

`schemas/permit_geospatial.v1.json` is a seven-column `PERMIT_GEOSPATIAL_ENRICHMENT` schema:

- `source_key`
- `source_row_number`
- `management_number`
- `parent_permit_build_id`
- `wgs84_longitude`
- `wgs84_latitude`
- `coordinate_quality`

`source_key + source_row_number + management_number` is lineage linkage to the parent row. It is not declared an official primary key, and `management_number` remains only a bounded continuity/expected uniqueness candidate.

`coordinate_quality` allows only `TRANSFORMED` or `MISSING_SOURCE_COORDINATES`. If both source X/Y values are absent, both longitude and latitude remain null.

## Fail-closed rules

Before writing, the materializer independently verifies the existing `PERMIT` build again. It then enforces:

- exact sequential parent `source_row_number` values starting at 1;
- no null/blank parent `management_number`;
- failure on a partial source X/Y pair;
- failure on EPSG:5174 → EPSG:4326 transform errors or non-finite results;
- failure outside the broad Korea envelope (lon 124..132, lat 32..40);
- exact agreement with reviewed source-level transformed/missing counts;
- no overwrite of an existing deterministic final directory; and
- staging cleanup on handled failures.

## Production plan

The deterministic build ID is **`permit-geo-v1-c4af8799de0283bb`**.

- total sidecar rows: 3,010,802
- `TRANSFORMED`: 2,811,767
- `MISSING_SOURCE_COORDINATES`: 199,035
- output: `data/local/canonical/permit_geospatial/v1/permit-geo-v1-c4af8799de0283bb/`
- format: Parquet 2.6
- compression: ZSTD level 9
- batch/row group: 50,000 rows
- `pyarrow==21.0.0`
- `pyproj==3.7.2`, PROJ 9.5.1

Without `--execute`, only the plan is printed:

```bash
python scripts/materialize_permit_geospatial.py
```

Long local execution:

```bash
python scripts/materialize_permit_geospatial.py --execute
```

## Independent verification

After materialization, run the separate verifier:

```bash
python scripts/verify_permit_geospatial_build.py
```

The verifier re-verifies the parent build and then rechecks the WGS84 sidecar manifest, file hashes, Arrow schema, ZSTD compression, row counts, linkage sequence, coordinate quality, and null/finite/range invariants across all rows.

## Publication boundary

WGS84 coordinates are precise coordinates. They remain non-public until the `privacy_review.json` field allowlist and the separate redistribution gate pass. Building this sidecar does not approve public row-level release, status semantics, or lifecycle episode reconstruction.

The 3,010,802-row sidecar materialization and independent verification are complete. Build `permit-geo-v1-c4af8799de0283bb` totals 50,805,782 Parquet bytes; 2,811,767 rows are `TRANSFORMED` and 199,035 are `MISSING_SOURCE_COORDINATES`. Parent re-verification, manifest/hash/schema/ZSTD checks, and full coordinate-invariant validation all passed. This completion still does not approve public row-level release.
