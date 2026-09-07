from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from korea_business_lifecycle.canonical_permit import (
    PermitTransformError,
    build_permit_transform_context,
    permit_transform_context_from_retrieval_manifest,
    transform_current_snapshot_rows,
    transform_permit_row,
)
from korea_business_lifecycle.canonical_schema import (
    FROZEN_V1_SOURCE_COLUMNS,
    FORBIDDEN_CANONICAL_COLUMNS,
    load_permit_parent_schema,
)


ROOT = Path(__file__).resolve().parents[1]


def _rows() -> list[dict[str, str]]:
    value = json.loads(
        (ROOT / "tests" / "fixtures" / "synthetic_permit_rows.json").read_text(encoding="utf-8")
    )
    assert isinstance(value, list)
    return value


def _context():
    return build_permit_transform_context(
        source_key="general_restaurants",
        source_artifact_sha256="a" * 64,
        source_retrieved_at_utc="2026-09-07T00:00:00Z",
    )


def test_synthetic_permit_rows_match_frozen_39_column_source_shape() -> None:
    rows = _rows()
    assert 1 <= len(rows) <= 10
    assert all(set(row) == FROZEN_V1_SOURCE_COLUMNS for row in rows)
    assert all(row["관리번호"].startswith("SYNTHETIC-MNG-") for row in rows)


def test_transform_current_snapshot_rows_matches_frozen_26_column_parent() -> None:
    schema = load_permit_parent_schema()
    expected_order = [item["name"] for item in schema["columns"]]
    result = transform_current_snapshot_rows(_rows(), context=_context())

    assert len(result) == 3
    assert all(list(row) == expected_order for row in result)
    assert [row["source_row_number"] for row in result] == [1, 2, 3]
    assert all(row["source_key"] == "general_restaurants" for row in result)
    assert all(row["source_artifact_sha256"] == "a" * 64 for row in result)
    assert all(row["source_retrieved_at_utc"] == datetime(2026, 9, 7, tzinfo=timezone.utc) for row in result)


def test_transform_normalizes_strings_without_identifier_coercion_or_deferred_leakage() -> None:
    first = transform_current_snapshot_rows(_rows(), context=_context())[0]
    assert first["authority_code"] == "0012345"
    assert first["lot_postal_code"] == "01234"
    assert first["business_name"] == "합성 식당 A"
    assert first["road_address"] == "합성로 1"
    assert first["source_status_name"] == "영업"
    assert first["source_coordinate_x"] == 200000.5
    assert first["source_coordinate_y"] == 500000.25
    assert "telephone" not in first
    assert "homepage" not in first
    assert not (set(first) & FORBIDDEN_CANONICAL_COLUMNS)
    assert "SYNTHETIC-PHONE-DEFERRED" not in str(first)
    assert "synthetic.invalid" not in str(first)


def test_transform_preserves_date_quality_and_unmapped_source_status() -> None:
    first, second, third = transform_current_snapshot_rows(_rows(), context=_context())
    assert first["permit_date"] == date(2020, 1, 2)
    assert first["permit_date_quality"] == "VALID"
    assert first["closure_date"] is None
    assert first["closure_date_quality"] == "MISSING"

    assert second["permit_date"] is None
    assert second["permit_date_quality"] == "INVALID"
    assert second["closure_date"] is None
    assert second["closure_date_quality"] == "MISSING"
    assert second["source_status_code"] == "05"
    assert second["source_detail_status_code"] == "05"

    assert third["permit_date"] == date(2020, 1, 3)
    assert third["closure_date"] == date(2021, 3, 4)
    assert third["closure_date_quality"] == "VALID"
    assert third["source_status_code"] == "03"
    assert third["source_coordinate_x"] == -1.25


def test_transform_is_deterministic_for_identical_rows_and_context() -> None:
    rows = _rows()
    assert transform_current_snapshot_rows(rows, context=_context()) == transform_current_snapshot_rows(
        deepcopy(rows), context=_context()
    )


def test_transform_fails_closed_on_duplicate_expected_linkage_candidate() -> None:
    rows = _rows()
    duplicate = deepcopy(rows[0])
    duplicate["사업장명"] = "different synthetic name does not change linkage"
    rows.append(duplicate)
    with pytest.raises(PermitTransformError, match="duplicate expected uniqueness candidate") as exc_info:
        transform_current_snapshot_rows(rows, context=_context())
    assert "SYNTHETIC-MNG-0001" not in str(exc_info.value)


def test_transform_rejects_source_schema_drift_and_blank_required_identifiers() -> None:
    row = deepcopy(_rows()[0])
    row.pop("관리번호")
    row["새필드"] = "synthetic"
    with pytest.raises(PermitTransformError, match="frozen 39-column inventory"):
        transform_permit_row(row, context=_context(), source_row_number=1)

    row = deepcopy(_rows()[0])
    row["관리번호"] = "   "
    with pytest.raises(PermitTransformError, match="required source identifier 관리번호"):
        transform_permit_row(row, context=_context(), source_row_number=1)


def test_transform_rejects_nonblank_invalid_or_nonfinite_coordinates() -> None:
    for value in ("not-a-coordinate", "NaN", "Infinity"):
        row = deepcopy(_rows()[0])
        row["좌표정보(X)"] = value
        with pytest.raises(PermitTransformError, match=r"좌표정보\(X\)"):
            transform_permit_row(row, context=_context(), source_row_number=1)


def test_transform_context_can_be_derived_from_acquisition_manifest() -> None:
    manifest = {
        "manifest_version": 1,
        "source_key": "rest_cafes",
        "artifact": {"sha256": "b" * 64},
        "request": {"completed": {"utc": "2026-09-07T09:30:00+09:00"}},
    }
    context = permit_transform_context_from_retrieval_manifest(manifest)
    assert context.source_key == "rest_cafes"
    assert context.source_artifact_sha256 == "b" * 64
    assert context.source_retrieved_at_utc == datetime(2026, 9, 7, 0, 30, tzinfo=timezone.utc)


def test_transform_context_rejects_non_v1_source_bad_hash_and_naive_time() -> None:
    with pytest.raises(PermitTransformError, match="unsupported v1 source"):
        build_permit_transform_context(
            source_key="not-v1",
            source_artifact_sha256="a" * 64,
            source_retrieved_at_utc="2026-09-07T00:00:00Z",
        )
    with pytest.raises(PermitTransformError, match="SHA-256"):
        build_permit_transform_context(
            source_key="bakeries",
            source_artifact_sha256="BAD",
            source_retrieved_at_utc="2026-09-07T00:00:00Z",
        )
    with pytest.raises(PermitTransformError, match="timezone-aware"):
        build_permit_transform_context(
            source_key="bakeries",
            source_artifact_sha256="c" * 64,
            source_retrieved_at_utc="2026-09-07T00:00:00",
        )
