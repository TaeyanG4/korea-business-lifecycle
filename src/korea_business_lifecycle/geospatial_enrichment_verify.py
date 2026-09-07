from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping

from .canonical_compatibility import V1_SOURCE_ORDER
from .canonical_materialization import COMPRESSION, _pyarrow_modules, _sha256_file
from .canonical_materialization_verify import (
    expected_permit_build_id,
    verify_permit_parent_build,
)
from .geospatial_enrichment import (
    BROAD_KOREA_LAT,
    BROAD_KOREA_LON,
    SOURCE_CRS,
    TARGET_CRS,
    _build_id,
    _schema_sha256,
    _validated_axis_review,
    _writer_contract,
    permit_geospatial_arrow_schema,
)
from .provenance import load_geospatial_full_axis, load_permit_parent_full_dry_run
from .storage import is_within, resolve_data_root


ProgressCallback = Callable[[dict[str, Any]], None]


class GeospatialBuildVerificationError(RuntimeError):
    """Raised when an immutable local WGS84 enrichment build fails verification."""


def expected_geospatial_build_id(
    *,
    parent_evidence: Mapping[str, Any] | None = None,
    axis_review: Mapping[str, Any] | None = None,
) -> str:
    selected_parent = parent_evidence or load_permit_parent_full_dry_run()
    selected_axis = axis_review or load_geospatial_full_axis()
    return _build_id(
        parent_build_id=expected_permit_build_id(selected_parent),
        axis_review=selected_axis,
    )


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GeospatialBuildVerificationError("geospatial build manifest cannot be read as JSON") from exc
    if not isinstance(value, dict):
        raise GeospatialBuildVerificationError("geospatial build manifest must be a JSON object")
    return value


def _percent(value: int, total: int) -> str:
    if total <= 0:
        return "100.0%"
    return f"{100.0 * value / total:.1f}%"


def format_geospatial_verification_progress(event: Mapping[str, Any]) -> str:
    kind = str(event.get("event") or "")
    if kind == "parent_verify_start":
        return "[parent] VERIFY immutable PERMIT build START"
    if kind == "parent_verify_complete":
        return "[parent] VERIFY immutable PERMIT build OK"
    source_key = str(event.get("source_key") or "")
    index = int(event.get("task_index", 1))
    total_tasks = int(event.get("task_total", 1))
    prefix = f"[{index}/{total_tasks}]"
    expected_rows = int(event.get("expected_rows", 0))
    rows_verified = int(event.get("rows_verified", 0))
    if kind == "task_start":
        return f"{prefix} VERIFY {source_key} START rows={expected_rows:,}"
    if kind == "row_progress":
        return (
            f"{prefix} VERIFY {source_key} {rows_verified:,}/{expected_rows:,} "
            f"({_percent(rows_verified, expected_rows)})"
        )
    if kind == "task_complete":
        return f"{prefix} VERIFY {source_key} PASS rows={rows_verified:,}"
    return f"{prefix} {kind or 'VERIFY'} {source_key}".strip()


