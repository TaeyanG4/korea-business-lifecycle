# Canonical PERMIT Production Materialization

Checked: **2026-09-07**

After the 3,010,802-row full-snapshot dry run passed, a **local-only production `PERMIT` Parquet/ZSTD materializer** was implemented. It accepts only the identical immutable source artifacts approved by the full dry run. Building a local canonical parent does not approve public redistribution.

## Input gate

The materializer accepts only the three artifacts recorded as `PASS` in `provenance/permit_parent_full_dry_run.json`:

- `general_restaurants`: 2,295,369 rows
- `rest_cafes`: 645,952 rows
- `bakeries`: 69,481 rows
- total: 3,010,802 rows

Before writing output, retrieval-manifest hash/bytes/retrieval ID must match the full-dry-run evidence, and SHA-256 is recomputed from the raw file bytes. Any mismatch fails closed before production output is committed.

The full dry run proved zero duplicate `source_key + management_number` candidates exactly. The production build reuses that proof **only for byte-identical SHA-256 artifacts**. This remains an expected uniqueness invariant, not a declaration that `MNG_NO` is an official source primary key.

## Writer contract

- `pyarrow==21.0.0`
- Parquet format version `2.6`
- ZSTD compression level `9`
- data page version `2.0`
- 50,000 rows per Arrow batch
- 50,000 rows per Parquet row group
- one Parquet file per source plus one local `manifest.json`

The Arrow schema exactly follows the frozen 26-column `PERMIT` schema in name, order, nullability, and type. `source_retrieved_at_utc` is `timestamp[us, UTC]`, dates are `date32`, and source X/Y remain `float64`.

## Output location and atomicity

Final output stays under the Git-ignored runtime tree:

```text
data/local/canonical/permit/v1/<build_id>/
  general_restaurants.parquet
  rest_cafes.parquet
  bakeries.parquet
  manifest.json
```

For the current inputs and writer contract, the build ID is `permit-v1-9908225df465e2ff`.

The build writes first to `data/local/.tmp/permit-materialization/<build_id>-<pid>/`. Only after all source row counts, Arrow schemas, Parquet metadata, and output SHA-256 values pass validation is the staging directory renamed to the final build directory. Handled failures remove staging. Existing immutable final builds are never overwritten.

## Semantic preservation

- the four unparseable permit dates remain null plus `INVALID` quality;
- status `03` is not converted into terminal closure;
- status `05` remains semantically unmapped;
- no WGS84 coordinates are generated;
- no episode reconstruction is performed; and
- deferred fields such as telephone/homepage do not enter canonical output.

## Execution

Default mode is plan-only:

```bash
python scripts/materialize_permit_parent.py
```

The real production build is a long local task and must be explicitly invoked by the user:

```bash
mkdir -p data/local/logs
python scripts/materialize_permit_parent.py --execute \
  | tee data/local/logs/permit-materialization-20260907.json
```

Hash/write progress is emitted on stderr; only the final local manifest summary JSON is written to stdout.

After the build completes, an independent verifier rechecks the manifest, Parquet SHA-256 values, row counts, frozen Arrow schema, ZSTD compression, and full-dry-run quality aggregates separately from the materializer.

```bash
python scripts/verify_permit_parent_build.py
```

The verifier also emits only aggregate verification results and never row-level values.

## Publication boundary

The generated Parquet files contain row-level business names, addresses, and source coordinates, so they are **local private runtime artifacts**. They must not be distributed until the public/Kaggle row allowlist and redistribution gates pass separately.

## Current state

Implementation, synthetic Parquet round trips, schema/compression validation, immutable-output protection, hash-mismatch atomic failure tests, the independent post-build verifier, and real-artifact plan validation are complete. The 3,010,802-row production materialization has not yet been executed.
