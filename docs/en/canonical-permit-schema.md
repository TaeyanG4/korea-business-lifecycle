# Canonical PERMIT Parent Schema

Checked: **2026-09-07**

The first Phase 4 step freezes the `PERMIT` parent schema. It does not yet build Parquet output or reconstruct `PERMIT_STATUS_EPISODE` rows.

## Row meaning

One row represents **one source permit record present in the selected current snapshot**. Different permits are never merged from business-name, address, or coordinate similarity.

`management_number` remains a bounded continuity candidate, not a declared source primary key. If expected `(source_key, management_number)` uniqueness fails during a build, the build must fail closed instead of deduplicating silently.

## 26 canonical columns

### Lineage / technical

- `source_key`
- `source_row_number`: 1-based data row after the CSV header
- `source_artifact_sha256`
- `source_retrieved_at_utc`

### Permit / lifecycle source attributes

- `authority_code` ← `개방자치단체코드`
- `management_number` ← `관리번호`
- `permit_date` + `permit_date_quality` ← `인허가일자`
- source status code/name and detail-status code/name
- `closure_date` + `closure_date_quality` ← `폐업일자`

Date quality is `VALID | MISSING | INVALID`. A nonblank unparseable date is not silently repaired or discarded: the canonical date is null, quality is `INVALID`, and the original remains recoverable from raw/staging.

### Business context

- `business_name`
- `business_type_name`
- `hygiene_business_type_name`

### Location

- lot/road postal codes
- lot/road addresses
- `source_coordinate_x`, `source_coordinate_y`

Coordinates are parsed to `float64` only. The catalog-declared `EPSG:5174` is metadata; WGS84 latitude/longitude are not created before axis/transform QA passes.

### Source update lineage

- `source_data_update_type`
- `source_data_updated_at_raw`
- `source_last_modified_at_raw`

The two source timestamps remain strings because their timezone semantics are not yet documented sufficiently for canonical timezone assignment.

## Treatment of all 39 source columns

The common 39-column source inventory is frozen explicitly. Twenty source columns map directly into the parent schema and 19 remain preserved in raw/staging but are intentionally deferred from the parent core.

Deferred fields include sparse workforce/facility/financial attributes, special traditional-shop attributes, telephone, and homepage. Deferral is not source-data deletion; it only means those fields are outside the `PERMIT` parent contract.

## Explicitly absent fields

- `establishment_id`
- canonical active/closed flags
- terminal-event flag
- physical opening date
- WGS84 latitude/longitude

The confirmed `03→01` reversals prohibit converting source code `03` or closure-date presence directly into an irreversible survival event.

## Publication

This is an internal canonical-processing contract. The row-level public allowlist and Kaggle redistribution gates remain unresolved, so schema inclusion is not publication approval.

The machine-readable contract is `schemas/permit_parent.v1.json`.
