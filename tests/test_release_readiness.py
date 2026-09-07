import json
from pathlib import Path

from korea_business_lifecycle.release_readiness import compute_release_readiness


ROOT = Path(__file__).resolve().parents[1]


def test_computed_release_readiness_matches_tracked_provenance() -> None:
    tracked = json.loads(
        (ROOT / "provenance" / "release_readiness.json").read_text(encoding="utf-8")
    )
    assert compute_release_readiness() == tracked


def test_local_parent_and_wgs84_enrichment_are_verified_while_publication_stays_blocked() -> None:
    readiness = compute_release_readiness()
    assert readiness["tracks"]["local_permit_parent"]["status"] == "COMPLETED_VERIFIED"
    assert readiness["tracks"]["local_permit_parent"]["build_id"] == (
        "permit-v1-9908225df465e2ff"
    )
    assert readiness["tracks"]["geospatial_derivation"]["coordinate_axis_order_verified_nationwide"] is True
    assert readiness["tracks"]["geospatial_derivation"]["local_wgs84_generation_approved"] is True
    assert readiness["tracks"]["geospatial_derivation"]["public_wgs84_release_approved"] is False
    assert readiness["tracks"]["geospatial_derivation"]["status"] == "COMPLETED_VERIFIED"
    assert readiness["tracks"]["geospatial_derivation"]["enrichment_schema"] == "FROZEN"
    assert readiness["tracks"]["geospatial_derivation"]["enrichment_builder"] == "COMPLETED_PASS"
    assert readiness["tracks"]["geospatial_derivation"]["independent_build_verifier"] == "PASS"
    assert readiness["tracks"]["geospatial_derivation"]["build_id"] == (
        "permit-geo-v1-c4af8799de0283bb"
    )
    assert readiness["tracks"]["geospatial_derivation"]["rows"] == 3_010_802
    assert readiness["tracks"]["geospatial_derivation"]["transformed_coordinates"] == 2_811_767
    assert readiness["tracks"]["geospatial_derivation"]["missing_source_coordinates"] == 199_035
    assert readiness["tracks"]["geospatial_derivation"]["output_bytes"] == 50_805_782
    assert readiness["tracks"]["core_v1"]["status"] == "COMPLETE"
    assert readiness["tracks"]["core_v1"]["nationwide_history_required"] is False
    assert readiness["tracks"]["public_kaggle"]["privacy_minimized_aggregate_candidate"] == (
        "COMPLETED_VERIFIED_RELEASE_APPROVED"
    )
    assert readiness["tracks"]["public_kaggle"]["aggregate_candidate_build_id"] == (
        "permit-public-agg-v1-bedd874de6619bee"
    )
    assert readiness["tracks"]["public_kaggle"]["aggregate_candidate_minimum_cell_count"] == 10
    assert readiness["tracks"]["public_kaggle"]["aggregate_cells_released_candidate"] == 67_267
    assert readiness["tracks"]["public_kaggle"]["aggregate_cells_suppressed"] == 229_928
    assert readiness["tracks"]["public_kaggle"]["aggregate_released_source_rows"] == 2_383_689
    assert readiness["tracks"]["public_kaggle"]["aggregate_suppressed_source_rows"] == 627_113
    assert readiness["tracks"]["public_kaggle"]["aggregate_output_bytes"] == 108_019
    assert readiness["tracks"]["public_kaggle"]["aggregate_independent_verifier"] == "PASS"
    assert readiness["tracks"]["public_kaggle"]["aggregate_technical_minimization_verified"] is True
    assert readiness["tracks"]["public_kaggle"]["aggregate_build_time_publication_flag"] is False
    assert readiness["tracks"]["public_kaggle"]["aggregate_publication_approved"] is True
    assert readiness["tracks"]["public_kaggle"]["source_use_license"] == "PASS_METADATA_CONFIRMED"
    assert readiness["tracks"]["public_kaggle"]["raw_external_mirror_gate"] == (
        "UNRESOLVED_THIRD_PARTY_RIGHTS_CLARIFICATION"
    )
    assert readiness["tracks"]["public_kaggle"]["aggregate_redistribution_gate"] == (
        "PERMITTED_FOR_VERIFIED_AGGREGATE"
    )
    assert readiness["tracks"]["public_kaggle"]["redistribution_clarification_plan"] == (
        "OPTIONAL_ADDITIONAL_CONFIRMATION"
    )
    assert readiness["tracks"]["public_kaggle"]["redistribution_prepared_inquiry_status"] == "READY_NOT_SENT"
    assert readiness["tracks"]["public_kaggle"]["redistribution_prepared_inquiry_source_count"] == 3
    assert readiness["tracks"]["public_kaggle"]["redistribution_clarification_outreach_performed"] is False
    assert readiness["tracks"]["public_kaggle"]["redistribution_written_response_received"] is False
    assert readiness["next_long_local_actions"] == []
    assert readiness["tracks"]["lifecycle_episode"]["bounded_reconstructor"] == (
        "IMPLEMENTED_SYNTHETIC_VALIDATED"
    )
    assert readiness["tracks"]["lifecycle_episode"]["bounded_reconstructor_max_observations"] == 100_000
    assert readiness["tracks"]["lifecycle_episode"]["bounded_reconstructor_in_memory_only"] is True
    assert readiness["tracks"]["lifecycle_episode"]["history_observation_strategy"] == (
        "OPTIONAL_MONTHLY_REFERENCE_CADENCE_AVAILABLE"
    )
    assert readiness["tracks"]["lifecycle_episode"]["status"] == "OPTIONAL_ADVANCED_WORKFLOW_READY"
    assert readiness["tracks"]["lifecycle_episode"]["history_selected_cadence"] == "MONTHLY_ANCHOR_PLUS_END"
    assert readiness["tracks"]["lifecycle_episode"]["history_selected_observation_dates"] == 10
    assert readiness["tracks"]["lifecycle_episode"]["history_selected_maximum_gap_days"] == 31
    assert readiness["tracks"]["lifecycle_episode"]["history_nationwide_snapshot_tasks_planned"] == 7_320
    assert readiness["tracks"]["lifecycle_episode"]["history_acquisition_hard_network_request_cap_per_run"] == 400_000
    assert readiness["tracks"]["lifecycle_episode"]["history_nationwide_acquisition_status"] == "OPTIONAL_NOT_REQUIRED_FOR_V1"
    assert readiness["tracks"]["lifecycle_episode"]["history_episode_materialization_status"] == "OPTIONAL_REQUIRES_COMPLETE_HISTORY"
    assert readiness["tracks"]["lifecycle_episode"]["history_authenticated_execution_available"] is True
    assert readiness["tracks"]["lifecycle_episode"]["history_bounded_deleted_partition_post_reform_freeze_confirmed"] is True
    assert readiness["tracks"]["lifecycle_episode"]["history_bounded_current_partition_post_reform_evolution_confirmed"] is True
    assert readiness["tracks"]["lifecycle_episode"]["history_current_plus_deleted_union_semantically_equivalent_to_current_snapshot"] is False
    assert readiness["tracks"]["lifecycle_episode"]["history_full_deleted_authority_count_probe_status"] == "COMPLETED_VERIFIED"
    assert readiness["tracks"]["lifecycle_episode"]["history_full_deleted_authority_count_probe_request_cap"] == 384
    assert readiness["tracks"]["lifecycle_episode"]["history_full_deleted_authority_count_probe_requests_executed"] == 384
    assert readiness["tracks"]["lifecycle_episode"]["history_deleted_source_authority_pairs_post_reform_count_frozen"] == 96
    assert readiness["tracks"]["lifecycle_episode"]["history_post_reform_current_state_enumeration_policy"] == "CURRENT_244_ONLY_EXCLUDE_DELETED_32"
    assert readiness["tracks"]["lifecycle_episode"]["history_pre_reform_current_state_enumeration_policy"] == "CURRENT_MINUS_NEW_PLUS_DELETED"
    assert readiness["tracks"]["lifecycle_episode"]["history_post_reform_date_effective_current_state_enumeration_policy"] == "CURRENT_ONLY_EXCLUDE_DELETED"
    assert readiness["tracks"]["lifecycle_episode"]["history_pre_reform_authority_domain_resolved"] is True
    assert readiness["tracks"]["lifecycle_episode"]["history_same_date_old_new_union_used"] is False
    assert readiness["tracks"]["lifecycle_episode"]["history_manual_reference_authority_count"] == 245
    assert readiness["tracks"]["lifecycle_episode"]["history_current_official_numeric_authority_count"] == 244
    assert readiness["tracks"]["lifecycle_episode"]["history_current_official_aggregate_token_count"] == 16
    assert readiness["tracks"]["lifecycle_episode"]["history_official_deleted_numeric_authority_count"] == 32
    assert readiness["tracks"]["lifecycle_episode"]["history_window_candidate_numeric_authority_union_count"] == 276
    assert readiness["tracks"]["lifecycle_episode"]["history_observed_current_authority_count"] == 230
    assert readiness["tracks"]["lifecycle_episode"]["history_current_official_unobserved_count"] == 14
    assert readiness["tracks"]["lifecycle_episode"]["history_window_candidate_unobserved_count"] == 46
    assert readiness["tracks"]["lifecycle_episode"]["history_exact_current_official_numeric_codes_ingested"] is True
    assert readiness["tracks"]["lifecycle_episode"]["history_exact_deleted_numeric_codes_ingested"] is True
    assert readiness["tracks"]["lifecycle_episode"]["history_exact_new_numeric_codes_ingested"] is True
    assert readiness["tracks"]["lifecycle_episode"]["history_current_reference_numeric_enumeration_ready"] is True
    assert readiness["tracks"]["lifecycle_episode"]["history_date_effective_authority_filter_semantics_verified"] is False
    assert readiness["tracks"]["lifecycle_episode"]["history_window_date_effective_numeric_enumeration_ready"] is True
    assert readiness["tracks"]["lifecycle_episode"]["history_current_official_numeric_domain_authoritatively_complete"] is True
    assert readiness["tracks"]["lifecycle_episode"]["history_future_authority_reference_refresh_required"] is True
    assert readiness["tracks"]["lifecycle_episode"]["history_pre_reform_requests_per_asof_date_lower_bound"] == 30_109
    assert readiness["tracks"]["lifecycle_episode"]["history_pre_reform_requests_per_asof_date_upper_bound"] == 30_838
    assert readiness["tracks"]["lifecycle_episode"]["history_post_reform_requests_per_asof_date_lower_bound"] == 30_151
    assert readiness["tracks"]["lifecycle_episode"]["history_post_reform_requests_per_asof_date_upper_bound"] == 30_838
    assert readiness["tracks"]["lifecycle_episode"]["daily_window_request_lower_bound"] == 7_499_997
    assert readiness["tracks"]["lifecycle_episode"]["daily_window_request_upper_bound"] == 7_678_662
    assert readiness["tracks"]["lifecycle_episode"]["monthly_window_request_lower_bound"] == 301_258
    assert readiness["tracks"]["lifecycle_episode"]["monthly_window_request_upper_bound"] == 308_380
    assert readiness["tracks"]["lifecycle_episode"]["production_reconstruction_enabled"] is False
    assert readiness["tracks"]["public_kaggle"]["status"] == "READY_AGGREGATE_ONLY"
    assert readiness["tracks"]["public_kaggle"]["row_level_public_build_allowed"] is False
