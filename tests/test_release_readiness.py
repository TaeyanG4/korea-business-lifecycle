import json
from pathlib import Path

from korea_business_lifecycle.release_readiness import compute_release_readiness


ROOT = Path(__file__).resolve().parents[1]


def test_computed_release_readiness_matches_tracked_provenance() -> None:
    tracked = json.loads(
        (ROOT / "provenance" / "release_readiness.json").read_text(encoding="utf-8")
    )
    assert compute_release_readiness() == tracked


def test_local_parent_is_ready_but_publication_and_derived_products_are_blocked() -> None:
    readiness = compute_release_readiness()
    assert readiness["tracks"]["local_permit_parent"]["status"] == "READY_FOR_USER_EXECUTION"
    assert readiness["tracks"]["local_permit_parent"]["expected_build_id"] == (
        "permit-v1-9908225df465e2ff"
    )
    assert readiness["tracks"]["geospatial_derivation"]["wgs84_generation_approved"] is False
    assert readiness["tracks"]["lifecycle_episode"]["production_reconstruction_enabled"] is False
    assert readiness["tracks"]["public_kaggle"]["status"] == "BLOCKED"
    assert readiness["tracks"]["public_kaggle"]["row_level_public_build_allowed"] is False
