from __future__ import annotations

import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from korea_business_lifecycle.canonical_materialization import (
    COMPRESSION_LEVEL,
    DATA_PAGE_VERSION,
    PARQUET_VERSION,
    PYARROW_VERSION,
    ROWS_PER_BATCH,
    ROWS_PER_ROW_GROUP,
    PermitMaterializationError,
    format_materialization_progress,
    materialization_plan,
    materialize_permit_parent,
    permit_arrow_schema,
)
from korea_business_lifecycle.canonical_schema import load_permit_parent_schema


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ORDER = ("general_restaurants", "rest_cafes", "bakeries")


def _rows() -> list[dict[str, str]]:
    value = json.loads(
        (ROOT / "tests" / "fixtures" / "synthetic_permit_rows.json").read_text(encoding="utf-8")
    )
    assert isinstance(value, list)
    return value


def _write_snapshot(data_root: Path, source_key: str, suffix: str) -> dict[str, object]:
    destination = data_root / "raw" / source_key / f"20260907T000000Z-{suffix}"
    destination.mkdir(parents=True)
    artifact_path = destination / "source.csv"
    rows = deepcopy(_rows())
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
        "expected_rows": 3,
        "rows_examined": 3,
        "rows_transformed": 3,
        "duplicate_linkage_candidates": 0,
        "temporary_uniqueness_index_removed": True,
        "status": "PASS",
    }


def _synthetic_evidence(data_root: Path) -> dict[str, object]:
    results = [
        _write_snapshot(data_root, source_key, f"{index:02d}")
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


def test_pyarrow_writer_version_is_pinned() -> None:
    assert pa.__version__ == PYARROW_VERSION == "21.0.0"
    assert PARQUET_VERSION == "2.6"
    assert DATA_PAGE_VERSION == "2.0"
    assert COMPRESSION_LEVEL == 9
    assert ROWS_PER_BATCH == ROWS_PER_ROW_GROUP == 50_000


def test_arrow_schema_exactly_matches_frozen_parent_contract() -> None:
    frozen = load_permit_parent_schema()
    arrow = permit_arrow_schema()
    assert arrow.names == [item["name"] for item in frozen["columns"]]
    assert len(arrow) == 26
    assert arrow.field("source_row_number").type == pa.int64()
    assert arrow.field("source_retrieved_at_utc").type == pa.timestamp("us", tz="UTC")
    assert arrow.field("permit_date").type == pa.date32()
    assert arrow.field("source_coordinate_x").type == pa.float64()
    assert arrow.metadata[b"kbl.publication_status"] == b"NOT_APPROVED_FOR_PUBLIC_ROW_LEVEL_BUILD"


def test_materialization_plan_is_deterministic_and_local_only(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _synthetic_evidence(data_root)
    first = materialization_plan(data_root=data_root, evidence=evidence)
    second = materialization_plan(data_root=data_root, evidence=deepcopy(evidence))
    assert first["build_id"] == second["build_id"]
    assert first["expected_rows_total"] == 9
    assert first["input_bytes_total"] > 0
    assert first["public_row_level_release_approved"] is False
    assert first["production_materialization_performed"] is False
    assert first["status"] == "READY_FOR_USER_EXECUTION"
    assert str(data_root.resolve()) in first["output_directory"]


def test_materializer_writes_three_verified_parquet_files_and_local_manifest(
    external_tmp_path: Path,
) -> None:
    data_root = external_tmp_path / "data"
    evidence = _synthetic_evidence(data_root)
    result = materialize_permit_parent(data_root=data_root, evidence=evidence)

    assert result["status"] == "PASS"
    assert result["rows_total"] == 9
    assert result["source_count"] == 3
    assert result["public_row_level_release_approved"] is False
    assert result["wgs84_generated"] is False
    assert result["episode_reconstruction_performed"] is False

    output_dir = Path(result["output_directory"])
    assert output_dir.is_dir()
    assert (output_dir / "manifest.json").is_file()
    assert {item["source_key"] for item in result["results"]} == set(SOURCE_ORDER)
    for item in result["results"]:
        parquet_path = output_dir / item["output_file"]
        assert parquet_path.is_file()
        file = pq.ParquetFile(parquet_path)
        assert file.metadata.num_rows == 3
        assert pq.read_schema(parquet_path).equals(permit_arrow_schema(), check_metadata=True)
        assert file.metadata.row_group(0).column(0).compression == "ZSTD"
        assert item["uniqueness_validation"] == "REUSED_EXACT_FULL_DRY_RUN_FOR_IDENTICAL_SHA256"


def test_materialized_invalid_date_remains_null_with_invalid_quality(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _synthetic_evidence(data_root)
    result = materialize_permit_parent(data_root=data_root, evidence=evidence)
    output_dir = Path(result["output_directory"])
    table = pq.read_table(
        output_dir / "general_restaurants.parquet",
        columns=["permit_date", "permit_date_quality"],
    )
    assert table.column("permit_date").to_pylist()[1] is None
    assert table.column("permit_date_quality").to_pylist()[1] == "INVALID"


def test_materializer_rejects_changed_input_hash_and_removes_staging(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _synthetic_evidence(data_root)
    source = evidence["results"][0]
    artifact = next((data_root / "raw" / source["source_key"]).glob("*/source.csv"))
    with artifact.open("ab") as handle:
        handle.write(b"tampered")

    with pytest.raises(PermitMaterializationError, match="byte count"):
        materialize_permit_parent(data_root=data_root, evidence=evidence)
    final_root = data_root / "canonical" / "permit" / "v1"
    assert not final_root.exists() or not any(final_root.iterdir())
    staging_root = data_root / ".tmp" / "permit-materialization"
    assert not staging_root.exists() or not any(staging_root.iterdir())


def test_materializer_never_overwrites_immutable_build(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _synthetic_evidence(data_root)
    materialize_permit_parent(data_root=data_root, evidence=evidence)
    with pytest.raises(PermitMaterializationError, match="never overwritten"):
        materialize_permit_parent(data_root=data_root, evidence=evidence)


def test_materialization_progress_is_aggregate_only() -> None:
    rendered = format_materialization_progress(
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
