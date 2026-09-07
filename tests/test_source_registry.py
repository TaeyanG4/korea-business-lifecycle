import pytest

from korea_business_lifecycle.provenance import (
    load_authority_domain_reference,
    load_bounded_episode_reconstruction,
    load_bounded_history_audit,
    load_expanded_history_audit,
    load_grain_decision,
    load_geospatial_axis_probe,
    load_geospatial_full_axis,
    load_geospatial_full_axis_plan,
    load_history_observation_strategy,
    load_kaggle_release,
    load_kaggle_dataset_maintenance_v2,
    load_kaggle_row_release_v1,
    load_kaggle_release_v2,
    load_history_authority_partition_findings,
    load_history_authority_partition_full_probe,
    load_history_authority_partition_probe_plan,
    load_history_authority_policy,
    load_history_episode_materialization_plan,
    load_history_nationwide_acquisition_plan,
    load_history_review,
    load_history_sample_plan,
    load_reverse_transition_probe_plan,
    load_reverse_transition_findings,
    load_license_review,
    load_observed_snapshot_summary,
    load_permit_parent_compatibility,
    load_permit_parent_full_dry_run,
    load_permit_parent_full_dry_run_plan,
    load_permit_parent_materialization_plan,
    load_permit_parent_materialization,
    load_permit_geospatial_materialization_plan,
    load_permit_geospatial_materialization,
    load_public_permit_aggregate,
    load_public_permit_aggregate_plan,
    load_redistribution_clarification_plan,
    load_v1_release_scope,
    validate_kaggle_row_release_v1,
    validate_kaggle_dataset_maintenance_v2,
    load_privacy_review,
    load_source_registry,
    validate_history_review,
    validate_history_sample_plan,
    validate_reverse_transition_probe_plan,
    validate_reverse_transition_findings,
    validate_bounded_history_audit,
    validate_authority_domain_reference,
    validate_bounded_episode_reconstruction,
    validate_expanded_history_audit,
    validate_grain_decision,
    validate_geospatial_axis_probe,
    validate_geospatial_full_axis,
    validate_geospatial_full_axis_plan,
    validate_history_observation_strategy,
    validate_kaggle_release,
    validate_kaggle_release_v2,
    validate_history_authority_partition_findings,
    validate_history_authority_partition_full_probe,
    validate_history_authority_partition_probe_plan,
    validate_history_authority_policy,
    validate_history_episode_materialization_plan,
    validate_history_nationwide_acquisition_plan,
    validate_license_review,
    validate_observed_snapshot_summary,
    validate_permit_parent_compatibility,
    validate_permit_parent_full_dry_run,
    validate_permit_parent_full_dry_run_plan,
    validate_permit_parent_materialization_plan,
    validate_permit_parent_materialization,
    validate_permit_geospatial_materialization_plan,
    validate_permit_geospatial_materialization,
    validate_public_permit_aggregate,
    validate_public_permit_aggregate_plan,
    validate_redistribution_clarification_plan,
    validate_v1_release_scope,
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
    assert review["evidence_refresh"]["source_use_license_gate"] == "PASS_METADATA_CONFIRMED"
    assert review["evidence_refresh"]["raw_external_mirror_gate"] == (
        "UNRESOLVED_THIRD_PARTY_RIGHTS_CLARIFICATION"
    )
    assert all(item["official_license_label"] == "이용허락범위 제한 없음" for item in review["categories"])
    assert all(item["kaggle_redistribution"] == "UNRESOLVED" for item in review["categories"])


def test_privacy_review_keeps_public_allowlist_blocked() -> None:
    review = load_privacy_review()
    assert validate_privacy_review(review) == []
    assert review["public_allowlist_approved"] is False
    assert review["field_inventory_complete"] is True


def test_history_review_is_finite_but_not_an_event_log() -> None:
    review = load_history_review()
    assert validate_history_review(review) == []
    assert review["decision"] == (
        "FINITE_AS_OF_DATE_QUERY_CONFIRMED_AUTHENTICATED_EXECUTION_AVAILABLE_"
        "DATE_EFFECTIVE_AUTHORITY_POLICY_APPROVED"
    )
    assert review["common_contract"]["lower_base_date"] == "2026-01-01"
    assert review["common_contract"]["max_num_of_rows"] == 100
    assert review["common_contract"]["event_log_claim"] is False
    assert review["common_contract"]["official_authority_reference"]["manual_reference_count"] == 245
    assert review["common_contract"]["official_authority_reference"]["current_official_numeric_count"] == 244
    assert review["common_contract"]["official_authority_reference"]["official_deleted_numeric_count"] == 32
    assert review["common_contract"]["official_authority_reference"]["history_window_candidate_numeric_union_count"] == 276
    assert review["common_contract"]["official_authority_reference"]["current_observed_count"] == 230
    assert review["common_contract"]["official_authority_reference"]["exact_current_official_numeric_code_values_ingested"] is True
    assert review["common_contract"]["official_authority_reference"]["exact_deleted_numeric_code_values_ingested"] is True
    assert review["common_contract"]["official_authority_reference"]["exact_new_numeric_code_values_ingested"] is True
    assert review["common_contract"]["official_authority_reference"]["history_window_date_effective_numeric_enumeration_ready"] is True
    assert review["common_contract"]["official_authority_reference"]["date_effective_history_authority_filter_semantics_verified"] is False
    assert review["common_contract"]["authenticated_probe_refresh_2026_09_07"]["result_code"] == "0"
    assert review["common_contract"]["authority_partition_semantics"]["authenticated_execution_available"] is True
    assert review["common_contract"]["authority_partition_semantics"]["full_32_deleted_count_probe_executed"] is True
    assert review["common_contract"]["authority_partition_semantics"]["all_96_deleted_source_authority_pairs_post_reform_count_frozen"] is True
    assert review["common_contract"]["authority_partition_semantics"]["post_reform_deleted_partition_policy"] == "CURRENT_244_ONLY_EXCLUDE_DELETED_32"
    assert review["common_contract"]["authority_partition_semantics"]["pre_reform_old_new_partition_domain_resolved"] is True
    assert review["common_contract"]["authority_partition_semantics"]["pre_reform_current_state_enumeration_policy"] == "CURRENT_MINUS_NEW_PLUS_DELETED"


def test_official_authority_reference_tracks_current_and_deleted_exact_codes_without_overclaiming_history_semantics() -> None:
    review = load_authority_domain_reference()
    assert validate_authority_domain_reference(review) == []
    assert review["official_reference"]["manual_claim_count"] == 245
    assert review["official_reference"]["active_numeric_code_count"] == 244
    assert review["official_reference"]["active_aggregate_token_count"] == 16
    assert review["official_reference"]["deleted_numeric_code_count"] == 32
    assert review["observed_current_snapshots"]["distinct_authority_count"] == 230
    assert review["observed_current_snapshots"]["current_official_numeric_not_observed_count"] == 14
    assert review["history_window_change_reference"]["current_plus_deleted_candidate_union_count"] == 276
    assert review["ingestion_gate"]["exact_current_official_numeric_code_values_ingested"] is True
    assert review["ingestion_gate"]["exact_deleted_numeric_code_values_ingested"] is True
    assert review["ingestion_gate"]["current_reference_numeric_enumeration_ready"] is True
    assert review["ingestion_gate"]["exact_new_numeric_code_values_ingested"] is True
    assert review["ingestion_gate"]["history_window_date_effective_numeric_enumeration_ready"] is True


def test_deleted_authority_partition_probe_plan_is_bounded_and_completed() -> None:
    plan = load_history_authority_partition_probe_plan()
    assert validate_history_authority_partition_probe_plan(plan) == []
    assert plan["scope"]["deleted_numeric_authority_count"] == 32
    assert plan["scope"]["tasks"] == 384
    assert plan["scope"]["maximum_network_requests"] == 384
    assert plan["execution"]["default_mode"] == "DRY_RUN"
    assert plan["execution"]["execution_performed"] is True
    assert plan["execution"]["result_provenance"] == "provenance/history_authority_partition_full_probe.json"
    assert plan["privacy"]["only_authority_date_source_total_count_emitted"] is True


def test_full_deleted_authority_probe_confirms_count_freeze_without_overclaiming_rows() -> None:
    result = load_history_authority_partition_full_probe()
    assert validate_history_authority_partition_full_probe(result) == []
    assert result["execution"]["requests_executed"] == 384
    assert result["assessment"]["pairs_with_equal_counts_20260630_20260701_20260906"] == 96
    assert result["assessment"]["post_reform_count_freeze_confirmed_all_pairs"] is True
    assert result["assessment"]["post_reform_row_content_freeze_confirmed_all_pairs"] is False
    assert result["legacy_partition_policy"]["post_reform_current_state_enumeration"] == (
        "CURRENT_244_ONLY_EXCLUDE_DELETED_32"
    )
    assert result["legacy_partition_policy"]["pre_reform_policy_approved"] is False


def test_bounded_deleted_authority_findings_confirm_freeze_without_overgeneralizing() -> None:
    findings = load_history_authority_partition_findings()
    assert validate_history_authority_partition_findings(findings) == []
    assert findings["count_probe_assessment"]["pairs_with_equal_counts_20260630_20260701_20260906"] == 9
    assert findings["count_probe_assessment"]["simple_deleted_code_becomes_zero_on_effective_date_model_rejected"] is True
    assert findings["bounded_overlap_audit"]["mng_no_overlap"] == 0
    assert findings["bounded_overlap_audit"]["management_number_values_emitted"] is False
    assert findings["interpretation"]["deleted_partition_frozen_after_reform_in_bounded_full_row_sample"] is True
    assert findings["interpretation"]["bounded_zero_overlap_proves_all_old_new_partitions_are_disjoint"] is False


def test_date_effective_history_authority_policy_is_approved_without_promoting_api_queryability() -> None:
    policy = load_history_authority_policy()
    assert validate_history_authority_policy(policy) == []
    assert policy["pre_reform"]["numeric_authority_count"] == 244
    assert policy["pre_reform"]["policy"] == "CURRENT_MINUS_NEW_PLUS_DELETED"
    assert policy["post_reform"]["numeric_authority_count"] == 244
    assert policy["post_reform"]["policy"] == "CURRENT_ONLY_EXCLUDE_DELETED"
    assert policy["overlap_semantics"]["same_date_old_new_union_used"] is False
    assert policy["overlap_semantics"]["api_queryability_defines_date_effective_membership"] is False
    assert policy["overlap_semantics"]["management_number_is_source_primary_key"] is False


def test_nationwide_monthly_history_plan_is_approved_but_not_executed() -> None:
    plan = load_history_nationwide_acquisition_plan()
    assert validate_history_nationwide_acquisition_plan(plan) == []
    assert plan["scope"]["planned_snapshot_tasks"] == 7_320
    assert plan["cadence"]["name"] == "MONTHLY_ANCHOR_PLUS_END"
    assert plan["execution"]["hard_network_request_cap_per_run"] == 400_000
    assert plan["execution"]["execution_performed"] is False


def test_production_episode_materialization_plan_waits_for_complete_history() -> None:
    plan = load_history_episode_materialization_plan()
    assert validate_history_episode_materialization_plan(plan) == []
    assert plan["scope"]["required_history_snapshot_tasks"] == 7_320
    assert plan["implementation"]["bucket_count"] == 256
    assert plan["execution"]["execution_performed"] is False


def test_redistribution_clarification_plan_is_prepared_but_not_executed() -> None:
    plan = load_redistribution_clarification_plan()
    assert validate_redistribution_clarification_plan(plan) == []
    assert plan["confirmed_evidence"]["source_use_metadata_gate"] == "PASS_METADATA_CONFIRMED"
    assert plan["confirmed_evidence"]["raw_external_mirror_permission_confirmed"] is False
    assert len(plan["questions_for_written_clarification"]) == 4
    assert plan["prepared_inquiry"]["status"] == "READY_NOT_SENT"
    assert plan["prepared_inquiry"]["requested_response_form"] == "WRITTEN_SOURCE_SPECIFIC"
    assert plan["prepared_inquiry"]["technical_minimization_is_not_claimed_as_legal_privacy_guarantee"] is True
    assert plan["execution"]["outreach_performed"] is False
    assert plan["execution"]["written_response_received"] is False


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
    assert decision["next_gate"]["phase"] == "Phase 7 Aggregate Publication Release"
    assert decision["next_gate"]["permit_parent_transformer"] == "src/korea_business_lifecycle/canonical_permit.py"
    assert decision["next_gate"]["permit_parent_transformer_status"] == "FULL_SNAPSHOT_VALIDATED"
    assert decision["next_gate"]["permit_parent_compatibility"] == "provenance/permit_parent_compatibility.json"
    assert decision["next_gate"]["permit_parent_compatibility_status"] == "PASSED_256_ROWS_PER_SOURCE"
    assert decision["next_gate"]["permit_parent_full_dry_run_plan"] == "provenance/permit_parent_full_dry_run_plan.json"
    assert decision["next_gate"]["permit_parent_full_dry_run"] == "provenance/permit_parent_full_dry_run.json"
    assert decision["next_gate"]["permit_parent_full_dry_run_status"] == "PASSED_3010802_ROWS"
    assert decision["next_gate"]["permit_parent_materialization_plan"] == "provenance/permit_parent_materialization_plan.json"
    assert decision["next_gate"]["permit_parent_materialization"] == "provenance/permit_parent_materialization.json"
    assert decision["next_gate"]["permit_parent_materialization_status"] == "COMPLETED_PASS_VERIFIED"
    assert decision["next_gate"]["geospatial_full_axis"] == "provenance/geospatial_full_axis.json"
    assert decision["next_gate"]["geospatial_full_axis_status"] == "PASSED_REVIEWED_CURRENT_V1"
    assert decision["next_gate"]["permit_geospatial_schema"] == "schemas/permit_geospatial.v1.json"
    assert decision["next_gate"]["permit_geospatial_schema_status"] == "FROZEN"
    assert decision["next_gate"]["permit_geospatial_materialization_plan"] == (
        "provenance/permit_geospatial_materialization_plan.json"
    )
    assert decision["next_gate"]["permit_geospatial_materialization"] == (
        "provenance/permit_geospatial_materialization.json"
    )
    assert decision["next_gate"]["permit_geospatial_materialization_status"] == "COMPLETED_PASS_VERIFIED"
    assert decision["next_gate"]["public_permit_aggregate_schema"] == (
        "schemas/public_permit_aggregate.v1.json"
    )
    assert decision["next_gate"]["public_permit_aggregate_schema_status"] == "FROZEN_CANDIDATE"
    assert decision["next_gate"]["public_permit_aggregate_plan"] == (
        "provenance/public_permit_aggregate_plan.json"
    )
    assert decision["next_gate"]["public_permit_aggregate"] == "provenance/public_permit_aggregate.json"
    assert decision["next_gate"]["public_permit_aggregate_status"] == (
        "COMPLETED_PASS_VERIFIED_NOT_PUBLICATION_APPROVED"
    )
    assert decision["next_gate"]["history_nationwide_acquisition_status"] == "OPTIONAL_NOT_REQUIRED_FOR_V1"
    assert decision["next_gate"]["history_episode_materialization_status"] == "OPTIONAL_REQUIRES_COMPLETE_HISTORY"
    assert decision["next_gate"]["v1_release_scope"] == "provenance/v1_release_scope.json"


def test_v1_release_scope_closes_core_and_consolidates_on_current_snapshot() -> None:
    scope = load_v1_release_scope()
    assert validate_v1_release_scope(scope) == []
    assert scope["core_v1"]["local_core_complete"] is True
    assert scope["core_v1"]["nationwide_history_required_for_core_v1"] is False
    assert scope["lifecycle_optional"]["status"] == "OPTIONAL_ADVANCED_WORKFLOW"
    assert scope["public_release"]["aggregate_publication_approved"] is True
    assert scope["public_release"]["aggregate_current_kaggle_product"] is False
    assert scope["public_release"]["aggregate_kaggle_dataset_retired"] is True
    assert scope["public_release"]["row_level_permit_publication_approved"] is True
    assert scope["public_release"]["row_level_kaggle_dataset_id"] == "taeyangg4/korea-food-service-permits"
    assert scope["public_release"]["row_level_rows"] == 3_010_802
    assert scope["public_release"]["row_level_columns"] == 26
    assert scope["public_release"]["row_level_serializations"] == ["CSV", "PARQUET"]
    assert scope["public_release"]["row_level_package_version"] == 1
    assert scope["public_release"]["canonical_source_epsg5174_coordinates_publication_approved"] is True
    assert scope["public_release"]["precise_wgs84_publication_approved"] is False
    assert scope["public_release"]["written_source_specific_confirmation_required_for_aggregate_publication"] is False
    assert scope["public_release"]["historical_aggregate_package_version"] == 2
    assert scope["public_release"]["historical_aggregate_serializations"] == ["CSV", "PARQUET"]
    assert scope["public_release"]["multiple_serializations_broaden_public_row_scope"] is False


def test_kaggle_canonical_row_release_is_public_ready_and_exact_shape() -> None:
    release = load_kaggle_row_release_v1()
    assert validate_kaggle_row_release_v1(release) == []
    assert release["dataset"]["dataset_id"] == "taeyangg4/korea-food-service-permits"
    assert release["dataset"]["visibility"] == "PUBLIC"
    assert release["dataset"]["status"] == "READY"
    assert release["package"]["rows"] == 3_010_802
    assert release["package"]["columns"] == 26
    assert release["package"]["serializations"] == ["CSV", "PARQUET"]
    assert release["package"]["source_epsg5174_coordinates_included"] is True
    assert release["package"]["wgs84_coordinates_included"] is False


def test_kaggle_current_snapshot_maintenance_v2_tracks_remaining_pending_actions() -> None:
    review = load_kaggle_dataset_maintenance_v2()
    assert validate_kaggle_dataset_maintenance_v2(review) == []
    assert review["dataset"]["dataset_id"] == "taeyangg4/korea-food-service-permits"
    assert review["dataset"]["current_version"] == 2
    assert review["dataset"]["dataset_version_id"] == 19_491_720
    assert review["dataset"]["databundle_version_id"] == 20_603_554
    assert review["dataset"]["usability_score"] == pytest.approx(0.8235294)
    assert review["dataset"]["usability_target"] == 1.0
    assert review["content"]["rows"] == 3_010_802
    assert review["content"]["columns"] == 26
    assert review["metadata"]["file_descriptions_authored"] == 8
    assert review["metadata"]["csv_column_descriptions_authored"] == 26
    assert review["metadata"]["parquet_column_descriptions_authored"] == 26
    assert review["metadata"]["source_summary_column_descriptions_authored"] == 4
    assert review["metadata"]["pending_actions"] == ["EDIT_FILE_INFO", "EDIT_COLUMN_DESCRIPTION"]
    assert review["metadata"]["data_explorer_file_descriptions_persisted"] is False
    assert review["metadata"]["data_explorer_column_descriptions_persisted"] is False
    assert review["data_explorer_sync"]["dry_run_passed"] is True
    assert review["data_explorer_sync"]["write_attempted"] is True
    assert review["data_explorer_sync"]["write_executed"] is False
    assert review["data_explorer_sync"]["write_status"] == "PENDING_AUTHENTICATED_WEB_SESSION"
    assert review["data_explorer_sync"]["last_write_attempt_http_status"] == 401
    assert review["notebook"]["status"] == "COMPLETE"
    assert review["notebook"]["successful_version"] == 5


def test_historical_kaggle_aggregate_publication_evidence_is_preserved() -> None:
    release = load_kaggle_release()
    assert validate_kaggle_release(release) == []
    assert release["dataset"]["dataset_id"] == "taeyangg4/korea-food-service-permit-aggregate"
    assert release["dataset"]["visibility"] == "PUBLIC"
    assert release["dataset"]["status"] == "READY"
    assert release["artifact"]["bytes"] == 108_019
    assert release["privacy"]["row_level_permit_published"] is False
    assert release["privacy"]["precise_coordinates_published"] is False


def test_historical_kaggle_aggregate_package_v2_evidence_is_preserved() -> None:
    release = load_kaggle_release_v2()
    assert validate_kaggle_release_v2(release) == []
    assert release["dataset"]["status"] == "READY"
    assert release["package"]["version"] == 2
    assert release["package"]["serializations"] == ["CSV", "PARQUET"]
    assert release["package"]["published_file_count"] == 8
    assert release["privacy"]["row_level_permit_published"] is False
    assert release["privacy"]["multiple_serializations_broaden_public_row_scope"] is False


def test_permit_parent_bounded_real_compatibility_is_aggregate_only() -> None:
    review = load_permit_parent_compatibility()
    assert validate_permit_parent_compatibility(review) == []
    assert review["decision"] == "BOUNDED_REAL_CURRENT_SNAPSHOT_COMPATIBILITY_PASSED"
    assert review["aggregate"]["rows_examined"] == 768
    assert review["aggregate"]["all_sources_passed"] is True
    assert review["scope"]["production_materialization_performed"] is False
    assert review["scope"]["full_snapshot_scan_performed"] is False
    assert all(value is False for value in review["privacy"].values())


def test_permit_parent_full_dry_run_plan_records_completed_user_execution() -> None:
    plan = load_permit_parent_full_dry_run_plan()
    assert validate_permit_parent_full_dry_run_plan(plan) == []
    assert plan["scope"]["expected_rows_total"] == 3_010_802
    assert plan["scope"]["execution_status"] == "COMPLETED_PASS"
    assert plan["execution"]["progress_stream"] == "stderr"
    assert plan["execution"]["final_aggregate_json_stream"] == "stdout"
    assert all(value is False for value in plan["privacy"].values())


def test_permit_parent_full_dry_run_is_complete_and_aggregate_only() -> None:
    review = load_permit_parent_full_dry_run()
    assert validate_permit_parent_full_dry_run(review) == []
    assert review["decision"] == "FULL_CURRENT_SNAPSHOT_DRY_RUN_PASSED"
    assert review["aggregate"]["rows_examined"] == 3_010_802
    assert review["aggregate"]["permit_date_quality"] == {"INVALID": 4, "VALID": 3_010_798}
    assert review["aggregate"]["duplicate_linkage_candidates"] == 0
    assert review["aggregate"]["all_temporary_uniqueness_indexes_removed"] is True
    assert all(value is False for value in review["privacy"].values())


def test_permit_parent_materialization_plan_records_completed_verified_execution() -> None:
    plan = load_permit_parent_materialization_plan()
    assert validate_permit_parent_materialization_plan(plan) == []
    assert plan["scope"]["execution_status"] == "COMPLETED_PASS_VERIFIED"
    assert plan["scope"]["public_row_level_release_approved"] is False
    assert plan["writer_contract"]["library_version"] == "21.0.0"
    assert plan["writer_contract"]["compression"] == "ZSTD"
    assert plan["implementation"]["verification_module"] == (
        "src/korea_business_lifecycle/canonical_materialization_verify.py"
    )
    assert plan["implementation"]["verification_script"] == "scripts/verify_permit_parent_build.py"
    assert plan["result_provenance"] == "provenance/permit_parent_materialization.json"


def test_permit_parent_materialization_result_is_verified_and_private() -> None:
    review = load_permit_parent_materialization()
    assert validate_permit_parent_materialization(review) == []
    assert review["scope"]["build_id"] == "permit-v1-9908225df465e2ff"
    assert review["scope"]["rows_total"] == 3_010_802
    assert review["scope"]["output_bytes_total"] == 165_176_236
    assert review["verification"]["parquet_hashes_verified"] is True
    assert review["verification"]["parquet_schemas_verified"] is True
    assert review["privacy"]["publication_status_changed"] is False


def test_bounded_geospatial_axis_probe_prefers_source_x_easting_without_enabling_wgs84() -> None:
    review = load_geospatial_axis_probe()
    assert validate_geospatial_axis_probe(review) == []
    assert review["aggregate"]["coordinate_pairs_sampled"] == 15_000
    assert review["aggregate"]["macro_region_candidate_a_match"] == 15_000
    assert review["aggregate"]["macro_region_candidate_b_match"] == 0
    assert review["scope"]["coordinate_axis_order_verified_nationwide"] is False
    assert review["scope"]["wgs84_generation_approved"] is False


def test_full_geospatial_axis_plan_records_completed_reviewed_execution() -> None:
    plan = load_geospatial_full_axis_plan()
    assert validate_geospatial_full_axis_plan(plan) == []
    assert plan["scope"]["expected_rows_total"] == 3_010_802
    assert plan["scope"]["expected_coordinate_pairs_total_from_prior_profile"] == 2_811_767
    assert plan["scope"]["execution_status"] == "COMPLETED_PASS_REVIEWED"
    assert plan["scope"]["wgs84_columns_generated"] is False
    assert plan["interpretation_policy"]["wgs84_generation_approved_before_execution"] is False
    assert plan["result_provenance"] == "provenance/geospatial_full_axis.json"


def test_full_geospatial_axis_result_approves_local_derivation_only() -> None:
    review = load_geospatial_full_axis()
    assert validate_geospatial_full_axis(review) == []
    assert review["scope"]["coordinate_pairs_total"] == 2_811_767
    assert review["method"]["candidate_a_only_match"] == 1_943_824
    assert review["method"]["candidate_b_only_match"] == 0
    assert review["review"]["coordinate_axis_order_verified_nationwide"] is True
    assert review["review"]["local_wgs84_derivation_approved"] is True
    assert review["review"]["public_wgs84_release_approved"] is False


def test_permit_geospatial_materialization_plan_records_completed_verified_execution() -> None:
    plan = load_permit_geospatial_materialization_plan()
    assert validate_permit_geospatial_materialization_plan(plan) == []
    assert plan["scope"]["parent_permit_build_id"] == "permit-v1-9908225df465e2ff"
    assert plan["scope"]["geospatial_build_id"] == "permit-geo-v1-c4af8799de0283bb"
    assert plan["scope"]["expected_rows_total"] == 3_010_802
    assert plan["scope"]["expected_transformed_total"] == 2_811_767
    assert plan["scope"]["expected_missing_total"] == 199_035
    assert plan["scope"]["execution_status"] == "COMPLETED_PASS_VERIFIED"
    assert plan["scope"]["parent_mutated"] is False
    assert plan["scope"]["public_row_level_release_approved"] is False
    assert plan["result_provenance"] == "provenance/permit_geospatial_materialization.json"


def test_permit_geospatial_materialization_result_is_verified_and_private() -> None:
    review = load_permit_geospatial_materialization()
    assert validate_permit_geospatial_materialization(review) == []
    assert review["scope"]["geospatial_build_id"] == "permit-geo-v1-c4af8799de0283bb"
    assert review["scope"]["rows_total"] == 3_010_802
    assert review["scope"]["transformed_coordinates_total"] == 2_811_767
    assert review["scope"]["missing_source_coordinates_total"] == 199_035
    assert review["scope"]["output_bytes_total"] == 50_805_782
    assert review["verification"]["parent_build_verified"] is True
    assert review["verification"]["coordinate_invariants_verified"] is True
    assert review["privacy"]["public_row_level_release_status_changed"] is False


def test_public_permit_aggregate_plan_is_privacy_minimized_but_not_publishable() -> None:
    plan = load_public_permit_aggregate_plan()
    assert validate_public_permit_aggregate_plan(plan) == []
    assert plan["scope"]["aggregate_build_id"] == "permit-public-agg-v1-bedd874de6619bee"
    assert plan["scope"]["expected_parent_rows"] == 3_010_802
    assert plan["scope"]["execution_status"] == "COMPLETED_PASS_VERIFIED"
    assert plan["contracts"]["minimum_cell_count"] == 10
    assert plan["contracts"]["minimum_cell_count_is_legal_privacy_guarantee"] is False
    assert plan["scope"]["row_level_public_projection_approved"] is False
    assert plan["scope"]["aggregate_publication_approved"] is False
    assert plan["scope"]["redistribution_status"] == "UNRESOLVED"
    assert "management_number" in plan["excluded_row_level_fields"]
    assert "wgs84_longitude" in plan["excluded_row_level_fields"]
    assert plan["result_provenance"] == "provenance/public_permit_aggregate.json"


def test_public_permit_aggregate_result_is_verified_but_not_publication_approved() -> None:
    review = load_public_permit_aggregate()
    assert validate_public_permit_aggregate(review) == []
    assert review["scope"]["rows_scanned"] == 3_010_802
    assert review["scope"]["aggregate_cells_total_before_suppression"] == 297_195
    assert review["scope"]["aggregate_cells_released_candidate"] == 67_267
    assert review["scope"]["aggregate_cells_suppressed"] == 229_928
    assert review["scope"]["released_source_rows"] == 2_383_689
    assert review["scope"]["suppressed_source_rows"] == 627_113
    assert review["scope"]["output_bytes"] == 108_019
    assert review["verification"]["suppression_invariants_verified"] is True
    assert review["privacy"]["technical_minimization_verified"] is True
    assert review["scope"]["aggregate_publication_approved"] is False


def test_bounded_episode_reconstructor_is_validated_but_production_remains_disabled() -> None:
    review = load_bounded_episode_reconstruction()
    assert validate_bounded_episode_reconstruction(review) == []
    assert review["scope"]["maximum_observations_per_call"] == 100_000
    assert review["scope"]["bounded_in_memory_only"] is True
    assert review["scope"]["history_acquisition_performed"] is False
    assert review["scope"]["nationwide_production_reconstruction_enabled"] is False
    assert review["episode_contract"]["first_episode_start_censoring"] == "LEFT_CENSORED"
    assert review["episode_contract"]["between_episode_boundary_censoring"] == "INTERVAL_CENSORED"
    assert review["episode_contract"]["last_episode_end_censoring"] == "RIGHT_CENSORED"
    assert review["semantic_safety"]["status_code_03_irreversible"] is False
    assert review["semantic_safety"]["status_code_05_semantics_resolved"] is False


def test_history_observation_strategy_quantifies_cost_and_approves_monthly_cadence() -> None:
    review = load_history_observation_strategy()
    assert validate_history_observation_strategy(review) == []
    assert review["paging_basis"]["pre_reform_request_lower_bound_per_asof_date"] == 30_109
    assert review["paging_basis"]["pre_reform_request_upper_bound_per_asof_date"] == 30_838
    assert review["paging_basis"]["post_reform_request_lower_bound_per_asof_date"] == 30_151
    assert review["paging_basis"]["post_reform_request_upper_bound_per_asof_date"] == 30_838
    assert review["paging_basis"]["current_official_numeric_domain_authoritatively_complete_for_reference_date"] is True
    assert review["paging_basis"]["history_window_date_effective_numeric_enumeration_ready"] is True
    daily = next(item for item in review["scenarios"] if item["name"] == "DAILY")
    assert daily["request_lower_bound"] == 7_499_997
    assert daily["request_upper_bound"] == 7_678_662
    assert daily["approved_for_production"] is False
    monthly = next(item for item in review["scenarios"] if item["name"] == "MONTHLY_ANCHOR_PLUS_END")
    assert monthly["request_lower_bound"] == 301_258
    assert monthly["request_upper_bound"] == 308_380
    assert monthly["approved_for_production"] is True
    assert review["scope"]["production_episode_reconstruction_enabled"] is False
