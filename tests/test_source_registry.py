from korea_business_lifecycle.provenance import (
    load_license_review,
    load_privacy_review,
    load_source_registry,
    validate_license_review,
    validate_privacy_review,
    validate_source_registry,
)


def test_source_registry_invariants() -> None:
    registry = load_source_registry()
    assert validate_source_registry(registry) == []


def test_v1_catalog_planning_scale() -> None:
    registry = load_source_registry()
    rows = [item["catalog_row_count"] for item in registry["categories"]]
    assert rows == [2_129_830, 561_397, 60_302]
    assert sum(rows) == 2_751_529


def test_no_category_claims_a_primary_key() -> None:
    registry = load_source_registry()
    assert all(item["documented_primary_key"] is None for item in registry["categories"])


def test_bakery_file_dataset_id_is_currently_verified() -> None:
    registry = load_source_registry()
    bakery = next(item for item in registry["categories"] if item["source_key"] == "bakeries")
    assert bakery["file_dataset_id"] == "15006688"


def test_license_review_keeps_kaggle_blocked() -> None:
    review = load_license_review()
    assert validate_license_review(review) == []


def test_privacy_review_keeps_public_allowlist_blocked() -> None:
    review = load_privacy_review()
    assert validate_privacy_review(review) == []
    assert review["public_allowlist_approved"] is False
