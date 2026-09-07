from __future__ import annotations

import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from korea_business_lifecycle.canonical_materialization import materialize_permit_parent
from korea_business_lifecycle.canonical_schema import (
    load_public_permit_aggregate_schema,
    validate_public_permit_aggregate_schema,
)
from korea_business_lifecycle.public_aggregate import (
    MIN_CELL_COUNT,
    PublicAggregateError,
    format_public_aggregate_progress,
    materialize_public_permit_aggregate,
    public_aggregate_arrow_schema,
    public_aggregate_plan,
)
from korea_business_lifecycle.public_aggregate_verify import (
    PublicAggregateVerificationError,
    verify_public_permit_aggregate,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ORDER = ("general_restaurants", "rest_cafes", "bakeries")


def _base_row() -> dict[str, str]:
    rows = json.loads(
        (ROOT / "tests" / "fixtures" / "synthetic_permit_rows.json").read_text(encoding="utf-8")
    )
    return deepcopy(rows[0])


def _write_snapshot(data_root: Path, source_key: str, suffix: str) -> dict[str, object]:
    destination = data_root / "raw" / source_key / f"20260907T000000Z-{suffix}"
    destination.mkdir(parents=True)
    artifact_path = destination / "source.csv"
    rows: list[dict[str, str]] = []
    for index in range(12):
        row = _base_row()
        row["관리번호"] = f"SYNTHETIC-{source_key}-{index:03d}"
        if index == 11:
            row["영업상태코드"] = "03"
            row["상세영업상태코드"] = "02"
            row["인허가일자"] = "20210101"
            row["폐업일자"] = "20220101"
        rows.append(row)
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
    return {
        "source_key": source_key,
        "retrieval_id": destination.name,
        "artifact_sha256": sha256,
        "artifact_bytes": len(payload),
        "expected_rows": 12,
        "rows_examined": 12,
        "rows_transformed": 12,
        "permit_date_quality": {"VALID": 12},
        "closure_date_quality": {"MISSING": 11, "VALID": 1},
        "null_source_coordinate_x": 0,
        "null_source_coordinate_y": 0,
        "duplicate_linkage_candidates": 0,
        "temporary_uniqueness_index_removed": True,
        "status": "PASS",
    }


def _parent_evidence(data_root: Path) -> dict[str, object]:
    results = [
        _write_snapshot(data_root, source_key, f"{index:02d}")
        for index, source_key in enumerate(SOURCE_ORDER, start=1)
    ]
    return {
        "decision": "FULL_CURRENT_SNAPSHOT_DRY_RUN_PASSED",
        "scope": {
            "sources": list(SOURCE_ORDER),
            "rows_examined_total": 36,
            "production_materialization_performed": False,
        },
        "results": results,
    }


def test_public_aggregate_schema_excludes_row_level_identifiers() -> None:
    schema = load_public_permit_aggregate_schema()
    assert validate_public_permit_aggregate_schema(schema) == []
    names = {item["name"] for item in schema["columns"]}
    assert len(names) == 7
    for forbidden in (
        "management_number",
        "business_name",
        "road_address",
        "source_coordinate_x",
        "wgs84_longitude",
    ):
        assert forbidden not in names
    assert schema["privacy_policy"]["minimum_cell_count"] == MIN_CELL_COUNT == 10
    assert schema["scope"]["aggregate_publication_approved"] is False
    assert schema["scope"]["redistribution_status"] == "UNRESOLVED"


def test_public_aggregate_plan_is_local_and_publication_blocked(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _parent_evidence(data_root)
    plan = public_aggregate_plan(data_root=data_root, parent_evidence=evidence)
    assert plan["expected_parent_rows"] == 36
    assert plan["minimum_cell_count"] == 10
    assert plan["row_level_public_projection_approved"] is False
    assert plan["aggregate_publication_approved"] is False
    assert plan["redistribution_status"] == "UNRESOLVED"
    assert plan["status"] == "READY_FOR_USER_EXECUTION"


def test_public_aggregate_materializer_and_verifier_enforce_suppression(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _parent_evidence(data_root)
    materialize_permit_parent(data_root=data_root, evidence=evidence)
    built = materialize_public_permit_aggregate(data_root=data_root, parent_evidence=evidence)
    assert built["status"] == "PASS"
    assert built["rows_scanned"] == 36
    assert built["aggregate_cells_total_before_suppression"] == 6
    assert built["aggregate_cells_released_candidate"] == 3
    assert built["aggregate_cells_suppressed"] == 3
    assert built["released_source_rows"] == 33
    assert built["suppressed_source_rows"] == 3
    assert built["row_level_values_written"] is False
    assert built["aggregate_publication_approved"] is False

    output_path = Path(built["output_directory"]) / "permit_aggregate.parquet"
    table = pq.read_table(output_path)
    assert table.num_rows == 3
    assert table.schema.equals(public_aggregate_arrow_schema(), check_metadata=True)
    assert table.column("cell_count").to_pylist() == [11, 11, 11]

    verified = verify_public_permit_aggregate(data_root=data_root, parent_evidence=evidence)
    assert verified["status"] == "PASS"
    assert verified["aggregate_cells_released_candidate"] == 3
    assert verified["released_source_rows"] == 33
    assert verified["suppressed_source_rows"] == 3
    assert verified["suppression_invariants_verified"] is True
    assert verified["row_level_values_returned"] is False


def test_public_aggregate_materializer_never_overwrites(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _parent_evidence(data_root)
    materialize_permit_parent(data_root=data_root, evidence=evidence)
    materialize_public_permit_aggregate(data_root=data_root, parent_evidence=evidence)
    with pytest.raises(PublicAggregateError, match="already exists"):
        materialize_public_permit_aggregate(data_root=data_root, parent_evidence=evidence)


def test_public_aggregate_verifier_rejects_tampered_bytes(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _parent_evidence(data_root)
    materialize_permit_parent(data_root=data_root, evidence=evidence)
    built = materialize_public_permit_aggregate(data_root=data_root, parent_evidence=evidence)
    output_path = Path(built["output_directory"]) / "permit_aggregate.parquet"
    with output_path.open("ab") as handle:
        handle.write(b"tamper")
    with pytest.raises(PublicAggregateVerificationError, match="byte count"):
        verify_public_permit_aggregate(data_root=data_root, parent_evidence=evidence)


def test_public_aggregate_progress_never_contains_row_level_values() -> None:
    rendered = format_public_aggregate_progress(
        {
            "event": "row_progress",
            "task_index": 1,
            "task_total": 3,
            "source_key": "general_restaurants",
            "rows_scanned": 50_000,
            "expected_rows": 2_000_000,
            "overall_rows_scanned": 50_000,
            "overall_expected_rows": 3_000_000,
        }
    )
    assert "50,000/2,000,000" in rendered
    assert "management" not in rendered.lower()
    assert "address" not in rendered.lower()
