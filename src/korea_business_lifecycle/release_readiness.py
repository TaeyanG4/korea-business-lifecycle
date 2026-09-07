from __future__ import annotations

from typing import Any

from .canonical_materialization_verify import expected_permit_build_id
from .provenance import (
    load_bounded_episode_reconstruction,
    load_geospatial_axis_probe,
    load_geospatial_full_axis,
    load_geospatial_full_axis_plan,
    load_grain_decision,
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
    grain = load_grain_decision()
    privacy = load_privacy_review()
    license_review = load_license_review()

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
        "READY"
        if privacy["public_allowlist_approved"] is True
        and all(
            item["kaggle_redistribution"] in {"PERMITTED", "PERMITTED_WITH_CONDITIONS"}
            for item in license_review["categories"]
        )
        else "BLOCKED"
    )

    return {
        "checked_at": "2026-09-07",
        "decision": "LOCAL_CANONICAL_AND_WGS84_VERIFIED_PUBLICATION_SAFETY_REVIEW_NEXT",
        "tracks": {
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
                "status": "BLOCKED_PRODUCTION_RECONSTRUCTION",
                "schema": episode["schema_status"],
                "bounded_reconstructor": "IMPLEMENTED_SYNTHETIC_VALIDATED",
                "bounded_reconstructor_module": bounded_episode["implementation"]["module"],
                "bounded_reconstructor_max_observations": bounded_episode["scope"][
                    "maximum_observations_per_call"
                ],
                "bounded_reconstructor_in_memory_only": bounded_episode["scope"]["bounded_in_memory_only"],
                "history_observation_strategy": "COST_BOUNDED_NO_CADENCE_APPROVED",
                "history_authority_domain_authoritatively_complete": history_strategy["paging_basis"][
                    "authority_domain_authoritatively_complete"
                ],
                "history_requests_per_asof_date_lower_bound": history_strategy["paging_basis"][
                    "request_lower_bound_per_asof_date"
                ],
                "history_requests_per_asof_date_upper_bound": history_strategy["paging_basis"][
                    "request_upper_bound_per_asof_date"
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
                "production_reconstruction_enabled": episode["production_reconstruction_enabled"],
                "status_code_05_semantics_resolved": semantics["status_code_05_semantics_resolved"],
                "reopening_vs_correction_resolved": semantics["reopening_vs_correction_resolved"],
                "nationwide_lossless_event_history_available": False,
            },
            "public_kaggle": {
                "status": public_status,
                "privacy_public_allowlist_approved": privacy["public_allowlist_approved"],
                "source_use_license": license_review["evidence_refresh"]["source_use_license_gate"],
                "kaggle_redistribution": "UNRESOLVED",
                "raw_external_mirror_gate": license_review["evidence_refresh"]["raw_external_mirror_gate"],
                "aggregate_redistribution_gate": license_review["evidence_refresh"][
                    "privacy_minimized_aggregate_redistribution_gate"
                ],
                "row_level_public_build_allowed": public_status == "READY",
                "privacy_minimized_aggregate_candidate": "COMPLETED_VERIFIED_NOT_PUBLICATION_APPROVED",
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
                "aggregate_publication_approved": public_aggregate_result["scope"]["aggregate_publication_approved"],
                "local_materialization_completion_does_not_change_publication_status": True,
            },
        },
        "next_long_local_actions": [],
        "next_product_action": "resolve redistribution clearance and define the nationwide history-observation strategy required before production episode reconstruction can be considered",
        "hard_blocks": [
            "do not publish row-level data until privacy allowlist and redistribution review pass",
            "do not add WGS84 columns to the frozen 26-column PERMIT parent; use a separately versioned local enrichment",
            "do not reconstruct production lifecycle episodes until the explicit history-observation strategy is approved; status 05 remains unmapped",
            "do not declare MNG_NO an official source primary key",
        ],
    }
