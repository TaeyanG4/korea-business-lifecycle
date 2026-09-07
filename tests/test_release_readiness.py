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
    assert readiness["tracks"]["public_kaggle"]["privacy_minimized_aggregate_candidate"] == (
        "COMPLETED_VERIFIED_NOT_PUBLICATION_APPROVED"
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
    assert readiness["tracks"]["public_kaggle"]["aggregate_publication_approved"] is False
    assert readiness["tracks"]["public_kaggle"]["source_use_license"] == "PASS_METADATA_CONFIRMED"
    assert readiness["tracks"]["public_kaggle"]["raw_external_mirror_gate"] == (
        "UNRESOLVED_THIRD_PARTY_RIGHTS_CLARIFICATION"
    )
    assert readiness["tracks"]["public_kaggle"]["aggregate_redistribution_gate"] == "UNRESOLVED"
    assert readiness["next_long_local_actions"] == []
    assert readiness["tracks"]["lifecycle_episode"]["production_reconstruction_enabled"] is False
    assert readiness["tracks"]["public_kaggle"]["status"] == "BLOCKED"
    assert readiness["tracks"]["public_kaggle"]["row_level_public_build_allowed"] is False
