from __future__ import annotations

import csv
import json
import os
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .canonical_compatibility import V1_SOURCE_ORDER, latest_retrieval_manifest
from .canonical_permit import (
    PermitTransformError,
    permit_transform_context_from_retrieval_manifest,
    transform_permit_row,
)
from .canonical_schema import FROZEN_V1_SOURCE_COLUMNS, REQUIRED_CANONICAL_COLUMNS
from .profiling import detect_encoding, sniff_dialect
from .provenance import V1_SOURCE_KEYS, load_observed_snapshot_summary
from .storage import require_external_artifact, resolve_data_root


DEFAULT_PROGRESS_EVERY_ROWS = 50_000
DEFAULT_SQLITE_BATCH_ROWS = 10_000
ProgressCallback = Callable[[dict[str, Any]], None]


class FullSnapshotDryRunError(RuntimeError):
    """Raised when a full current-snapshot dry run cannot pass safely."""


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FullSnapshotDryRunError("retrieval manifest cannot be read as JSON") from exc
    if not isinstance(value, dict):
        raise FullSnapshotDryRunError("retrieval manifest must be a JSON object")
    return value


def _artifact_from_manifest(
    manifest: Mapping[str, Any],
    *,
    data_root: Path,
) -> tuple[Path, int, str]:
    artifact = manifest.get("artifact")
    if not isinstance(artifact, Mapping):
        raise FullSnapshotDryRunError("retrieval manifest artifact metadata is missing")
    relative_path = artifact.get("relative_path")
    declared_bytes = artifact.get("bytes")
    declared_sha256 = artifact.get("sha256")
    if not isinstance(relative_path, str) or not relative_path:
        raise FullSnapshotDryRunError("retrieval manifest artifact path is invalid")
    if not isinstance(declared_bytes, int) or declared_bytes < 1:
        raise FullSnapshotDryRunError("retrieval manifest artifact byte count is invalid")
    if not isinstance(declared_sha256, str):
        raise FullSnapshotDryRunError("retrieval manifest artifact SHA-256 is invalid")
    artifact_path = require_external_artifact(data_root / relative_path, data_root)
    if artifact_path.stat().st_size != declared_bytes:
        raise FullSnapshotDryRunError("current-snapshot artifact byte count does not match retrieval manifest")
    return artifact_path, declared_bytes, declared_sha256


def _sample_text(path: Path, encoding: str, sample_chars: int = 128_000) -> str:
    with path.open("r", encoding=encoding, errors="strict", newline="") as handle:
        return handle.read(sample_chars)


