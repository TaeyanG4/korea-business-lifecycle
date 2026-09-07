# Canonical PERMIT Transformer

Checked: **2026-09-07**

After freezing the `PERMIT` parent schema, this milestone implements the **deterministic transformation core** from current-snapshot source rows to the frozen 26-column `PERMIT` row. Validation is synthetic-fixture-only; no nationwide real-data materialization is performed.

## Input contract

Each input row is already strictly decoded source text and must match the frozen 39-column inventory exactly. Missing or extra columns fail closed.

Lineage context requires:

- a v1 `source_key`;
- the retrieval artifact's 64-character lowercase SHA-256; and
- a timezone-aware retrieval UTC timestamp.

The same context can be derived from the existing acquisition `retrieval.json` fields `source_key`, `artifact.sha256`, and `request.completed.utc`.

## Transformation rules

- Strings are trimmed only at the edges; blank becomes null.
- Authority codes, management numbers, and postal codes remain strings so leading zeroes are preserved.
- `인허가일자` and `폐업일자` accept `YYYYMMDD`, `YYYY-MM-DD`, or `YYYY/MM/DD`.
  - blank: null + `MISSING`
  - parseable: date + `VALID`
  - nonblank unparseable: null + `INVALID`
- Nonblank X/Y values are parsed only as finite float64 values. No CRS transform or range correction is performed.
- The four source status code/name fields are preserved without canonical active/closed mapping.
- Deferred source columns, including telephone and homepage, do not flow into canonical output.

## Fail-closed identity invariant

If `source_key + management_number` repeats within one current-snapshot batch, the transformation fails. This enforces the frozen expected uniqueness candidate; it is not a source primary-key declaration. Error messages do not expose the actual management number.

## Intentionally not implemented

- `establishment_id`
- conversion of `03` into terminal closure
- semantic mapping of `05`
- WGS84 coordinates
- nationwide raw-artifact reading/writing
- Parquet/ZSTD materialization
- episode reconstruction

The current functions are for synthetic/bounded in-memory validation and are not claimed to be a production streaming writer.

## Next gate

Bounded compatibility and the complete 3,010,802-row full-snapshot dry run have now passed. The current next gate is local-only production Parquet/ZSTD materialization for the identical approved input hashes.
