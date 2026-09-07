from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .canonical_compatibility import V1_SOURCE_ORDER
from .canonical_materialization import (
    COMPRESSION,
    _build_id,
    _pyarrow_modules,
    _schema_sha256,
    _sha256_file,
    _validated_full_dry_run,
    _writer_contract,
    permit_arrow_schema,
)
from .provenance import load_permit_parent_full_dry_run
from .storage import is_within, resolve_data_root


class PermitBuildVerificationError(RuntimeError):
    """Raised when an immutable local PERMIT build fails independent verification."""


def _load_build_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PermitBuildVerificationError("PERMIT build manifest cannot be read as JSON") from exc
    if not isinstance(value, dict):
        raise PermitBuildVerificationError("PERMIT build manifest must be a JSON object")
    return value


def expected_permit_build_id(evidence: Mapping[str, Any] | None = None) -> str:
    return _build_id(evidence or load_permit_parent_full_dry_run())


def verify_permit_parent_build(
    *,
    data_root: str | Path | None = None,
    build_id: str | None = None,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    selected_evidence = evidence or load_permit_parent_full_dry_run()
    approved = _validated_full_dry_run(selected_evidence)
    expected_build_id = _build_id(selected_evidence)
    selected_build_id = build_id or expected_build_id
    if selected_build_id != expected_build_id:
        raise PermitBuildVerificationError("requested build_id does not match the deterministic approved build")

    build_dir = root / "canonical" / "permit" / "v1" / selected_build_id
    if not is_within(build_dir, root):
        raise PermitBuildVerificationError("PERMIT build directory escaped KBL_DATA_ROOT")
    if not build_dir.is_dir():
        raise PermitBuildVerificationError("expected immutable PERMIT build directory does not exist")
    manifest_path = build_dir / "manifest.json"
    manifest = _load_build_manifest(manifest_path)

    if manifest.get("manifest_version") != 1:
        raise PermitBuildVerificationError("PERMIT build manifest version changed")
    if manifest.get("build_id") != expected_build_id:
        raise PermitBuildVerificationError("PERMIT build manifest build_id mismatch")
    if manifest.get("grain") != "PERMIT":
        raise PermitBuildVerificationError("PERMIT build grain changed")
    if manifest.get("schema") != "schemas/permit_parent.v1.json":
        raise PermitBuildVerificationError("PERMIT build schema reference changed")
    if manifest.get("permit_schema_sha256") != _schema_sha256():
        raise PermitBuildVerificationError("PERMIT build schema SHA-256 mismatch")
    if manifest.get("full_dry_run_evidence") != "provenance/permit_parent_full_dry_run.json":
        raise PermitBuildVerificationError("PERMIT build full-dry-run evidence reference changed")
    if manifest.get("writer_contract") != _writer_contract():
        raise PermitBuildVerificationError("PERMIT build writer contract changed")
    if manifest.get("production_materialization_performed") is not True:
        raise PermitBuildVerificationError("PERMIT build manifest does not record production materialization")
    if manifest.get("public_row_level_release_approved") is not False:
        raise PermitBuildVerificationError("PERMIT build must keep public row-level release blocked")
    if manifest.get("wgs84_generated") is not False:
        raise PermitBuildVerificationError("PERMIT build must not contain derived WGS84 columns")
    if manifest.get("episode_reconstruction_performed") is not False:
        raise PermitBuildVerificationError("PERMIT build must not claim episode reconstruction")
    if manifest.get("status") != "PASS":
        raise PermitBuildVerificationError("PERMIT build manifest status is not PASS")

    expected_total = sum(int(approved[key]["expected_rows"]) for key in V1_SOURCE_ORDER)
    if manifest.get("rows_total") != expected_total or manifest.get("source_count") != 3:
        raise PermitBuildVerificationError("PERMIT build manifest row/source totals changed")
    results = manifest.get("results")
    if not isinstance(results, list) or len(results) != 3:
        raise PermitBuildVerificationError("PERMIT build manifest must contain three source results")
    by_source = {
        str(item.get("source_key")): dict(item)
        for item in results
        if isinstance(item, Mapping) and item.get("source_key") in V1_SOURCE_ORDER
    }
    if set(by_source) != set(V1_SOURCE_ORDER):
        raise PermitBuildVerificationError("PERMIT build result source scope changed")

    _, pq = _pyarrow_modules()
    arrow_schema = permit_arrow_schema()
    verified_results: list[dict[str, Any]] = []
    for source_key in V1_SOURCE_ORDER:
        item = by_source[source_key]
        expected = approved[source_key]
        if item.get("status") != "PASS":
            raise PermitBuildVerificationError(f"{source_key}: build result status is not PASS")
        if item.get("input_retrieval_id") != expected.get("retrieval_id"):
            raise PermitBuildVerificationError(f"{source_key}: input retrieval id mismatch")
        if item.get("input_artifact_sha256") != expected.get("artifact_sha256"):
            raise PermitBuildVerificationError(f"{source_key}: input artifact SHA-256 mismatch")
        if item.get("input_artifact_bytes") != expected.get("artifact_bytes"):
            raise PermitBuildVerificationError(f"{source_key}: input artifact byte count mismatch")
        if item.get("rows") != expected.get("expected_rows"):
            raise PermitBuildVerificationError(f"{source_key}: materialized row count mismatch")
        if item.get("permit_date_quality") != expected.get("permit_date_quality"):
            raise PermitBuildVerificationError(f"{source_key}: permit-date quality aggregate mismatch")
        if item.get("closure_date_quality") != expected.get("closure_date_quality"):
            raise PermitBuildVerificationError(f"{source_key}: closure-date quality aggregate mismatch")
        if item.get("null_source_coordinate_x") != expected.get("null_source_coordinate_x"):
            raise PermitBuildVerificationError(f"{source_key}: null X aggregate mismatch")
        if item.get("null_source_coordinate_y") != expected.get("null_source_coordinate_y"):
            raise PermitBuildVerificationError(f"{source_key}: null Y aggregate mismatch")
        if item.get("uniqueness_validation") != "REUSED_EXACT_FULL_DRY_RUN_FOR_IDENTICAL_SHA256":
            raise PermitBuildVerificationError(f"{source_key}: uniqueness proof reference changed")

        expected_filename = f"{source_key}.parquet"
        if item.get("output_file") != expected_filename:
            raise PermitBuildVerificationError(f"{source_key}: output filename changed")
        parquet_path = build_dir / expected_filename
        if not is_within(parquet_path, build_dir) or not parquet_path.is_file():
            raise PermitBuildVerificationError(f"{source_key}: Parquet output is missing or escaped build directory")
        actual_bytes = parquet_path.stat().st_size
        if actual_bytes != item.get("output_bytes"):
            raise PermitBuildVerificationError(f"{source_key}: Parquet output byte count mismatch")
        actual_sha256 = _sha256_file(parquet_path)
        if actual_sha256 != item.get("output_sha256"):
            raise PermitBuildVerificationError(f"{source_key}: Parquet output SHA-256 mismatch")

        parquet_file = pq.ParquetFile(parquet_path)
        if parquet_file.metadata.num_rows != expected.get("expected_rows"):
            raise PermitBuildVerificationError(f"{source_key}: Parquet metadata row count mismatch")
        if parquet_file.metadata.num_row_groups != item.get("parquet_row_groups"):
            raise PermitBuildVerificationError(f"{source_key}: Parquet row-group count mismatch")
        if not pq.read_schema(parquet_path).equals(arrow_schema, check_metadata=True):
            raise PermitBuildVerificationError(f"{source_key}: Parquet Arrow schema mismatch")
        for row_group_index in range(parquet_file.metadata.num_row_groups):
            row_group = parquet_file.metadata.row_group(row_group_index)
            for column_index in range(row_group.num_columns):
                if row_group.column(column_index).compression != COMPRESSION.upper():
                    raise PermitBuildVerificationError(f"{source_key}: Parquet compression changed")

        verified_results.append(
            {
                "source_key": source_key,
                "rows": int(item["rows"]),
                "output_bytes": actual_bytes,
                "output_sha256": actual_sha256,
                "parquet_row_groups": parquet_file.metadata.num_row_groups,
                "schema_verified": True,
                "zstd_verified": True,
                "quality_aggregates_match_full_dry_run": True,
                "status": "PASS",
            }
        )

    return {
        "build_id": expected_build_id,
        "build_directory": str(build_dir),
        "rows_verified_total": sum(int(item["rows"]) for item in verified_results),
        "output_bytes_total": sum(int(item["output_bytes"]) for item in verified_results),
        "source_count": len(verified_results),
        "results": verified_results,
        "permit_schema_sha256": _schema_sha256(),
        "writer_contract": _writer_contract(),
        "manifest_verified": True,
        "parquet_hashes_verified": True,
        "parquet_schemas_verified": True,
        "zstd_verified": True,
        "quality_aggregates_match_full_dry_run": True,
        "public_row_level_release_approved": False,
        "wgs84_generated": False,
        "episode_reconstruction_performed": False,
        "row_level_values_returned": False,
        "status": "PASS",
    }
