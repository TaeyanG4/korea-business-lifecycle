from __future__ import annotations

import hashlib
import json
import math
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
from .canonical_materialization_verify import (
    expected_permit_build_id,
    verify_permit_parent_build,
)
from .canonical_schema import load_permit_geospatial_schema
from .config import project_root
from .provenance import load_geospatial_full_axis, load_permit_parent_full_dry_run
from .storage import is_within, resolve_data_root


PYPROJ_VERSION = "3.7.2"
PROJ_VERSION = "9.5.1"
SOURCE_CRS = "EPSG:5174"
TARGET_CRS = "EPSG:4326"
BROAD_KOREA_LON = (124.0, 132.0)
BROAD_KOREA_LAT = (32.0, 40.0)
ProgressCallback = Callable[[dict[str, Any]], None]


class GeospatialEnrichmentError(RuntimeError):
    """Raised when the local WGS84 enrichment cannot proceed safely."""


def _pyproj_modules():
    try:
        import pyproj
        from pyproj import Transformer
    except ImportError as exc:
        raise GeospatialEnrichmentError(
            'pyproj is required for geospatial enrichment; install with python -m pip install -e ".[geo]"'
        ) from exc
    if pyproj.__version__ != PYPROJ_VERSION:
        raise GeospatialEnrichmentError(
            f"geospatial enrichment requires pyproj {PYPROJ_VERSION}, found {pyproj.__version__}"
        )
    if pyproj.proj_version_str != PROJ_VERSION:
        raise GeospatialEnrichmentError(
            f"geospatial enrichment requires PROJ {PROJ_VERSION}, found {pyproj.proj_version_str}"
        )
    return pyproj, Transformer


def _schema_sha256() -> str:
    return _sha256_file(project_root() / "schemas" / "permit_geospatial.v1.json")


def _writer_contract() -> dict[str, Any]:
    return {
        "pyarrow_version": PYARROW_VERSION,
        "pyproj_version": PYPROJ_VERSION,
        "proj_version": PROJ_VERSION,
        "format": "PARQUET",
        "parquet_version": PARQUET_VERSION,
        "compression": COMPRESSION.upper(),
        "compression_level": COMPRESSION_LEVEL,
        "data_page_version": DATA_PAGE_VERSION,
        "rows_per_batch": ROWS_PER_BATCH,
        "rows_per_row_group": ROWS_PER_ROW_GROUP,
    }


