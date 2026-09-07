from __future__ import annotations

from typing import Any

from .canonical_materialization_verify import expected_permit_build_id
from .provenance import (
    load_geospatial_axis_probe,
    load_geospatial_full_axis_plan,
    load_grain_decision,
    load_license_review,
    load_permit_parent_full_dry_run,
    load_permit_parent_materialization_plan,
    load_privacy_review,
)


def compute_release_readiness() -> dict[str, Any]:
    full_dry_run = load_permit_parent_full_dry_run()
    materialization = load_permit_parent_materialization_plan()
    geospatial_probe = load_geospatial_axis_probe()
    geospatial_full = load_geospatial_full_axis_plan()
    grain = load_grain_decision()
    privacy = load_privacy_review()
    license_review = load_license_review()

    episode = grain["selected_grains"]["lifecycle_analysis_grain"]
    semantics = grain["episode_semantics"]
    local_status = (
        "READY_FOR_USER_EXECUTION"
        if full_dry_run["decision"] == "FULL_CURRENT_SNAPSHOT_DRY_RUN_PASSED"
        and materialization["scope"]["execution_status"] == "NOT_EXECUTED"
        else "REVIEW_REQUIRED"
    )
    geospatial_status = (
        "READY_FOR_FULL_AXIS_QA_USER_EXECUTION"
        if geospatial_full["scope"]["execution_status"] == "NOT_EXECUTED"
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
        "decision": "LOCAL_PERMIT_BUILD_READY_PUBLICATION_AND_DERIVED_PRODUCTS_BLOCKED",
        "tracks": {
            "local_permit_parent": {
                "status": local_status,
                "full_snapshot_transform_validation": "PASS_3010802_ROWS",
                "materializer": "IMPLEMENTED_TESTED_NOT_EXECUTED",
                "independent_build_verifier": "IMPLEMENTED_TESTED",
                "expected_build_id": expected_permit_build_id(),
                "public_release_implied": False,
            },
            "geospatial_derivation": {
                "status": geospatial_status,
                "bounded_axis_evidence": geospatial_probe["aggregate"]["assessment"],
                "full_axis_validator": "IMPLEMENTED_NOT_EXECUTED",
                "coordinate_axis_order_verified_nationwide": grain["evidence"][
                    "coordinate_axis_order_verified_nationwide"
                ],
                "wgs84_generation_approved": grain["evidence"]["wgs84_generation_approved"],
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
                "local_materialization_completion_does_not_change_publication_status": True,
            },
        },
        "next_long_local_actions": [
            {
                "priority": 1,
                "name": "materialize_permit_parent",
                "command": "python scripts/materialize_permit_parent.py --execute",
                "follow_up": "python scripts/verify_permit_parent_build.py",
            },
            {
                "priority": 2,
                "name": "validate_full_coordinate_axis",
                "command": "python scripts/validate_full_coordinate_axis.py --execute",
                "follow_up": (
                    "review aggregate result before changing schema axis metadata or enabling WGS84"
                ),
            },
        ],
        "hard_blocks": [
            "do not publish row-level data until privacy allowlist and redistribution review pass",
            "do not generate WGS84 columns until full coordinate-axis QA result is reviewed and transformation QA is approved",
            "do not reconstruct production lifecycle episodes until the explicit history-observation strategy is approved; status 05 remains unmapped",
            "do not declare MNG_NO an official source primary key",
        ],
    }
