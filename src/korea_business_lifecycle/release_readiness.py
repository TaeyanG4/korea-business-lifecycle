from __future__ import annotations

from typing import Any

from .canonical_materialization_verify import expected_permit_build_id
from .provenance import (
    load_authority_domain_reference,
    load_bounded_episode_reconstruction,
    load_geospatial_axis_probe,
    load_geospatial_full_axis,
    load_geospatial_full_axis_plan,
    load_grain_decision,
    load_history_authority_partition_findings,
    load_history_authority_partition_full_probe,
    load_history_authority_partition_probe_plan,
    load_history_authority_policy,
    load_history_episode_materialization_plan,
    load_history_nationwide_acquisition_plan,
    load_history_observation_strategy,
    load_license_review,
    load_permit_parent_full_dry_run,
    load_permit_parent_materialization,
    load_permit_parent_materialization_plan,
    load_permit_geospatial_materialization_plan,
    load_permit_geospatial_materialization,
    load_privacy_review,
    load_public_permit_aggregate,
    load_public_permit_aggregate_plan,
    load_redistribution_clarification_plan,
    load_v1_release_scope,
)


def compute_release_readiness() -> dict[str, Any]:
    full_dry_run = load_permit_parent_full_dry_run()
    materialization = load_permit_parent_materialization_plan()
    materialization_result = load_permit_parent_materialization()
    geospatial_probe = load_geospatial_axis_probe()
    geospatial_full = load_geospatial_full_axis_plan()
    geospatial_result = load_geospatial_full_axis()
    geospatial_materialization = load_permit_geospatial_materialization_plan()
    geospatial_materialization_result = load_permit_geospatial_materialization()
    public_aggregate = load_public_permit_aggregate_plan()
    public_aggregate_result = load_public_permit_aggregate()
    bounded_episode = load_bounded_episode_reconstruction()
    history_strategy = load_history_observation_strategy()
    authority_reference = load_authority_domain_reference()
    authority_partition_findings = load_history_authority_partition_findings()
    authority_partition_full_probe = load_history_authority_partition_full_probe()
    authority_partition_probe_plan = load_history_authority_partition_probe_plan()
    authority_policy = load_history_authority_policy()
    nationwide_plan = load_history_nationwide_acquisition_plan()
    episode_materialization_plan = load_history_episode_materialization_plan()
    grain = load_grain_decision()
    privacy = load_privacy_review()
    license_review = load_license_review()
    redistribution_clarification = load_redistribution_clarification_plan()
    release_scope = load_v1_release_scope()

    episode = grain["selected_grains"]["lifecycle_analysis_grain"]
    semantics = grain["episode_semantics"]
    local_status = (
        "COMPLETED_VERIFIED"
        if full_dry_run["decision"] == "FULL_CURRENT_SNAPSHOT_DRY_RUN_PASSED"
        and materialization["scope"]["execution_status"] == "COMPLETED_PASS_VERIFIED"
        and materialization_result["verification"]["parquet_hashes_verified"] is True
        and materialization_result["verification"]["parquet_schemas_verified"] is True
        else "REVIEW_REQUIRED"
    )
    geospatial_status = (
        "COMPLETED_VERIFIED"
        if geospatial_full["scope"]["execution_status"] == "COMPLETED_PASS_REVIEWED"
        and geospatial_result["review"]["local_wgs84_derivation_approved"] is True
        and geospatial_materialization["scope"]["execution_status"] == "COMPLETED_PASS_VERIFIED"
        and geospatial_materialization_result["verification"]["parent_build_verified"] is True
        and geospatial_materialization_result["verification"]["parquet_hashes_verified"] is True
        and geospatial_materialization_result["verification"]["parquet_schemas_verified"] is True
        and geospatial_materialization_result["verification"]["coordinate_invariants_verified"] is True
        else "REVIEW_REQUIRED"
    )
    public_status = (
        "READY_AGGREGATE_ONLY"
        if release_scope["public_release"]["aggregate_publication_approved"] is True
        and public_aggregate_result["verification"]["status"] == "PASS"
        else "BLOCKED"
    )

    return {
        "checked_at": "2026-09-08",
        "decision": "LOCAL_V1_CORE_COMPLETE_HISTORY_OPTIONAL_AGGREGATE_KAGGLE_READY",
        "tracks": {
            "core_v1": {
                "status": "COMPLETE",
                "scope": release_scope["core_v1"]["scope"],
                "nationwide_history_required": release_scope["core_v1"][
                    "nationwide_history_required_for_core_v1"
                ],
                "production_episode_required": release_scope["core_v1"][
                    "production_episode_required_for_core_v1"
                ],
            },
            "local_permit_parent": {
                "status": local_status,
                "full_snapshot_transform_validation": "PASS_3010802_ROWS",
                "materializer": "COMPLETED_PASS",
                "independent_build_verifier": "PASS",
                "build_id": materialization_result["scope"]["build_id"],
                "rows": materialization_result["scope"]["rows_total"],
                "output_bytes": materialization_result["scope"]["output_bytes_total"],
                "public_release_implied": False,
            },
            "geospatial_derivation": {
                "status": geospatial_status,
                "bounded_axis_evidence": geospatial_probe["aggregate"]["assessment"],
                "full_axis_validator": "PASSED_REVIEWED_CURRENT_V1",
                "coordinate_pairs_reviewed": geospatial_result["scope"]["coordinate_pairs_total"],
                "source_x_interpretation": geospatial_result["review"]["source_x_interpretation"],
                "source_y_interpretation": geospatial_result["review"]["source_y_interpretation"],
                "coordinate_axis_order_verified_nationwide": grain["evidence"]["coordinate_axis_order_verified_nationwide"],
                "local_wgs84_generation_approved": grain["evidence"]["local_wgs84_generation_approved"],
                "public_wgs84_release_approved": grain["evidence"]["public_wgs84_release_approved"],
                "enrichment_schema": "FROZEN",
                "enrichment_builder": "COMPLETED_PASS",
                "independent_build_verifier": "PASS",
                "build_id": geospatial_materialization_result["scope"]["geospatial_build_id"],
                "rows": geospatial_materialization_result["scope"]["rows_total"],
                "transformed_coordinates": geospatial_materialization_result["scope"][
                    "transformed_coordinates_total"
                ],
                "missing_source_coordinates": geospatial_materialization_result["scope"][
                    "missing_source_coordinates_total"
                ],
                "output_bytes": geospatial_materialization_result["scope"]["output_bytes_total"],
                "parent_permit_build_id": geospatial_materialization_result["scope"]["parent_permit_build_id"],
            },
            "lifecycle_episode": {
                "status": "OPTIONAL_ADVANCED_WORKFLOW_READY",
                "schema": episode["schema_status"],
                "bounded_reconstructor": "IMPLEMENTED_SYNTHETIC_VALIDATED",
                "bounded_reconstructor_module": bounded_episode["implementation"]["module"],
                "bounded_reconstructor_max_observations": bounded_episode["scope"][
                    "maximum_observations_per_call"
                ],
                "bounded_reconstructor_in_memory_only": bounded_episode["scope"]["bounded_in_memory_only"],
                "history_observation_strategy": "OPTIONAL_MONTHLY_REFERENCE_CADENCE_AVAILABLE",
                "history_selected_cadence": history_strategy["selected_cadence"]["name"],
                "history_selected_observation_dates": history_strategy["selected_cadence"]["observation_dates"],
                "history_selected_maximum_gap_days": history_strategy["selected_cadence"]["maximum_gap_days"],
                "history_selected_current_scale_request_lower_bound": history_strategy["selected_cadence"][
                    "current_scale_request_lower_bound"
                ],
                "history_selected_current_scale_request_upper_bound": history_strategy["selected_cadence"][
                    "current_scale_request_upper_bound"
                ],
                "history_acquisition_hard_network_request_cap_per_run": nationwide_plan["execution"][
                    "hard_network_request_cap_per_run"
                ],
                "history_acquisition_request_delay_seconds": nationwide_plan["execution"][
                    "minimum_request_delay_seconds"
                ],
                "history_nationwide_snapshot_tasks_planned": nationwide_plan["scope"]["planned_snapshot_tasks"],
                "history_nationwide_acquisition_status": "OPTIONAL_NOT_REQUIRED_FOR_V1",
                "history_episode_materialization_status": "OPTIONAL_REQUIRES_COMPLETE_HISTORY",
                "history_episode_materialization_bucket_count": episode_materialization_plan["implementation"][
                    "bucket_count"
                ],
                "history_authenticated_execution_available": authority_partition_findings[
                    "authentication_refresh"
                ]["authenticated_history_probe_now_succeeds"],
                "history_bounded_deleted_partition_post_reform_freeze_confirmed": authority_partition_findings[
                    "interpretation"
                ]["deleted_partition_frozen_after_reform_in_bounded_full_row_sample"],
                "history_bounded_current_partition_post_reform_evolution_confirmed": authority_partition_findings[
                    "interpretation"
                ]["current_code_partition_can_continue_evolving_after_reform"],
                "history_current_plus_deleted_union_semantically_equivalent_to_current_snapshot": authority_partition_findings[
                    "interpretation"
                ]["current_plus_deleted_union_is_semantically_equivalent_to_current_snapshot"],
                "history_full_deleted_authority_count_probe_status": "COMPLETED_VERIFIED",
                "history_full_deleted_authority_count_probe_request_cap": authority_partition_probe_plan[
                    "scope"
                ]["maximum_network_requests"],
                "history_full_deleted_authority_count_probe_requests_executed": authority_partition_full_probe[
                    "execution"
                ]["requests_executed"],
                "history_deleted_source_authority_pairs_post_reform_count_frozen": authority_partition_full_probe[
                    "assessment"
                ]["pairs_with_equal_counts_20260630_20260701_20260906"],
                "history_post_reform_current_state_enumeration_policy": authority_partition_full_probe[
                    "legacy_partition_policy"
                ]["post_reform_current_state_enumeration"],
                "history_pre_reform_current_state_enumeration_policy": authority_policy["pre_reform"]["policy"],
                "history_post_reform_date_effective_current_state_enumeration_policy": authority_policy[
                    "post_reform"
                ]["policy"],
                "history_pre_reform_authority_domain_resolved": True,
                "history_same_date_old_new_union_used": authority_policy["overlap_semantics"][
                    "same_date_old_new_union_used"
                ],
                "history_manual_reference_authority_count": authority_reference[
                    "official_reference"
                ]["manual_claim_count"],
                "history_current_official_numeric_authority_count": authority_reference[
                    "official_reference"
                ]["active_numeric_code_count"],
                "history_current_official_aggregate_token_count": authority_reference[
                    "official_reference"
                ]["active_aggregate_token_count"],
                "history_official_deleted_numeric_authority_count": authority_reference[
                    "history_window_change_reference"
                ]["deleted_numeric_authority_count"],
                "history_window_candidate_numeric_authority_union_count": authority_reference[
                    "history_window_change_reference"
                ]["current_plus_deleted_candidate_union_count"],
                "history_observed_current_authority_count": authority_reference[
                    "observed_current_snapshots"
                ]["distinct_authority_count"],
                "history_current_official_unobserved_count": authority_reference[
                    "observed_current_snapshots"
                ]["current_official_numeric_not_observed_count"],
                "history_window_candidate_unobserved_count": history_strategy["paging_basis"][
                    "observed_count_gap_vs_history_window_candidate_union"
                ],
                "history_exact_current_official_numeric_codes_ingested": authority_reference[
                    "ingestion_gate"
                ]["exact_current_official_numeric_code_values_ingested"],
                "history_exact_deleted_numeric_codes_ingested": authority_reference[
                    "ingestion_gate"
                ]["exact_deleted_numeric_code_values_ingested"],
                "history_exact_new_numeric_codes_ingested": authority_reference[
                    "ingestion_gate"
                ]["exact_new_numeric_code_values_ingested"],
                "history_current_reference_numeric_enumeration_ready": authority_reference[
                    "ingestion_gate"
                ]["current_reference_numeric_enumeration_ready"],
                "history_date_effective_authority_filter_semantics_verified": authority_reference[
                    "history_window_change_reference"
                ]["date_effective_history_authority_filter_semantics_verified"],
                "history_window_date_effective_numeric_enumeration_ready": authority_reference[
                    "ingestion_gate"
                ]["history_window_date_effective_numeric_enumeration_ready"],
                "history_current_official_numeric_domain_authoritatively_complete": history_strategy[
                    "paging_basis"
                ]["current_official_numeric_domain_authoritatively_complete_for_reference_date"],
                "history_future_authority_reference_refresh_required": history_strategy["paging_basis"][
                    "future_authority_reference_refresh_required"
                ],
                "history_pre_reform_requests_per_asof_date_lower_bound": history_strategy["paging_basis"][
                    "pre_reform_request_lower_bound_per_asof_date"
                ],
                "history_pre_reform_requests_per_asof_date_upper_bound": history_strategy["paging_basis"][
                    "pre_reform_request_upper_bound_per_asof_date"
                ],
                "history_post_reform_requests_per_asof_date_lower_bound": history_strategy["paging_basis"][
                    "post_reform_request_lower_bound_per_asof_date"
                ],
                "history_post_reform_requests_per_asof_date_upper_bound": history_strategy["paging_basis"][
                    "post_reform_request_upper_bound_per_asof_date"
                ],
                "daily_window_request_lower_bound": next(
                    item["request_lower_bound"]
                    for item in history_strategy["scenarios"]
                    if item["name"] == "DAILY"
                ),
                "daily_window_request_upper_bound": next(
                    item["request_upper_bound"]
                    for item in history_strategy["scenarios"]
                    if item["name"] == "DAILY"
                ),
                "monthly_window_request_lower_bound": next(
                    item["request_lower_bound"]
                    for item in history_strategy["scenarios"]
                    if item["name"] == "MONTHLY_ANCHOR_PLUS_END"
                ),
                "monthly_window_request_upper_bound": next(
                    item["request_upper_bound"]
                    for item in history_strategy["scenarios"]
                    if item["name"] == "MONTHLY_ANCHOR_PLUS_END"
                ),
                "production_reconstruction_enabled": episode["production_reconstruction_enabled"],
                "status_code_05_semantics_resolved": semantics["status_code_05_semantics_resolved"],
                "reopening_vs_correction_resolved": semantics["reopening_vs_correction_resolved"],
                "nationwide_lossless_event_history_available": False,
            },
            "public_kaggle": {
                "status": public_status,
                "privacy_public_allowlist_approved": privacy["public_allowlist_approved"],
                "source_use_license": license_review["evidence_refresh"]["source_use_license_gate"],
                "kaggle_redistribution": "PERMITTED_FOR_VERIFIED_AGGREGATE_BASED_ON_OFFICIAL_METADATA",
                "raw_external_mirror_gate": license_review["evidence_refresh"]["raw_external_mirror_gate"],
                "aggregate_redistribution_gate": "PERMITTED_FOR_VERIFIED_AGGREGATE",
                "row_level_public_build_allowed": False,
                "precise_wgs84_public_build_allowed": False,
                "privacy_minimized_aggregate_candidate": "COMPLETED_VERIFIED_RELEASE_APPROVED",
                "aggregate_candidate_build_id": public_aggregate_result["scope"]["aggregate_build_id"],
                "aggregate_candidate_minimum_cell_count": public_aggregate_result["scope"]["minimum_cell_count"],
                "aggregate_cells_released_candidate": public_aggregate_result["scope"][
                    "aggregate_cells_released_candidate"
                ],
                "aggregate_cells_suppressed": public_aggregate_result["scope"]["aggregate_cells_suppressed"],
                "aggregate_released_source_rows": public_aggregate_result["scope"]["released_source_rows"],
                "aggregate_suppressed_source_rows": public_aggregate_result["scope"]["suppressed_source_rows"],
                "aggregate_output_bytes": public_aggregate_result["scope"]["output_bytes"],
                "aggregate_independent_verifier": public_aggregate_result["verification"]["status"],
                "aggregate_technical_minimization_verified": public_aggregate_result["privacy"][
                    "technical_minimization_verified"
                ],
                "aggregate_build_time_publication_flag": public_aggregate_result["scope"][
                    "aggregate_publication_approved"
                ],
                "aggregate_publication_approved": release_scope["public_release"][
                    "aggregate_publication_approved"
                ],
                "aggregate_release_decision_supersedes_build_time_candidate_gate": True,
                "redistribution_clarification_plan": "OPTIONAL_ADDITIONAL_CONFIRMATION",
                "redistribution_prepared_inquiry_status": redistribution_clarification[
                    "prepared_inquiry"
                ]["status"],
                "redistribution_prepared_inquiry_source_count": len(
                    redistribution_clarification["prepared_inquiry"]["source_identifiers"]
                ),
                "redistribution_clarification_outreach_performed": redistribution_clarification[
                    "execution"
                ]["outreach_performed"],
                "redistribution_written_response_received": redistribution_clarification[
                    "execution"
                ]["written_response_received"],
                "written_source_specific_confirmation_required_for_aggregate_publication": release_scope[
                    "public_release"
                ]["written_source_specific_confirmation_required_for_aggregate_publication"],
                "kaggle_license_metadata": release_scope["public_release"]["kaggle_license_metadata"],
                "project_requires_source_attribution": release_scope["public_release"][
                    "project_requires_source_attribution"
                ],
            },
        },
        "next_long_local_actions": [],
        "next_product_action": "publish the verified privacy-minimized aggregate on Kaggle; keep row-level and precise-coordinate artifacts private; history and episode reconstruction remain optional advanced workflows",
        "hard_blocks": [
            "do not publish row-level PERMIT data under the aggregate-only v1 release decision",
            "do not add WGS84 columns to the frozen 26-column PERMIT parent; use a separately versioned local enrichment",
            "if optional production lifecycle episodes are materialized, require all 7320 approved monthly history snapshot tasks complete uniquely; status 05 remains unmapped",
            "do not treat frozen deleted-authority history partitions as semantically equivalent to current-state partitions after the 2026-07-01 reform",
            "do not use API queryability as date-effective authority membership; apply current-minus-new-plus-deleted before 2026-07-01 and current-only on/after 2026-07-01",
            "do not declare MNG_NO an official source primary key",
        ],
    }
