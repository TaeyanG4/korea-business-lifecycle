from __future__ import annotations

from typing import Any

from .config import load_json


V1_SOURCE_KEYS = {"general_restaurants", "rest_cafes", "bakeries"}
ALLOWED_REDISTRIBUTION = {"PERMITTED", "PERMITTED_WITH_CONDITIONS"}


def load_source_registry() -> dict[str, Any]:
    return load_json("provenance/source_registry.json")


def validate_source_registry(registry: dict[str, Any]) -> list[str]:
    """Return invariant violations without inventing source semantics."""
    errors: list[str] = []
    inventory = registry.get("inventory", {})
    if inventory.get("current_permit_dataset_count") != 195:
        errors.append("current permit dataset inventory must be the verified 195")

    categories = registry.get("categories", [])
    keys = {item.get("source_key") for item in categories}
    if keys != V1_SOURCE_KEYS:
        errors.append(f"v1 source keys mismatch: {sorted(keys)}")

    for item in categories:
        if item.get("documented_primary_key") is not None:
            errors.append(f"{item.get('source_key')}: source PK must remain unresolved")
        if item.get("closure_semantics") not in {"UNRESOLVED", "VERIFIED"}:
            errors.append(f"{item.get('source_key')}: invalid closure semantic state")
        if item.get("kaggle_redistribution") in ALLOWED_REDISTRIBUTION:
            errors.append(
                f"{item.get('source_key')}: Kaggle redistribution cannot be pre-approved in bootstrap"
            )
    return errors

