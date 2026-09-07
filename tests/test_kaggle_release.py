from __future__ import annotations

import json

import pytest

from korea_business_lifecycle.kaggle_release import _metadata, _validate_owner, KaggleReleaseError


def test_kaggle_metadata_is_aggregate_only_and_uses_other_license() -> None:
    metadata = _metadata("example-owner")
    assert metadata["id"] == "example-owner/korea-food-service-permit-aggregate"
    assert metadata["licenses"] == [{"name": "other"}]
    assert metadata["resources"] == [
        {
            "path": "korea_food_service_permit_aggregate.parquet",
            "description": (
                "Verified k=10 privacy-minimized aggregate. Columns: source_key, authority_code, "
                "source_status_code, source_detail_status_code, permit_year, closure_year, cell_count."
            ),
        }
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
    json.dumps(metadata, ensure_ascii=False)
