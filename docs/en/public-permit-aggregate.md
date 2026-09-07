# Privacy-Minimized Public Permit Aggregate

Checked: **2026-09-08**

This document preserves the design and verification of the historical privacy-minimized aggregate. That artifact passed technical minimization checks and was published to Kaggle, but after canonical row-level `PERMIT` publication was separately approved and completed, the **separate aggregate Kaggle dataset was retired to remove a duplicate product**. The current Kaggle product is the 3,010,802-row snapshot at `taeyangg4/korea-food-service-permits`. The derived WGS84 sidecar remains separate and unpublished.

## Input

- verified parent build: `permit-v1-9908225df465e2ff`
- parent rows: 3,010,802
- parent independent verifier: PASS
- network access: none
- row-level public projection at aggregate build time: not approved (later approved by a separate release decision)

## Seven-column aggregate schema

`schemas/public_permit_aggregate.v1.json` allows only:

- `source_key`
- `authority_code`
- `source_status_code`
- `source_detail_status_code`
- `permit_year`
- `closure_year`
- `cell_count`

Exact `permit_date` and `closure_date` values are not emitted; only years are derived. `permit_year` is not represented as a physical opening year, `closure_year` is not an irreversible terminal event, and no canonical meaning is added to source status codes `03` or `05`.

## Explicit exclusions

The aggregate output excludes row-level fields including:

- `management_number`, `source_row_number`, and artifact/retrieval lineage;
- business name;
- lot/road addresses and postal codes;
- source X/Y and WGS84 longitude/latitude;
- raw update timestamps; and
- telephone/homepage.

## Cell suppression

The grouping key is `source + authority + source status codes + permit year + closure year`. A cell with **fewer than 10 rows is suppressed entirely** from the candidate output.

`k=10` is only a technical suppression threshold for this project. It is **not claimed as a legal or statistical guarantee of privacy**. Technical verification and the final release-scope decision are recorded separately.

## Local build

The deterministic build ID is `permit-public-agg-v1-bedd874de6619bee`.

Default mode is plan-only:

```bash
python scripts/materialize_public_permit_aggregate.py
```

Long local execution:

```bash
python scripts/materialize_public_permit_aggregate.py --execute
```

The materializer scans all 3,010,802 verified parent rows but reads only the six input fields required for aggregation. The candidate remains under `data/local/public_candidate/permit_aggregate/v1/...`.

## Independent verification

```bash
python scripts/verify_public_permit_aggregate.py
```

The verifier re-verifies the parent build and checks the aggregate manifest/hash/schema/ZSTD, `cell_count >= 10`, and released/suppressed row accounting.

## Current release state

- implementation + synthetic suppression/tamper tests: PASS
- real parent plan-only validation: PASS
- production aggregate scan: **PASS (3,010,802 rows)**
- cells before suppression: 297,195
- released candidate cells (`cell_count >= 10`): 67,267
- suppressed cells: 229,928
- source rows represented by released cells: 2,383,689
- source rows represented by suppressed cells: 627,113
- verified aggregate Parquet: 108,019 bytes, independent verifier PASS
- deterministic aggregate CSV: 2,977,515 bytes / same 67,267 rows
- technical minimization: VERIFIED
- row-level public release: **LATER APPROVED AND PUBLISHED** — `taeyangg4/korea-food-service-permits`
- aggregate publication: **APPROVED**
- Kaggle redistribution: **APPROVED FOR THIS VERIFIED AGGREGATE**
- historical Kaggle publication: `taeyangg4/korea-food-service-permit-aggregate` — **RETIRED / DELETED AFTER CONSOLIDATION**
- current Kaggle product: `taeyangg4/korea-food-service-permits` — canonical 3,010,802-row current snapshot
- release decision: `provenance/v1_release_scope.json`
- initial publication result: `provenance/kaggle_release.json`
- package-v2 publication result: `provenance/kaggle_release_v2.json` — **PUBLISHED / READY**, 8 files

The candidate-time publication flag embedded in the immutable build records the gate at build time. Later release decisions separately approved publication of this **same verified aggregate hash** and the canonical row-level release. The aggregate now remains only as a verified local derivative plus historical publication evidence.

## Kaggle package v2 contract

The historical package-v2 release added usability files without adding row-level records. It serialized the same verified aggregate as:

- `korea_food_service_permit_aggregate.csv` — UTF-8, LF, empty fields for nulls, preserving Parquet row order;
- `korea_food_service_permit_aggregate.parquet` — byte-for-byte copy of the verified artifact, SHA-256 `112fbec3187b2d77df2744edb878fa0f3ecb850cf675496cd4383404092911fb`;
- `source_summary.csv` — safe source-level row/byte, private build-size, and published aggregate-scale metrics only;
- `schema.json` — release-oriented seven-column/type/semantic contract that does not present historical candidate-time gates as the current release gate;
- `DATA_DICTIONARY.md` — column definitions plus lifecycle/privacy limits; and
- `README.md`, `SOURCES.md`, `release-manifest.json`.

The raw current CSV totals **926,587,446 bytes (~926.6 MB)**, the private canonical `PERMIT` Parquet totals **165,176,236 bytes**, and the private WGS84 sidecar totals **50,805,782 bytes**. The 108,019-byte public Parquet is small because 3,010,802 row-level records are reduced to 67,267 aggregate cells, high-cardinality fields are removed, and the remaining low-cardinality columns compress efficiently with ZSTD. Rows are never repeated merely to inflate file size.
