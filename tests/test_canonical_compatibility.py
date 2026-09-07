from __future__ import annotations

import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from korea_business_lifecycle.canonical_compatibility import (
    CompatibilityValidationError,
    latest_retrieval_manifest,
    validate_latest_current_snapshots,
    validate_snapshot_compatibility,
)


ROOT = Path(__file__).resolve().parents[1]


def _synthetic_rows() -> list[dict[str, str]]:
    value = json.loads(
        (ROOT / "tests" / "fixtures" / "synthetic_permit_rows.json").read_text(encoding="utf-8")
    )
    assert isinstance(value, list)
    return value


def _write_snapshot(
    data_root: Path,
    source_key: str,
    retrieval_id: str,
    *,
    rows: list[dict[str, str]] | None = None,
    fieldnames: list[str] | None = None,
) -> Path:
    selected_rows = deepcopy(rows if rows is not None else _synthetic_rows())
    destination = data_root / "raw" / source_key / retrieval_id
    destination.mkdir(parents=True)
    artifact_path = destination / "source.csv"
    selected_fieldnames = fieldnames or list(selected_rows[0])
    with artifact_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=selected_fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(selected_rows)
    payload = artifact_path.read_bytes()
    manifest = {
        "manifest_version": 1,
        "retrieval_id": retrieval_id,
        "source_key": source_key,
        "request": {"completed": {"utc": "2026-09-07T00:00:00+00:00"}},
        "artifact": {
            "relative_path": artifact_path.relative_to(data_root).as_posix(),
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        },
    }
    manifest_path = destination / "retrieval.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_bounded_real_compatibility_returns_only_aggregate_contract(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    manifest_path = _write_snapshot(data_root, "general_restaurants", "20260907T000000Z-a")

    result = validate_snapshot_compatibility(manifest_path, data_root=data_root, max_rows=3)

    assert result["source_key"] == "general_restaurants"
    assert result["rows_examined"] == 3
    assert result["rows_transformed"] == 3
    assert result["source_column_count"] == 39
    assert result["output_column_count"] == 26
    assert sum(result["permit_date_quality"].values()) == 3
    assert sum(result["closure_date_quality"].values()) == 3
    assert result["duplicate_linkage_candidates"] == 0
    assert result["row_level_values_returned"] is False
    assert result["production_materialization_performed"] is False
    assert "management_number" not in result
    assert "business_name" not in result


def test_bounded_compatibility_honors_row_cap(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    manifest_path = _write_snapshot(data_root, "rest_cafes", "20260907T000000Z-a")
    result = validate_snapshot_compatibility(manifest_path, data_root=data_root, max_rows=2)
    assert result["rows_examined"] == 2
    assert result["max_rows"] == 2


def test_bounded_compatibility_rejects_header_drift(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    rows = _synthetic_rows()
    fields = list(rows[0])[:-1]
    manifest_path = _write_snapshot(
        data_root,
        "bakeries",
        "20260907T000000Z-a",
        rows=rows,
        fieldnames=fields,
    )
    with pytest.raises(CompatibilityValidationError, match="frozen 39-column inventory"):
        validate_snapshot_compatibility(manifest_path, data_root=data_root)


def test_bounded_compatibility_fails_closed_on_duplicate_without_exposing_id(
    external_tmp_path: Path,
) -> None:
    data_root = external_tmp_path / "data"
    rows = _synthetic_rows()[:2]
    rows[1]["관리번호"] = rows[0]["관리번호"]
    manifest_path = _write_snapshot(
        data_root,
        "general_restaurants",
        "20260907T000000Z-a",
        rows=rows,
    )
    with pytest.raises(CompatibilityValidationError, match="duplicate expected uniqueness candidate") as exc:
        validate_snapshot_compatibility(manifest_path, data_root=data_root)
    assert rows[0]["관리번호"] not in str(exc.value)


def test_bounded_compatibility_rejects_manifest_byte_mismatch(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    manifest_path = _write_snapshot(data_root, "bakeries", "20260907T000000Z-a")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifact"]["bytes"] += 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CompatibilityValidationError, match="byte count"):
        validate_snapshot_compatibility(manifest_path, data_root=data_root)


def test_latest_manifest_selection_and_three_source_summary(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    for source_key in ("general_restaurants", "rest_cafes", "bakeries"):
        older = _write_snapshot(data_root, source_key, "20260906T000000Z-a")
        newer = _write_snapshot(data_root, source_key, "20260907T000000Z-b")
        assert latest_retrieval_manifest(source_key, data_root=data_root) == newer.resolve()
        assert older.exists()

    summary = validate_latest_current_snapshots(data_root=data_root, max_rows=1)
    assert summary["scope"] == ["general_restaurants", "rest_cafes", "bakeries"]
    assert summary["rows_examined_total"] == 3
    assert summary["production_materialization_performed"] is False
    assert summary["row_level_values_returned"] is False
    assert summary["status"] == "PASS"
