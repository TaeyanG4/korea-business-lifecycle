from korea_business_lifecycle.provenance import (
    load_bounded_history_audit,
    load_history_review,
    load_license_review,
    load_observed_snapshot_summary,
    load_privacy_review,
    load_source_registry,
    validate_history_review,
    validate_bounded_history_audit,
    validate_license_review,
    validate_observed_snapshot_summary,
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


def test_direct_bulk_download_urls_are_recorded() -> None:
    registry = load_source_registry()
    for item in registry["categories"]:
        assert item["bulk_url"].startswith("https://file.localdata.go.kr/file/")
        assert item["bulk_download_url"].startswith(
            "https://file.localdata.go.kr/file/download/"
        )
        assert item["observed_download_bytes_2026_09_07"] > 0


def test_license_review_keeps_kaggle_blocked() -> None:
    review = load_license_review()
    assert validate_license_review(review) == []


def test_privacy_review_keeps_public_allowlist_blocked() -> None:
    review = load_privacy_review()
    assert validate_privacy_review(review) == []
    assert review["public_allowlist_approved"] is False
    assert review["field_inventory_complete"] is True


def test_history_review_is_finite_but_not_an_event_log() -> None:
    review = load_history_review()
    assert validate_history_review(review) == []
    assert review["common_contract"]["lower_base_date"] == "2026-01-01"
    assert review["common_contract"]["max_num_of_rows"] == 100
    assert review["common_contract"]["event_log_claim"] is False


def test_observed_snapshot_summary_matches_empirical_v1_scale() -> None:
    summary = load_observed_snapshot_summary()
    assert validate_observed_snapshot_summary(summary) == []
    assert summary["totals"]["rows"] == 3_010_802
    assert summary["totals"]["bytes"] == 926_587_446
    assert summary["totals"]["cross_category_management_number_overlap"] == 0


def test_bounded_history_audit_keeps_identity_claim_scoped() -> None:
    audit = load_bounded_history_audit()
    assert validate_bounded_history_audit(audit) == []
    assert audit["decision"] == "BOUNDED_CONTINUITY_SUPPORTED_FURTHER_AUDIT_REQUIRED"
    rest = next(item for item in audit["categories"] if item["source_key"] == "rest_cafes")
    assert rest["status_codes_added"] == ["05"]
    assert audit["identity_claim"]["source_primary_key_declared"] is False
    assert audit["identity_claim"]["establishment_identity_declared"] is False
