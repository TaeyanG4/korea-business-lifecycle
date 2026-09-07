from __future__ import annotations

from typing import Any

from .config import load_json


V1_SOURCE_KEYS = {"general_restaurants", "rest_cafes", "bakeries"}
ALLOWED_REDISTRIBUTION = {"PERMITTED", "PERMITTED_WITH_CONDITIONS"}


def load_source_registry() -> dict[str, Any]:
    return load_json("provenance/source_registry.json")


def load_license_review() -> dict[str, Any]:
    return load_json("provenance/license_review.json")


def load_privacy_review() -> dict[str, Any]:
    return load_json("provenance/privacy_review.json")


def load_history_review() -> dict[str, Any]:
    return load_json("provenance/history_review.json")


def load_observed_snapshot_summary() -> dict[str, Any]:
    return load_json("provenance/observed_snapshot_summary.json")


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
        if not item.get("bulk_download_url"):
            errors.append(f"{item.get('source_key')}: direct bulk download URL missing")
        if item.get("documented_primary_key") is not None:
            errors.append(f"{item.get('source_key')}: source PK must remain unresolved")
        if item.get("closure_semantics") not in {"UNRESOLVED", "VERIFIED"}:
            errors.append(f"{item.get('source_key')}: invalid closure semantic state")
        if item.get("kaggle_redistribution") in ALLOWED_REDISTRIBUTION:
            errors.append(
                f"{item.get('source_key')}: Kaggle redistribution cannot be pre-approved in bootstrap"
            )
    return errors


def validate_license_review(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    categories = review.get("categories", [])
    keys = {item.get("source_key") for item in categories}
    if keys != V1_SOURCE_KEYS:
        errors.append(f"license-review source keys mismatch: {sorted(keys)}")
    for item in categories:
        if item.get("kaggle_redistribution") != "UNRESOLVED":
            errors.append(f"{item.get('source_key')}: redistribution must remain unresolved")
        if item.get("privacy_review") != "REVIEW_REQUIRED":
            errors.append(f"{item.get('source_key')}: privacy review must remain required")
    return errors


def validate_privacy_review(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(review.get("scope", [])) != V1_SOURCE_KEYS:
        errors.append("privacy-review scope must exactly match the three v1 sources")
    if review.get("field_inventory_complete") is not True:
        errors.append("field inventory must reflect completed current snapshot profiling")
    if review.get("public_allowlist_approved") is not False:
        errors.append("public allowlist cannot be approved before privacy profiling")
    return errors


def validate_history_review(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("common_contract", {}).get("event_log_claim") is not False:
        errors.append("history must not be represented as a lossless event log")
    if review.get("common_contract", {}).get("authentication") != "data.go.kr serviceKey required":
        errors.append("history authentication requirement must remain explicit")
    if {item.get("source_key") for item in review.get("categories", [])} != V1_SOURCE_KEYS:
        errors.append("history-review scope must exactly match v1 sources")
    return errors


def validate_observed_snapshot_summary(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    totals = summary.get("totals", {})
    categories = summary.get("categories", [])
    if {item.get("source_key") for item in categories} != V1_SOURCE_KEYS:
        errors.append("observed snapshot summary must exactly match v1 sources")
    if totals.get("rows") != sum(item.get("rows", 0) for item in categories):
        errors.append("observed total rows must equal category row totals")
    if any(item.get("management_number_distinct") != item.get("rows") for item in categories):
        errors.append("current-snapshot management-number uniqueness observation changed")
    if "not declared" not in summary.get("interpretation", {}).get("identity", ""):
        errors.append("observed uniqueness must not be upgraded to a declared primary key")
    return errors
