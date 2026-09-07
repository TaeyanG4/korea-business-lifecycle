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


def load_history_sample_plan() -> dict[str, Any]:
    return load_json("provenance/history_sample_plan.json")


def load_reverse_transition_probe_plan() -> dict[str, Any]:
    return load_json("provenance/reverse_transition_probe_plan.json")


def load_reverse_transition_findings() -> dict[str, Any]:
    return load_json("provenance/reverse_transition_findings.json")


def load_observed_snapshot_summary() -> dict[str, Any]:
    return load_json("provenance/observed_snapshot_summary.json")


def load_bounded_history_audit() -> dict[str, Any]:
    return load_json("provenance/bounded_history_audit.json")


def load_expanded_history_audit() -> dict[str, Any]:
    return load_json("provenance/expanded_history_audit.json")


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


def validate_history_sample_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    representatives = plan.get("selection", {}).get("representatives", [])
    codes = [item.get("authority_code") for item in representatives]
    labels = [item.get("label") for item in representatives]
    if labels != ["q10", "q50", "q90", "max"]:
        errors.append("history sample labels must be q10/q50/q90/max in deterministic order")
    if len(set(codes)) != 4:
        errors.append("history sample must contain four distinct added authority codes")
    if plan.get("baseline_authority") in set(codes):
        errors.append("baseline authority must be excluded from added representatives")
    if plan.get("selection", {}).get("eligible_authorities") != 229:
        errors.append("history sample eligible-authority count changed")
    page_total = sum(int(item.get("history_pages_two_dates", 0)) for item in representatives)
    if page_total != plan.get("additional_history_requests"):
        errors.append("history sample request total must equal representative page totals")
    if plan.get("history_dates") != ["20260101", "20260906"]:
        errors.append("history sample dates changed")
    return errors


def validate_reverse_transition_probe_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    cases = plan.get("cases", [])
    expected = {
        ("rest_cafes", "3830000", "20260901"),
        ("general_restaurants", "4530000", "20260317"),
    }
    observed = {
        (
            str(item.get("source_key")),
            str(item.get("authority_code")),
            str(item.get("candidate_date")),
        )
        for item in cases
    }
    if observed != expected:
        errors.append("reverse-transition probe cases changed")
    if len(cases) != 2:
        errors.append("reverse-transition probe must contain exactly two cases")
    task_count = sum(len(item.get("probe_dates", [])) for item in cases)
    if task_count != plan.get("planned_tasks") or task_count != 6:
        errors.append("reverse-transition probe must contain exactly six date tasks")
    request_cap = sum(
        len(item.get("probe_dates", [])) * int(item.get("max_pages_per_snapshot", 0))
        for item in cases
    )
    if request_cap != plan.get("max_network_requests") or request_cap != 411:
        errors.append("reverse-transition request cap changed")
    privacy = plan.get("privacy", {})
    if any(privacy.get(key) is not False for key in (
        "management_numbers_committed",
        "business_names_committed",
        "addresses_committed",
        "coordinates_committed",
    )):
        errors.append("reverse-transition probe privacy flags must remain false")
    return errors


def validate_reverse_transition_findings(findings: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if findings.get("decision") != "SOURCE_STATE_REVERSALS_CONFIRMED_TERMINAL_IRREVERSIBILITY_REJECTED":
        errors.append("reverse-transition finding decision changed")
    cases = findings.get("cases", [])
    if len(cases) != 2:
        errors.append("reverse-transition findings must contain exactly two cases")
    expected = {
        ("rest_cafes", "3830000", "20260831", "20260901"),
        ("general_restaurants", "4530000", "20260316", "20260317"),
    }
    observed = {
        (
            str(item.get("source_key")),
            str(item.get("authority_code")),
            str(item.get("last_observed_closed_date")),
            str(item.get("first_observed_active_date")),
        )
        for item in cases
    }
    if observed != expected:
        errors.append("reverse-transition boundaries changed")
    for item in cases:
        if item.get("status_transition") != "03->01":
            errors.append(f"{item.get('source_key')}: reverse status transition changed")
        if item.get("closure_transition") != "value->blank":
            errors.append(f"{item.get('source_key')}: closure reversal pattern changed")
        for key in ("permit_date_stable", "business_name_stable", "address_stable", "coordinates_stable"):
            if item.get(key) is not True:
                errors.append(f"{item.get('source_key')}: identity stability observation changed for {key}")
    conclusion = findings.get("lifecycle_conclusion", {})
    if conclusion.get("code_03_can_be_assumed_irreversible_terminal") is not False:
        errors.append("code 03 must not be treated as irreversible terminal")
    if conclusion.get("closure_date_can_be_assumed_permanent_terminal_event") is not False:
        errors.append("closure date must not be treated as permanent terminal event")
    if conclusion.get("reopening_vs_correction_resolved") is not False:
        errors.append("reopening-versus-correction semantics must remain unresolved")
    identity = findings.get("identity_conclusion", {})
    if identity.get("mng_no_primary_key_declared") is not False:
        errors.append("reverse-transition findings must not declare MNG_NO as primary key")
    if identity.get("establishment_identity_declared") is not False:
        errors.append("reverse-transition findings must not declare establishment identity")
    evidence = findings.get("evidence", {})
    if len(evidence.get("probe_manifest_sha256", [])) != 6:
        errors.append("reverse-transition findings must retain six probe manifest hashes")
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


def validate_expanded_history_audit(audit: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    scope = audit.get("scope", {})
    if scope.get("pair_count") != 15:
        errors.append("expanded-history audit must contain 15 source/authority pairs")
    if set(scope.get("authorities", [])) != {
        "3000000",
        "3220000",
        "3830000",
        "4420000",
        "4530000",
    }:
        errors.append("expanded-history authority scope changed")
    if audit.get("assessment_counts", {}).get("mng_no_continuity", {}).get("STRONG") != 15:
        errors.append("expanded-history MNG_NO continuity is no longer strong across all pairs")
    totals = audit.get("totals", {})
    if totals.get("disappeared_mng_no") != 0:
        errors.append("expanded-history starting MNG_NO values disappeared")
    if totals.get("start_duplicate_mng_no_rows") != 0 or totals.get("end_duplicate_mng_no_rows") != 0:
        errors.append("expanded-history duplicate MNG_NO values observed")
    if audit.get("changed_common_rows", {}).get("permit_date") != 0:
        errors.append("expanded-history permit-date changes observed")
    alignment = audit.get("status_closure_alignment", {})
    if alignment.get("status_changed_without_closure_change") != 0:
        errors.append("expanded-history status/closure alignment changed")
    if alignment.get("closure_changed_without_status_change") != 0:
        errors.append("expanded-history closure/status alignment changed")
    if audit.get("status_code_transitions", {}).get("03->01") != 2:
        errors.append("expanded-history reverse-transition evidence changed")
    if audit.get("identity_claim", {}).get("source_primary_key_declared") is not False:
        errors.append("expanded-history audit must not declare a source primary key")
    if audit.get("identity_claim", {}).get("establishment_identity_declared") is not False:
        errors.append("expanded-history audit must not declare establishment identity")
    if audit.get("lifecycle_claim", {}).get("terminal_closure_declared_irreversible") is not False:
        errors.append("expanded-history audit must not freeze irreversible closure semantics")
    return errors