def verify_permit_geospatial_build(
    *,
    data_root: str | Path | None = None,
    build_id: str | None = None,
    parent_evidence: Mapping[str, Any] | None = None,
    axis_review: Mapping[str, Any] | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    selected_parent = parent_evidence or load_permit_parent_full_dry_run()
    selected_axis = axis_review or load_geospatial_full_axis()
    axis_by_source = _validated_axis_review(selected_axis)
    parent_build_id = expected_permit_build_id(selected_parent)
    expected_build_id = _build_id(parent_build_id=parent_build_id, axis_review=selected_axis)
    selected_build_id = build_id or expected_build_id
    if selected_build_id != expected_build_id:
        raise GeospatialBuildVerificationError("requested geospatial build_id does not match approved deterministic build")

    if progress is not None:
        progress({"event": "parent_verify_start"})
    parent = verify_permit_parent_build(data_root=root, evidence=selected_parent)
    if progress is not None:
        progress({"event": "parent_verify_complete"})
    parent_by_source = {item["source_key"]: item for item in parent["results"]}

    build_dir = root / "canonical" / "permit_geospatial" / "v1" / selected_build_id
    if not is_within(build_dir, root) or not build_dir.is_dir():
        raise GeospatialBuildVerificationError("expected immutable geospatial build directory does not exist")
    manifest = _load_manifest(build_dir / "manifest.json")
    if manifest.get("manifest_version") != 1:
        raise GeospatialBuildVerificationError("geospatial manifest version changed")
    if manifest.get("build_id") != expected_build_id:
        raise GeospatialBuildVerificationError("geospatial manifest build id mismatch")
    if manifest.get("grain") != "PERMIT_GEOSPATIAL_ENRICHMENT":
        raise GeospatialBuildVerificationError("geospatial build grain changed")
    if manifest.get("schema") != "schemas/permit_geospatial.v1.json":
        raise GeospatialBuildVerificationError("geospatial schema reference changed")
    if manifest.get("geospatial_schema_sha256") != _schema_sha256():
        raise GeospatialBuildVerificationError("geospatial schema SHA-256 mismatch")
    if manifest.get("parent_permit_build_id") != parent_build_id:
        raise GeospatialBuildVerificationError("geospatial parent build id changed")
    if manifest.get("parent_build_verification") != "PASS":
        raise GeospatialBuildVerificationError("geospatial manifest does not record verified parent")
    if manifest.get("axis_evidence") != "provenance/geospatial_full_axis.json":
        raise GeospatialBuildVerificationError("geospatial axis evidence reference changed")
    if manifest.get("source_crs") != SOURCE_CRS or manifest.get("target_crs") != TARGET_CRS:
        raise GeospatialBuildVerificationError("geospatial CRS contract changed")
    if manifest.get("source_x_interpretation") != "EASTING" or manifest.get("source_y_interpretation") != "NORTHING":
        raise GeospatialBuildVerificationError("geospatial axis interpretation changed")
    if manifest.get("writer_contract") != _writer_contract():
        raise GeospatialBuildVerificationError("geospatial writer contract changed")
    if manifest.get("parent_mutated") is not False:
        raise GeospatialBuildVerificationError("geospatial build must not mutate the parent")
    if manifest.get("public_row_level_release_approved") is not False:
        raise GeospatialBuildVerificationError("geospatial public release must remain blocked")
    if manifest.get("episode_reconstruction_performed") is not False:
        raise GeospatialBuildVerificationError("geospatial build must not claim episode reconstruction")
    if manifest.get("status") != "PASS":
        raise GeospatialBuildVerificationError("geospatial manifest status is not PASS")

    results = manifest.get("results")
    if not isinstance(results, list) or len(results) != 3:
        raise GeospatialBuildVerificationError("geospatial manifest must contain three source results")
    by_source = {
        str(item.get("source_key")): dict(item)
        for item in results
        if isinstance(item, Mapping) and item.get("source_key") in V1_SOURCE_ORDER
    }
    if set(by_source) != set(V1_SOURCE_ORDER):
        raise GeospatialBuildVerificationError("geospatial manifest source scope changed")

    _, pq = _pyarrow_modules()
    arrow_schema = permit_geospatial_arrow_schema(parent_build_id)
    verified_results: list[dict[str, Any]] = []
    for task_index, source_key in enumerate(V1_SOURCE_ORDER, start=1):
        item = by_source[source_key]
        axis_item = axis_by_source[source_key]
        parent_item = parent_by_source[source_key]
        expected_rows = int(parent_item["rows"])
        expected_transformed = int(axis_item["coordinate_pairs"])
        expected_missing = int(axis_item["missing_coordinate_pairs"])
        if item.get("status") != "PASS":
            raise GeospatialBuildVerificationError(f"{source_key}: geospatial result status is not PASS")
        if item.get("parent_parquet_sha256") != parent_item.get("output_sha256"):
            raise GeospatialBuildVerificationError(f"{source_key}: parent Parquet SHA-256 lineage changed")
        if item.get("rows") != expected_rows:
            raise GeospatialBuildVerificationError(f"{source_key}: geospatial row count changed")
        if item.get("transformed_coordinates") != expected_transformed:
            raise GeospatialBuildVerificationError(f"{source_key}: transformed coordinate count changed")
        if item.get("missing_source_coordinates") != expected_missing:
            raise GeospatialBuildVerificationError(f"{source_key}: missing coordinate count changed")

        expected_filename = f"{source_key}.parquet"
        if item.get("output_file") != expected_filename:
            raise GeospatialBuildVerificationError(f"{source_key}: geospatial output filename changed")
        output_path = build_dir / expected_filename
        if not is_within(output_path, build_dir) or not output_path.is_file():
            raise GeospatialBuildVerificationError(f"{source_key}: geospatial Parquet output missing")
        if output_path.stat().st_size != item.get("output_bytes"):
            raise GeospatialBuildVerificationError(f"{source_key}: geospatial output byte count mismatch")
        actual_sha256 = _sha256_file(output_path)
        if actual_sha256 != item.get("output_sha256"):
            raise GeospatialBuildVerificationError(f"{source_key}: geospatial output SHA-256 mismatch")

        parquet_file = pq.ParquetFile(output_path)
        if parquet_file.metadata.num_rows != expected_rows:
            raise GeospatialBuildVerificationError(f"{source_key}: geospatial metadata row count mismatch")
        if parquet_file.metadata.num_row_groups != item.get("parquet_row_groups"):
            raise GeospatialBuildVerificationError(f"{source_key}: geospatial row-group count mismatch")
        if not pq.read_schema(output_path).equals(arrow_schema, check_metadata=True):
            raise GeospatialBuildVerificationError(f"{source_key}: geospatial Arrow schema mismatch")
        for group_index in range(parquet_file.metadata.num_row_groups):
            group = parquet_file.metadata.row_group(group_index)
            for column_index in range(group.num_columns):
                if group.column(column_index).compression != COMPRESSION.upper():
                    raise GeospatialBuildVerificationError(f"{source_key}: geospatial compression changed")

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
        rows_verified = 0
        quality_counts: Counter[str] = Counter()
        for batch in parquet_file.iter_batches(
            batch_size=50_000,
            columns=[
                "source_key",
                "source_row_number",
                "management_number",
                "parent_permit_build_id",
                "wgs84_longitude",
                "wgs84_latitude",
                "coordinate_quality",
            ],
        ):
            names = batch.schema.names
            source_keys = batch.column(names.index("source_key")).to_pylist()
            row_numbers = batch.column(names.index("source_row_number")).to_pylist()
            management_numbers = batch.column(names.index("management_number")).to_pylist()
            parent_ids = batch.column(names.index("parent_permit_build_id")).to_pylist()
            longitudes = batch.column(names.index("wgs84_longitude")).to_pylist()
            latitudes = batch.column(names.index("wgs84_latitude")).to_pylist()
            qualities = batch.column(names.index("coordinate_quality")).to_pylist()
            if any(value != source_key for value in source_keys):
                raise GeospatialBuildVerificationError(f"{source_key}: output source_key values changed")
            if row_numbers != list(range(rows_verified + 1, rows_verified + 1 + len(row_numbers))):
                raise GeospatialBuildVerificationError(f"{source_key}: output source_row_number sequence changed")
            if any(value is None or str(value) == "" for value in management_numbers):
                raise GeospatialBuildVerificationError(f"{source_key}: output management linkage contains null/blank")
            if any(value != parent_build_id for value in parent_ids):
                raise GeospatialBuildVerificationError(f"{source_key}: output parent build lineage changed")
            for lon, lat, quality in zip(longitudes, latitudes, qualities):
                quality_counts[str(quality)] += 1
                if quality == "TRANSFORMED":
                    if lon is None or lat is None:
                        raise GeospatialBuildVerificationError(f"{source_key}: transformed quality has null WGS84")
                    lon_value = float(lon)
                    lat_value = float(lat)
                    if not math.isfinite(lon_value) or not math.isfinite(lat_value):
                        raise GeospatialBuildVerificationError(f"{source_key}: nonfinite WGS84 output")
                    if not (
                        BROAD_KOREA_LON[0] <= lon_value <= BROAD_KOREA_LON[1]
                        and BROAD_KOREA_LAT[0] <= lat_value <= BROAD_KOREA_LAT[1]
                    ):
                        raise GeospatialBuildVerificationError(f"{source_key}: WGS84 output outside broad Korea envelope")
                elif quality == "MISSING_SOURCE_COORDINATES":
                    if lon is not None or lat is not None:
                        raise GeospatialBuildVerificationError(f"{source_key}: missing quality must have null WGS84")
                else:
                    raise GeospatialBuildVerificationError(f"{source_key}: unexpected coordinate quality value")
            rows_verified += len(row_numbers)
            if progress is not None:
                progress(
                    {
                        "event": "row_progress",
                        "task_index": task_index,
                        "task_total": len(V1_SOURCE_ORDER),
                        "source_key": source_key,
                        "expected_rows": expected_rows,
                        "rows_verified": rows_verified,
                    }
                )

        if rows_verified != expected_rows:
            raise GeospatialBuildVerificationError(f"{source_key}: verified geospatial rows incomplete")
        if quality_counts.get("TRANSFORMED", 0) != expected_transformed:
            raise GeospatialBuildVerificationError(f"{source_key}: verified transformed count mismatch")
        if quality_counts.get("MISSING_SOURCE_COORDINATES", 0) != expected_missing:
            raise GeospatialBuildVerificationError(f"{source_key}: verified missing count mismatch")
        if progress is not None:
            progress(
                {
                    "event": "task_complete",
                    "task_index": task_index,
                    "task_total": len(V1_SOURCE_ORDER),
                    "source_key": source_key,
                    "expected_rows": expected_rows,
                    "rows_verified": rows_verified,
                }
            )
        verified_results.append(
            {
                "source_key": source_key,
                "rows": rows_verified,
                "transformed_coordinates": expected_transformed,
                "missing_source_coordinates": expected_missing,
                "output_bytes": output_path.stat().st_size,
                "output_sha256": actual_sha256,
                "parquet_row_groups": parquet_file.metadata.num_row_groups,
                "schema_verified": True,
                "zstd_verified": True,
                "coordinate_invariants_verified": True,
                "status": "PASS",
            }
        )

    rows_total = sum(int(item["rows"]) for item in verified_results)
    transformed_total = sum(int(item["transformed_coordinates"]) for item in verified_results)
    missing_total = sum(int(item["missing_source_coordinates"]) for item in verified_results)
    if manifest.get("rows_total") != rows_total:
        raise GeospatialBuildVerificationError("geospatial manifest total rows changed")
    if manifest.get("transformed_coordinates_total") != transformed_total:
        raise GeospatialBuildVerificationError("geospatial manifest transformed total changed")
    if manifest.get("missing_source_coordinates_total") != missing_total:
        raise GeospatialBuildVerificationError("geospatial manifest missing total changed")

    return {
        "build_id": expected_build_id,
        "build_directory": str(build_dir),
        "parent_permit_build_id": parent_build_id,
        "rows_verified_total": rows_total,
        "transformed_coordinates_total": transformed_total,
        "missing_source_coordinates_total": missing_total,
        "output_bytes_total": sum(int(item["output_bytes"]) for item in verified_results),
        "source_count": len(verified_results),
        "results": verified_results,
        "geospatial_schema_sha256": _schema_sha256(),
        "writer_contract": _writer_contract(),
        "manifest_verified": True,
        "parquet_hashes_verified": True,
        "parquet_schemas_verified": True,
        "zstd_verified": True,
        "coordinate_invariants_verified": True,
        "parent_build_verified": True,
        "public_row_level_release_approved": False,
        "row_level_values_returned": False,
        "status": "PASS",
    }
