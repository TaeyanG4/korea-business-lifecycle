from __future__ import annotations

from typing import Any

from .canonical_materialization_verify import expected_permit_build_id
from .provenance import (
    load_geospatial_axis_probe,
    load_geospatial_full_axis,
    load_geospatial_full_axis_plan,
    load_grain_decision,
    load_license_review,
    load_permit_parent_full_dry_run,
    load_permit_parent_materialization,
    load_permit_parent_materialization_plan,
    load_permit_geospatial_materialization_plan,
    load_permit_geospatial_materialization,
    load_privacy_review,
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
                "production_reconstruction_enabled": episode["production_reconstruction_enabled"],
                "status_code_05_semantics_resolved": semantics["status_code_05_semantics_resolved"],
                "reopening_vs_correction_resolved": semantics["reopening_vs_correction_resolved"],
                "nationwide_lossless_event_history_available": False,
            },
            "public_kaggle": {
                "status": public_status,
                "privacy_public_allowlist_approved": privacy["public_allowlist_approved"],
                "kaggle_redistribution": "UNRESOLVED",
                "row_level_public_build_allowed": public_status == "READY",
                "privacy_minimized_aggregate_candidate": "IMPLEMENTED_NOT_EXECUTED",
                "aggregate_candidate_build_id": public_aggregate["scope"]["aggregate_build_id"],
                "aggregate_candidate_minimum_cell_count": public_aggregate["contracts"][
                    "minimum_cell_count"
                ],
                "aggregate_publication_approved": public_aggregate["scope"]["aggregate_publication_approved"],
                "local_materialization_completion_does_not_change_publication_status": True,
            },
        },
        "next_long_local_actions": [
            {
                "priority": 1,
                "name": "materialize_public_permit_aggregate",
                "command": "python scripts/materialize_public_permit_aggregate.py --execute",
                "follow_up": "python scripts/verify_public_permit_aggregate.py",
            }
        ],
        "next_product_action": "execute and verify the local privacy-minimized aggregate candidate; publication still requires redistribution clearance",
        "hard_blocks": [
            "do not publish row-level data until privacy allowlist and redistribution review pass",
            "do not add WGS84 columns to the frozen 26-column PERMIT parent; use a separately versioned local enrichment",
            "do not reconstruct production lifecycle episodes until the explicit history-observation strategy is approved; status 05 remains unmapped",
            "do not declare MNG_NO an official source primary key",
        ],
    }
