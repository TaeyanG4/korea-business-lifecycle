import json
from pathlib import Path

from korea_business_lifecycle.release_readiness import compute_release_readiness


ROOT = Path(__file__).resolve().parents[1]


def test_computed_release_readiness_matches_tracked_provenance() -> None:
    tracked = json.loads(
        (ROOT / "provenance" / "release_readiness.json").read_text(encoding="utf-8")
    )
    assert compute_release_readiness() == tracked


def test_local_parent_is_verified_and_wgs84_enrichment_is_ready_for_user_execution() -> None:
    readiness = compute_release_readiness()
    assert readiness["tracks"]["local_permit_parent"]["status"] == "COMPLETED_VERIFIED"
    assert readiness["tracks"]["local_permit_parent"]["build_id"] == (
        "permit-v1-9908225df465e2ff"
    )
    assert readiness["tracks"]["geospatial_derivation"]["coordinate_axis_order_verified_nationwide"] is True
    assert readiness["tracks"]["geospatial_derivation"]["local_wgs84_generation_approved"] is True
    assert readiness["tracks"]["geospatial_derivation"]["public_wgs84_release_approved"] is False
    assert readiness["tracks"]["geospatial_derivation"]["status"] == (
        "READY_FOR_WGS84_ENRICHMENT_USER_EXECUTION"
    )
    assert readiness["tracks"]["geospatial_derivation"]["enrichment_schema"] == "FROZEN"
    assert readiness["tracks"]["geospatial_derivation"]["enrichment_builder"] == (
        "IMPLEMENTED_TESTED_NOT_EXECUTED"
    )
    assert readiness["tracks"]["geospatial_derivation"]["expected_build_id"] == (
        "permit-geo-v1-c4af8799de0283bb"
    )
    assert readiness["tracks"]["geospatial_derivation"]["expected_rows"] == 3_010_802
    assert readiness["tracks"]["geospatial_derivation"]["expected_transformed_coordinates"] == 2_811_767
    assert readiness["tracks"]["geospatial_derivation"]["expected_missing_source_coordinates"] == 199_035
    assert readiness["next_long_local_actions"][0]["command"] == (
        "python scripts/materialize_permit_geospatial.py --execute"
    )
    assert readiness["tracks"]["lifecycle_episode"]["production_reconstruction_enabled"] is False
    assert readiness["tracks"]["public_kaggle"]["status"] == "BLOCKED"
    assert readiness["tracks"]["public_kaggle"]["row_level_public_build_allowed"] is False
