from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

from .provenance import load_v1_release_scope
from .storage import resolve_data_root


AGGREGATE_BUILD_ID = "permit-public-agg-v1-bedd874de6619bee"
AGGREGATE_FILENAME = "permit_aggregate.parquet"
PUBLIC_FILENAME = "korea_food_service_permit_aggregate.parquet"
EXPECTED_SHA256 = "112fbec3187b2d77df2744edb878fa0f3ecb850cf675496cd4383404092911fb"
EXPECTED_BYTES = 108_019
DATASET_SLUG = "korea-food-service-permit-aggregate"


class KaggleReleaseError(RuntimeError):
    """Raised when the aggregate release package cannot be prepared safely."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _validate_owner(owner: str) -> str:
    value = owner.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
        raise KaggleReleaseError("Kaggle owner must be a username/organization slug")
    return value


def _metadata(owner: str) -> dict[str, Any]:
    dataset_id = f"{owner}/{DATASET_SLUG}"
    return {
        "title": "Korea Food-Service Permit Aggregate",
        "subtitle": "Privacy-minimized nationwide local permit snapshot aggregate",
        "description": (
            "A privacy-minimized aggregate derived from the nationwide current snapshot of "
            "three Korean Ministry of the Interior and Safety local-government food-service "
            "permit categories: general restaurants, rest cafes, and bakeries. The verified "
            "parent contains 3,010,802 permit records. This release contains 67,267 aggregate "
            "cells after suppressing cells with fewer than 10 source rows. It excludes business "
            "names, exact addresses, management numbers, phone numbers, precise coordinates, "
            "and other row-level/linkable fields. Permit year is not claimed to be physical "
            "opening year; closure year is not claimed to be an irreversible terminal event. "
            "Status 03 is not treated as irreversible and status 05 remains unresolved. The "
            "official source pages display no restriction on the permitted-use scope. License metadata is therefore "
            "recorded as Other and the official source pages/terms are the controlling source-use "
            "reference; this project does not relicense upstream source records."
        ),
        "id": dataset_id,
        "licenses": [{"name": "other"}],
        "keywords": ["business", "restaurants"],
        "resources": [
            {
                "path": PUBLIC_FILENAME,
                "description": (
                    "Verified k=10 privacy-minimized aggregate. Columns: source_key, authority_code, "
                    "source_status_code, source_detail_status_code, permit_year, closure_year, cell_count."
                ),
            }
        ],
    }


def prepare_kaggle_release(
    *,
    owner: str | None = None,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    source = (
        root
        / "public_candidate"
        / "permit_aggregate"
        / "v1"
        / AGGREGATE_BUILD_ID
        / AGGREGATE_FILENAME
    )
    if not source.is_file():
        raise KaggleReleaseError(f"verified aggregate artifact not found: {source}")
    if source.stat().st_size != EXPECTED_BYTES:
        raise KaggleReleaseError("aggregate byte size does not match verified provenance")
    actual_sha = _sha256(source)
    if actual_sha != EXPECTED_SHA256:
        raise KaggleReleaseError("aggregate SHA-256 does not match verified provenance")

    release_scope = load_v1_release_scope()
    public = release_scope["public_release"]
    if public.get("aggregate_publication_approved") is not True:
        raise KaggleReleaseError("final v1 release scope does not approve aggregate publication")
    if public.get("row_level_permit_publication_approved") is not False:
        raise KaggleReleaseError("row-level publication invariant changed")
    if public.get("aggregate_sha256") != actual_sha:
        raise KaggleReleaseError("release-scope aggregate hash mismatch")

    output = root / "kaggle_release" / "v1" / AGGREGATE_BUILD_ID
    output.mkdir(parents=True, exist_ok=True)
    destination = output / PUBLIC_FILENAME
    shutil.copyfile(source, destination)
    if _sha256(destination) != actual_sha:
        raise KaggleReleaseError("copied Kaggle artifact hash mismatch")

    readme = """# Korea Food-Service Permit Aggregate

This Kaggle release contains only a privacy-minimized aggregate derived from the verified nationwide current permit snapshot for three Korean food-service permit categories.

## Coverage

- General restaurants
- Rest cafes
- Bakeries
- Verified parent snapshot rows: 3,010,802
- Released aggregate cells: 67,267
- Minimum released cell count: 10

## Columns

`source_key`, `authority_code`, `source_status_code`, `source_detail_status_code`, `permit_year`, `closure_year`, `cell_count`

## Important interpretation limits

- `permit_year` is not claimed to be a physical opening year.
- `closure_year` is not claimed to be a permanent terminal event.
- Status `03` is not treated as irreversible; two source-level `03->01` reversals were observed during project validation.
- Status `05` remains unresolved.
- `k=10` is a technical minimization threshold, not a legal privacy guarantee.
- This release does not contain row-level permit data, business names, exact addresses, management numbers, phone numbers, or precise coordinates.

See `SOURCES.md` for official source pages and the repository for full reproducibility/provenance.
"""
    sources = """# Official sources and terms

Provider: Ministry of the Interior and Safety (MOIS), Republic of Korea.

- General restaurants - data.go.kr ID 15154916: https://www.data.go.kr/data/15154916/openapi.do
- Rest cafes - data.go.kr ID 15154921: https://www.data.go.kr/data/15154921/openapi.do
- Bakeries - data.go.kr ID 15155252: https://www.data.go.kr/data/15155252/openapi.do
- Public Data Portal policy: https://www.data.go.kr/ugs/selectPortalPolicyView.do

The three official API detail pages were rechecked on 2026-09-08 and displayed no restriction on the permitted-use scope. Kaggle metadata uses the `other` license category so this project does not invent or impose a different license on upstream government records. This public package contains only the independently verified privacy-minimized aggregate; row-level records and precise coordinates are not included.
"""
    (output / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    (output / "SOURCES.md").write_text(sources, encoding="utf-8", newline="\n")

    manifest = {
        "decision": "KAGGLE_AGGREGATE_RELEASE_PACKAGE_PREPARED",
        "aggregate_build_id": AGGREGATE_BUILD_ID,
        "source_sha256": actual_sha,
        "packaged_sha256": _sha256(destination),
        "bytes": destination.stat().st_size,
        "aggregate_cells": public["aggregate_rows"],
        "row_level_values_included": False,
        "precise_coordinates_included": False,
        "kaggle_license_metadata": public["kaggle_license_metadata"],
        "owner_configured": owner is not None,
        "dataset_slug": DATASET_SLUG,
    }
    if owner is not None:
        normalized_owner = _validate_owner(owner)
        metadata = _metadata(normalized_owner)
        (output / "dataset-metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        manifest["dataset_id"] = metadata["id"]

    (output / "release-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return {
        "status": "PASS",
        "output_dir": str(output),
        "artifact": str(destination),
        "sha256": actual_sha,
        "bytes": EXPECTED_BYTES,
        "owner_configured": owner is not None,
        "dataset_id": manifest.get("dataset_id"),
        "row_level_values_emitted": False,
    }
