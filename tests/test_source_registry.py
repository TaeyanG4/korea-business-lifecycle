from korea_business_lifecycle.provenance import (
    load_bounded_history_audit,
    load_expanded_history_audit,
    load_grain_decision,
    load_history_review,
    load_history_sample_plan,
    load_reverse_transition_probe_plan,
    load_reverse_transition_findings,
    load_license_review,
    load_observed_snapshot_summary,
    load_privacy_review,
    load_source_registry,
    validate_history_review,
    validate_history_sample_plan,
    validate_reverse_transition_probe_plan,
    validate_reverse_transition_findings,
    validate_bounded_history_audit,
    validate_expanded_history_audit,
    validate_grain_decision,
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


def test_history_sample_plan_is_bounded_and_deterministic() -> None:
    plan = load_history_sample_plan()
    assert validate_history_sample_plan(plan) == []
    assert plan["additional_history_requests"] == 2192
    assert [item["authority_code"] for item in plan["selection"]["representatives"]] == [
        "4420000",
        "4530000",
        "3830000",
        "3220000",
    ]


def test_reverse_transition_probe_plan_is_tightly_bounded() -> None:
    plan = load_reverse_transition_probe_plan()
    assert validate_reverse_transition_probe_plan(plan) == []
    assert plan["planned_tasks"] == 6
    assert plan["max_network_requests"] == 411


def test_reverse_transition_findings_reject_irreversible_terminal_closure() -> None:
    findings = load_reverse_transition_findings()
    assert validate_reverse_transition_findings(findings) == []
    assert findings["decision"] == "SOURCE_STATE_REVERSALS_CONFIRMED_TERMINAL_IRREVERSIBILITY_REJECTED"
    assert findings["lifecycle_conclusion"]["code_03_can_be_assumed_irreversible_terminal"] is False
    assert findings["lifecycle_conclusion"]["reopening_vs_correction_resolved"] is False
    assert all(item["status_transition"] == "03->01" for item in findings["cases"])


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


def test_expanded_history_audit_records_reversibility_without_pk_claim() -> None:
    audit = load_expanded_history_audit()
    assert validate_expanded_history_audit(audit) == []
    assert audit["decision"] == "MNG_NO_CONTINUITY_CONSISTENT_REVERSIBLE_SIGNAL_PRESENT"
    assert audit["status_code_transitions"]["03->01"] == 2
    assert audit["assessment_counts"]["mng_no_continuity"] == {"STRONG": 15}
    assert audit["identity_claim"]["source_primary_key_declared"] is False
    assert audit["lifecycle_claim"]["terminal_closure_declared_irreversible"] is False


def test_v1_grain_is_permit_parent_with_reversible_status_episodes() -> None:
    decision = load_grain_decision()
    assert validate_grain_decision(decision) == []
    assert decision["selected_grains"]["canonical_parent_grain"]["name"] == "PERMIT"
    assert decision["selected_grains"]["lifecycle_analysis_grain"]["name"] == "PERMIT_STATUS_EPISODE"
    assert decision["identity_policy"]["mng_no_primary_key_declared"] is False
    assert decision["episode_semantics"]["active_end_observations"] == "right-censored"
    assert decision["episode_semantics"]["closure_code_03_irreversible"] is False
    assert decision["next_gate"]["permit_parent_schema"] == "schemas/permit_parent.v1.json"
    assert decision["next_gate"]["permit_parent_schema_status"] == "FROZEN"
    assert decision["next_gate"]["permit_status_episode_schema"] == "schemas/permit_status_episode.v1.json"
    assert decision["next_gate"]["permit_status_episode_schema_status"] == "FROZEN"
    assert decision["next_gate"]["phase"] == "Phase 5 Canonical Parent Transformation"
    assert decision["next_gate"]["permit_parent_transformer"] == "src/korea_business_lifecycle/canonical_permit.py"
    assert decision["next_gate"]["permit_parent_transformer_status"] == "SYNTHETIC_VALIDATED"