def _expected_categories(summary: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    categories = summary.get("categories")
    if not isinstance(categories, list):
        raise FullSnapshotDryRunError("observed snapshot summary categories are missing")
    by_source = {
        str(item.get("source_key")): dict(item)
        for item in categories
        if isinstance(item, Mapping) and item.get("source_key") in V1_SOURCE_KEYS
    }
    if set(by_source) != V1_SOURCE_KEYS:
        raise FullSnapshotDryRunError("observed snapshot summary does not exactly cover v1 sources")
    return by_source


def _validate_expected_artifact(
    *,
    source_key: str,
    expected: Mapping[str, Any],
    artifact_bytes: int,
    artifact_sha256: str,
) -> int:
    expected_rows = expected.get("rows")
    expected_bytes = expected.get("bytes")
    expected_sha256 = expected.get("artifact_sha256")
    if not isinstance(expected_rows, int) or expected_rows < 1:
        raise FullSnapshotDryRunError(f"{source_key}: expected snapshot row count is invalid")
    if expected_bytes != artifact_bytes:
        raise FullSnapshotDryRunError(f"{source_key}: latest artifact byte count differs from observed summary")
    if expected_sha256 != artifact_sha256:
        raise FullSnapshotDryRunError(f"{source_key}: latest artifact SHA-256 differs from observed summary")
    return expected_rows


def _flush_uniqueness_batch(
    connection: sqlite3.Connection,
    pending_management_numbers: list[str],
) -> None:
    if not pending_management_numbers:
        return
    before = connection.total_changes
    connection.executemany(
        "INSERT OR IGNORE INTO linkage(management_number) VALUES (?)",
        ((value,) for value in pending_management_numbers),
    )
    inserted = connection.total_changes - before
    if inserted != len(pending_management_numbers):
        raise FullSnapshotDryRunError(
            "duplicate expected uniqueness candidate encountered during full-snapshot dry run"
        )
    connection.commit()
    pending_management_numbers.clear()


def _percent(value: int, total: int) -> str:
    if total <= 0:
        return "100.0%"
    return f"{100.0 * value / total:.1f}%"


def format_full_dry_run_progress(event: Mapping[str, Any]) -> str:
    """Render aggregate-only progress; never include row values or identifiers."""
    kind = str(event.get("event") or "")
    index = int(event.get("task_index", 1))
    total_tasks = int(event.get("task_total", 1))
    source_key = str(event.get("source_key") or "")
    prefix = f"[{index}/{total_tasks}]"
    expected_rows = int(event.get("expected_rows", 0))
    rows_processed = int(event.get("rows_processed", 0))
    overall_rows_processed = int(event.get("overall_rows_processed", 0))
    overall_expected_rows = int(event.get("overall_expected_rows", 0))

    if kind == "task_start":
        return f"{prefix} START {source_key} full dry-run rows={expected_rows:,}"
    if kind == "row_progress":
        return (
            f"{prefix} ROWS {source_key} {rows_processed:,}/{expected_rows:,} "
            f"({_percent(rows_processed, expected_rows)}) | overall "
            f"{overall_rows_processed:,}/{overall_expected_rows:,} "
            f"({_percent(overall_rows_processed, overall_expected_rows)})"
        )
    if kind == "task_complete":
        return (
            f"{prefix} DONE {source_key} rows={rows_processed:,} | overall "
            f"{overall_rows_processed:,}/{overall_expected_rows:,} "
            f"({_percent(overall_rows_processed, overall_expected_rows)})"
        )
    return f"{prefix} {kind or 'PROGRESS'} {source_key}".strip()


def dry_run_full_snapshot(
    manifest_path: str | Path,
    *,
    expected: Mapping[str, Any],
    data_root: str | Path | None = None,
    progress_every_rows: int = DEFAULT_PROGRESS_EVERY_ROWS,
    sqlite_batch_rows: int = DEFAULT_SQLITE_BATCH_ROWS,
    progress: ProgressCallback | None = None,
    task_index: int = 1,
    task_total: int = 1,
    overall_rows_before: int = 0,
    overall_expected_rows: int | None = None,
) -> dict[str, Any]:
    """Stream one full snapshot through the PERMIT transformer without materializing output."""
    if progress_every_rows < 1:
        raise FullSnapshotDryRunError("progress_every_rows must be positive")
    if sqlite_batch_rows < 1:
        raise FullSnapshotDryRunError("sqlite_batch_rows must be positive")

    root = resolve_data_root(data_root)
    manifest_file = require_external_artifact(manifest_path, root)
    manifest = _load_manifest(manifest_file)
    context = permit_transform_context_from_retrieval_manifest(manifest)
    artifact_path, artifact_bytes, artifact_sha256 = _artifact_from_manifest(
        manifest,
        data_root=root,
    )
    expected_rows = _validate_expected_artifact(
        source_key=context.source_key,
        expected=expected,
        artifact_bytes=artifact_bytes,
        artifact_sha256=artifact_sha256,
    )
    overall_expected = overall_expected_rows if overall_expected_rows is not None else expected_rows

    encoding_info = detect_encoding(artifact_path)
    encoding = str(encoding_info["selected"])
    dialect = sniff_dialect(_sample_text(artifact_path, encoding))

    temp_root = root / ".tmp" / "canonical-full-dry-run"
    temp_root.mkdir(parents=True, exist_ok=True)
    sqlite_path = temp_root / f"{context.source_key}-{os.getpid()}.sqlite3"
    if sqlite_path.exists():
        sqlite_path.unlink()

    permit_quality: Counter[str] = Counter()
    closure_quality: Counter[str] = Counter()
    null_x = 0
    null_y = 0
    rows_processed = 0
    pending_management_numbers: list[str] = []
    connection: sqlite3.Connection | None = None

    if progress is not None:
        progress(
            {
                "event": "task_start",
                "task_index": task_index,
                "task_total": task_total,
                "source_key": context.source_key,
                "expected_rows": expected_rows,
                "rows_processed": 0,
                "overall_rows_processed": overall_rows_before,
                "overall_expected_rows": overall_expected,
            }
        )

    try:
        connection = sqlite3.connect(sqlite_path)
        connection.execute("PRAGMA journal_mode=OFF")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute("PRAGMA temp_store=MEMORY")
        connection.execute(
            "CREATE TABLE linkage (management_number TEXT PRIMARY KEY) WITHOUT ROWID"
        )

        with artifact_path.open("r", encoding=encoding, errors="strict", newline="") as handle:
            reader = csv.reader(
                handle,
                delimiter=str(dialect["delimiter"]),
                quotechar=str(dialect["quotechar"]),
                doublequote=bool(dialect["doublequote"]),
                escapechar=dialect["escapechar"],
                strict=True,
            )
            try:
                header = next(reader)
            except StopIteration as exc:
                raise FullSnapshotDryRunError("current-snapshot CSV is empty") from exc
            if len(header) != len(set(header)):
                raise FullSnapshotDryRunError("current-snapshot CSV contains duplicate header names")
            if len(header) != 39 or set(header) != FROZEN_V1_SOURCE_COLUMNS:
                raise FullSnapshotDryRunError(
                    "current-snapshot CSV header does not match the frozen 39-column inventory"
                )

            for source_row_number, values in enumerate(reader, start=1):
                if len(values) != len(header):
                    raise FullSnapshotDryRunError(
                        f"current-snapshot CSV row width differs from frozen inventory at source row {source_row_number}"
                    )
                raw_row = dict(zip(header, values))
                try:
                    canonical = transform_permit_row(
                        raw_row,
                        context=context,
                        source_row_number=source_row_number,
                    )
                except PermitTransformError as exc:
                    raise FullSnapshotDryRunError(
                        f"PERMIT transform failed at source row {source_row_number}: {exc}"
                    ) from exc

                pending_management_numbers.append(str(canonical["management_number"]))
                permit_quality[str(canonical["permit_date_quality"])] += 1
                closure_quality[str(canonical["closure_date_quality"])] += 1
                null_x += int(canonical["source_coordinate_x"] is None)
                null_y += int(canonical["source_coordinate_y"] is None)
                rows_processed += 1

                if len(pending_management_numbers) >= sqlite_batch_rows:
                    _flush_uniqueness_batch(connection, pending_management_numbers)

                if rows_processed > expected_rows:
                    raise FullSnapshotDryRunError(
                        f"{context.source_key}: full scan exceeded expected row count from observed summary"
                    )

                if progress is not None and (
                    rows_processed % progress_every_rows == 0 or rows_processed == expected_rows
                ):
                    progress(
                        {
                            "event": "row_progress",
                            "task_index": task_index,
                            "task_total": task_total,
                            "source_key": context.source_key,
                            "expected_rows": expected_rows,
                            "rows_processed": rows_processed,
                            "overall_rows_processed": overall_rows_before + rows_processed,
                            "overall_expected_rows": overall_expected,
                        }
                    )

        _flush_uniqueness_batch(connection, pending_management_numbers)
        if rows_processed != expected_rows:
            raise FullSnapshotDryRunError(
                f"{context.source_key}: full scan row count differs from observed summary"
            )
    except (csv.Error, UnicodeDecodeError) as exc:
        raise FullSnapshotDryRunError("full current-snapshot CSV parse/decode failed") from exc
    finally:
        if connection is not None:
            connection.close()
        if sqlite_path.exists():
            sqlite_path.unlink()

    if progress is not None:
        progress(
            {
                "event": "task_complete",
                "task_index": task_index,
                "task_total": task_total,
                "source_key": context.source_key,
                "expected_rows": expected_rows,
                "rows_processed": rows_processed,
                "overall_rows_processed": overall_rows_before + rows_processed,
                "overall_expected_rows": overall_expected,
            }
        )

    return {
        "source_key": context.source_key,
        "retrieval_id": manifest.get("retrieval_id"),
        "artifact_sha256": artifact_sha256,
        "artifact_bytes": artifact_bytes,
        "expected_rows": expected_rows,
        "rows_examined": rows_processed,
        "rows_transformed": rows_processed,
        "encoding": encoding,
        "source_column_count": len(FROZEN_V1_SOURCE_COLUMNS),
        "output_column_count": len(REQUIRED_CANONICAL_COLUMNS),
        "permit_date_quality": dict(sorted(permit_quality.items())),
        "closure_date_quality": dict(sorted(closure_quality.items())),
        "null_source_coordinate_x": null_x,
        "null_source_coordinate_y": null_y,
        "duplicate_linkage_candidates": 0,
        "uniqueness_backend": "EPHEMERAL_SQLITE_EXACT_TEXT_PRIMARY_KEY",
        "temporary_uniqueness_index_removed": not sqlite_path.exists(),
        "row_level_values_returned": False,
        "production_materialization_performed": False,
        "status": "PASS",
    }


def full_dry_run_plan(
    *,
    source_keys: Sequence[str] = V1_SOURCE_ORDER,
    observed_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    summary = observed_summary or load_observed_snapshot_summary()
    expected_by_source = _expected_categories(summary)
    selected = tuple(source_keys)
    if not selected or any(source_key not in V1_SOURCE_KEYS for source_key in selected):
        raise FullSnapshotDryRunError("source_keys must contain one or more v1 sources")
    sources = [
        {
            "source_key": source_key,
            "artifact_sha256": expected_by_source[source_key]["artifact_sha256"],
            "artifact_bytes": expected_by_source[source_key]["bytes"],
            "expected_rows": expected_by_source[source_key]["rows"],
        }
        for source_key in selected
    ]
    return {
        "scope": list(selected),
        "sources": sources,
        "expected_rows_total": sum(int(item["expected_rows"]) for item in sources),
        "production_materialization_performed": False,
        "row_level_values_returned": False,
        "network_access_required": False,
        "status": "READY_FOR_USER_EXECUTION",
    }


def dry_run_latest_full_snapshots(
    *,
    data_root: str | Path | None = None,
    source_keys: Sequence[str] = V1_SOURCE_ORDER,
    progress_every_rows: int = DEFAULT_PROGRESS_EVERY_ROWS,
    sqlite_batch_rows: int = DEFAULT_SQLITE_BATCH_ROWS,
    progress: ProgressCallback | None = None,
    observed_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    summary = observed_summary or load_observed_snapshot_summary()
    expected_by_source = _expected_categories(summary)
    selected = tuple(source_keys)
    if not selected or any(source_key not in V1_SOURCE_KEYS for source_key in selected):
        raise FullSnapshotDryRunError("source_keys must contain one or more v1 sources")

    expected_total = sum(int(expected_by_source[source_key]["rows"]) for source_key in selected)
    results: list[dict[str, Any]] = []
    overall_before = 0
    for index, source_key in enumerate(selected, start=1):
        result = dry_run_full_snapshot(
            latest_retrieval_manifest(source_key, data_root=root),
            expected=expected_by_source[source_key],
            data_root=root,
            progress_every_rows=progress_every_rows,
            sqlite_batch_rows=sqlite_batch_rows,
            progress=progress,
            task_index=index,
            task_total=len(selected),
            overall_rows_before=overall_before,
            overall_expected_rows=expected_total,
        )
        results.append(result)
        overall_before += int(result["rows_examined"])

    return {
        "scope": list(selected),
        "full_snapshot_scan_performed": True,
        "expected_rows_total": expected_total,
        "rows_examined_total": sum(int(item["rows_examined"]) for item in results),
        "rows_transformed_total": sum(int(item["rows_transformed"]) for item in results),
        "duplicate_linkage_candidates": sum(
            int(item["duplicate_linkage_candidates"]) for item in results
        ),
        "production_materialization_performed": False,
        "row_level_values_returned": False,
        "results": results,
        "status": "PASS",
    }
