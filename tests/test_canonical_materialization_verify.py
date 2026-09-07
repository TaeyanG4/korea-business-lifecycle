from __future__ import annotations

import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from korea_business_lifecycle.canonical_materialization import materialize_permit_parent
from korea_business_lifecycle.canonical_materialization_verify import (
    PermitBuildVerificationError,
    expected_permit_build_id,
    verify_permit_parent_build,
)


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
    transformed_rows = deepcopy(rows)
    permit_quality = {"INVALID": 1, "VALID": 2}
    closure_quality = {"MISSING": 2, "VALID": 1}
    return {
        "source_key": source_key,
        "retrieval_id": destination.name,
        "artifact_sha256": sha256,
        "artifact_bytes": len(payload),
        "expected_rows": len(transformed_rows),
        "rows_examined": len(transformed_rows),
        "rows_transformed": len(transformed_rows),
        "permit_date_quality": permit_quality,
        "closure_date_quality": closure_quality,
        "null_source_coordinate_x": 1,
        "null_source_coordinate_y": 1,
        "duplicate_linkage_candidates": 0,
        "temporary_uniqueness_index_removed": True,
        "status": "PASS",
    }


def _evidence(data_root: Path) -> dict[str, object]:
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


def test_independent_verifier_accepts_materializer_output(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _evidence(data_root)
    built = materialize_permit_parent(data_root=data_root, evidence=evidence)
    verified = verify_permit_parent_build(data_root=data_root, evidence=evidence)
    assert verified["build_id"] == built["build_id"] == expected_permit_build_id(evidence)
    assert verified["rows_verified_total"] == 9
    assert verified["source_count"] == 3
    assert verified["manifest_verified"] is True
    assert verified["parquet_hashes_verified"] is True
    assert verified["parquet_schemas_verified"] is True
    assert verified["zstd_verified"] is True
    assert verified["quality_aggregates_match_full_dry_run"] is True
    assert verified["row_level_values_returned"] is False
    assert verified["status"] == "PASS"


def test_verifier_rejects_wrong_build_id(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _evidence(data_root)
    materialize_permit_parent(data_root=data_root, evidence=evidence)
    with pytest.raises(PermitBuildVerificationError, match="build_id"):
        verify_permit_parent_build(data_root=data_root, build_id="permit-v1-not-approved", evidence=evidence)


def test_verifier_rejects_tampered_parquet_bytes(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _evidence(data_root)
    built = materialize_permit_parent(data_root=data_root, evidence=evidence)
    parquet_path = Path(built["output_directory"]) / "bakeries.parquet"
    with parquet_path.open("ab") as handle:
        handle.write(b"tamper")
    with pytest.raises(PermitBuildVerificationError, match="byte count"):
        verify_permit_parent_build(data_root=data_root, evidence=evidence)


def test_verifier_rejects_manifest_quality_aggregate_drift(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    evidence = _evidence(data_root)
    built = materialize_permit_parent(data_root=data_root, evidence=evidence)
    manifest_path = Path(built["output_directory"]) / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["results"][0]["permit_date_quality"] = {"VALID": 3}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(PermitBuildVerificationError, match="permit-date quality"):
        verify_permit_parent_build(data_root=data_root, evidence=evidence)
