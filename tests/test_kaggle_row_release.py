from __future__ import annotations

from korea_business_lifecycle.kaggle_row_release import (
    EXPECTED_COLUMNS,
    EXPECTED_ROWS,
    PUBLIC_CSV_FILENAME,
    PUBLIC_PARQUET_FILENAME,
    _metadata,
    _public_arrow_schema,
    _csv_arrow_schema,
    _validated_owner,
    KaggleRowReleaseError,
)
import pytest


def test_row_release_exact_shape_and_full_canonical_schema() -> None:
    schema = _public_arrow_schema()
    assert EXPECTED_ROWS == 3_010_802
    assert EXPECTED_COLUMNS == 26
    assert len(schema.names) == 26
    assert "management_number" in schema.names
    assert "business_name" in schema.names
    assert "road_address" in schema.names
    assert "source_coordinate_x" in schema.names
    assert "source_coordinate_y" in schema.names
    assert schema.metadata[b"kbl.publication_status"] == b"APPROVED_CANONICAL_ROW_LEVEL_RELEASE"


def test_row_release_kaggle_metadata_exposes_csv_and_parquet() -> None:
    metadata = _metadata("taeyangg4")
    assert metadata["id"] == "taeyangg4/korea-food-service-permits"
    paths = [resource["path"] for resource in metadata["resources"]]
    assert paths[:2] == [PUBLIC_CSV_FILENAME, PUBLIC_PARQUET_FILENAME]
    assert "3,010,802" in metadata["description"]


def test_csv_schema_keeps_26_columns_and_renders_utc_without_timezone_dependency() -> None:
    schema = _csv_arrow_schema(_public_arrow_schema())
    assert len(schema.names) == 26
    assert str(schema.field("source_retrieved_at_utc").type) == "timestamp[us]"


def test_row_release_owner_is_pinned_to_approved_dataset() -> None:
    assert _validated_owner("taeyangg4") == "taeyangg4"
    with pytest.raises(KaggleRowReleaseError):
        _validated_owner("other-owner")
    with pytest.raises(KaggleRowReleaseError):
        _validated_owner("bad owner")
