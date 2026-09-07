from __future__ import annotations

import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pyproj

from korea_business_lifecycle.geospatial_qa import (
    BROAD_KOREA_WGS84_ENVELOPE,
    PYPROJ_VERSION,
    epsg_5174_metadata,
    format_full_geospatial_progress,
    full_geospatial_axis_plan,
    probe_latest_coordinate_axes,
    probe_snapshot_coordinate_axis,
    validate_full_snapshot_coordinate_axes,
)


ROOT = Path(__file__).resolve().parents[1]


def _rows() -> list[dict[str, str]]:
    rows = json.loads(
        (ROOT / "tests" / "fixtures" / "synthetic_permit_rows.json").read_text(encoding="utf-8")
    )
    assert isinstance(rows, list)
    selected = deepcopy(rows)
    for row in selected:
        row["좌표정보(X)"] = "200000"
        row["좌표정보(Y)"] = "500000"
        row["도로명주소"] = "서울특별시 합성로 1"
        row["지번주소"] = "서울특별시 합성동 1"
    return selected


def _write_snapshot(data_root: Path, source_key: str, retrieval_id: str) -> Path:
    destination = data_root / "raw" / source_key / retrieval_id
    destination.mkdir(parents=True)
    artifact = destination / "source.csv"
    rows = _rows()
    with artifact.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    payload = artifact.read_bytes()
    manifest = {
        "manifest_version": 1,
        "retrieval_id": retrieval_id,
        "source_key": source_key,
        "request": {"completed": {"utc": "2026-09-07T00:00:00+00:00"}},
        "artifact": {
            "relative_path": artifact.relative_to(data_root).as_posix(),
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        },
    }
    manifest_path = destination / "retrieval.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _full_evidence(data_root: Path) -> dict[str, object]:
    results = []
    for index, source_key in enumerate(("general_restaurants", "rest_cafes", "bakeries"), start=1):
        manifest_path = _write_snapshot(data_root, source_key, f"20260907T000000Z-{index}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        results.append(
            {
                "source_key": source_key,
                "retrieval_id": manifest["retrieval_id"],
                "artifact_sha256": manifest["artifact"]["sha256"],
                "artifact_bytes": manifest["artifact"]["bytes"],
                "expected_rows": 3,
                "rows_examined": 3,
                "status": "PASS",
            }
        )
    return {
        "decision": "FULL_CURRENT_SNAPSHOT_DRY_RUN_PASSED",
        "results": results,
    }


def test_pyproj_version_is_pinned_for_supported_python_matrix() -> None:
    assert pyproj.__version__ == PYPROJ_VERSION == "3.7.2"


def test_epsg_5174_metadata_records_axis_order_without_source_claim() -> None:
    metadata = epsg_5174_metadata()
    assert metadata["crs_authority"] == "EPSG:5174"
    assert metadata["axis_info"][0]["direction"] == "north"
    assert metadata["axis_info"][1]["direction"] == "east"
    assert metadata["area_of_use_bounds_wgs84"] is not None


def test_bounded_axis_probe_returns_aggregate_only(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    manifest = _write_snapshot(data_root, "general_restaurants", "20260907T000000Z-a")
    result = probe_snapshot_coordinate_axis(manifest, data_root=data_root, max_pairs=3)
    assert result["coordinate_pairs_sampled"] == 3
    assert result["row_level_coordinate_values_returned"] is False
    assert result["wgs84_columns_generated"] is False
    assert "source_coordinate_x" not in result
    assert "source_coordinate_y" not in result
    assert result["candidate_source_x_as_easting_y_as_northing"]["finite_transform_count"] == 3
    assert result["broad_korea_envelope_wgs84"] == BROAD_KOREA_WGS84_ENVELOPE
    assert result["address_macro_region_comparison"]["eligible_pairs"] == 3
    assert result["address_macro_region_comparison"]["xy_match"] == 3


def test_three_source_probe_is_consistent_and_never_emits_coordinates(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    for index, source_key in enumerate(("general_restaurants", "rest_cafes", "bakeries"), start=1):
        _write_snapshot(data_root, source_key, f"20260907T000000Z-{index}")
    result = probe_latest_coordinate_axes(data_root=data_root, max_pairs=3)
    assert result["coordinate_pairs_sampled_total"] == 9
    assert result["row_level_coordinate_values_returned"] is False
    assert result["wgs84_columns_generated"] is False
    assert len(result["results"]) == 3


def test_full_geospatial_plan_is_aggregate_only(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _full_evidence(data_root)
    plan = full_geospatial_axis_plan(evidence=evidence)
    assert plan["expected_rows_total"] == 9
    assert plan["row_level_coordinate_values_returned"] is False
    assert plan["row_level_address_values_returned"] is False
    assert plan["wgs84_columns_generated"] is False
    assert plan["status"] == "READY_FOR_USER_EXECUTION"


def test_full_geospatial_validator_scans_every_synthetic_row_without_wgs84(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _full_evidence(data_root)
    result = validate_full_snapshot_coordinate_axes(
        data_root=data_root,
        progress_every_rows=1,
        evidence=evidence,
    )
    assert result["rows_examined_total"] == 9
    assert result["coordinate_pairs_total"] == 9
    assert result["macro_region_eligible_pairs_total"] == 9
    assert result["row_level_coordinate_values_returned"] is False
    assert result["row_level_address_values_returned"] is False
    assert result["coordinate_axis_order_verified_nationwide"] is False
    assert result["wgs84_generation_approved"] is False
    assert result["wgs84_columns_generated"] is False


def test_full_geospatial_progress_is_aggregate_only() -> None:
    rendered = format_full_geospatial_progress(
        {
            "event": "row_progress",
            "task_index": 2,
            "task_total": 3,
            "source_key": "rest_cafes",
            "expected_rows": 600_000,
            "rows_processed": 300_000,
            "overall_rows_processed": 2_600_000,
            "overall_expected_rows": 3_000_000,
        }
    )
    assert rendered == (
        "[2/3] ROWS rest_cafes 300,000/600,000 (50.0%) | overall "
        "2,600,000/3,000,000 (86.7%)"
    )
    assert "address" not in rendered.lower()
