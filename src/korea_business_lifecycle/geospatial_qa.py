from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping

from .canonical_compatibility import V1_SOURCE_ORDER, latest_retrieval_manifest
from .canonical_schema import FROZEN_V1_SOURCE_COLUMNS
from .profiling import detect_encoding, sniff_dialect
from .provenance import load_permit_parent_full_dry_run
from .storage import require_external_artifact, resolve_data_root


PYPROJ_VERSION = "3.7.2"
DEFAULT_MAX_COORDINATE_PAIRS = 5_000
DEFAULT_FULL_PROGRESS_EVERY_ROWS = 50_000
ProgressCallback = Callable[[dict[str, Any]], None]
BROAD_KOREA_WGS84_ENVELOPE = {
    "west": 124.0,
    "south": 32.0,
    "east": 132.0,
    "north": 40.0,
}
MACRO_REGION_ENVELOPES = {
    "capital": {
        "bounds": {"west": 125.5, "south": 36.0, "east": 128.5, "north": 38.8},
        "address_prefixes": ("서울특별시", "인천광역시", "경기도"),
    },
    "gangwon": {
        "bounds": {"west": 127.0, "south": 36.5, "east": 130.0, "north": 39.0},
        "address_prefixes": ("강원특별자치도", "강원도"),
    },
    "chungcheong": {
        "bounds": {"west": 125.8, "south": 35.0, "east": 128.7, "north": 37.5},
        "address_prefixes": ("충청북도", "충청남도", "대전광역시", "세종특별자치시"),
    },
    "jeolla": {
        "bounds": {"west": 125.0, "south": 33.8, "east": 128.3, "north": 36.5},
        "address_prefixes": ("전북특별자치도", "전라북도", "전라남도", "광주광역시"),
    },
    "gyeongsang": {
        "bounds": {"west": 127.0, "south": 34.0, "east": 130.8, "north": 37.3},
        "address_prefixes": ("경상북도", "경상남도", "대구광역시", "부산광역시", "울산광역시"),
    },
    "jeju": {
        "bounds": {"west": 125.8, "south": 32.8, "east": 127.3, "north": 34.0},
        "address_prefixes": ("제주특별자치도", "제주도"),
    },
}


class GeospatialQaError(RuntimeError):
    """Raised when bounded coordinate-axis QA cannot be performed safely."""


def _pyproj_modules():
    try:
        import pyproj
        from pyproj import CRS, Transformer
    except ImportError as exc:
        raise GeospatialQaError(
            'pyproj is required for geospatial QA; install with python -m pip install -e ".[geo]"'
        ) from exc
    if pyproj.__version__ != PYPROJ_VERSION:
        raise GeospatialQaError(
            f"geospatial QA requires pyproj {PYPROJ_VERSION}, found {pyproj.__version__}"
        )
    return pyproj, CRS, Transformer


def epsg_5174_metadata() -> dict[str, Any]:
    pyproj, CRS, _ = _pyproj_modules()
    crs = CRS.from_epsg(5174)
    area = crs.area_of_use
    return {
        "pyproj_version": pyproj.__version__,
        "proj_version": pyproj.proj_version_str,
        "crs_authority": "EPSG:5174",
        "crs_name": crs.name,
        "axis_info": [
            {
                "name": item.name,
                "abbrev": item.abbrev,
                "direction": item.direction,
                "unit_name": item.unit_name,
            }
            for item in crs.axis_info
        ],
        "area_of_use_name": area.name if area else None,
        "area_of_use_bounds_wgs84": (
            {
                "west": area.west,
                "south": area.south,
                "east": area.east,
                "north": area.north,
            }
            if area
            else None
        ),
    }


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GeospatialQaError("retrieval manifest cannot be read as JSON") from exc
    if not isinstance(value, dict):
        raise GeospatialQaError("retrieval manifest must be a JSON object")
    return value


def _artifact_path(manifest: Mapping[str, Any], *, root: Path) -> Path:
    artifact = manifest.get("artifact")
    if not isinstance(artifact, Mapping):
        raise GeospatialQaError("retrieval manifest artifact metadata missing")
    relative_path = artifact.get("relative_path")
    if not isinstance(relative_path, str):
        raise GeospatialQaError("retrieval manifest artifact path invalid")
    path = require_external_artifact(root / relative_path, root)
    declared_bytes = artifact.get("bytes")
    if not isinstance(declared_bytes, int) or path.stat().st_size != declared_bytes:
        raise GeospatialQaError("retrieval artifact byte count mismatch")
    return path


def _sample_text(path: Path, encoding: str, sample_chars: int = 128_000) -> str:
    with path.open("r", encoding=encoding, errors="strict", newline="") as handle:
        return handle.read(sample_chars)


def _inside_broad_korea(lon: float, lat: float) -> bool:
    box = BROAD_KOREA_WGS84_ENVELOPE
    return box["west"] <= lon <= box["east"] and box["south"] <= lat <= box["north"]


def _macro_region(address: str) -> str | None:
    for region, config in MACRO_REGION_ENVELOPES.items():
        if any(address.startswith(prefix) for prefix in config["address_prefixes"]):
            return region
    return None


def _inside_macro_region(region: str, lon: float, lat: float) -> bool:
    bounds = MACRO_REGION_ENVELOPES[region]["bounds"]
    return (
        bounds["west"] <= lon <= bounds["east"]
        and bounds["south"] <= lat <= bounds["north"]
    )


def _finite_pair(first: float, second: float) -> bool:
    return math.isfinite(first) and math.isfinite(second)


def _assessment(
    xy_inside: int,
    swapped_inside: int,
    sampled: int,
    *,
    macro_eligible: int,
    xy_macro_match: int,
    swapped_macro_match: int,
) -> str:
    if macro_eligible >= 100:
        xy_macro_rate = xy_macro_match / macro_eligible
        swapped_macro_rate = swapped_macro_match / macro_eligible
        if xy_macro_rate >= 0.90 and xy_macro_rate - swapped_macro_rate >= 0.40:
            return "SOURCE_X_AS_EASTING_Y_AS_NORTHING_STRONGLY_PREFERRED"
        if swapped_macro_rate >= 0.90 and swapped_macro_rate - xy_macro_rate >= 0.40:
            return "SOURCE_X_AS_NORTHING_Y_AS_EASTING_STRONGLY_PREFERRED"
    if sampled < 100:
        return "INSUFFICIENT_SAMPLE"
    xy_rate = xy_inside / sampled
    swapped_rate = swapped_inside / sampled
    if xy_rate >= 0.95 and xy_rate - swapped_rate >= 0.50:
        return "SOURCE_X_AS_EASTING_Y_AS_NORTHING_STRONGLY_PREFERRED"
    if swapped_rate >= 0.95 and swapped_rate - xy_rate >= 0.50:
        return "SOURCE_X_AS_NORTHING_Y_AS_EASTING_STRONGLY_PREFERRED"
    return "AMBIGUOUS_BOUNDED_EVIDENCE"


def probe_snapshot_coordinate_axis(
    manifest_path: str | Path,
    *,
    data_root: str | Path | None = None,
    max_pairs: int = DEFAULT_MAX_COORDINATE_PAIRS,
) -> dict[str, Any]:
    if max_pairs < 1 or max_pairs > 100_000:
        raise GeospatialQaError("max_pairs must be between 1 and 100000")
    pyproj, CRS, Transformer = _pyproj_modules()
    root = resolve_data_root(data_root)
    manifest_file = require_external_artifact(manifest_path, root)
    manifest = _load_manifest(manifest_file)
    source_key = manifest.get("source_key")
    if source_key not in V1_SOURCE_ORDER:
        raise GeospatialQaError("retrieval manifest source is outside v1 scope")
    artifact_path = _artifact_path(manifest, root=root)
    encoding = str(detect_encoding(artifact_path)["selected"])
    dialect = sniff_dialect(_sample_text(artifact_path, encoding))

    crs = CRS.from_epsg(5174)
    transformer = Transformer.from_crs(crs, CRS.from_epsg(4326), always_xy=True)
    sampled = 0
    rows_read = 0
    rows_missing_pair = 0
    xy_finite = 0
    swapped_finite = 0
    xy_inside = 0
    swapped_inside = 0
    xy_only_inside = 0
    swapped_only_inside = 0
    both_inside = 0
    neither_inside = 0
    macro_eligible = 0
    xy_macro_match = 0
    swapped_macro_match = 0
    macro_both_match = 0
    macro_xy_only = 0
    macro_swapped_only = 0
    macro_neither = 0

    try:
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
                raise GeospatialQaError("current-snapshot CSV is empty") from exc
            if len(header) != len(set(header)):
                raise GeospatialQaError("current-snapshot CSV contains duplicate header names")
            if len(header) != 39 or set(header) != FROZEN_V1_SOURCE_COLUMNS:
                raise GeospatialQaError("current-snapshot CSV header differs from frozen inventory")
            x_index = header.index("좌표정보(X)")
            y_index = header.index("좌표정보(Y)")
            road_address_index = header.index("도로명주소")
            lot_address_index = header.index("지번주소")

            for values in reader:
                if sampled >= max_pairs:
                    break
                rows_read += 1
                if len(values) != len(header):
                    raise GeospatialQaError("current-snapshot CSV row width differs from frozen inventory")
                raw_x = values[x_index].strip()
                raw_y = values[y_index].strip()
                if not raw_x or not raw_y:
                    rows_missing_pair += 1
                    continue
                try:
                    source_x = float(raw_x)
                    source_y = float(raw_y)
                except ValueError as exc:
                    raise GeospatialQaError("nonblank coordinate pair cannot be parsed as float64") from exc
                if not _finite_pair(source_x, source_y):
                    raise GeospatialQaError("nonblank coordinate pair must be finite")

                lon_xy, lat_xy = transformer.transform(source_x, source_y)
                lon_swapped, lat_swapped = transformer.transform(source_y, source_x)
                xy_is_finite = _finite_pair(lon_xy, lat_xy)
                swapped_is_finite = _finite_pair(lon_swapped, lat_swapped)
                xy_finite += int(xy_is_finite)
                swapped_finite += int(swapped_is_finite)
                xy_is_inside = xy_is_finite and _inside_broad_korea(lon_xy, lat_xy)
                swapped_is_inside = swapped_is_finite and _inside_broad_korea(lon_swapped, lat_swapped)
                xy_inside += int(xy_is_inside)
                swapped_inside += int(swapped_is_inside)
                both_inside += int(xy_is_inside and swapped_is_inside)
                xy_only_inside += int(xy_is_inside and not swapped_is_inside)
                swapped_only_inside += int(swapped_is_inside and not xy_is_inside)
                neither_inside += int(not xy_is_inside and not swapped_is_inside)

                address = values[road_address_index].strip() or values[lot_address_index].strip()
                region = _macro_region(address) if address else None
                if region is not None:
                    xy_macro = xy_is_finite and _inside_macro_region(region, lon_xy, lat_xy)
                    swapped_macro = swapped_is_finite and _inside_macro_region(
                        region, lon_swapped, lat_swapped
                    )
                    macro_eligible += 1
                    xy_macro_match += int(xy_macro)
                    swapped_macro_match += int(swapped_macro)
                    macro_both_match += int(xy_macro and swapped_macro)
                    macro_xy_only += int(xy_macro and not swapped_macro)
                    macro_swapped_only += int(swapped_macro and not xy_macro)
                    macro_neither += int(not xy_macro and not swapped_macro)
                sampled += 1
    except (csv.Error, UnicodeDecodeError) as exc:
        raise GeospatialQaError("current-snapshot CSV parse/decode failed") from exc

    if sampled == 0:
        raise GeospatialQaError("no nonblank coordinate pairs found in bounded scan")
    return {
        "source_key": source_key,
        "retrieval_id": manifest.get("retrieval_id"),
        "artifact_sha256": manifest["artifact"]["sha256"],
        "sample_policy": "FIRST_NONBLANK_COORDINATE_PAIRS_AFTER_HEADER",
        "max_pairs": max_pairs,
        "rows_read_until_sample_complete": rows_read,
        "rows_skipped_missing_pair": rows_missing_pair,
        "coordinate_pairs_sampled": sampled,
        "encoding": encoding,
        "candidate_source_x_as_easting_y_as_northing": {
            "finite_transform_count": xy_finite,
            "inside_broad_korea_count": xy_inside,
        },
        "candidate_source_x_as_northing_y_as_easting": {
            "finite_transform_count": swapped_finite,
            "inside_broad_korea_count": swapped_inside,
        },
        "comparison": {
            "xy_only_inside": xy_only_inside,
            "swapped_only_inside": swapped_only_inside,
            "both_inside": both_inside,
            "neither_inside": neither_inside,
        },
        "address_macro_region_comparison": {
            "eligible_pairs": macro_eligible,
            "xy_match": xy_macro_match,
            "swapped_match": swapped_macro_match,
            "both_match": macro_both_match,
            "xy_only_match": macro_xy_only,
            "swapped_only_match": macro_swapped_only,
            "neither_match": macro_neither,
            "heuristic": "COARSE_SIDO_PREFIX_TO_MACRO_REGION_ENVELOPE",
        },
        "assessment": _assessment(
            xy_inside,
            swapped_inside,
            sampled,
            macro_eligible=macro_eligible,
            xy_macro_match=xy_macro_match,
            swapped_macro_match=swapped_macro_match,
        ),
        "broad_korea_envelope_wgs84": dict(BROAD_KOREA_WGS84_ENVELOPE),
        "row_level_coordinate_values_returned": False,
        "wgs84_columns_generated": False,
        "status": "PASS",
        "software": {
            "pyproj_version": pyproj.__version__,
            "proj_version": pyproj.proj_version_str,
        },
    }


