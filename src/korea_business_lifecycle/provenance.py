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


def load_bounded_history_audit() -> dict[str, Any]:
    return load_json("provenance/bounded_history_audit.json")


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


def validate_bounded_history_audit(audit: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    categories = audit.get("categories", [])
    if {item.get("source_key") for item in categories} != V1_SOURCE_KEYS:
        errors.append("bounded-history audit must exactly match v1 sources")
    if audit.get("scope", {}).get("authority_code") != "3000000":
        errors.append("bounded-history audit must remain scoped to authority 3000000")
    if audit.get("scope", {}).get("start_date") != "20260101":
        errors.append("bounded-history audit start date changed")
    if audit.get("scope", {}).get("end_date") != "20260906":
        errors.append("bounded-history audit end date changed")
    for item in categories:
        if item.get("assessment", {}).get("mng_no_continuity") != "STRONG":
            errors.append(f"{item.get('source_key')}: bounded MNG_NO continuity is not STRONG")
        if item.get("assessment", {}).get("lifecycle_signal") != "USABLE_FOR_FURTHER_AUDIT":
            errors.append(f"{item.get('source_key')}: lifecycle signal changed")
        if item.get("start_duplicate_mng_no_rows") != 0 or item.get("end_duplicate_mng_no_rows") != 0:
            errors.append(f"{item.get('source_key')}: duplicate MNG_NO observed")
        if item.get("disappeared_mng_no") != 0:
            errors.append(f"{item.get('source_key')}: starting MNG_NO disappeared")
        if item.get("changed_common_rows", {}).get("permit_date") != 0:
            errors.append(f"{item.get('source_key')}: permit date changed")
        alignment = item.get("status_closure_alignment", {})
        if alignment.get("status_changed_without_closure_change") != 0:
            errors.append(f"{item.get('source_key')}: status changed without closure-date change")
        if alignment.get("closure_changed_without_status_change") != 0:
            errors.append(f"{item.get('source_key')}: closure date changed without status change")
    return errors