def _validated_axis_review(review: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    if review.get("decision") != (
        "FULL_SNAPSHOT_AXIS_QA_PASSED_X_EASTING_Y_NORTHING_APPROVED_FOR_LOCAL_DERIVATION"
    ):
        raise GeospatialEnrichmentError("full geospatial axis evidence is not in reviewed PASS state")
    scope = review.get("scope")
    if not isinstance(scope, Mapping):
        raise GeospatialEnrichmentError("full geospatial axis evidence scope is invalid")
    reviewed = review.get("review")
    if not isinstance(reviewed, Mapping):
        raise GeospatialEnrichmentError("full geospatial axis reviewed interpretation is missing")
    if reviewed.get("source_x_interpretation") != "EASTING":
        raise GeospatialEnrichmentError("full geospatial axis evidence does not approve source X as easting")
    if reviewed.get("source_y_interpretation") != "NORTHING":
        raise GeospatialEnrichmentError("full geospatial axis evidence does not approve source Y as northing")
    if reviewed.get("coordinate_axis_order_verified_nationwide") is not True:
        raise GeospatialEnrichmentError("full geospatial axis evidence is not verified for current v1")
    if reviewed.get("local_wgs84_derivation_approved") is not True:
        raise GeospatialEnrichmentError("local WGS84 derivation is not approved")
    if reviewed.get("public_wgs84_release_approved") is not False:
        raise GeospatialEnrichmentError("public WGS84 release must remain blocked")

    results = review.get("results")
    if not isinstance(results, list) or len(results) != 3:
        raise GeospatialEnrichmentError("full geospatial axis evidence must contain three source results")
    by_source = {
        str(item.get("source_key")): dict(item)
        for item in results
        if isinstance(item, Mapping) and item.get("source_key") in V1_SOURCE_ORDER
    }
    if set(by_source) != set(V1_SOURCE_ORDER):
        raise GeospatialEnrichmentError("full geospatial axis evidence source scope changed")
    for source_key, item in by_source.items():
        if item.get("status") != "PASS":
            raise GeospatialEnrichmentError(f"{source_key}: full geospatial axis QA did not pass")
        if item.get("partial_coordinate_pairs") != 0:
            raise GeospatialEnrichmentError(f"{source_key}: full geospatial QA observed partial coordinate pairs")
        if item.get("assessment") != "SOURCE_X_AS_EASTING_Y_AS_NORTHING_STRONGLY_PREFERRED":
            raise GeospatialEnrichmentError(f"{source_key}: full geospatial axis assessment changed")
    return by_source


def permit_geospatial_arrow_schema(parent_build_id: str):
    pa, _ = _pyarrow_modules()
    schema = load_permit_geospatial_schema()
    logical_types = {
        "string": pa.string(),
        "int64": pa.int64(),
        "float64": pa.float64(),
    }
    fields = [
        pa.field(
            str(item["name"]),
            logical_types[str(item["logical_type"])],
            nullable=bool(item["nullable"]),
        )
        for item in schema["columns"]
    ]
    metadata = {
        b"kbl.schema_name": b"permit_geospatial",
        b"kbl.schema_version": b"1",
        b"kbl.grain": b"PERMIT_GEOSPATIAL_ENRICHMENT",
        b"kbl.parent_permit_build_id": parent_build_id.encode("ascii"),
        b"kbl.source_crs": SOURCE_CRS.encode("ascii"),
        b"kbl.target_crs": TARGET_CRS.encode("ascii"),
        b"kbl.source_x_interpretation": b"EASTING",
        b"kbl.source_y_interpretation": b"NORTHING",
        b"kbl.publication_status": b"LOCAL_PRIVATE_ONLY_PUBLICATION_REVIEW_REQUIRED",
    }
    return pa.schema(fields, metadata=metadata)


def _build_id(
    *,
    parent_build_id: str,
    axis_review: Mapping[str, Any],
) -> str:
    _validated_axis_review(axis_review)
    payload = {
        "geospatial_materializer_version": 1,
        "parent_permit_build_id": parent_build_id,
        "geospatial_schema_sha256": _schema_sha256(),
        "axis_contract": {
            "evidence": "provenance/geospatial_full_axis.json",
            "source_crs": SOURCE_CRS,
            "target_crs": TARGET_CRS,
            "source_x_interpretation": "EASTING",
            "source_y_interpretation": "NORTHING",
        },
        "writer_contract": _writer_contract(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"permit-geo-v1-{hashlib.sha256(encoded).hexdigest()[:16]}"


def geospatial_enrichment_plan(
    *,
    data_root: str | Path | None = None,
    parent_evidence: Mapping[str, Any] | None = None,
    axis_review: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    selected_parent_evidence = parent_evidence or load_permit_parent_full_dry_run()
    selected_axis_review = axis_review or load_geospatial_full_axis()
    axis_by_source = _validated_axis_review(selected_axis_review)
    parent_build_id = expected_permit_build_id(selected_parent_evidence)
    build_id = _build_id(parent_build_id=parent_build_id, axis_review=selected_axis_review)
    final_dir = root / "canonical" / "permit_geospatial" / "v1" / build_id
    expected_rows = sum(
        int(axis_by_source[source_key]["coordinate_pairs"])
        + int(axis_by_source[source_key]["missing_coordinate_pairs"])
        for source_key in V1_SOURCE_ORDER
    )
    return {
        "build_id": build_id,
        "parent_permit_build_id": parent_build_id,
        "scope": list(V1_SOURCE_ORDER),
        "expected_rows_total": expected_rows,
        "expected_transformed_total": sum(
            int(axis_by_source[source_key]["coordinate_pairs"]) for source_key in V1_SOURCE_ORDER
        ),
        "expected_missing_total": sum(
            int(axis_by_source[source_key]["missing_coordinate_pairs"]) for source_key in V1_SOURCE_ORDER
        ),
        "geospatial_schema_sha256": _schema_sha256(),
        "axis_evidence": "provenance/geospatial_full_axis.json",
        "writer_contract": _writer_contract(),
        "output_directory": str(final_dir),
        "output_directory_exists": final_dir.exists(),
        "parent_mutated": False,
        "public_row_level_release_approved": False,
        "network_access_required": False,
        "status": "READY_FOR_USER_EXECUTION" if not final_dir.exists() else "OUTPUT_ALREADY_EXISTS",
    }


def _percent(value: int, total: int) -> str:
    if total <= 0:
        return "100.0%"
    return f"{100.0 * value / total:.1f}%"


def format_geospatial_enrichment_progress(event: Mapping[str, Any]) -> str:
    kind = str(event.get("event") or "")
    source_key = str(event.get("source_key") or "")
    index = int(event.get("task_index", 1))
    total_tasks = int(event.get("task_total", 1))
    prefix = f"[{index}/{total_tasks}]"
    if kind == "parent_verify_start":
        return "[parent] VERIFY immutable PERMIT build START"
    if kind == "parent_verify_complete":
        return "[parent] VERIFY immutable PERMIT build OK"
    expected_rows = int(event.get("expected_rows", 0))
    rows_written = int(event.get("rows_written", 0))
    overall_rows = int(event.get("overall_rows_written", 0))
    overall_expected = int(event.get("overall_expected_rows", 0))
    if kind == "task_start":
        return f"{prefix} START {source_key} WGS84 enrichment rows={expected_rows:,}"
    if kind == "row_progress":
        return (
            f"{prefix} WRITE {source_key} {rows_written:,}/{expected_rows:,} "
            f"({_percent(rows_written, expected_rows)}) | overall "
            f"{overall_rows:,}/{overall_expected:,} ({_percent(overall_rows, overall_expected)})"
        )
    if kind == "task_complete":
        return (
            f"{prefix} DONE {source_key} rows={rows_written:,} | overall "
            f"{overall_rows:,}/{overall_expected:,} ({_percent(overall_rows, overall_expected)})"
        )
    return f"{prefix} {kind or 'PROGRESS'} {source_key}".strip()


def _transform_batch(
    *,
    batch: Any,
    source_key: str,
    parent_build_id: str,
    expected_start_row: int,
    transformer: Any,
    arrow_schema: Any,
) -> tuple[Any, Counter[str]]:
    pa, _ = _pyarrow_modules()
    names = batch.schema.names
    source_keys = batch.column(names.index("source_key")).to_pylist()
    row_numbers = batch.column(names.index("source_row_number")).to_pylist()
    management_numbers = batch.column(names.index("management_number")).to_pylist()
    xs = batch.column(names.index("source_coordinate_x")).to_pylist()
    ys = batch.column(names.index("source_coordinate_y")).to_pylist()

    if any(value != source_key for value in source_keys):
        raise GeospatialEnrichmentError(f"{source_key}: parent source_key values changed")
    expected_numbers = list(range(expected_start_row, expected_start_row + len(row_numbers)))
    if row_numbers != expected_numbers:
        raise GeospatialEnrichmentError(f"{source_key}: parent source_row_number sequence changed")
    if any(value is None or str(value) == "" for value in management_numbers):
        raise GeospatialEnrichmentError(f"{source_key}: parent management_number contains null/blank values")

    present_indexes: list[int] = []
    valid_x: list[float] = []
    valid_y: list[float] = []
    for index, (x_value, y_value) in enumerate(zip(xs, ys)):
        if (x_value is None) != (y_value is None):
            raise GeospatialEnrichmentError(f"{source_key}: partial source coordinate pair encountered")
        if x_value is not None:
            present_indexes.append(index)
            valid_x.append(float(x_value))
            valid_y.append(float(y_value))

    longitudes: list[float | None] = [None] * len(xs)
    latitudes: list[float | None] = [None] * len(xs)
    quality = ["MISSING_SOURCE_COORDINATES"] * len(xs)
    if valid_x:
        try:
            transformed_lon, transformed_lat = transformer.transform(valid_x, valid_y, errcheck=True)
        except Exception as exc:
            raise GeospatialEnrichmentError(f"{source_key}: EPSG:5174 to EPSG:4326 transform failed") from exc
        for index, lon, lat in zip(present_indexes, transformed_lon, transformed_lat):
            lon_value = float(lon)
            lat_value = float(lat)
            if not math.isfinite(lon_value) or not math.isfinite(lat_value):
                raise GeospatialEnrichmentError(f"{source_key}: nonfinite WGS84 transform result")
            if not (
                BROAD_KOREA_LON[0] <= lon_value <= BROAD_KOREA_LON[1]
                and BROAD_KOREA_LAT[0] <= lat_value <= BROAD_KOREA_LAT[1]
            ):
                raise GeospatialEnrichmentError(
                    f"{source_key}: WGS84 transform result outside approved broad Korea envelope"
                )
            longitudes[index] = lon_value
            latitudes[index] = lat_value
            quality[index] = "TRANSFORMED"

    quality_counts: Counter[str] = Counter(quality)
    table = pa.Table.from_pydict(
        {
            "source_key": source_keys,
            "source_row_number": row_numbers,
            "management_number": management_numbers,
            "parent_permit_build_id": [parent_build_id] * len(row_numbers),
            "wgs84_longitude": longitudes,
            "wgs84_latitude": latitudes,
            "coordinate_quality": quality,
        },
        schema=arrow_schema,
    )
    return table, quality_counts


def materialize_permit_geospatial(
    *,
    data_root: str | Path | None = None,
    parent_evidence: Mapping[str, Any] | None = None,
    axis_review: Mapping[str, Any] | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    selected_parent_evidence = parent_evidence or load_permit_parent_full_dry_run()
    selected_axis_review = axis_review or load_geospatial_full_axis()
    axis_by_source = _validated_axis_review(selected_axis_review)
    parent_build_id = expected_permit_build_id(selected_parent_evidence)
    build_id = _build_id(parent_build_id=parent_build_id, axis_review=selected_axis_review)
    final_dir = root / "canonical" / "permit_geospatial" / "v1" / build_id
    if final_dir.exists():
        raise GeospatialEnrichmentError("final geospatial build directory already exists; immutable builds are never overwritten")

    if progress is not None:
        progress({"event": "parent_verify_start"})
    verified_parent = verify_permit_parent_build(data_root=root, evidence=selected_parent_evidence)
    if verified_parent["build_id"] != parent_build_id or verified_parent["status"] != "PASS":
        raise GeospatialEnrichmentError("independent parent PERMIT verification did not pass")
    if progress is not None:
        progress({"event": "parent_verify_complete"})

    parent_by_source = {item["source_key"]: item for item in verified_parent["results"]}
    staging_dir = root / ".tmp" / "permit-geospatial-materialization" / f"{build_id}-{os.getpid()}"
    if staging_dir.exists():
        raise GeospatialEnrichmentError("unique geospatial staging directory unexpectedly already exists")
    staging_dir.mkdir(parents=True)
    if not is_within(staging_dir, root):
        raise GeospatialEnrichmentError("geospatial staging directory escaped KBL_DATA_ROOT")

    _, Transformer = _pyproj_modules()
    transformer = Transformer.from_crs(SOURCE_CRS, TARGET_CRS, always_xy=True)
    pa, pq = _pyarrow_modules()
    arrow_schema = permit_geospatial_arrow_schema(parent_build_id)
    expected_total = int(verified_parent["rows_verified_total"])
    results: list[dict[str, Any]] = []
    overall_before = 0

    try:
        for task_index, source_key in enumerate(V1_SOURCE_ORDER, start=1):
            axis_item = axis_by_source[source_key]
            parent_item = parent_by_source[source_key]
            expected_rows = int(parent_item["rows"])
            expected_transformed = int(axis_item["coordinate_pairs"])
            expected_missing = int(axis_item["missing_coordinate_pairs"])
            if expected_transformed + expected_missing != expected_rows:
                raise GeospatialEnrichmentError(f"{source_key}: geospatial evidence does not cover parent rows")

            parent_path = (
                root
                / "canonical"
                / "permit"
                / "v1"
                / parent_build_id
                / f"{source_key}.parquet"
            )
            output_path = staging_dir / f"{source_key}.parquet"
            if progress is not None:
                progress(
                    {
                        "event": "task_start",
                        "task_index": task_index,
                        "task_total": len(V1_SOURCE_ORDER),
                        "source_key": source_key,
                        "expected_rows": expected_rows,
                        "overall_rows_written": overall_before,
                        "overall_expected_rows": expected_total,
                    }
                )

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
            rows_written = 0
            quality_counts: Counter[str] = Counter()
            try:
                parent_file = pq.ParquetFile(parent_path)
                try:
                    for batch in parent_file.iter_batches(
                        batch_size=ROWS_PER_BATCH,
                        columns=[
                            "source_key",
                            "source_row_number",
                            "management_number",
                            "source_coordinate_x",
                            "source_coordinate_y",
                        ],
                    ):
                        output_table, batch_counts = _transform_batch(
                            batch=batch,
                            source_key=source_key,
                            parent_build_id=parent_build_id,
                            expected_start_row=rows_written + 1,
                            transformer=transformer,
                            arrow_schema=arrow_schema,
                        )
                        writer.write_table(output_table, row_group_size=ROWS_PER_ROW_GROUP)
                        rows_written += output_table.num_rows
                        quality_counts.update(batch_counts)
                        if progress is not None:
                            progress(
                                {
                                    "event": "row_progress",
                                    "task_index": task_index,
                                    "task_total": len(V1_SOURCE_ORDER),
                                    "source_key": source_key,
                                    "expected_rows": expected_rows,
                                    "rows_written": rows_written,
                                    "overall_rows_written": overall_before + rows_written,
                                    "overall_expected_rows": expected_total,
                                }
                            )
                finally:
                    parent_file.close()
            finally:
                writer.close()

            if rows_written != expected_rows:
                raise GeospatialEnrichmentError(f"{source_key}: geospatial row count differs from parent")
            if quality_counts.get("TRANSFORMED", 0) != expected_transformed:
                raise GeospatialEnrichmentError(f"{source_key}: transformed coordinate count differs from reviewed QA")
            if quality_counts.get("MISSING_SOURCE_COORDINATES", 0) != expected_missing:
                raise GeospatialEnrichmentError(f"{source_key}: missing coordinate count differs from reviewed QA")
            if set(quality_counts) - {"TRANSFORMED", "MISSING_SOURCE_COORDINATES"}:
                raise GeospatialEnrichmentError(f"{source_key}: unexpected coordinate quality state")

            output_file = pq.ParquetFile(output_path)
            try:
                if output_file.metadata.num_rows != expected_rows:
                    raise GeospatialEnrichmentError(f"{source_key}: geospatial Parquet metadata row count mismatch")
                row_group_count = output_file.metadata.num_row_groups
            finally:
                output_file.close()
            if not pq.read_schema(output_path).equals(arrow_schema, check_metadata=True):
                raise GeospatialEnrichmentError(f"{source_key}: geospatial Parquet Arrow schema mismatch")

            result = {
                "source_key": source_key,
                "parent_parquet_sha256": parent_item["output_sha256"],
                "rows": rows_written,
                "transformed_coordinates": quality_counts.get("TRANSFORMED", 0),
                "missing_source_coordinates": quality_counts.get("MISSING_SOURCE_COORDINATES", 0),
                "output_file": output_path.name,
                "output_bytes": output_path.stat().st_size,
                "output_sha256": _sha256_file(output_path),
                "parquet_row_groups": row_group_count,
                "status": "PASS",
            }
            results.append(result)
            overall_before += rows_written
            if progress is not None:
                progress(
                    {
                        "event": "task_complete",
                        "task_index": task_index,
                        "task_total": len(V1_SOURCE_ORDER),
                        "source_key": source_key,
                        "expected_rows": expected_rows,
                        "rows_written": rows_written,
                        "overall_rows_written": overall_before,
                        "overall_expected_rows": expected_total,
                    }
                )

        manifest = {
            "manifest_version": 1,
            "build_id": build_id,
            "grain": "PERMIT_GEOSPATIAL_ENRICHMENT",
            "schema": "schemas/permit_geospatial.v1.json",
            "geospatial_schema_sha256": _schema_sha256(),
            "parent_permit_build_id": parent_build_id,
            "parent_build_verification": "PASS",
            "axis_evidence": "provenance/geospatial_full_axis.json",
            "source_crs": SOURCE_CRS,
            "target_crs": TARGET_CRS,
            "source_x_interpretation": "EASTING",
            "source_y_interpretation": "NORTHING",
            "writer_contract": _writer_contract(),
            "rows_total": sum(int(item["rows"]) for item in results),
            "transformed_coordinates_total": sum(int(item["transformed_coordinates"]) for item in results),
            "missing_source_coordinates_total": sum(int(item["missing_source_coordinates"]) for item in results),
            "source_count": len(results),
            "results": results,
            "parent_mutated": False,
            "public_row_level_release_approved": False,
            "episode_reconstruction_performed": False,
            "status": "PASS",
        }
        if manifest["rows_total"] != expected_total:
            raise GeospatialEnrichmentError("geospatial total row count differs from verified parent")
        (staging_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        final_dir.parent.mkdir(parents=True, exist_ok=True)
        staging_dir.rename(final_dir)
        manifest["output_directory"] = str(final_dir)
        return manifest
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise
