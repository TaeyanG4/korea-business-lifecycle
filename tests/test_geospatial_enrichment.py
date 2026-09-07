from __future__ import annotations

import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from korea_business_lifecycle.canonical_materialization import materialize_permit_parent
from korea_business_lifecycle.canonical_schema import (
    load_permit_geospatial_schema,
    validate_permit_geospatial_schema,
)
from korea_business_lifecycle.geospatial_enrichment import (
    GeospatialEnrichmentError,
    format_geospatial_enrichment_progress,
    geospatial_enrichment_plan,
    materialize_permit_geospatial,
    permit_geospatial_arrow_schema,
)
from korea_business_lifecycle.geospatial_enrichment_verify import (
    GeospatialBuildVerificationError,
    expected_geospatial_build_id,
    verify_permit_geospatial_build,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ORDER = ("general_restaurants", "rest_cafes", "bakeries")


def _rows() -> list[dict[str, str]]:
    value = json.loads(
        (ROOT / "tests" / "fixtures" / "synthetic_permit_rows.json").read_text(encoding="utf-8")
    )
    assert isinstance(value, list)
    return value


def _write_snapshot(
    data_root: Path,
    source_key: str,
    suffix: str,
    *,
    mutate: str | None = None,
) -> dict[str, object]:
    destination = data_root / "raw" / source_key / f"20260907T000000Z-{suffix}"
    destination.mkdir(parents=True)
    artifact_path = destination / "source.csv"
    rows = deepcopy(_rows())
    if mutate == "partial":
        rows[0]["좌표정보(Y)"] = ""
    elif mutate == "outside":
        rows[0]["좌표정보(X)"] = "99999999"
        rows[0]["좌표정보(Y)"] = "99999999"
    with artifact_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    payload = artifact_path.read_bytes()
    sha256 = hashlib.sha256(payload).hexdigest()
    manifest = {
        "manifest_version": 1,
        "retrieval_id": destination.name,
        "source_key": source_key,
        "request": {"completed": {"utc": "2026-09-07T00:00:00+00:00"}},
        "artifact": {
            "relative_path": artifact_path.relative_to(data_root).as_posix(),
            "bytes": len(payload),
            "sha256": sha256,
        },
    }
    (destination / "retrieval.json").write_text(json.dumps(manifest), encoding="utf-8")
    null_x = sum(row["좌표정보(X)"].strip() == "" for row in rows)
    null_y = sum(row["좌표정보(Y)"].strip() == "" for row in rows)
    return {
        "source_key": source_key,
        "retrieval_id": destination.name,
        "artifact_sha256": sha256,
        "artifact_bytes": len(payload),
        "expected_rows": 3,
        "rows_examined": 3,
        "rows_transformed": 3,
        "permit_date_quality": {"INVALID": 1, "VALID": 2},
        "closure_date_quality": {"MISSING": 2, "VALID": 1},
        "null_source_coordinate_x": null_x,
        "null_source_coordinate_y": null_y,
        "duplicate_linkage_candidates": 0,
        "temporary_uniqueness_index_removed": True,
        "status": "PASS",
    }


def _parent_evidence(data_root: Path, *, mutate_first: str | None = None) -> dict[str, object]:
    results = [
        _write_snapshot(
            data_root,
            source_key,
            f"{index:02d}",
            mutate=mutate_first if index == 1 else None,
        )
        for index, source_key in enumerate(SOURCE_ORDER, start=1)
    ]
    return {
        "decision": "FULL_CURRENT_SNAPSHOT_DRY_RUN_PASSED",
        "scope": {
            "sources": list(SOURCE_ORDER),
            "rows_examined_total": 9,
            "production_materialization_performed": False,
        },
        "results": results,
    }


def _axis_review(*, first_partial: int = 0) -> dict[str, object]:
    results = []
    for index, source_key in enumerate(SOURCE_ORDER, start=1):
        partial = first_partial if index == 1 else 0
        transformed = 2 if partial == 0 else 1
        missing = 1
        results.append(
            {
                "source_key": source_key,
                "coordinate_pairs": transformed,
                "missing_coordinate_pairs": missing,
                "partial_coordinate_pairs": partial,
                "assessment": "SOURCE_X_AS_EASTING_Y_AS_NORTHING_STRONGLY_PREFERRED",
                "status": "PASS",
            }
        )
    return {
        "decision": "FULL_SNAPSHOT_AXIS_QA_PASSED_X_EASTING_Y_NORTHING_APPROVED_FOR_LOCAL_DERIVATION",
        "scope": {"sources": list(SOURCE_ORDER)},
        "review": {
            "source_x_interpretation": "EASTING",
            "source_y_interpretation": "NORTHING",
            "coordinate_axis_order_verified_nationwide": True,
            "local_wgs84_derivation_approved": True,
            "public_wgs84_release_approved": False,
        },
        "results": results,
    }


def test_geospatial_schema_is_frozen_seven_column_sidecar() -> None:
    schema = load_permit_geospatial_schema()
    assert validate_permit_geospatial_schema(schema) == []
    assert [item["name"] for item in schema["columns"]] == [
        "source_key",
        "source_row_number",
        "management_number",
        "parent_permit_build_id",
        "wgs84_longitude",
        "wgs84_latitude",
        "coordinate_quality",
    ]
    assert schema["scope"]["parent_mutated"] is False
    assert schema["scope"]["public_row_level_release_approved"] is False


def test_geospatial_arrow_schema_has_runtime_parent_lineage() -> None:
    schema = permit_geospatial_arrow_schema("permit-v1-synthetic")
    assert len(schema) == 7
    assert schema.field("source_row_number").type == pa.int64()
    assert schema.field("wgs84_longitude").type == pa.float64()
    assert schema.field("wgs84_latitude").nullable is True
    assert schema.metadata[b"kbl.parent_permit_build_id"] == b"permit-v1-synthetic"
    assert schema.metadata[b"kbl.source_x_interpretation"] == b"EASTING"


def test_geospatial_plan_is_deterministic_and_one_to_one(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    parent_evidence = _parent_evidence(data_root)
    axis_review = _axis_review()
    first = geospatial_enrichment_plan(
        data_root=data_root,
        parent_evidence=parent_evidence,
        axis_review=axis_review,
    )
    second = geospatial_enrichment_plan(
        data_root=data_root,
        parent_evidence=deepcopy(parent_evidence),
        axis_review=deepcopy(axis_review),
    )
    assert first["build_id"] == second["build_id"]
    assert first["expected_rows_total"] == 9
    assert first["expected_transformed_total"] == 6
    assert first["expected_missing_total"] == 3
    assert first["parent_mutated"] is False
    assert first["public_row_level_release_approved"] is False
    assert first["status"] == "READY_FOR_USER_EXECUTION"


def test_geospatial_materializer_and_independent_verifier_round_trip(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    parent_evidence = _parent_evidence(data_root)
    axis_review = _axis_review()
    parent = materialize_permit_parent(data_root=data_root, evidence=parent_evidence)
    built = materialize_permit_geospatial(
        data_root=data_root,
        parent_evidence=parent_evidence,
        axis_review=axis_review,
    )
    assert built["parent_permit_build_id"] == parent["build_id"]
    assert built["rows_total"] == 9
    assert built["transformed_coordinates_total"] == 6
    assert built["missing_source_coordinates_total"] == 3
    assert built["parent_mutated"] is False
    assert built["public_row_level_release_approved"] is False

    output_dir = Path(built["output_directory"])
    table = pq.read_table(
        output_dir / "general_restaurants.parquet",
        columns=["wgs84_longitude", "wgs84_latitude", "coordinate_quality"],
    )
    assert table.column("coordinate_quality").to_pylist() == [
        "TRANSFORMED",
        "MISSING_SOURCE_COORDINATES",
        "TRANSFORMED",
    ]
    assert table.column("wgs84_longitude").to_pylist()[1] is None
    assert table.column("wgs84_latitude").to_pylist()[1] is None
    assert all(
        124.0 <= value <= 132.0
        for value in table.column("wgs84_longitude").to_pylist()
        if value is not None
    )

    verified = verify_permit_geospatial_build(
        data_root=data_root,
        parent_evidence=parent_evidence,
        axis_review=axis_review,
    )
    assert verified["build_id"] == built["build_id"] == expected_geospatial_build_id(
        parent_evidence=parent_evidence,
        axis_review=axis_review,
    )
    assert verified["rows_verified_total"] == 9
    assert verified["transformed_coordinates_total"] == 6
    assert verified["missing_source_coordinates_total"] == 3
    assert verified["parent_build_verified"] is True
    assert verified["coordinate_invariants_verified"] is True
    assert verified["row_level_values_returned"] is False


def test_geospatial_materializer_never_overwrites_immutable_output(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    parent_evidence = _parent_evidence(data_root)
    axis_review = _axis_review()
    materialize_permit_parent(data_root=data_root, evidence=parent_evidence)
    materialize_permit_geospatial(
        data_root=data_root,
        parent_evidence=parent_evidence,
        axis_review=axis_review,
    )
    with pytest.raises(GeospatialEnrichmentError, match="never overwritten"):
        materialize_permit_geospatial(
            data_root=data_root,
            parent_evidence=parent_evidence,
            axis_review=axis_review,
        )


def test_geospatial_materializer_rejects_unreviewed_axis_evidence(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    parent_evidence = _parent_evidence(data_root)
    materialize_permit_parent(data_root=data_root, evidence=parent_evidence)
    axis_review = _axis_review()
    axis_review["review"]["local_wgs84_derivation_approved"] = False
    with pytest.raises(GeospatialEnrichmentError, match="not approved"):
        materialize_permit_geospatial(
            data_root=data_root,
            parent_evidence=parent_evidence,
            axis_review=axis_review,
        )


def test_geospatial_materializer_rejects_partial_parent_coordinate_pair(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    parent_evidence = _parent_evidence(data_root, mutate_first="partial")
    materialize_permit_parent(data_root=data_root, evidence=parent_evidence)
    axis_review = _axis_review(first_partial=0)
    with pytest.raises(GeospatialEnrichmentError, match="partial source coordinate pair"):
        materialize_permit_geospatial(
            data_root=data_root,
            parent_evidence=parent_evidence,
            axis_review=axis_review,
        )


def test_geospatial_materializer_rejects_transform_outside_broad_korea(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    parent_evidence = _parent_evidence(data_root, mutate_first="outside")
    materialize_permit_parent(data_root=data_root, evidence=parent_evidence)
    with pytest.raises(
        GeospatialEnrichmentError,
        match="(outside approved broad Korea envelope|EPSG:5174 to EPSG:4326 transform failed)",
    ):
        materialize_permit_geospatial(
            data_root=data_root,
            parent_evidence=parent_evidence,
            axis_review=_axis_review(),
        )


def test_geospatial_verifier_rejects_tampered_output(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    parent_evidence = _parent_evidence(data_root)
    axis_review = _axis_review()
    materialize_permit_parent(data_root=data_root, evidence=parent_evidence)
    built = materialize_permit_geospatial(
        data_root=data_root,
        parent_evidence=parent_evidence,
        axis_review=axis_review,
    )
    target = Path(built["output_directory"]) / "bakeries.parquet"
    with target.open("ab") as handle:
        handle.write(b"tamper")
    with pytest.raises(GeospatialBuildVerificationError, match="byte count"):
        verify_permit_geospatial_build(
            data_root=data_root,
            parent_evidence=parent_evidence,
            axis_review=axis_review,
        )


def test_geospatial_progress_is_aggregate_only() -> None:
    rendered = format_geospatial_enrichment_progress(
        {
            "event": "row_progress",
            "task_index": 1,
            "task_total": 3,
            "source_key": "general_restaurants",
            "expected_rows": 2_000_000,
            "rows_written": 500_000,
            "overall_rows_written": 500_000,
            "overall_expected_rows": 3_000_000,
        }
    )
    assert rendered == (
        "[1/3] WRITE general_restaurants 500,000/2,000,000 (25.0%) | overall "
        "500,000/3,000,000 (16.7%)"
    )
    assert "management" not in rendered.lower()
