# Canonical PERMIT Full-Snapshot Dry Run

Checked: **2026-09-07**

A streaming dry-run validator is now implemented to pass every real current-snapshot row through the frozen 26-column `PERMIT` transformer **without writing canonical rows**. Because the local scan covers roughly 3.01 million rows, repository work stops after implementation, tests, and plan verification; the long local execution is handed to the user.

## Execution scope

- `general_restaurants`: 2,295,369 rows
- `rest_cafes`: 645,952 rows
- `bakeries`: 69,481 rows
- total: 3,010,802 rows
- network calls: none
- canonical CSV/Parquet/ZSTD output: none
- row-level values on stdout/stderr: none

Before scanning, the latest retrieval manifest's artifact SHA-256 and byte count must match the current evidence in `observed_snapshot_summary.json`. A newer/different latest artifact fails closed instead of silently reusing stale evidence.

## Streaming validation

Each source row is strictly decoded and parsed, then passed through the frozen `PERMIT` transformer one at a time. Canonical rows are neither accumulated nor written. Only aggregate counters are retained:

- transformed row count;
- permit/closure date-quality counts;
- null X/Y counts;
- source/canonical column counts; and
- duplicate linkage-candidate detection.

To verify `source_key + management_number` uniqueness exactly without retaining roughly three million identifiers in memory, the dry run uses an ephemeral SQLite primary-key index under `data/local/.tmp/canonical-full-dry-run/`. The database is removed on normal completion and handled failures. A forced process termination or system failure can leave an ignored local temp file, so that directory can be checked before rerunning.

## Progress reporting

By default, aggregate progress is emitted to stderr every 50,000 transformed rows:

```text
[1/3] START general_restaurants full dry-run rows=2,295,369
[1/3] ROWS general_restaurants 100,000/2,295,369 (4.4%) | overall 100,000/3,010,802 (3.3%)
[1/3] DONE general_restaurants rows=2,295,369 | overall 2,295,369/3,010,802 (76.2%)
```

Management numbers, business names, addresses, telephone numbers, and coordinate values are never included in progress. Only the final aggregate JSON is written to stdout.

## Safety gate

Without `--execute`, the script prints the plan and does not start the full scan.

```powershell
python scripts/dry_run_full_current_snapshot.py
```

The full run is an explicitly invoked long local task:

```powershell
python scripts/dry_run_full_current_snapshot.py --execute
```

A single source can also be rerun independently:

```powershell
python scripts/dry_run_full_current_snapshot.py --execute --source bakeries
```

## Current state

Implementation, synthetic tests, and real-artifact plan verification are complete. The 3,010,802-row full scan has not yet been executed. `provenance/permit_parent_full_dry_run_plan.json` therefore keeps execution status `NOT_EXECUTED`.

The next gate is to analyze the aggregate JSON returned by the user's full dry run. Production canonical materialization design should proceed only if all sources pass.
