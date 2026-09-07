from __future__ import annotations

import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping

from .canonical_compatibility import V1_SOURCE_ORDER
from .canonical_materialization import (
    COMPRESSION,
    COMPRESSION_LEVEL,
    DATA_PAGE_VERSION,
    PARQUET_VERSION,
    PYARROW_VERSION,
    ROWS_PER_BATCH,
    ROWS_PER_ROW_GROUP,
    _pyarrow_modules,
    _sha256_file,
)
from .canonical_materialization_verify import expected_permit_build_id, verify_permit_parent_build
from .canonical_schema import load_public_permit_aggregate_schema
from .config import project_root
from .provenance import load_permit_parent_full_dry_run
from .storage import is_within, resolve_data_root


MIN_CELL_COUNT = 10
ProgressCallback = Callable[[dict[str, Any]], None]


class PublicAggregateError(RuntimeError):
    """Raised when a privacy-minimized aggregate candidate cannot be built safely."""


def _schema_sha256() -> str:
    return _sha256_file(project_root() / "schemas" / "public_permit_aggregate.v1.json")


def _writer_contract() -> dict[str, Any]:
    return {
        "pyarrow_version": PYARROW_VERSION,
        "format": "PARQUET",
        "parquet_version": PARQUET_VERSION,
        "compression": COMPRESSION.upper(),
        "compression_level": COMPRESSION_LEVEL,
        "data_page_version": DATA_PAGE_VERSION,
        "rows_per_batch": ROWS_PER_BATCH,
        "rows_per_row_group": ROWS_PER_ROW_GROUP,
        "minimum_cell_count": MIN_CELL_COUNT,
    }


def public_aggregate_arrow_schema():
    pa, _ = _pyarrow_modules()
    logical_types = {
        "string": pa.string(),
        "int32": pa.int32(),
        "int64": pa.int64(),
    }
    schema = load_public_permit_aggregate_schema()
    fields = [
        pa.field(
            str(item["name"]),
            logical_types[str(item["logical_type"])],
            nullable=bool(item["nullable"]),
        )
        for item in schema["columns"]
    ]
    metadata = {
        b"kbl.schema_name": b"public_permit_aggregate",
        b"kbl.schema_version": b"1",
        b"kbl.grain": b"PRIVACY_MINIMIZED_PERMIT_AGGREGATE_CELL",
        b"kbl.minimum_cell_count": str(MIN_CELL_COUNT).encode("ascii"),
        b"kbl.publication_status": b"LOCAL_CANDIDATE_ONLY_REDISTRIBUTION_UNRESOLVED",
    }
    return pa.schema(fields, metadata=metadata)


def _build_id(parent_build_id: str) -> str:
    payload = {
        "aggregate_version": 1,
        "parent_permit_build_id": parent_build_id,
        "schema_sha256": _schema_sha256(),
        "writer_contract": _writer_contract(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"permit-public-agg-v1-{hashlib.sha256(encoded).hexdigest()[:16]}"


def public_aggregate_plan(
    *,
    data_root: str | Path | None = None,
    parent_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    evidence = parent_evidence or load_permit_parent_full_dry_run()
    parent_build_id = expected_permit_build_id(evidence)
    build_id = _build_id(parent_build_id)
    final_dir = root / "public_candidate" / "permit_aggregate" / "v1" / build_id
    return {
        "build_id": build_id,
        "parent_permit_build_id": parent_build_id,
        "expected_parent_rows": int(evidence["scope"]["rows_examined_total"]),
        "minimum_cell_count": MIN_CELL_COUNT,
        "schema_sha256": _schema_sha256(),
        "writer_contract": _writer_contract(),
        "output_directory": str(final_dir),
        "output_directory_exists": final_dir.exists(),
        "row_level_public_projection_approved": False,
        "aggregate_publication_approved": False,
        "redistribution_status": "UNRESOLVED",
        "network_access_required": False,
        "status": "READY_FOR_USER_EXECUTION" if not final_dir.exists() else "OUTPUT_ALREADY_EXISTS",
    }


def _percent(value: int, total: int) -> str:
    if total <= 0:
        return "100.0%"
    return f"{100.0 * value / total:.1f}%"


def format_public_aggregate_progress(event: Mapping[str, Any]) -> str:
    kind = str(event.get("event") or "")
    source_key = str(event.get("source_key") or "")
    index = int(event.get("task_index", 1))
    total_tasks = int(event.get("task_total", len(V1_SOURCE_ORDER)))
    prefix = f"[{index}/{total_tasks}]"
    rows = int(event.get("rows_scanned", 0))
    expected = int(event.get("expected_rows", 0))
    overall = int(event.get("overall_rows_scanned", 0))
    overall_expected = int(event.get("overall_expected_rows", 0))
    if kind == "parent_verify_start":
        return "[VERIFY] parent PERMIT START"
    if kind == "parent_verify_complete":
        return "[VERIFY] parent PERMIT PASS"
    if kind == "task_start":
        return f"{prefix} START {source_key} aggregate scan rows={expected:,}"
    if kind == "row_progress":
        return (
            f"{prefix} SCAN {source_key} {rows:,}/{expected:,} ({_percent(rows, expected)}) | "
            f"overall {overall:,}/{overall_expected:,} ({_percent(overall, overall_expected)})"
        )
    if kind == "task_complete":
        return f"{prefix} DONE {source_key} rows={rows:,}"
    if kind == "write_start":
        return f"[WRITE] released aggregate cells={int(event.get('aggregate_cells', 0)):,}"
    if kind == "write_complete":
        return "[WRITE] aggregate candidate PASS"
    return f"{prefix} {kind or 'PROGRESS'} {source_key}".strip()


def _sort_key(key: tuple[Any, ...]) -> tuple[str, ...]:
    return tuple("" if value is None else str(value) for value in key)


def materialize_public_permit_aggregate(
    *,
    data_root: str | Path | None = None,
    parent_evidence: Mapping[str, Any] | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    evidence = parent_evidence or load_permit_parent_full_dry_run()
    parent_build_id = expected_permit_build_id(evidence)
    build_id = _build_id(parent_build_id)
    final_dir = root / "public_candidate" / "permit_aggregate" / "v1" / build_id
    if final_dir.exists():
        raise PublicAggregateError("final public aggregate candidate directory already exists")

    if progress is not None:
        progress({"event": "parent_verify_start"})
    verified_parent = verify_permit_parent_build(data_root=root, evidence=evidence)
    if verified_parent.get("status") != "PASS" or verified_parent.get("build_id") != parent_build_id:
        raise PublicAggregateError("independent parent PERMIT verification did not pass")
    if progress is not None:
        progress({"event": "parent_verify_complete"})

    expected_total = int(verified_parent["rows_verified_total"])
    parent_by_source = {item["source_key"]: item for item in verified_parent["results"]}
    counts: Counter[tuple[Any, ...]] = Counter()
    rows_scanned_total = 0
    _, pq = _pyarrow_modules()

    for task_index, source_key in enumerate(V1_SOURCE_ORDER, start=1):
        expected_rows = int(parent_by_source[source_key]["rows"])
        parent_path = root / "canonical" / "permit" / "v1" / parent_build_id / f"{source_key}.parquet"
        if progress is not None:
            progress(
                {
                    "event": "task_start",
                    "task_index": task_index,
                    "task_total": len(V1_SOURCE_ORDER),
                    "source_key": source_key,
                    "expected_rows": expected_rows,
                }
            )
        source_rows = 0
        parquet_file = pq.ParquetFile(parent_path)
        try:
            for batch in parquet_file.iter_batches(
                batch_size=ROWS_PER_BATCH,
                columns=[
                    "source_key",
                    "authority_code",
                    "source_status_code",
                    "source_detail_status_code",
                    "permit_date",
                    "closure_date",
                ],
            ):
                names = batch.schema.names
                columns = {name: batch.column(names.index(name)).to_pylist() for name in names}
                for idx in range(batch.num_rows):
                    observed_source = columns["source_key"][idx]
                    authority_code = columns["authority_code"][idx]
                    if observed_source != source_key:
                        raise PublicAggregateError(f"{source_key}: parent source_key values changed")
                    if authority_code is None or str(authority_code) == "":
                        raise PublicAggregateError(f"{source_key}: authority_code is null/blank")
                    permit_date = columns["permit_date"][idx]
                    closure_date = columns["closure_date"][idx]
                    key = (
                        source_key,
                        str(authority_code),
                        columns["source_status_code"][idx],
                        columns["source_detail_status_code"][idx],
                        permit_date.year if permit_date is not None else None,
                        closure_date.year if closure_date is not None else None,
                    )
                    counts[key] += 1
                source_rows += batch.num_rows
                rows_scanned_total += batch.num_rows
                if source_rows > expected_rows or rows_scanned_total > expected_total:
                    raise PublicAggregateError("parent row count exceeded verified totals")
                if progress is not None:
                    progress(
                        {
                            "event": "row_progress",
                            "task_index": task_index,
                            "task_total": len(V1_SOURCE_ORDER),
                            "source_key": source_key,
                            "rows_scanned": source_rows,
                            "expected_rows": expected_rows,
                            "overall_rows_scanned": rows_scanned_total,
                            "overall_expected_rows": expected_total,
                        }
                    )
        finally:
            close = getattr(parquet_file, "close", None)
            if callable(close):
                close()
        if source_rows != expected_rows:
            raise PublicAggregateError(f"{source_key}: parent row count changed")
        if progress is not None:
            progress(
                {
                    "event": "task_complete",
                    "task_index": task_index,
                    "task_total": len(V1_SOURCE_ORDER),
                    "source_key": source_key,
                    "rows_scanned": source_rows,
                    "expected_rows": expected_rows,
                }
            )

    if rows_scanned_total != expected_total:
        raise PublicAggregateError("aggregate scan did not cover the verified parent")

    released = [(key, count) for key, count in counts.items() if count >= MIN_CELL_COUNT]
    suppressed = [(key, count) for key, count in counts.items() if count < MIN_CELL_COUNT]
    released.sort(key=lambda item: _sort_key(item[0]))
    released_source_rows = sum(count for _, count in released)
    suppressed_source_rows = sum(count for _, count in suppressed)
    if released_source_rows + suppressed_source_rows != expected_total:
        raise PublicAggregateError("suppression accounting does not cover parent rows")

    staging_dir = root / ".tmp" / "public-permit-aggregate" / f"{build_id}-{os.getpid()}"
    if staging_dir.exists():
        raise PublicAggregateError("unique public aggregate staging directory already exists")
    staging_dir.mkdir(parents=True)
    if not is_within(staging_dir, root):
        raise PublicAggregateError("public aggregate staging directory escaped KBL_DATA_ROOT")

    pa, pq = _pyarrow_modules()
    arrow_schema = public_aggregate_arrow_schema()
    output_path = staging_dir / "permit_aggregate.parquet"
    try:
        if progress is not None:
            progress({"event": "write_start", "aggregate_cells": len(released)})
        writer = pq.ParquetWriter(
            output_path,
            arrow_schema,
            version=PARQUET_VERSION,
            compression=COMPRESSION,
            compression_level=COMPRESSION_LEVEL,
            use_dictionary=True,
            write_statistics=True,
            data_page_version=DATA_PAGE_VERSION,
        )
        try:
            batch_rows: list[dict[str, Any]] = []
            for key, count in released:
                batch_rows.append(
                    {
                        "source_key": key[0],
                        "authority_code": key[1],
                        "source_status_code": key[2],
                        "source_detail_status_code": key[3],
                        "permit_year": key[4],
                        "closure_year": key[5],
                        "cell_count": count,
                    }
                )
                if len(batch_rows) >= ROWS_PER_BATCH:
                    writer.write_table(pa.Table.from_pylist(batch_rows, schema=arrow_schema), row_group_size=ROWS_PER_ROW_GROUP)
                    batch_rows.clear()
            if batch_rows:
                writer.write_table(pa.Table.from_pylist(batch_rows, schema=arrow_schema), row_group_size=ROWS_PER_ROW_GROUP)
        finally:
            writer.close()

        parquet_file = pq.ParquetFile(output_path)
        try:
            aggregate_rows = parquet_file.metadata.num_rows
            row_groups = parquet_file.metadata.num_row_groups
        finally:
            close = getattr(parquet_file, "close", None)
            if callable(close):
                close()
        if aggregate_rows != len(released):
            raise PublicAggregateError("public aggregate Parquet row count changed")
        if not pq.read_schema(output_path).equals(arrow_schema, check_metadata=True):
            raise PublicAggregateError("public aggregate Arrow schema mismatch")

        manifest = {
            "manifest_version": 1,
            "build_id": build_id,
            "grain": "PRIVACY_MINIMIZED_PERMIT_AGGREGATE_CELL",
            "schema": "schemas/public_permit_aggregate.v1.json",
            "schema_sha256": _schema_sha256(),
            "parent_permit_build_id": parent_build_id,
            "parent_build_verified": True,
            "rows_scanned": expected_total,
            "aggregate_cells_total_before_suppression": len(counts),
            "aggregate_cells_released_candidate": len(released),
            "aggregate_cells_suppressed": len(suppressed),
            "released_source_rows": released_source_rows,
            "suppressed_source_rows": suppressed_source_rows,
            "minimum_cell_count": MIN_CELL_COUNT,
            "output_file": output_path.name,
            "output_bytes": output_path.stat().st_size,
            "output_sha256": _sha256_file(output_path),
            "parquet_row_groups": row_groups,
            "writer_contract": _writer_contract(),
            "row_level_values_written": False,
            "row_level_public_projection_approved": False,
            "aggregate_publication_approved": False,
            "redistribution_status": "UNRESOLVED",
            "status": "PASS",
        }
        (staging_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        final_dir.parent.mkdir(parents=True, exist_ok=True)
        staging_dir.rename(final_dir)
        manifest["output_directory"] = str(final_dir)
        if progress is not None:
            progress({"event": "write_complete"})
        return manifest
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise
