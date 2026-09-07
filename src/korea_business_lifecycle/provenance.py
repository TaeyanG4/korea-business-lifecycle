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


def load_grain_decision() -> dict[str, Any]:
    return load_json("provenance/grain_decision.json")


def load_permit_parent_compatibility() -> dict[str, Any]:
    return load_json("provenance/permit_parent_compatibility.json")


def load_permit_parent_full_dry_run_plan() -> dict[str, Any]:
    return load_json("provenance/permit_parent_full_dry_run_plan.json")


def load_permit_parent_full_dry_run() -> dict[str, Any]:
    return load_json("provenance/permit_parent_full_dry_run.json")


def load_permit_parent_materialization_plan() -> dict[str, Any]:
    return load_json("provenance/permit_parent_materialization_plan.json")


def load_permit_parent_materialization() -> dict[str, Any]:
    return load_json("provenance/permit_parent_materialization.json")


def load_geospatial_axis_probe() -> dict[str, Any]:
    return load_json("provenance/geospatial_axis_probe.json")


def load_geospatial_full_axis_plan() -> dict[str, Any]:
    return load_json("provenance/geospatial_full_axis_plan.json")


def load_geospatial_full_axis() -> dict[str, Any]:
    return load_json("provenance/geospatial_full_axis.json")


def load_permit_geospatial_materialization_plan() -> dict[str, Any]:
    return load_json("provenance/permit_geospatial_materialization_plan.json")


def load_permit_geospatial_materialization() -> dict[str, Any]:
    return load_json("provenance/permit_geospatial_materialization.json")


def load_public_permit_aggregate_plan() -> dict[str, Any]:
    return load_json("provenance/public_permit_aggregate_plan.json")


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
    if review.get("decision") != "SOURCE_USE_LICENSE_LABELS_CONFIRMED_KAGGLE_REDISTRIBUTION_UNRESOLVED":
        errors.append("license-review decision changed")
    refresh = review.get("evidence_refresh", {})
    if refresh.get("official_detail_pages_reviewed") != 3:
        errors.append("license review must record all three official detail pages")
    if refresh.get("all_three_show_no_restriction_label") is not True:
        errors.append("license review must retain the observed no-restriction labels")
    if refresh.get("source_use_license_gate") != "PASS_METADATA_CONFIRMED":
        errors.append("source-use license metadata gate changed")
    if refresh.get("raw_external_mirror_gate") != "UNRESOLVED_THIRD_PARTY_RIGHTS_CLARIFICATION":
        errors.append("raw external mirror gate must remain unresolved")
    if refresh.get("privacy_minimized_aggregate_redistribution_gate") != "UNRESOLVED":
        errors.append("aggregate redistribution gate must remain unresolved")
    if refresh.get("absence_of_source_specific_third_party_statement_is_proof_of_no_third_party_rights") is not False:
        errors.append("absence of a third-party statement must not be promoted to proof")
    categories = review.get("categories", [])
    keys = {item.get("source_key") for item in categories}
    if keys != V1_SOURCE_KEYS:
        errors.append(f"license-review source keys mismatch: {sorted(keys)}")
    for item in categories:
        if item.get("official_license_label") != "이용허락범위 제한 없음":
            errors.append(f"{item.get('source_key')}: official no-restriction label changed")
        if item.get("source_use_license") != "PASS_METADATA_CONFIRMED":
            errors.append(f"{item.get('source_key')}: source-use metadata gate changed")
        if item.get("kaggle_redistribution") != "UNRESOLVED":
            errors.append(f"{item.get('source_key')}: redistribution must remain unresolved")
        if item.get("third_party_rights") != "NO_SOURCE_SPECIFIC_STATEMENT_IDENTIFIED_REVIEW_REQUIRED":
            errors.append(f"{item.get('source_key')}: third-party-rights review state changed")
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


def validate_grain_decision(decision: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if decision.get("decision") != "V1_GRAIN_FROZEN_PERMIT_PARENT_WITH_REVERSIBLE_STATUS_EPISODES":
        errors.append("v1 grain decision changed")
    if set(decision.get("scope", {}).get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("grain-decision scope must exactly match the three v1 sources")

    selected = decision.get("selected_grains", {})
    if selected.get("canonical_parent_grain", {}).get("name") != "PERMIT":
        errors.append("canonical parent grain must remain PERMIT")
    lifecycle = selected.get("lifecycle_analysis_grain", {})
    if lifecycle.get("name") != "PERMIT_STATUS_EPISODE":
        errors.append("lifecycle analysis grain must remain PERMIT_STATUS_EPISODE")
    if lifecycle.get("schema") != "schemas/permit_status_episode.v1.json":
        errors.append("lifecycle analysis schema reference changed")
    if lifecycle.get("schema_status") != "FROZEN":
        errors.append("permit status episode schema must remain frozen")
    if lifecycle.get("production_reconstruction_enabled") is not False:
        errors.append("production episode reconstruction must remain disabled at this gate")

    rejected = {item.get("name"): item.get("status") for item in decision.get("rejected_grains", [])}
    if rejected.get("ESTABLISHMENT_CATEGORY_EPISODE") != "REJECTED_FOR_V1":
        errors.append("establishment-category episode grain must remain rejected for v1")
    if rejected.get("SINGLE_TERMINAL_SURVIVAL_ROW") != "REJECTED":
        errors.append("single terminal survival row must remain rejected")

    identity = decision.get("identity_policy", {})
    for key in (
        "source_primary_key_declared",
        "mng_no_primary_key_declared",
        "establishment_identity_declared",
        "cross_permit_entity_resolution_allowed",
    ):
        if identity.get(key) is not False:
            errors.append(f"grain decision must keep {key}=false")

    semantics = decision.get("episode_semantics", {})
    if semantics.get("exact_transition_time_claimed_from_sparse_snapshots") is not False:
        errors.append("sparse episode transitions must remain interval-censored")
    if semantics.get("active_end_observations") != "right-censored":
        errors.append("active episode endpoints must remain right-censored")
    if semantics.get("closure_code_03_irreversible") is not False:
        errors.append("status code 03 must remain reversible in the grain decision")
    if semantics.get("closure_date_permanent_terminal_event") is not False:
        errors.append("closure date must not be promoted to a permanent terminal event")
    if semantics.get("status_code_05_semantics_resolved") is not False:
        errors.append("status code 05 must remain unresolved at this gate")

    evidence = decision.get("evidence", {})
    if evidence.get("current_snapshot_rows") != 3_010_802:
        errors.append("grain decision current-snapshot evidence changed")
    if evidence.get("bounded_history_pairs_with_strong_mng_no_continuity") != 15:
        errors.append("grain decision continuity evidence changed")
    if evidence.get("confirmed_03_to_01_reversals") != 2:
        errors.append("grain decision reversal evidence changed")
    if evidence.get("bounded_geospatial_axis_probe") != "provenance/geospatial_axis_probe.json":
        errors.append("grain decision bounded geospatial evidence reference changed")
    if evidence.get("bounded_geospatial_axis_assessment") != (
        "SOURCE_X_AS_EASTING_Y_AS_NORTHING_STRONGLY_PREFERRED"
    ):
        errors.append("grain decision bounded geospatial assessment changed")
    if evidence.get("full_geospatial_axis_plan") != "provenance/geospatial_full_axis_plan.json":
        errors.append("grain decision full geospatial axis plan reference changed")
    if evidence.get("full_geospatial_axis_result") != "provenance/geospatial_full_axis.json":
        errors.append("grain decision full geospatial axis result reference changed")
    if evidence.get("full_geospatial_axis_status") != "PASSED_REVIEWED_CURRENT_V1":
        errors.append("grain decision full geospatial axis status changed")
    if evidence.get("coordinate_axis_order_verified_nationwide") is not True:
        errors.append("grain decision must record completed current-v1 nationwide axis verification")
    if evidence.get("source_x_interpretation") != "EASTING":
        errors.append("grain decision source X interpretation changed")
    if evidence.get("source_y_interpretation") != "NORTHING":
        errors.append("grain decision source Y interpretation changed")
    if evidence.get("local_wgs84_generation_approved") is not True:
        errors.append("grain decision must approve local WGS84 derivation after reviewed full QA")
    if evidence.get("public_wgs84_release_approved") is not False:
        errors.append("grain decision must keep public WGS84 release blocked")

    next_gate = decision.get("next_gate", {})
    if next_gate.get("permit_parent_schema") != "schemas/permit_parent.v1.json":
        errors.append("permit parent schema gate reference changed")
    if next_gate.get("permit_parent_schema_status") != "FROZEN":
        errors.append("permit parent schema must remain frozen")
    if next_gate.get("permit_status_episode_schema") != "schemas/permit_status_episode.v1.json":
        errors.append("permit status episode schema gate reference changed")
    if next_gate.get("permit_status_episode_schema_status") != "FROZEN":
        errors.append("permit status episode schema gate must remain frozen")
    if next_gate.get("phase") != "Phase 7 Publication Safety Review":
        errors.append("next gate must be Phase 7 publication safety review")
    if next_gate.get("permit_parent_transformer") != "src/korea_business_lifecycle/canonical_permit.py":
        errors.append("permit parent transformer reference changed")
    if next_gate.get("permit_parent_transformer_status") != "FULL_SNAPSHOT_VALIDATED":
        errors.append("permit parent transformer must remain full-snapshot validated at this gate")
    if next_gate.get("permit_parent_compatibility") != "provenance/permit_parent_compatibility.json":
        errors.append("permit parent compatibility provenance reference changed")
    if next_gate.get("permit_parent_compatibility_status") != "PASSED_256_ROWS_PER_SOURCE":
        errors.append("permit parent compatibility gate status changed")
    if next_gate.get("permit_parent_full_dry_run_plan") != (
        "provenance/permit_parent_full_dry_run_plan.json"
    ):
        errors.append("permit parent full dry-run plan reference changed")
    if next_gate.get("permit_parent_full_dry_run") != "provenance/permit_parent_full_dry_run.json":
        errors.append("permit parent full dry-run provenance reference changed")
    if next_gate.get("permit_parent_full_dry_run_status") != "PASSED_3010802_ROWS":
        errors.append("permit parent full dry-run pass status changed")
    if next_gate.get("permit_parent_materialization_plan") != "provenance/permit_parent_materialization_plan.json":
        errors.append("permit parent materialization plan reference changed")
    if next_gate.get("permit_parent_materialization") != "provenance/permit_parent_materialization.json":
        errors.append("permit parent materialization result reference changed")
    if next_gate.get("permit_parent_materialization_status") != "COMPLETED_PASS_VERIFIED":
        errors.append("permit parent materialization status changed")
    if next_gate.get("geospatial_full_axis") != "provenance/geospatial_full_axis.json":
        errors.append("geospatial full-axis result reference changed")
    if next_gate.get("geospatial_full_axis_status") != "PASSED_REVIEWED_CURRENT_V1":
        errors.append("geospatial full-axis status changed")
    if next_gate.get("permit_geospatial_schema") != "schemas/permit_geospatial.v1.json":
        errors.append("permit geospatial schema gate reference changed")
    if next_gate.get("permit_geospatial_schema_status") != "FROZEN":
        errors.append("permit geospatial schema must remain frozen")
    if next_gate.get("permit_geospatial_materialization_plan") != (
        "provenance/permit_geospatial_materialization_plan.json"
    ):
        errors.append("permit geospatial materialization plan reference changed")
    if next_gate.get("permit_geospatial_materialization") != (
        "provenance/permit_geospatial_materialization.json"
    ):
        errors.append("permit geospatial materialization result reference changed")
    if next_gate.get("permit_geospatial_materialization_status") != "COMPLETED_PASS_VERIFIED":
        errors.append("permit geospatial materialization status changed")
    if next_gate.get("public_permit_aggregate_schema") != "schemas/public_permit_aggregate.v1.json":
        errors.append("public permit aggregate schema reference changed")
    if next_gate.get("public_permit_aggregate_schema_status") != "FROZEN_CANDIDATE":
        errors.append("public permit aggregate schema status changed")
    if next_gate.get("public_permit_aggregate_plan") != "provenance/public_permit_aggregate_plan.json":
        errors.append("public permit aggregate plan reference changed")
    if next_gate.get("public_permit_aggregate_status") != "IMPLEMENTED_NOT_EXECUTED":
        errors.append("public permit aggregate status changed")
    return errors


def validate_permit_parent_compatibility(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("decision") != "BOUNDED_REAL_CURRENT_SNAPSHOT_COMPATIBILITY_PASSED":
        errors.append("bounded real-snapshot compatibility decision changed")

    scope = review.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("permit compatibility scope must exactly match v1 sources")
    if scope.get("sample_policy") != "HEAD_ROWS_AFTER_HEADER":
        errors.append("permit compatibility sample policy changed")
    if scope.get("max_rows_per_source") != 256:
        errors.append("permit compatibility bounded row cap changed")
    for key in (
        "production_materialization_performed",
        "full_snapshot_scan_performed",
        "row_level_values_recorded",
    ):
        if scope.get(key) is not False:
            errors.append(f"permit compatibility must keep {key}=false")

    contracts = review.get("contracts", {})
    if contracts.get("permit_parent_schema") != "schemas/permit_parent.v1.json":
        errors.append("permit compatibility parent schema reference changed")
    if contracts.get("permit_parent_transformer") != "src/korea_business_lifecycle/canonical_permit.py":
        errors.append("permit compatibility transformer reference changed")
    if contracts.get("compatibility_validator") != (
        "src/korea_business_lifecycle/canonical_compatibility.py"
    ):
        errors.append("permit compatibility validator reference changed")

    results = review.get("results", [])
    if {item.get("source_key") for item in results} != V1_SOURCE_KEYS or len(results) != 3:
        errors.append("permit compatibility must contain exactly three v1 source results")
    for item in results:
        source_key = item.get("source_key")
        if item.get("status") != "PASS":
            errors.append(f"{source_key}: bounded compatibility did not pass")
        if item.get("rows_examined") != 256 or item.get("rows_transformed") != 256:
            errors.append(f"{source_key}: bounded compatibility row count changed")
        if item.get("source_column_count") != 39 or item.get("output_column_count") != 26:
            errors.append(f"{source_key}: source/canonical column count changed")
        if item.get("encoding") != "cp949":
            errors.append(f"{source_key}: observed bounded compatibility encoding changed")
        if item.get("duplicate_linkage_candidates") != 0:
            errors.append(f"{source_key}: duplicate linkage candidate observed in bounded sample")
        if sum(item.get("permit_date_quality", {}).values()) != 256:
            errors.append(f"{source_key}: permit-date quality counts do not sum to sample size")
        if sum(item.get("closure_date_quality", {}).values()) != 256:
            errors.append(f"{source_key}: closure-date quality counts do not sum to sample size")

    aggregate = review.get("aggregate", {})
    if aggregate.get("rows_examined") != 768 or aggregate.get("rows_transformed") != 768:
        errors.append("permit compatibility aggregate row count changed")
    if aggregate.get("duplicate_linkage_candidates") != 0:
        errors.append("permit compatibility aggregate duplicate count changed")
    if aggregate.get("all_sources_passed") is not True:
        errors.append("permit compatibility aggregate pass flag changed")

    privacy = review.get("privacy", {})
    for key in (
        "management_numbers_recorded",
        "business_names_recorded",
        "addresses_recorded",
        "telephone_numbers_recorded",
        "coordinate_values_recorded",
    ):
        if privacy.get(key) is not False:
            errors.append(f"permit compatibility provenance must keep {key}=false")
    return errors


def validate_permit_parent_full_dry_run_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("decision") != "FULL_CURRENT_SNAPSHOT_DRY_RUN_IMPLEMENTED_USER_EXECUTION_REQUIRED":
        errors.append("full current-snapshot dry-run plan decision changed")

    scope = plan.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("full dry-run plan must exactly cover v1 sources")
    if scope.get("expected_rows_total") != 3_010_802:
        errors.append("full dry-run expected row total changed")
    if scope.get("network_access_required") is not False:
        errors.append("full dry-run must remain local-only")
    if scope.get("production_materialization_performed") is not False:
        errors.append("full dry-run must not materialize production canonical output")
    if scope.get("row_level_values_recorded") is not False:
        errors.append("full dry-run plan must not record row-level values")
    if scope.get("execution_status") != "COMPLETED_PASS":
        errors.append("full dry-run plan must record the completed passing user execution")

    implementation = plan.get("implementation", {})
    if implementation.get("module") != "src/korea_business_lifecycle/canonical_full_dry_run.py":
        errors.append("full dry-run module reference changed")
    if implementation.get("script") != "scripts/dry_run_full_current_snapshot.py":
        errors.append("full dry-run script reference changed")
    if implementation.get("default_progress_every_rows") != 50_000:
        errors.append("full dry-run default progress interval changed")
    if implementation.get("uniqueness_backend") != "EPHEMERAL_SQLITE_EXACT_TEXT_PRIMARY_KEY":
        errors.append("full dry-run exact uniqueness backend changed")
    if implementation.get("temporary_state_git_ignored") is not True:
        errors.append("full dry-run temporary uniqueness state must remain Git-ignored")
    if implementation.get("temporary_state_removed_on_normal_completion_or_handled_failure") is not True:
        errors.append("full dry-run temporary uniqueness state cleanup contract changed")

    artifacts = plan.get("expected_artifacts", [])
    if {item.get("source_key") for item in artifacts} != V1_SOURCE_KEYS or len(artifacts) != 3:
        errors.append("full dry-run expected artifacts must exactly cover three v1 sources")
    if sum(int(item.get("expected_rows", 0)) for item in artifacts) != 3_010_802:
        errors.append("full dry-run per-source row totals changed")
    if sum(int(item.get("artifact_bytes", 0)) for item in artifacts) != 926_587_446:
        errors.append("full dry-run expected artifact byte total changed")
    if any(len(str(item.get("artifact_sha256", ""))) != 64 for item in artifacts):
        errors.append("full dry-run expected artifact hashes are invalid")

    execution = plan.get("execution", {})
    if execution.get("execute_command") != "python scripts/dry_run_full_current_snapshot.py --execute":
        errors.append("full dry-run execute command changed")
    if execution.get("progress_stream") != "stderr":
        errors.append("full dry-run progress must remain on stderr")
    if execution.get("final_aggregate_json_stream") != "stdout":
        errors.append("full dry-run final aggregate JSON must remain on stdout")
    if plan.get("result_provenance") != "provenance/permit_parent_full_dry_run.json":
        errors.append("full dry-run result provenance reference changed")

    privacy = plan.get("privacy", {})
    for key in (
        "management_numbers_in_stdout_or_stderr",
        "business_names_in_stdout_or_stderr",
        "addresses_in_stdout_or_stderr",
        "telephone_numbers_in_stdout_or_stderr",
        "coordinate_values_in_stdout_or_stderr",
        "canonical_rows_written",
    ):
        if privacy.get(key) is not False:
            errors.append(f"full dry-run privacy contract must keep {key}=false")
    return errors


def validate_permit_parent_full_dry_run(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("decision") != "FULL_CURRENT_SNAPSHOT_DRY_RUN_PASSED":
        errors.append("full current-snapshot dry-run decision changed")
    scope = review.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("full dry-run scope must exactly match v1 sources")
    if scope.get("expected_rows_total") != 3_010_802:
        errors.append("full dry-run expected row total changed")
    if scope.get("rows_examined_total") != 3_010_802 or scope.get("rows_transformed_total") != 3_010_802:
        errors.append("full dry-run transformed row total changed")
    if scope.get("full_snapshot_scan_performed") is not True:
        errors.append("full dry-run must record completed full snapshot scan")
    if scope.get("production_materialization_performed") is not False:
        errors.append("full dry-run must not claim production materialization")
    if scope.get("row_level_values_recorded") is not False:
        errors.append("full dry-run provenance must remain aggregate-only")

    results = review.get("results", [])
    expected_rows = {
        "general_restaurants": 2_295_369,
        "rest_cafes": 645_952,
        "bakeries": 69_481,
    }
    if {item.get("source_key") for item in results} != V1_SOURCE_KEYS or len(results) != 3:
        errors.append("full dry-run must contain exactly three v1 source results")
    for item in results:
        source_key = item.get("source_key")
        expected = expected_rows.get(source_key)
        if item.get("status") != "PASS":
            errors.append(f"{source_key}: full dry-run did not pass")
        if expected is None or item.get("rows_examined") != expected or item.get("rows_transformed") != expected:
            errors.append(f"{source_key}: full dry-run row count changed")
        if item.get("source_column_count") != 39 or item.get("output_column_count") != 26:
            errors.append(f"{source_key}: full dry-run column contract changed")
        if item.get("encoding") != "cp949":
            errors.append(f"{source_key}: full dry-run encoding changed")
        if item.get("duplicate_linkage_candidates") != 0:
            errors.append(f"{source_key}: full dry-run uniqueness invariant failed")
        if item.get("temporary_uniqueness_index_removed") is not True:
            errors.append(f"{source_key}: full dry-run temporary uniqueness index was not removed")
        if expected is not None and sum(item.get("permit_date_quality", {}).values()) != expected:
            errors.append(f"{source_key}: permit-date quality counts do not sum to full source rows")
        if expected is not None and sum(item.get("closure_date_quality", {}).values()) != expected:
            errors.append(f"{source_key}: closure-date quality counts do not sum to full source rows")

    aggregate = review.get("aggregate", {})
    if aggregate.get("rows_examined") != 3_010_802 or aggregate.get("rows_transformed") != 3_010_802:
        errors.append("full dry-run aggregate row total changed")
    if aggregate.get("permit_date_quality") != {"INVALID": 4, "VALID": 3_010_798}:
        errors.append("full dry-run permit-date quality aggregate changed")
    if aggregate.get("closure_date_quality") != {"MISSING": 895_118, "VALID": 2_115_684}:
        errors.append("full dry-run closure-date quality aggregate changed")
    if aggregate.get("duplicate_linkage_candidates") != 0:
        errors.append("full dry-run aggregate uniqueness result changed")
    if aggregate.get("all_sources_passed") is not True:
        errors.append("full dry-run aggregate pass flag changed")
    if aggregate.get("all_temporary_uniqueness_indexes_removed") is not True:
        errors.append("full dry-run temporary-state cleanup flag changed")

    privacy = review.get("privacy", {})
    for key in (
        "management_numbers_recorded",
        "business_names_recorded",
        "addresses_recorded",
        "telephone_numbers_recorded",
        "coordinate_values_recorded",
    ):
        if privacy.get(key) is not False:
            errors.append(f"full dry-run provenance must keep {key}=false")
    return errors


def validate_permit_parent_materialization_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("decision") != "LOCAL_PRODUCTION_PERMIT_MATERIALIZER_IMPLEMENTATION_GATE":
        errors.append("permit parent materialization plan decision changed")
    scope = plan.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("materialization plan scope must exactly match v1 sources")
    if scope.get("expected_rows_total") != 3_010_802:
        errors.append("materialization plan expected row total changed")
    if scope.get("input_evidence") != "provenance/permit_parent_full_dry_run.json":
        errors.append("materialization plan input evidence changed")
    if scope.get("git_ignored") is not True:
        errors.append("materialization output must remain Git-ignored")
    if scope.get("public_row_level_release_approved") is not False:
        errors.append("materialization plan must keep public row-level release blocked")
    if scope.get("execution_status") != "COMPLETED_PASS_VERIFIED":
        errors.append("tracked materialization plan must record completed verified execution")

    writer = plan.get("writer_contract", {})
    expected_writer = {
        "library": "pyarrow",
        "library_version": "21.0.0",
        "format": "PARQUET",
        "parquet_version": "2.6",
        "compression": "ZSTD",
        "compression_level": 9,
        "data_page_version": "2.0",
        "rows_per_batch": 50_000,
        "rows_per_row_group": 50_000,
        "files": "one Parquet file per source plus one local build manifest",
    }
    if writer != expected_writer:
        errors.append("materialization writer contract changed")

    safety = plan.get("safety", {})
    for key in (
        "recompute_input_sha256_before_write",
        "require_exact_full_dry_run_artifact_hashes",
        "require_full_dry_run_duplicate_count_zero",
        "reuse_uniqueness_proof_only_for_identical_sha256",
        "fail_if_final_build_directory_exists",
        "write_to_unique_staging_directory_first",
        "remove_staging_directory_on_handled_failure",
    ):
        if safety.get(key) is not True:
            errors.append(f"materialization safety control {key} must remain enabled")
    for key in (
        "canonical_status_mapping_enabled",
        "wgs84_generation_enabled",
        "episode_reconstruction_enabled",
    ):
        if safety.get(key) is not False:
            errors.append(f"materialization safety control {key} must remain disabled")

    implementation = plan.get("implementation", {})
    if implementation.get("module") != "src/korea_business_lifecycle/canonical_materialization.py":
        errors.append("materialization module reference changed")
    if implementation.get("script") != "scripts/materialize_permit_parent.py":
        errors.append("materialization script reference changed")
    if implementation.get("verification_module") != (
        "src/korea_business_lifecycle/canonical_materialization_verify.py"
    ):
        errors.append("materialization verification module reference changed")
    if implementation.get("verification_script") != "scripts/verify_permit_parent_build.py":
        errors.append("materialization verification script reference changed")
    if implementation.get("default_mode") != "PLAN_ONLY":
        errors.append("materialization default mode changed")
    if implementation.get("execute_flag") != "--execute":
        errors.append("materialization execute flag changed")
    if plan.get("result_provenance") != "provenance/permit_parent_materialization.json":
        errors.append("materialization result provenance reference changed")
    return errors


def validate_permit_parent_materialization(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("decision") != "LOCAL_PRODUCTION_PERMIT_PARENT_MATERIALIZED_AND_VERIFIED":
        errors.append("permit materialization decision changed")
    scope = review.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("permit materialization scope must exactly match v1 sources")
    if scope.get("build_id") != "permit-v1-9908225df465e2ff":
        errors.append("permit materialization build id changed")
    if scope.get("rows_total") != 3_010_802:
        errors.append("permit materialization row total changed")
    if scope.get("output_bytes_total") != 165_176_236:
        errors.append("permit materialization output byte total changed")
    if scope.get("git_ignored") is not True:
        errors.append("permit materialization output must remain Git-ignored")
    for key in ("public_row_level_release_approved", "wgs84_generated", "episode_reconstruction_performed"):
        if scope.get(key) is not False:
            errors.append(f"permit materialization must keep {key}=false")

    verification = review.get("verification", {})
    for key in (
        "manifest_verified",
        "parquet_hashes_verified",
        "parquet_schemas_verified",
        "quality_aggregates_match_full_dry_run",
        "zstd_verified",
    ):
        if verification.get(key) is not True:
            errors.append(f"permit materialization verification {key} must remain true")
    if verification.get("rows_verified_total") != 3_010_802:
        errors.append("permit materialization verified row total changed")
    if verification.get("row_level_values_recorded") is not False:
        errors.append("permit materialization provenance must remain aggregate-only")

    results = review.get("results", [])
    expected_rows = {
        "general_restaurants": 2_295_369,
        "rest_cafes": 645_952,
        "bakeries": 69_481,
    }
    if {item.get("source_key") for item in results} != V1_SOURCE_KEYS or len(results) != 3:
        errors.append("permit materialization results must exactly cover three v1 sources")
    if sum(int(item.get("rows", 0)) for item in results) != 3_010_802:
        errors.append("permit materialization result rows do not sum to full scope")
    if sum(int(item.get("output_bytes", 0)) for item in results) != 165_176_236:
        errors.append("permit materialization result bytes do not sum to verified total")
    for item in results:
        source_key = item.get("source_key")
        if item.get("rows") != expected_rows.get(source_key):
            errors.append(f"{source_key}: materialized row count changed")
        if item.get("status") != "PASS":
            errors.append(f"{source_key}: materialization status changed")
        if len(str(item.get("output_sha256", ""))) != 64:
            errors.append(f"{source_key}: materialization output SHA-256 invalid")
    return errors


def validate_geospatial_axis_probe(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("decision") != (
        "BOUNDED_AXIS_EVIDENCE_X_EASTING_Y_NORTHING_STRONGLY_PREFERRED_WGS84_STILL_BLOCKED"
    ):
        errors.append("bounded geospatial axis decision changed")

    scope = review.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("bounded geospatial axis scope must exactly match v1 sources")
    if scope.get("declared_source_crs") != "EPSG:5174":
        errors.append("bounded geospatial axis CRS reference changed")
    if scope.get("sample_policy") != "FIRST_NONBLANK_COORDINATE_PAIRS_AFTER_HEADER":
        errors.append("bounded geospatial sample policy changed")
    if scope.get("max_coordinate_pairs_per_source") != 5_000:
        errors.append("bounded geospatial per-source sample size changed")
    if scope.get("coordinate_pairs_sampled_total") != 15_000:
        errors.append("bounded geospatial total sample size changed")
    for key in (
        "coordinate_axis_order_verified_nationwide",
        "wgs84_generation_approved",
        "row_level_coordinate_values_recorded",
        "row_level_address_values_recorded",
    ):
        if scope.get(key) is not False:
            errors.append(f"bounded geospatial gate must keep {key}=false")

    software = review.get("software", {})
    if software.get("pyproj_version") != "3.7.2":
        errors.append("bounded geospatial pyproj version changed")
    if software.get("proj_version") != "9.5.1":
        errors.append("bounded geospatial PROJ version changed")

    crs_reference = review.get("crs_reference", {})
    if crs_reference.get("authority") != "EPSG:5174":
        errors.append("bounded geospatial EPSG authority changed")
    if crs_reference.get("formal_axis_1", {}).get("direction") != "north":
        errors.append("EPSG:5174 formal first-axis direction changed")
    if crs_reference.get("formal_axis_2", {}).get("direction") != "east":
        errors.append("EPSG:5174 formal second-axis direction changed")

    results = review.get("results", [])
    if {item.get("source_key") for item in results} != V1_SOURCE_KEYS or len(results) != 3:
        errors.append("bounded geospatial results must contain exactly three v1 sources")
    for item in results:
        source_key = item.get("source_key")
        if item.get("coordinate_pairs_sampled") != 5_000:
            errors.append(f"{source_key}: bounded geospatial sample count changed")
        if item.get("broad_korea_candidate_a_inside") != 5_000:
            errors.append(f"{source_key}: candidate A broad plausibility count changed")
        if item.get("broad_korea_candidate_b_inside") != 5_000:
            errors.append(f"{source_key}: candidate B broad plausibility count changed")
        if item.get("macro_region_eligible_pairs") != 5_000:
            errors.append(f"{source_key}: macro-region eligible count changed")
        if item.get("macro_region_candidate_a_match") != 5_000:
            errors.append(f"{source_key}: candidate A macro-region match count changed")
        if item.get("macro_region_candidate_b_match") != 0:
            errors.append(f"{source_key}: candidate B macro-region match count changed")
        if item.get("assessment") != "SOURCE_X_AS_EASTING_Y_AS_NORTHING_STRONGLY_PREFERRED":
            errors.append(f"{source_key}: bounded geospatial axis assessment changed")

    aggregate = review.get("aggregate", {})
    if aggregate.get("coordinate_pairs_sampled") != 15_000:
        errors.append("bounded geospatial aggregate sample count changed")
    if aggregate.get("macro_region_candidate_a_match") != 15_000:
        errors.append("bounded geospatial aggregate candidate A match count changed")
    if aggregate.get("macro_region_candidate_b_match") != 0:
        errors.append("bounded geospatial aggregate candidate B match count changed")
    if aggregate.get("assessment_consistent_across_sources") is not True:
        errors.append("bounded geospatial assessment must remain consistent across sources")
    if aggregate.get("assessment") != "SOURCE_X_AS_EASTING_Y_AS_NORTHING_STRONGLY_PREFERRED":
        errors.append("bounded geospatial aggregate assessment changed")
    if review.get("full_snapshot_plan") != "provenance/geospatial_full_axis_plan.json":
        errors.append("bounded geospatial full-snapshot plan reference changed")
    return errors


def validate_geospatial_full_axis_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("decision") != "FULL_SNAPSHOT_GEOSPATIAL_AXIS_VALIDATOR_IMPLEMENTED_USER_EXECUTION_REQUIRED":
        errors.append("full geospatial axis plan decision changed")
    scope = plan.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("full geospatial axis plan must exactly cover v1 sources")
    if scope.get("expected_rows_total") != 3_010_802:
        errors.append("full geospatial axis expected row total changed")
    if scope.get("expected_coordinate_pairs_total_from_prior_profile") != 2_811_767:
        errors.append("full geospatial axis expected coordinate-pair total changed")
    if scope.get("declared_source_crs") != "EPSG:5174":
        errors.append("full geospatial axis declared CRS changed")
    if scope.get("execution_status") != "COMPLETED_PASS_REVIEWED":
        errors.append("tracked full geospatial axis plan must record completed reviewed execution")
    for key in (
        "network_access_required",
        "row_level_coordinate_values_recorded",
        "row_level_address_values_recorded",
        "wgs84_columns_generated",
    ):
        if scope.get(key) is not False:
            errors.append(f"full geospatial axis plan must keep {key}=false")

    input_gate = plan.get("input_gate", {})
    if input_gate.get("approved_evidence") != "provenance/permit_parent_full_dry_run.json":
        errors.append("full geospatial axis approved input evidence changed")
    for key in (
        "require_exact_retrieval_id",
        "require_exact_artifact_bytes",
        "require_exact_artifact_sha256",
        "recompute_artifact_sha256_before_scan",
    ):
        if input_gate.get(key) is not True:
            errors.append(f"full geospatial axis input gate {key} must remain enabled")

    method = plan.get("method", {})
    if method.get("name") != "FULL_SNAPSHOT_AGGREGATE_AXIS_COMPARISON_WITH_COARSE_ADDRESS_MACRO_REGIONS":
        errors.append("full geospatial axis method changed")
    if method.get("progress_every_rows") != 50_000:
        errors.append("full geospatial axis progress interval changed")
    if method.get("software", {}).get("pyproj_version") != "3.7.2":
        errors.append("full geospatial axis pyproj version changed")

    artifacts = plan.get("expected_artifacts", [])
    if {item.get("source_key") for item in artifacts} != V1_SOURCE_KEYS or len(artifacts) != 3:
        errors.append("full geospatial axis expected artifacts must exactly cover v1 sources")
    if sum(int(item.get("expected_rows", 0)) for item in artifacts) != 3_010_802:
        errors.append("full geospatial axis source row totals changed")
    if sum(int(item.get("artifact_bytes", 0)) for item in artifacts) != 926_587_446:
        errors.append("full geospatial axis artifact byte total changed")

    execution = plan.get("execution", {})
    if execution.get("execute_command") != "python scripts/validate_full_coordinate_axis.py --execute":
        errors.append("full geospatial axis execute command changed")
    if execution.get("progress_stream") != "stderr":
        errors.append("full geospatial axis progress stream changed")
    if execution.get("final_aggregate_json_stream") != "stdout":
        errors.append("full geospatial axis result stream changed")

    policy = plan.get("interpretation_policy", {})
    if policy.get("coordinate_axis_order_verified_nationwide_before_execution") is not False:
        errors.append("full geospatial axis plan must not pre-verify nationwide axis order")
    if policy.get("wgs84_generation_approved_before_execution") is not False:
        errors.append("full geospatial axis plan must keep WGS84 blocked before execution")
    if policy.get("full_scan_pass_alone_does_not_approve_publication") is not True:
        errors.append("full geospatial axis scan must remain separate from publication approval")
    if policy.get("result_requires_review_before_schema_metadata_change") is not True:
        errors.append("full geospatial axis result must require review before schema change")
    if plan.get("result_provenance") != "provenance/geospatial_full_axis.json":
        errors.append("full geospatial axis result provenance reference changed")
    return errors


def validate_geospatial_full_axis(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("decision") != (
        "FULL_SNAPSHOT_AXIS_QA_PASSED_X_EASTING_Y_NORTHING_APPROVED_FOR_LOCAL_DERIVATION"
    ):
        errors.append("full geospatial axis review decision changed")
    scope = review.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("full geospatial axis review must exactly cover v1 sources")
    if scope.get("rows_examined_total") != 3_010_802:
        errors.append("full geospatial axis reviewed row total changed")
    if scope.get("coordinate_pairs_total") != 2_811_767:
        errors.append("full geospatial axis coordinate-pair total changed")
    if scope.get("macro_region_eligible_pairs_total") != 2_631_605:
        errors.append("full geospatial axis eligible-pair total changed")
    if scope.get("declared_source_crs") != "EPSG:5174":
        errors.append("full geospatial axis reviewed CRS changed")
    for key in ("row_level_coordinate_values_recorded", "row_level_address_values_recorded", "wgs84_columns_generated"):
        if scope.get(key) is not False:
            errors.append(f"full geospatial axis review must keep {key}=false")
    if scope.get("future_snapshot_revalidation_required") is not True:
        errors.append("future geospatial snapshots must require revalidation")

    method = review.get("method", {})
    if method.get("candidate_a_match") != 2_630_497:
        errors.append("full geospatial candidate A match count changed")
    if method.get("candidate_b_match") != 686_673:
        errors.append("full geospatial candidate B match count changed")
    if method.get("candidate_a_only_match") != 1_943_824:
        errors.append("full geospatial candidate A-only count changed")
    if method.get("candidate_b_only_match") != 0:
        errors.append("full geospatial candidate B-only count changed")
    if method.get("neither_match") != 1_108:
        errors.append("full geospatial neither-match count changed")
    if method.get("assessment_consistent_across_sources") is not True:
        errors.append("full geospatial assessment must remain consistent across sources")
    if method.get("assessment") != "SOURCE_X_AS_EASTING_Y_AS_NORTHING_STRONGLY_PREFERRED":
        errors.append("full geospatial assessment changed")

    results = review.get("results", [])
    if {item.get("source_key") for item in results} != V1_SOURCE_KEYS or len(results) != 3:
        errors.append("full geospatial results must exactly cover three v1 sources")
    if sum(int(item.get("coordinate_pairs", 0)) for item in results) != 2_811_767:
        errors.append("full geospatial source coordinate-pair counts do not sum")
    if any(item.get("partial_coordinate_pairs") != 0 for item in results):
        errors.append("full geospatial review observed partial coordinate pairs")
    if any(item.get("candidate_b_only_match") != 0 for item in results):
        errors.append("full geospatial review observed candidate-B-only matches")
    if any(item.get("status") != "PASS" for item in results):
        errors.append("full geospatial review contains a non-passing source")

    reviewed = review.get("review", {})
    if reviewed.get("source_x_interpretation") != "EASTING":
        errors.append("reviewed source X interpretation changed")
    if reviewed.get("source_y_interpretation") != "NORTHING":
        errors.append("reviewed source Y interpretation changed")
    if reviewed.get("coordinate_axis_order_verified_nationwide") is not True:
        errors.append("reviewed current-v1 axis order must remain verified")
    if reviewed.get("local_wgs84_derivation_approved") is not True:
        errors.append("reviewed full geospatial result must approve local WGS84 derivation")
    if reviewed.get("public_wgs84_release_approved") is not False:
        errors.append("reviewed full geospatial result must keep public WGS84 release blocked")
    if reviewed.get("frozen_permit_parent_schema_mutated") is not False:
        errors.append("geospatial review must not mutate the frozen PERMIT parent schema")
    return errors


def validate_permit_geospatial_materialization_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("decision") != "LOCAL_WGS84_PERMIT_ENRICHMENT_IMPLEMENTED_AND_VERIFIED":
        errors.append("permit geospatial materialization plan decision changed")

    scope = plan.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("permit geospatial materialization scope must exactly match v1 sources")
    if scope.get("parent_permit_build_id") != "permit-v1-9908225df465e2ff":
        errors.append("permit geospatial parent build id changed")
    if scope.get("geospatial_build_id") != "permit-geo-v1-c4af8799de0283bb":
        errors.append("permit geospatial deterministic build id changed")
    if scope.get("expected_rows_total") != 3_010_802:
        errors.append("permit geospatial expected row total changed")
    if scope.get("expected_transformed_total") != 2_811_767:
        errors.append("permit geospatial expected transformed total changed")
    if scope.get("expected_missing_total") != 199_035:
        errors.append("permit geospatial expected missing total changed")
    if scope.get("execution_status") != "COMPLETED_PASS_VERIFIED":
        errors.append("permit geospatial tracked plan must record completed verified execution")
    for key in ("parent_mutated", "public_row_level_release_approved", "network_access_required"):
        if scope.get(key) is not False:
            errors.append(f"permit geospatial plan must keep {key}=false")

    contracts = plan.get("contracts", {})
    if contracts.get("schema") != "schemas/permit_geospatial.v1.json":
        errors.append("permit geospatial schema reference changed")
    if contracts.get("schema_sha256") != "585a2b7c04559b947f1d35a51f332b18488e9f263ce450464cf575251c9cb762":
        errors.append("permit geospatial schema SHA-256 changed")
    if contracts.get("axis_evidence") != "provenance/geospatial_full_axis.json":
        errors.append("permit geospatial axis evidence reference changed")
    if contracts.get("source_crs") != "EPSG:5174" or contracts.get("target_crs") != "EPSG:4326":
        errors.append("permit geospatial CRS contract changed")
    if contracts.get("source_x_interpretation") != "EASTING":
        errors.append("permit geospatial source X interpretation changed")
    if contracts.get("source_y_interpretation") != "NORTHING":
        errors.append("permit geospatial source Y interpretation changed")
    if contracts.get("parent_linkage") != ["source_key", "source_row_number", "management_number"]:
        errors.append("permit geospatial parent linkage changed")
    if contracts.get("official_primary_key_claim") is not False:
        errors.append("permit geospatial linkage must not claim an official primary key")

    writer = plan.get("writer_contract", {})
    expected_writer = {
        "pyarrow_version": "21.0.0",
        "pyproj_version": "3.7.2",
        "proj_version": "9.5.1",
        "format": "PARQUET",
        "parquet_version": "2.6",
        "compression": "ZSTD",
        "compression_level": 9,
        "data_page_version": "2.0",
        "rows_per_batch": 50_000,
        "rows_per_row_group": 50_000,
    }
    if writer != expected_writer:
        errors.append("permit geospatial writer contract changed")

    safety = plan.get("safety", {})
    for key in (
        "independently_verify_parent_before_write",
        "require_reviewed_axis_evidence",
        "partial_coordinate_pair_fails_closed",
        "nonfinite_transform_fails_closed",
        "outside_broad_korea_envelope_fails_closed",
        "missing_source_coordinates_emit_null_wgs84",
        "write_to_unique_staging_directory_first",
        "remove_staging_directory_on_handled_failure",
        "fail_if_final_build_directory_exists",
        "future_snapshot_revalidation_required",
    ):
        if safety.get(key) is not True:
            errors.append(f"permit geospatial safety control {key} must remain enabled")
    for key in ("frozen_parent_schema_mutated", "public_release_approved"):
        if safety.get(key) is not False:
            errors.append(f"permit geospatial safety control {key} must remain false")

    implementation = plan.get("implementation", {})
    if implementation.get("module") != "src/korea_business_lifecycle/geospatial_enrichment.py":
        errors.append("permit geospatial implementation module changed")
    if implementation.get("script") != "scripts/materialize_permit_geospatial.py":
        errors.append("permit geospatial materialization script changed")
    if implementation.get("verification_module") != (
        "src/korea_business_lifecycle/geospatial_enrichment_verify.py"
    ):
        errors.append("permit geospatial verification module changed")
    if implementation.get("verification_script") != "scripts/verify_permit_geospatial_build.py":
        errors.append("permit geospatial verification script changed")
    if implementation.get("default_mode") != "PLAN_ONLY" or implementation.get("execute_flag") != "--execute":
        errors.append("permit geospatial execution safety defaults changed")

    execution = plan.get("execution", {})
    if execution.get("execute_command") != "python scripts/materialize_permit_geospatial.py --execute":
        errors.append("permit geospatial execute command changed")
    if execution.get("verify_command") != "python scripts/verify_permit_geospatial_build.py":
        errors.append("permit geospatial verify command changed")
    if execution.get("progress_stream") != "stderr":
        errors.append("permit geospatial progress stream changed")
    if execution.get("final_aggregate_json_stream") != "stdout":
        errors.append("permit geospatial final JSON stream changed")
    if plan.get("result_provenance") != "provenance/permit_geospatial_materialization.json":
        errors.append("permit geospatial result provenance reference changed")
    return errors


def validate_permit_geospatial_materialization(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("decision") != "LOCAL_WGS84_PERMIT_ENRICHMENT_MATERIALIZED_AND_VERIFIED":
        errors.append("permit geospatial materialization decision changed")

    scope = review.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("permit geospatial materialization scope must exactly match v1 sources")
    if scope.get("parent_permit_build_id") != "permit-v1-9908225df465e2ff":
        errors.append("permit geospatial materialization parent build id changed")
    if scope.get("geospatial_build_id") != "permit-geo-v1-c4af8799de0283bb":
        errors.append("permit geospatial materialization build id changed")
    if scope.get("rows_total") != 3_010_802:
        errors.append("permit geospatial materialization row total changed")
    if scope.get("transformed_coordinates_total") != 2_811_767:
        errors.append("permit geospatial transformed coordinate total changed")
    if scope.get("missing_source_coordinates_total") != 199_035:
        errors.append("permit geospatial missing coordinate total changed")
    if scope.get("output_bytes_total") != 50_805_782:
        errors.append("permit geospatial output byte total changed")
    if scope.get("git_ignored") is not True:
        errors.append("permit geospatial output must remain Git-ignored")
    for key in ("parent_mutated", "public_row_level_release_approved"):
        if scope.get(key) is not False:
            errors.append(f"permit geospatial materialization must keep {key}=false")

    verification = review.get("verification", {})
    for key in (
        "parent_build_verified",
        "manifest_verified",
        "parquet_hashes_verified",
        "parquet_schemas_verified",
        "zstd_verified",
        "coordinate_invariants_verified",
    ):
        if verification.get(key) is not True:
            errors.append(f"permit geospatial verification {key} must remain true")
    if verification.get("rows_verified_total") != 3_010_802:
        errors.append("permit geospatial verified row total changed")
    if verification.get("row_level_values_recorded") is not False:
        errors.append("permit geospatial provenance must remain aggregate-only")

    results = review.get("results", [])
    expected = {
        "general_restaurants": (2_295_369, 2_134_446, 160_923, 38_060_311),
        "rest_cafes": (645_952, 611_802, 34_150, 11_420_027),
        "bakeries": (69_481, 65_519, 3_962, 1_325_444),
    }
    if {item.get("source_key") for item in results} != V1_SOURCE_KEYS or len(results) != 3:
        errors.append("permit geospatial materialization results must exactly cover v1 sources")
    for item in results:
        source_key = item.get("source_key")
        expected_values = expected.get(source_key)
        if expected_values is None:
            continue
        observed = (
            item.get("rows"),
            item.get("transformed_coordinates"),
            item.get("missing_source_coordinates"),
            item.get("output_bytes"),
        )
        if observed != expected_values:
            errors.append(f"{source_key}: permit geospatial aggregate changed")
        if item.get("status") != "PASS":
            errors.append(f"{source_key}: permit geospatial status changed")
        if len(str(item.get("output_sha256", ""))) != 64:
            errors.append(f"{source_key}: permit geospatial output SHA-256 invalid")

    privacy = review.get("privacy", {})
    for key in (
        "row_level_values_recorded_in_provenance",
        "public_row_level_release_status_changed",
        "redistribution_status_changed",
    ):
        if privacy.get(key) is not False:
            errors.append(f"permit geospatial provenance must keep {key}=false")
    return errors


def validate_public_permit_aggregate_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("decision") != "PRIVACY_MINIMIZED_PERMIT_AGGREGATE_IMPLEMENTED_USER_EXECUTION_REQUIRED":
        errors.append("public permit aggregate plan decision changed")

    scope = plan.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("public permit aggregate plan scope must exactly match v1 sources")
    if scope.get("parent_permit_build_id") != "permit-v1-9908225df465e2ff":
        errors.append("public permit aggregate parent build id changed")
    if scope.get("aggregate_build_id") != "permit-public-agg-v1-bedd874de6619bee":
        errors.append("public permit aggregate deterministic build id changed")
    if scope.get("expected_parent_rows") != 3_010_802:
        errors.append("public permit aggregate expected parent row count changed")
    if scope.get("execution_status") != "NOT_EXECUTED":
        errors.append("public permit aggregate plan must remain not executed until user run")
    for key in ("row_level_public_projection_approved", "aggregate_publication_approved", "network_access_required"):
        if scope.get(key) is not False:
            errors.append(f"public permit aggregate plan must keep {key}=false")
    if scope.get("redistribution_status") != "UNRESOLVED":
        errors.append("public permit aggregate redistribution status changed")

    contracts = plan.get("contracts", {})
    if contracts.get("schema") != "schemas/public_permit_aggregate.v1.json":
        errors.append("public permit aggregate schema contract changed")
    if contracts.get("schema_sha256") != "35b3145a3e6aace98881b9d0efb8c6298c740130f71f57b78f45aee74a480a45":
        errors.append("public permit aggregate schema SHA-256 changed")
    if contracts.get("minimum_cell_count") != 10:
        errors.append("public permit aggregate minimum cell count changed")
    if contracts.get("minimum_cell_count_is_legal_privacy_guarantee") is not False:
        errors.append("public permit aggregate k threshold must not be a legal privacy guarantee")
    if contracts.get("publication_requires_separate_redistribution_clearance") is not True:
        errors.append("public permit aggregate must require separate redistribution clearance")
    expected_grouping = [
        "source_key",
        "authority_code",
        "source_status_code",
        "source_detail_status_code",
        "permit_year",
        "closure_year",
    ]
    if contracts.get("grouping_columns") != expected_grouping:
        errors.append("public permit aggregate grouping contract changed")

    excluded = set(plan.get("excluded_row_level_fields", []))
    required_excluded = {
        "management_number",
        "business_name",
        "lot_address",
        "road_address",
        "lot_postal_code",
        "road_postal_code",
        "source_coordinate_x",
        "source_coordinate_y",
        "wgs84_longitude",
        "wgs84_latitude",
        "source_row_number",
        "source_artifact_sha256",
        "source_retrieved_at_utc",
        "source_data_updated_at_raw",
        "source_last_modified_at_raw",
    }
    if excluded != required_excluded:
        errors.append("public permit aggregate excluded row-level field set changed")

    semantics = plan.get("semantic_safety", {})
    for key in (
        "permit_year_is_physical_open_year",
        "closure_year_is_irreversible_terminal_event",
        "canonical_status_mapping_enabled",
        "status_code_03_irreversible",
        "status_code_05_semantics_resolved",
    ):
        if semantics.get(key) is not False:
            errors.append(f"public permit aggregate semantic safety must keep {key}=false")

    writer = plan.get("writer_contract", {})
    expected_writer = {
        "pyarrow_version": "21.0.0",
        "format": "PARQUET",
        "parquet_version": "2.6",
        "compression": "ZSTD",
        "compression_level": 9,
        "data_page_version": "2.0",
        "rows_per_batch": 50_000,
        "rows_per_row_group": 50_000,
        "minimum_cell_count": 10,
    }
    if writer != expected_writer:
        errors.append("public permit aggregate writer contract changed")

    implementation = plan.get("implementation", {})
    if implementation.get("module") != "src/korea_business_lifecycle/public_aggregate.py":
        errors.append("public permit aggregate implementation module changed")
    if implementation.get("script") != "scripts/materialize_public_permit_aggregate.py":
        errors.append("public permit aggregate materialization script changed")
    if implementation.get("verification_module") != "src/korea_business_lifecycle/public_aggregate_verify.py":
        errors.append("public permit aggregate verification module changed")
    if implementation.get("verification_script") != "scripts/verify_public_permit_aggregate.py":
        errors.append("public permit aggregate verification script changed")
    if implementation.get("default_mode") != "PLAN_ONLY" or implementation.get("execute_flag") != "--execute":
        errors.append("public permit aggregate execution defaults changed")

    execution = plan.get("execution", {})
    if execution.get("execute_command") != "python scripts/materialize_public_permit_aggregate.py --execute":
        errors.append("public permit aggregate execute command changed")
    if execution.get("verify_command") != "python scripts/verify_public_permit_aggregate.py":
        errors.append("public permit aggregate verify command changed")
    if execution.get("progress_stream") != "stderr":
        errors.append("public permit aggregate progress stream changed")
    if execution.get("final_aggregate_json_stream") != "stdout":
        errors.append("public permit aggregate final JSON stream changed")
    return errors
