from __future__ import annotations

import csv
import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import korea_business_lifecycle.kaggle_release as kaggle_release
from korea_business_lifecycle.kaggle_release import (
    PUBLIC_COLUMNS,
    KaggleReleaseError,
    _metadata,
    _release_schema,
    _validate_owner,
    _write_aggregate_csv,
)


def test_kaggle_metadata_is_aggregate_only_and_uses_other_license() -> None:
    metadata = _metadata("example-owner")
    assert metadata["id"] == "example-owner/korea-food-service-permit-aggregate"
    assert metadata["licenses"] == [{"name": "other"}]
    assert [item["path"] for item in metadata["resources"]] == [
        "korea_food_service_permit_aggregate.parquet",
        "korea_food_service_permit_aggregate.csv",
        "source_summary.csv",
    ]
    assert 6 <= len(metadata["title"]) <= 50
    assert 20 <= len(metadata["subtitle"]) <= 80


def test_kaggle_owner_slug_is_validated() -> None:
    assert _validate_owner("abc_123-team") == "abc_123-team"
    with pytest.raises(KaggleReleaseError):
        _validate_owner("bad owner/name")


def test_kaggle_description_keeps_semantic_limits() -> None:
    metadata = _metadata("owner")
    description = metadata["description"]
    assert "Status 03 is not treated as irreversible" in description
    assert "status 05 remains unresolved" in description
    assert "does not relicense upstream source records" in description
    assert "CSV and Parquet are two serializations of the same aggregate" in description
    json.dumps(metadata, ensure_ascii=False)


def test_release_schema_is_current_release_contract_without_stale_candidate_gate() -> None:
    schema = _release_schema()
    assert schema["release_package_version"] == 2
    assert [item["name"] for item in schema["columns"]] == PUBLIC_COLUMNS
    assert schema["privacy"]["row_level_records_included"] is False
    assert schema["privacy"]["precise_coordinates_included"] is False
    assert schema["semantic_limits"]["permit_year_is_physical_open_year"] is False
    assert schema["semantic_limits"]["closure_year_is_permanent_terminal_event"] is False
    assert "aggregate_publication_approved" not in schema
    assert "redistribution_status" not in schema


def test_csv_serialization_is_deterministic_and_preserves_nulls(tmp_path, monkeypatch) -> None:
    table = pa.table(
        {
            "source_key": pa.array(
                ["general_restaurants", "rest_cafes", "bakeries"], type=pa.string()
            ),
            "authority_code": pa.array(["3000000", "3010000", "3020000"], type=pa.string()),
            "source_status_code": pa.array(["01", None, "03"], type=pa.string()),
            "source_detail_status_code": pa.array([None, "10", "20"], type=pa.string()),
            "permit_year": pa.array([2020, None, 2021], type=pa.int32()),
            "closure_year": pa.array([None, 2022, 2023], type=pa.int32()),
            "cell_count": pa.array([10, 11, 12], type=pa.int64()),
        }
    )
    parquet_path = tmp_path / "aggregate.parquet"
    first_csv = tmp_path / "first.csv"
    second_csv = tmp_path / "second.csv"
    pq.write_table(table, parquet_path)
    monkeypatch.setattr(kaggle_release, "EXPECTED_ROWS", 3)
    monkeypatch.setattr(kaggle_release, "EXPECTED_RELEASED_SOURCE_ROWS", 33)

    first = _write_aggregate_csv(parquet_path, first_csv)
    second = _write_aggregate_csv(parquet_path, second_csv)
    assert first == second
    assert first_csv.read_bytes() == second_csv.read_bytes()
    assert first["rows"] == 3
    assert first["represented_source_rows"] == 33

    with first_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == PUBLIC_COLUMNS
    assert rows[1][3] == ""
    assert rows[2][2] == ""
    assert rows[2][4] == ""


def test_csv_serialization_rejects_cells_below_threshold(tmp_path, monkeypatch) -> None:
    table = pa.table(
        {
            "source_key": pa.array(["bakeries"], type=pa.string()),
            "authority_code": pa.array(["3000000"], type=pa.string()),
            "source_status_code": pa.array(["01"], type=pa.string()),
            "source_detail_status_code": pa.array([None], type=pa.string()),
            "permit_year": pa.array([2020], type=pa.int32()),
            "closure_year": pa.array([None], type=pa.int32()),
            "cell_count": pa.array([9], type=pa.int64()),
        }
    )
    parquet_path = tmp_path / "aggregate.parquet"
    pq.write_table(table, parquet_path)
    monkeypatch.setattr(kaggle_release, "EXPECTED_ROWS", 1)
    monkeypatch.setattr(kaggle_release, "EXPECTED_RELEASED_SOURCE_ROWS", 9)

    with pytest.raises(KaggleReleaseError, match="below k=10"):
        _write_aggregate_csv(parquet_path, tmp_path / "bad.csv")