def probe_latest_coordinate_axes(
    *,
    data_root: str | Path | None = None,
    max_pairs: int = DEFAULT_MAX_COORDINATE_PAIRS,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    results = [
        probe_snapshot_coordinate_axis(
            latest_retrieval_manifest(source_key, data_root=root),
            data_root=root,
            max_pairs=max_pairs,
        )
        for source_key in V1_SOURCE_ORDER
    ]
    assessments = {item["assessment"] for item in results}
    return {
        "scope": list(V1_SOURCE_ORDER),
        "declared_crs": epsg_5174_metadata(),
        "sample_policy": "FIRST_NONBLANK_COORDINATE_PAIRS_AFTER_HEADER",
        "max_pairs_per_source": max_pairs,
        "coordinate_pairs_sampled_total": sum(int(item["coordinate_pairs_sampled"]) for item in results),
        "results": results,
        "assessment_consistent_across_sources": len(assessments) == 1,
        "assessments": sorted(assessments),
        "row_level_coordinate_values_returned": False,
        "wgs84_columns_generated": False,
        "status": "PASS",
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _approved_full_sources(evidence: Mapping[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    selected = evidence or load_permit_parent_full_dry_run()
    if selected.get("decision") != "FULL_CURRENT_SNAPSHOT_DRY_RUN_PASSED":
        raise GeospatialQaError("full-snapshot PERMIT evidence is not in PASSED state")
    results = selected.get("results")
    if not isinstance(results, list):
        raise GeospatialQaError("full-snapshot PERMIT evidence results are missing")
    by_source = {
        str(item.get("source_key")): dict(item)
        for item in results
        if isinstance(item, Mapping) and item.get("source_key") in V1_SOURCE_ORDER
    }
    if set(by_source) != set(V1_SOURCE_ORDER):
        raise GeospatialQaError("full-snapshot PERMIT evidence does not exactly cover v1 sources")
    for source_key, item in by_source.items():
        if item.get("status") != "PASS":
            raise GeospatialQaError(f"{source_key}: approved full-snapshot evidence did not pass")
        if item.get("rows_examined") != item.get("expected_rows"):
            raise GeospatialQaError(f"{source_key}: approved full-snapshot evidence is incomplete")
    return by_source


def full_geospatial_axis_plan(
    *,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    approved = _approved_full_sources(evidence)
    return {
        "scope": list(V1_SOURCE_ORDER),
        "expected_rows_total": sum(int(approved[key]["expected_rows"]) for key in V1_SOURCE_ORDER),
        "expected_coordinate_pairs_total_from_prior_profile": 2_811_767,
        "input_artifacts": [
            {
                "source_key": source_key,
                "retrieval_id": approved[source_key]["retrieval_id"],
                "artifact_sha256": approved[source_key]["artifact_sha256"],
                "artifact_bytes": approved[source_key]["artifact_bytes"],
                "expected_rows": approved[source_key]["expected_rows"],
            }
            for source_key in V1_SOURCE_ORDER
        ],
        "declared_source_crs": "EPSG:5174",
        "method": "FULL_SNAPSHOT_AGGREGATE_AXIS_COMPARISON_WITH_COARSE_ADDRESS_MACRO_REGIONS",
        "recompute_input_sha256": True,
        "row_level_coordinate_values_returned": False,
        "row_level_address_values_returned": False,
        "wgs84_columns_generated": False,
        "network_access_required": False,
        "status": "READY_FOR_USER_EXECUTION",
    }


def format_full_geospatial_progress(event: Mapping[str, Any]) -> str:
    kind = str(event.get("event") or "")
    index = int(event.get("task_index", 1))
    task_total = int(event.get("task_total", 1))
    source_key = str(event.get("source_key") or "")
    prefix = f"[{index}/{task_total}]"
    expected_rows = int(event.get("expected_rows", 0))
    rows_processed = int(event.get("rows_processed", 0))
    overall_rows = int(event.get("overall_rows_processed", 0))
    overall_expected = int(event.get("overall_expected_rows", 0))
    if kind == "hash_start":
        return f"{prefix} HASH {source_key} START"
    if kind == "hash_complete":
        return f"{prefix} HASH {source_key} OK"
    if kind == "task_start":
        return f"{prefix} START {source_key} full geospatial QA rows={expected_rows:,}"
    if kind == "row_progress":
        return (
            f"{prefix} ROWS {source_key} {rows_processed:,}/{expected_rows:,} "
            f"({100.0 * rows_processed / expected_rows:.1f}%) | overall "
            f"{overall_rows:,}/{overall_expected:,} ({100.0 * overall_rows / overall_expected:.1f}%)"
        )
    if kind == "task_complete":
        return (
            f"{prefix} DONE {source_key} rows={rows_processed:,} | overall "
            f"{overall_rows:,}/{overall_expected:,} ({100.0 * overall_rows / overall_expected:.1f}%)"
        )
    return f"{prefix} {kind or 'PROGRESS'} {source_key}".strip()


def _validate_full_source_manifest(
    source_key: str,
    *,
    root: Path,
    approved: Mapping[str, Any],
) -> tuple[Path, dict[str, Any]]:
    manifest_path = latest_retrieval_manifest(source_key, data_root=root)
    manifest = _load_manifest(manifest_path)
    if manifest.get("retrieval_id") != approved.get("retrieval_id"):
        raise GeospatialQaError(f"{source_key}: latest retrieval differs from approved full-snapshot evidence")
    artifact = manifest.get("artifact")
    if not isinstance(artifact, Mapping):
        raise GeospatialQaError(f"{source_key}: retrieval artifact metadata missing")
    if artifact.get("sha256") != approved.get("artifact_sha256"):
        raise GeospatialQaError(f"{source_key}: manifest SHA-256 differs from approved evidence")
    if artifact.get("bytes") != approved.get("artifact_bytes"):
        raise GeospatialQaError(f"{source_key}: manifest byte count differs from approved evidence")
    artifact_path = _artifact_path(manifest, root=root)
    return artifact_path, manifest


def _full_source_axis_validation(
    source_key: str,
    *,
    root: Path,
    approved: Mapping[str, Any],
    progress_every_rows: int,
    progress: ProgressCallback | None,
    task_index: int,
    task_total: int,
    overall_rows_before: int,
    overall_expected_rows: int,
) -> dict[str, Any]:
    if progress_every_rows < 1:
        raise GeospatialQaError("progress_every_rows must be positive")
    pyproj, CRS, Transformer = _pyproj_modules()
    artifact_path, manifest = _validate_full_source_manifest(
        source_key,
        root=root,
        approved=approved,
    )
    expected_rows = int(approved["expected_rows"])
    if progress is not None:
        progress({"event": "hash_start", "task_index": task_index, "task_total": task_total, "source_key": source_key})
    if _sha256_file(artifact_path) != approved["artifact_sha256"]:
        raise GeospatialQaError(f"{source_key}: artifact bytes do not match approved SHA-256")
    if progress is not None:
        progress({"event": "hash_complete", "task_index": task_index, "task_total": task_total, "source_key": source_key})

    encoding = str(detect_encoding(artifact_path)["selected"])
    dialect = sniff_dialect(_sample_text(artifact_path, encoding))
    transformer = Transformer.from_crs(CRS.from_epsg(5174), CRS.from_epsg(4326), always_xy=True)
    rows_processed = 0
    coordinate_pairs = 0
    missing_pairs = 0
    partial_pairs = 0
    broad_a_inside = 0
    broad_b_inside = 0
    macro_eligible = 0
    macro_a_match = 0
    macro_b_match = 0
    macro_a_only = 0
    macro_b_only = 0
    macro_both = 0
    macro_neither = 0

    if progress is not None:
        progress(
            {
                "event": "task_start",
                "task_index": task_index,
                "task_total": task_total,
                "source_key": source_key,
                "expected_rows": expected_rows,
                "rows_processed": 0,
                "overall_rows_processed": overall_rows_before,
                "overall_expected_rows": overall_expected_rows,
            }
        )

    try:
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
                raise GeospatialQaError(f"{source_key}: current-snapshot CSV is empty") from exc
            if len(header) != len(set(header)) or len(header) != 39 or set(header) != FROZEN_V1_SOURCE_COLUMNS:
                raise GeospatialQaError(f"{source_key}: source header differs from frozen inventory")
            x_index = header.index("좌표정보(X)")
            y_index = header.index("좌표정보(Y)")
            road_address_index = header.index("도로명주소")
            lot_address_index = header.index("지번주소")

            for values in reader:
                rows_processed += 1
                if len(values) != len(header):
                    raise GeospatialQaError(f"{source_key}: source row width differs at row {rows_processed}")
                raw_x = values[x_index].strip()
                raw_y = values[y_index].strip()
                if not raw_x and not raw_y:
                    missing_pairs += 1
                elif not raw_x or not raw_y:
                    partial_pairs += 1
                else:
                    try:
                        source_x = float(raw_x)
                        source_y = float(raw_y)
                    except ValueError as exc:
                        raise GeospatialQaError(
                            f"{source_key}: nonblank coordinate pair cannot be parsed at row {rows_processed}"
                        ) from exc
                    if not _finite_pair(source_x, source_y):
                        raise GeospatialQaError(f"{source_key}: nonfinite coordinate pair at row {rows_processed}")
                    lon_a, lat_a = transformer.transform(source_x, source_y)
                    lon_b, lat_b = transformer.transform(source_y, source_x)
                    a_finite = _finite_pair(lon_a, lat_a)
                    b_finite = _finite_pair(lon_b, lat_b)
                    a_inside = a_finite and _inside_broad_korea(lon_a, lat_a)
                    b_inside = b_finite and _inside_broad_korea(lon_b, lat_b)
                    broad_a_inside += int(a_inside)
                    broad_b_inside += int(b_inside)
                    coordinate_pairs += 1
                    address = values[road_address_index].strip() or values[lot_address_index].strip()
                    region = _macro_region(address) if address else None
                    if region is not None:
                        a_macro = a_finite and _inside_macro_region(region, lon_a, lat_a)
                        b_macro = b_finite and _inside_macro_region(region, lon_b, lat_b)
                        macro_eligible += 1
                        macro_a_match += int(a_macro)
                        macro_b_match += int(b_macro)
                        macro_a_only += int(a_macro and not b_macro)
                        macro_b_only += int(b_macro and not a_macro)
                        macro_both += int(a_macro and b_macro)
                        macro_neither += int(not a_macro and not b_macro)

                if rows_processed > expected_rows:
                    raise GeospatialQaError(f"{source_key}: scan exceeded approved row count")
                if progress is not None and (
                    rows_processed % progress_every_rows == 0 or rows_processed == expected_rows
                ):
                    progress(
                        {
                            "event": "row_progress",
                            "task_index": task_index,
                            "task_total": task_total,
                            "source_key": source_key,
                            "expected_rows": expected_rows,
                            "rows_processed": rows_processed,
                            "overall_rows_processed": overall_rows_before + rows_processed,
                            "overall_expected_rows": overall_expected_rows,
                        }
                    )
    except (csv.Error, UnicodeDecodeError) as exc:
        raise GeospatialQaError(f"{source_key}: CSV parse/decode failed") from exc

    if rows_processed != expected_rows:
        raise GeospatialQaError(f"{source_key}: full scan row count differs from approved evidence")
    assessment = _assessment(
        broad_a_inside,
        broad_b_inside,
        coordinate_pairs,
        macro_eligible=macro_eligible,
        xy_macro_match=macro_a_match,
        swapped_macro_match=macro_b_match,
    )
    if progress is not None:
        progress(
            {
                "event": "task_complete",
                "task_index": task_index,
                "task_total": task_total,
                "source_key": source_key,
                "expected_rows": expected_rows,
                "rows_processed": rows_processed,
                "overall_rows_processed": overall_rows_before + rows_processed,
                "overall_expected_rows": overall_expected_rows,
            }
        )
    return {
        "source_key": source_key,
        "retrieval_id": manifest.get("retrieval_id"),
        "artifact_sha256": approved["artifact_sha256"],
        "rows_examined": rows_processed,
        "coordinate_pairs": coordinate_pairs,
        "missing_coordinate_pairs": missing_pairs,
        "partial_coordinate_pairs": partial_pairs,
        "broad_korea_candidate_a_inside": broad_a_inside,
        "broad_korea_candidate_b_inside": broad_b_inside,
        "macro_region_eligible_pairs": macro_eligible,
        "macro_region_candidate_a_match": macro_a_match,
        "macro_region_candidate_b_match": macro_b_match,
        "macro_region_candidate_a_only_match": macro_a_only,
        "macro_region_candidate_b_only_match": macro_b_only,
        "macro_region_both_match": macro_both,
        "macro_region_neither_match": macro_neither,
        "assessment": assessment,
        "row_level_coordinate_values_returned": False,
        "row_level_address_values_returned": False,
        "wgs84_columns_generated": False,
        "software": {"pyproj_version": pyproj.__version__, "proj_version": pyproj.proj_version_str},
        "status": "PASS",
    }


def validate_full_snapshot_coordinate_axes(
    *,
    data_root: str | Path | None = None,
    progress_every_rows: int = DEFAULT_FULL_PROGRESS_EVERY_ROWS,
    progress: ProgressCallback | None = None,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    approved = _approved_full_sources(evidence)
    expected_total = sum(int(approved[key]["expected_rows"]) for key in V1_SOURCE_ORDER)
    results: list[dict[str, Any]] = []
    overall_before = 0
    for index, source_key in enumerate(V1_SOURCE_ORDER, start=1):
        result = _full_source_axis_validation(
            source_key,
            root=root,
            approved=approved[source_key],
            progress_every_rows=progress_every_rows,
            progress=progress,
            task_index=index,
            task_total=len(V1_SOURCE_ORDER),
            overall_rows_before=overall_before,
            overall_expected_rows=expected_total,
        )
        results.append(result)
        overall_before += int(result["rows_examined"])
    assessments = {item["assessment"] for item in results}
    return {
        "scope": list(V1_SOURCE_ORDER),
        "method": "FULL_SNAPSHOT_AGGREGATE_AXIS_COMPARISON_WITH_COARSE_ADDRESS_MACRO_REGIONS",
        "declared_crs": epsg_5174_metadata(),
        "rows_examined_total": sum(int(item["rows_examined"]) for item in results),
        "coordinate_pairs_total": sum(int(item["coordinate_pairs"]) for item in results),
        "macro_region_eligible_pairs_total": sum(int(item["macro_region_eligible_pairs"]) for item in results),
        "macro_region_candidate_a_match_total": sum(int(item["macro_region_candidate_a_match"]) for item in results),
        "macro_region_candidate_b_match_total": sum(int(item["macro_region_candidate_b_match"]) for item in results),
        "assessment_consistent_across_sources": len(assessments) == 1,
        "assessments": sorted(assessments),
        "results": results,
        "row_level_coordinate_values_returned": False,
        "row_level_address_values_returned": False,
        "coordinate_axis_order_verified_nationwide": False,
        "wgs84_generation_approved": False,
        "wgs84_columns_generated": False,
        "status": "PASS",
    }
