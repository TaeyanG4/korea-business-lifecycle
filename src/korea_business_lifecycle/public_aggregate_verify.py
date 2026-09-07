from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .canonical_materialization import COMPRESSION, _pyarrow_modules, _sha256_file
from .canonical_materialization_verify import expected_permit_build_id, verify_permit_parent_build
from .provenance import load_permit_parent_full_dry_run
from .public_aggregate import (
    MIN_CELL_COUNT,
    _build_id,
    _schema_sha256,
    _writer_contract,
    public_aggregate_arrow_schema,
)
from .storage import is_within, resolve_data_root


class PublicAggregateVerificationError(RuntimeError):
    """Raised when a local privacy-minimized aggregate candidate fails verification."""


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicAggregateVerificationError("public aggregate manifest cannot be read") from exc
    if not isinstance(value, dict):
        raise PublicAggregateVerificationError("public aggregate manifest must be an object")
    return value


def verify_public_permit_aggregate(
    *,
    data_root: str | Path | None = None,
    parent_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    evidence = parent_evidence or load_permit_parent_full_dry_run()
    parent_build_id = expected_permit_build_id(evidence)
    verified_parent = verify_permit_parent_build(data_root=root, evidence=evidence)
    if verified_parent.get("status") != "PASS":
        raise PublicAggregateVerificationError("parent PERMIT verification failed")

    build_id = _build_id(parent_build_id)
    build_dir = root / "public_candidate" / "permit_aggregate" / "v1" / build_id
    if not is_within(build_dir, root) or not build_dir.is_dir():
        raise PublicAggregateVerificationError("expected public aggregate build directory does not exist")
    manifest = _load_manifest(build_dir / "manifest.json")

    expected_fields = {
        "manifest_version": 1,
        "build_id": build_id,
        "grain": "PRIVACY_MINIMIZED_PERMIT_AGGREGATE_CELL",
        "schema": "schemas/public_permit_aggregate.v1.json",
        "schema_sha256": _schema_sha256(),
        "parent_permit_build_id": parent_build_id,
        "parent_build_verified": True,
        "rows_scanned": int(verified_parent["rows_verified_total"]),
        "minimum_cell_count": MIN_CELL_COUNT,
        "writer_contract": _writer_contract(),
        "row_level_values_written": False,
        "row_level_public_projection_approved": False,
        "aggregate_publication_approved": False,
        "redistribution_status": "UNRESOLVED",
        "status": "PASS",
    }
    for key, value in expected_fields.items():
        if manifest.get(key) != value:
            raise PublicAggregateVerificationError(f"public aggregate manifest field changed: {key}")

    released_rows = int(manifest.get("released_source_rows", -1))
    suppressed_rows = int(manifest.get("suppressed_source_rows", -1))
    if released_rows + suppressed_rows != int(verified_parent["rows_verified_total"]):
        raise PublicAggregateVerificationError("public aggregate suppression accounting changed")
    released_cells = int(manifest.get("aggregate_cells_released_candidate", -1))
    suppressed_cells = int(manifest.get("aggregate_cells_suppressed", -1))
    total_cells = int(manifest.get("aggregate_cells_total_before_suppression", -1))
    if released_cells < 0 or suppressed_cells < 0 or released_cells + suppressed_cells != total_cells:
        raise PublicAggregateVerificationError("public aggregate cell accounting changed")

    output_path = build_dir / "permit_aggregate.parquet"
    if not output_path.is_file() or not is_within(output_path, build_dir):
        raise PublicAggregateVerificationError("public aggregate Parquet output is missing")
    if output_path.stat().st_size != manifest.get("output_bytes"):
        raise PublicAggregateVerificationError("public aggregate Parquet byte count mismatch")
    if _sha256_file(output_path) != manifest.get("output_sha256"):
        raise PublicAggregateVerificationError("public aggregate Parquet SHA-256 mismatch")

    _, pq = _pyarrow_modules()
    arrow_schema = public_aggregate_arrow_schema()
    if not pq.read_schema(output_path).equals(arrow_schema, check_metadata=True):
        raise PublicAggregateVerificationError("public aggregate Arrow schema mismatch")
    parquet_file = pq.ParquetFile(output_path)
    try:
        if parquet_file.metadata.num_rows != released_cells:
            raise PublicAggregateVerificationError("public aggregate Parquet row count mismatch")
        for row_group_index in range(parquet_file.metadata.num_row_groups):
            row_group = parquet_file.metadata.row_group(row_group_index)
            for column_index in range(row_group.num_columns):
                if row_group.column(column_index).compression != COMPRESSION.upper():
                    raise PublicAggregateVerificationError("public aggregate compression changed")

        observed_released_rows = 0
        observed_cells = 0
        for batch in parquet_file.iter_batches(batch_size=50_000, columns=["cell_count"]):
            values = batch.column(0).to_pylist()
            if any(value is None or int(value) < MIN_CELL_COUNT for value in values):
                raise PublicAggregateVerificationError("public aggregate contains an unsuppressed small cell")
            observed_cells += len(values)
            observed_released_rows += sum(int(value) for value in values)
    finally:
        close = getattr(parquet_file, "close", None)
        if callable(close):
            close()

    if observed_cells != released_cells or observed_released_rows != released_rows:
        raise PublicAggregateVerificationError("public aggregate content totals differ from manifest")

    return {
        "build_id": build_id,
        "parent_permit_build_id": parent_build_id,
        "rows_scanned": int(verified_parent["rows_verified_total"]),
        "aggregate_cells_released_candidate": observed_cells,
        "released_source_rows": observed_released_rows,
        "suppressed_source_rows": suppressed_rows,
        "minimum_cell_count": MIN_CELL_COUNT,
        "output_bytes": output_path.stat().st_size,
        "manifest_verified": True,
        "parquet_hash_verified": True,
        "parquet_schema_verified": True,
        "zstd_verified": True,
        "suppression_invariants_verified": True,
        "row_level_values_returned": False,
        "aggregate_publication_approved": False,
        "redistribution_status": "UNRESOLVED",
        "status": "PASS",
    }
