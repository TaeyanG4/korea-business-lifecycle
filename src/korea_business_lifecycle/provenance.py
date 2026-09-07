from __future__ import annotations

import hashlib
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


def load_public_permit_aggregate() -> dict[str, Any]:
    return load_json("provenance/public_permit_aggregate.json")


def load_bounded_episode_reconstruction() -> dict[str, Any]:
    return load_json("provenance/bounded_episode_reconstruction.json")


def load_history_observation_strategy() -> dict[str, Any]:
    return load_json("provenance/history_observation_strategy.json")


def load_authority_domain_reference() -> dict[str, Any]:
    return load_json("provenance/authority_domain_reference.json")


def load_history_authority_partition_probe_plan() -> dict[str, Any]:
    return load_json("provenance/history_authority_partition_probe_plan.json")


def load_history_authority_partition_full_probe() -> dict[str, Any]:
    return load_json("provenance/history_authority_partition_full_probe.json")


def load_history_authority_partition_findings() -> dict[str, Any]:
    return load_json("provenance/history_authority_partition_findings.json")


def load_history_authority_policy() -> dict[str, Any]:
    return load_json("provenance/history_authority_policy.json")


def load_history_nationwide_acquisition_plan() -> dict[str, Any]:
    return load_json("provenance/history_nationwide_acquisition_plan.json")


def load_history_episode_materialization_plan() -> dict[str, Any]:
    return load_json("provenance/history_episode_materialization_plan.json")


def load_redistribution_clarification_plan() -> dict[str, Any]:
    return load_json("provenance/redistribution_clarification_plan.json")


def load_v1_release_scope() -> dict[str, Any]:
    return load_json("provenance/v1_release_scope.json")


def validate_v1_release_scope(scope: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if scope.get("decision") != (
        "LOCAL_V1_CORE_COMPLETE_HISTORY_OPTIONAL_AGGREGATE_KAGGLE_PUBLICATION_APPROVED"
    ):
        errors.append("v1 release-scope decision changed")

    core = scope.get("core_v1", {})
    if set(core.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("v1 release scope must exactly match the three v1 sources")
    if core.get("permit_parent_build_id") != "permit-v1-9908225df465e2ff":
        errors.append("v1 release scope permit parent build changed")
    if core.get("permit_parent_rows") != 3_010_802:
        errors.append("v1 release scope permit parent row count changed")
    if core.get("wgs84_sidecar_build_id") != "permit-geo-v1-c4af8799de0283bb":
        errors.append("v1 release scope geospatial build changed")
    if core.get("wgs84_sidecar_rows") != 3_010_802:
        errors.append("v1 release scope geospatial row count changed")
    for key in ("local_core_complete",):
        if core.get(key) is not True:
            errors.append(f"v1 release scope must keep {key}=true")
    for key in ("nationwide_history_required_for_core_v1", "production_episode_required_for_core_v1"):
        if core.get(key) is not False:
            errors.append(f"v1 release scope must keep {key}=false")

    lifecycle = scope.get("lifecycle_optional", {})
    if lifecycle.get("status") != "OPTIONAL_ADVANCED_WORKFLOW":
        errors.append("lifecycle workflow must remain optional for core v1")
    if lifecycle.get("episode_schema") != "schemas/permit_status_episode.v1.json":
        errors.append("optional episode schema reference changed")
    if lifecycle.get("approved_reference_snapshot_tasks") != 7_320:
        errors.append("optional monthly reference task count changed")
    if lifecycle.get("partial_history_is_production_episode_input") is not False:
        errors.append("partial history must not become production episode input")
    if lifecycle.get("history_is_lossless_event_log") is not False:
        errors.append("optional history must not be promoted to an event log")

    public = scope.get("public_release", {})
    if public.get("kaggle_target") != "PRIVACY_MINIMIZED_AGGREGATE_ONLY":
        errors.append("Kaggle release target changed")
    if public.get("aggregate_build_id") != "permit-public-agg-v1-bedd874de6619bee":
        errors.append("Kaggle aggregate build changed")
    if public.get("aggregate_sha256") != (
        "112fbec3187b2d77df2744edb878fa0f3ecb850cf675496cd4383404092911fb"
    ):
        errors.append("Kaggle aggregate hash changed")
    if public.get("aggregate_rows") != 67_267:
        errors.append("Kaggle aggregate row count changed")
    if public.get("aggregate_publication_approved") is not True:
        errors.append("verified aggregate publication must remain approved")
    for key in ("row_level_permit_publication_approved", "precise_wgs84_publication_approved"):
        if public.get(key) is not False:
            errors.append(f"v1 release scope must keep {key}=false")
    if public.get("all_three_source_pages_display_no_restriction") is not True:
        errors.append("official no-restriction metadata evidence changed")
    if public.get("written_source_specific_confirmation_required_for_aggregate_publication") is not False:
        errors.append("written clarification must remain optional for the approved aggregate release")
    if public.get("minimum_cell_count") != 10:
        errors.append("aggregate suppression threshold changed")
    if public.get("minimum_cell_count_is_legal_privacy_guarantee") is not False:
        errors.append("k=10 must not be promoted to a legal privacy guarantee")
    if public.get("kaggle_license_metadata") != "other":
        errors.append("Kaggle license metadata must remain 'other' unless source terms are remapped explicitly")
    if public.get("project_requires_source_attribution") is not True:
        errors.append("Kaggle release must retain source attribution")
    return errors


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
    if refresh.get("written_clarification_plan") != "provenance/redistribution_clarification_plan.json":
        errors.append("license review written clarification plan reference changed")
    if refresh.get("written_source_specific_clarification_received") is not False:
        errors.append("license review must not claim written source-specific clearance")
    if review.get("next_gate") != "provenance/redistribution_clarification_plan.json":
        errors.append("license review next gate changed")
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
    aggregate = review.get("aggregate_candidate_technical_assessment", {})
    if aggregate.get("result_provenance") != "provenance/public_permit_aggregate.json":
        errors.append("privacy review aggregate result reference changed")
    if aggregate.get("status") != "TECHNICAL_MINIMIZATION_VERIFIED_NOT_PUBLICATION_APPROVED":
        errors.append("privacy review aggregate technical status changed")
    if aggregate.get("minimum_cell_count") != 10:
        errors.append("privacy review aggregate minimum cell count changed")
    for key in (
        "direct_or_linkable_row_fields_emitted",
        "precise_coordinates_emitted",
        "exact_addresses_emitted",
        "business_names_emitted",
        "management_numbers_emitted",
        "minimum_cell_count_is_legal_privacy_guarantee",
        "aggregate_publication_approved",
    ):
        if aggregate.get(key) is not False:
            errors.append(f"privacy review aggregate assessment must keep {key}=false")
    if aggregate.get("suppression_invariants_verified") is not True:
        errors.append("privacy review aggregate suppression invariants must remain verified")
    return errors


def validate_history_review(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("decision") != (
        "FINITE_AS_OF_DATE_QUERY_CONFIRMED_AUTHENTICATED_EXECUTION_AVAILABLE_"
        "DATE_EFFECTIVE_AUTHORITY_POLICY_APPROVED"
    ):
        errors.append("history-review decision changed")
    if review.get("common_contract", {}).get("event_log_claim") is not False:
        errors.append("history must not be represented as a lossless event log")
    if review.get("common_contract", {}).get("authentication") != "data.go.kr serviceKey required":
        errors.append("history authentication requirement must remain explicit")
    common = review.get("common_contract", {})
    observed_domain = common.get("observed_current_authority_code_domain", {})
    if observed_domain.get("distinct_count") != 230 or observed_domain.get("authoritative_completeness") is not False:
        errors.append("history observed-current authority-domain state changed")
    official_domain = common.get("official_authority_reference", {})
    expected_official_domain = {
        "evidence": "provenance/authority_domain_reference.json",
        "manual_reference_count": 245,
        "current_official_numeric_count": 244,
        "current_official_aggregate_token_count": 16,
        "official_deleted_numeric_count": 32,
        "history_window_candidate_numeric_union_count": 276,
        "current_observed_count": 230,
        "current_official_unobserved_count": 14,
        "current_window_candidate_unobserved_count": 46,
        "exact_current_official_numeric_code_values_ingested": True,
        "exact_deleted_numeric_code_values_ingested": True,
        "exact_new_numeric_code_values_ingested": True,
        "pre_reform_numeric_authority_count": 244,
        "current_official_numeric_domain_authoritatively_complete_for_reference_date": True,
        "date_effective_history_authority_filter_semantics_verified": False,
        "date_effective_current_state_enumeration_policy_approved": True,
        "history_window_date_effective_numeric_enumeration_ready": True,
        "future_reference_refresh_required": True,
    }
    if official_domain != expected_official_domain:
        errors.append("history official authority reference state changed")
    refresh = common.get("authenticated_probe_refresh_2026_09_07", {})
    expected_refresh = {
        "source_key": "bakeries",
        "base_date": "20260630",
        "authority_code": "3490000",
        "result_code": "0",
        "total_count": 314,
        "service_key_value_recorded": False,
        "interpretation": (
            "A later bounded authenticated page-1 probe succeeded. The earlier 403 remains "
            "historical evidence rather than the current execution state."
        ),
    }
    if refresh != expected_refresh:
        errors.append("history authenticated probe refresh changed")
    partition = common.get("authority_partition_semantics", {})
    expected_partition = {
        "findings": "provenance/history_authority_partition_findings.json",
        "full_deleted_count_probe_plan": "provenance/history_authority_partition_probe_plan.json",
        "full_deleted_count_probe_result": "provenance/history_authority_partition_full_probe.json",
        "date_effective_current_state_policy": "provenance/history_authority_policy.json",
        "authenticated_execution_available": True,
        "bounded_deleted_partition_post_reform_freeze_confirmed": True,
        "bounded_current_partition_post_reform_evolution_confirmed": True,
        "simple_date_effective_active_authority_domain_model_supported": False,
        "full_32_deleted_count_probe_executed": True,
        "all_96_deleted_source_authority_pairs_post_reform_count_frozen": True,
        "post_reform_deleted_partition_policy": "CURRENT_244_ONLY_EXCLUDE_DELETED_32",
        "pre_reform_old_new_partition_domain_resolved": True,
        "pre_reform_current_state_enumeration_policy": "CURRENT_MINUS_NEW_PLUS_DELETED",
        "same_date_old_new_union_used": False,
    }
    if partition != expected_partition:
        errors.append("history authority-partition semantics state changed")
    if common.get("nationwide_acquisition_state") != (
        "date-effective authority code-set policy and monthly observation cadence are approved; "
        "nationwide acquisition has not yet been executed and production episodes remain gated on "
        "all 7320 snapshot tasks completing uniquely"
    ):
        errors.append("history nationwide acquisition state changed")
    if {item.get("source_key") for item in review.get("categories", [])} != V1_SOURCE_KEYS:
        errors.append("history-review scope must exactly match v1 sources")
    return errors


def validate_history_authority_partition_probe_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("decision") != "FULL_32_DELETED_AUTHORITY_COUNT_PROBE_COMPLETED_VERIFIED":
        errors.append("deleted-authority probe-plan decision changed")
    scope = plan.get("scope", {})
    expected_scope = {
        "sources": ["general_restaurants", "rest_cafes", "bakeries"],
        "authority_reference": "provenance/authority_domain_reference.json",
        "deleted_numeric_authority_count": 32,
        "probe_dates": ["20260101", "20260630", "20260701", "20260906"],
        "tasks": 384,
        "requests_per_task": 1,
        "maximum_network_requests": 384,
        "page_no": 1,
        "num_rows": 1,
    }
    if scope != expected_scope:
        errors.append("deleted-authority probe-plan scope changed")
    purpose = plan.get("purpose", {})
    for key in (
        "verify_all_deleted_codes_remain_queryable",
        "measure_pre_reform_count_change",
        "test_post_reform_count_freeze_pattern",
    ):
        if purpose.get(key) is not True:
            errors.append(f"deleted-authority probe-plan purpose must keep {key}=true")
    for key in ("prove_row_level_overlap_or_identity", "prove_history_is_lossless_event_log"):
        if purpose.get(key) is not False:
            errors.append(f"deleted-authority probe-plan purpose must keep {key}=false")
    execution = plan.get("execution", {})
    if execution.get("default_mode") != "DRY_RUN" or execution.get("execute_flag") != "--execute":
        errors.append("deleted-authority probe-plan execution defaults changed")
    if execution.get("execution_performed") is not True:
        errors.append("deleted-authority full count probe execution must remain recorded")
    if execution.get("result_provenance") != "provenance/history_authority_partition_full_probe.json":
        errors.append("deleted-authority full count probe result reference changed")
    if execution.get("long_running_action_requires_visible_user_command") is not True:
        errors.append("deleted-authority long-run visibility policy changed")
    privacy = plan.get("privacy", {})
    for key in (
        "source_rows_emitted",
        "management_numbers_emitted",
        "business_names_emitted",
        "addresses_emitted",
        "coordinates_emitted",
        "service_key_emitted",
    ):
        if privacy.get(key) is not False:
            errors.append(f"deleted-authority probe-plan privacy must keep {key}=false")
    if privacy.get("only_authority_date_source_total_count_emitted") is not True:
        errors.append("deleted-authority probe-plan aggregate-only output changed")
    implementation = plan.get("implementation", {})
    expected_implementation = {
        "module": "src/korea_business_lifecycle/history_authority_semantics.py",
        "script": "scripts/probe_deleted_authority_semantics.py",
        "test_module": "tests/test_history_authority_semantics.py",
    }
    if implementation != expected_implementation:
        errors.append("deleted-authority probe-plan implementation changed")
    return errors


def validate_history_authority_partition_full_probe(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("decision") != (
        "FULL_32_DELETED_AUTHORITY_COUNT_PROBE_COMPLETED_POST_REFORM_COUNT_FREEZE_CONFIRMED"
    ):
        errors.append("deleted-authority full-probe decision changed")
    scope = result.get("scope", {})
    expected_scope = {
        "sources": ["general_restaurants", "rest_cafes", "bakeries"],
        "deleted_numeric_authority_count": 32,
        "probe_dates": ["20260101", "20260630", "20260701", "20260906"],
        "tasks": 384,
        "source_authority_pairs": 96,
    }
    if scope != expected_scope:
        errors.append("deleted-authority full-probe scope changed")
    execution = result.get("execution", {})
    expected_execution = {
        "mode": "EXECUTED",
        "requests_executed": 384,
        "unique_tasks": 384,
        "stderr_progress_lines": 384,
        "errors_detected": False,
        "service_key_value_recorded": False,
        "row_level_values_emitted": False,
        "local_json_bytes": 56827,
        "local_json_sha256": "3f8326fe2b82835ffda148b2bb1fda0049452e7719c67d58f439c9977e19ad7f",
        "local_stderr_bytes": 21600,
        "local_stderr_sha256": "1a24ab5c37ab2914628dde3bb049cd31ee27aef328d2eb48671b6b66d794055a",
        "local_artifacts_git_tracked": False,
    }
    if execution != expected_execution:
        errors.append("deleted-authority full-probe execution evidence changed")
    assessment = result.get("assessment", {})
    expected_assessment = {
        "complete_four_date_pairs": 96,
        "pairs_queryable_on_all_four_dates": 96,
        "pairs_with_positive_20260630_count": 90,
        "pairs_with_all_zero_counts": 6,
        "all_zero_authority_codes": ["6290000", "6460000"],
        "pairs_with_count_growth_20260101_to_20260630": 81,
        "positive_no_growth_pair_count": 9,
        "positive_no_growth_pair_source": "bakeries",
        "pairs_with_equal_counts_20260630_20260701_20260906": 96,
        "post_reform_count_freeze_confirmed_all_pairs": True,
        "post_reform_row_content_freeze_confirmed_all_pairs": False,
    }
    if assessment != expected_assessment:
        errors.append("deleted-authority full-probe assessment changed")
    policy = result.get("legacy_partition_policy", {})
    expected_policy = {
        "effective_date": "2026-07-01",
        "post_reform_current_state_enumeration": "CURRENT_244_ONLY_EXCLUDE_DELETED_32",
        "post_reform_policy_approved": True,
        "pre_reform_current_plus_deleted_union": "UNRESOLVED_DO_NOT_AUTO_UNION",
        "pre_reform_policy_approved": False,
        "full_window_numeric_enumeration_ready": False,
        "reason": (
            "all 96 deleted-code source pairs keep identical counts from 2026-06-30 through "
            "2026-09-06, while bounded full-row evidence confirms frozen deleted partitions and "
            "evolving current partitions; current/new codes are also queryable before the reform, "
            "so a pre-reform union cannot be assumed complete or non-overlapping"
        ),
    }
    if policy != expected_policy:
        errors.append("deleted-authority legacy-partition policy changed")
    limits = result.get("semantic_limits", {})
    for key in (
        "count_freeze_proves_row_content_freeze_for_all_96_pairs",
        "current_plus_deleted_union_is_semantically_equivalent_to_current_snapshot",
        "history_is_lossless_event_log",
        "mng_no_primary_key_declared",
    ):
        if limits.get(key) is not False:
            errors.append(f"deleted-authority full-probe semantic limit must keep {key}=false")
    return errors


def validate_history_authority_partition_findings(findings: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if findings.get("decision") != (
        "BOUNDED_DELETED_AUTHORITY_PARTITIONS_FREEZE_AFTER_REFORM_LEGACY_STATE_CONFIRMED"
    ):
        errors.append("authority-partition findings decision changed")
    scope = findings.get("scope", {})
    if set(scope.get("count_probe_deleted_codes", [])) != {"3490000", "3590000", "4800000"}:
        errors.append("authority-partition bounded deleted-code scope changed")
    if set(scope.get("count_probe_sources", [])) != V1_SOURCE_KEYS:
        errors.append("authority-partition bounded source scope changed")
    if scope.get("count_probe_dates") != ["20260101", "20260630", "20260701", "20260906"]:
        errors.append("authority-partition bounded count-probe dates changed")
    if scope.get("count_probe_source_authority_pairs") != 9 or scope.get("bounded_not_nationwide") is not True:
        errors.append("authority-partition bounded scope accounting changed")

    auth = findings.get("authentication_refresh", {})
    if auth.get("authenticated_history_probe_now_succeeds") is not True:
        errors.append("authority-partition authenticated probe success changed")
    if auth.get("service_key_value_recorded") is not False:
        errors.append("authority-partition findings must not record the service key")
    first = auth.get("first_successful_deleted_code_probe", {})
    if first != {
        "source_key": "bakeries",
        "base_date": "20260630",
        "authority_code": "3490000",
        "result_code": "0",
        "total_count": 314,
    }:
        errors.append("authority-partition first successful probe evidence changed")

    rows = findings.get("count_probe_results", [])
    if len(rows) != 9:
        errors.append("authority-partition bounded count probe must contain nine source/code pairs")
    pair_keys = {(item.get("source_key"), item.get("authority_code")) for item in rows}
    if len(pair_keys) != 9:
        errors.append("authority-partition bounded count probe pairs must be unique")
    for item in rows:
        try:
            start = int(item["20260101"])
            pre = int(item["20260630"])
            effective = int(item["20260701"])
            end = int(item["20260906"])
        except (KeyError, TypeError, ValueError):
            errors.append("authority-partition count probe values must be integers")
            continue
        if not (start < pre and pre > 0 and pre == effective == end):
            errors.append("authority-partition bounded freeze count pattern changed")
    assessment = findings.get("count_probe_assessment", {})
    expected_assessment = {
        "pairs_queryable_on_all_four_dates": 9,
        "pairs_with_positive_20260630_count": 9,
        "pairs_with_count_growth_20260101_to_20260630": 9,
        "pairs_with_equal_counts_20260630_20260701_20260906": 9,
        "simple_deleted_code_becomes_zero_on_effective_date_model_rejected": True,
    }
    if assessment != expected_assessment:
        errors.append("authority-partition bounded count assessment changed")

    audits = findings.get("full_row_audits", [])
    if len(audits) != 3:
        errors.append("authority-partition full-row audit scope changed")
    by_code = {str(item.get("authority_code")): item for item in audits}
    for code, rows_expected, active_expected in (("3490000", 314, 101), ("4800000", 332, 75)):
        item = by_code.get(code, {})
        if item.get("start_rows") != rows_expected or item.get("end_rows") != rows_expected:
            errors.append(f"{code}: deleted partition row count changed")
        if item.get("common_mng_no") != rows_expected or item.get("added_mng_no") != 0 or item.get("disappeared_mng_no") != 0:
            errors.append(f"{code}: deleted partition bounded linkage accounting changed")
        if any(int(value) != 0 for value in item.get("changed_common_rows", {}).values()):
            errors.append(f"{code}: deleted partition is no longer fully frozen in bounded audit")
        if item.get("active_status_01_rows_at_end") != active_expected:
            errors.append(f"{code}: deleted partition active-status evidence changed")
    control = by_code.get("3491000", {})
    if control.get("role") != "CURRENT_CODE_CONTROL" or control.get("changed_common_rows", {}).get("status") != 1:
        errors.append("authority-partition current-code control must retain observed evolution")

    overlap = findings.get("bounded_overlap_audit", {})
    expected_overlap_scalars = {
        "source_key": "bakeries",
        "base_date": "20260906",
        "deleted_authority_code": "3490000",
        "deleted_partition_rows": 314,
        "current_partition_union_rows": 932,
        "mng_no_overlap": 0,
        "deleted_only_mng_no": 314,
        "current_union_only_mng_no": 932,
        "current_snapshot_deleted_authority_rows": 0,
        "current_snapshot_current_authority_rows": 932,
        "current_snapshot_current_authority_counts_match_20260906_history": True,
        "management_number_values_emitted": False,
    }
    for key, expected in expected_overlap_scalars.items():
        if overlap.get(key) != expected:
            errors.append(f"authority-partition overlap evidence {key} changed")
    if set(overlap.get("current_authority_codes", [])) != {"3491000", "3501000", "3561000", "3565000"}:
        errors.append("authority-partition current-code overlap scope changed")

    interpretation = findings.get("interpretation", {})
    for key in (
        "deleted_partition_queryable_after_reform",
        "deleted_partition_frozen_after_reform_in_bounded_full_row_sample",
        "deleted_partition_may_contain_source_status_01_after_reform",
        "current_code_partition_can_continue_evolving_after_reform",
    ):
        if interpretation.get(key) is not True:
            errors.append(f"authority-partition interpretation must keep {key}=true")
    for key in (
        "authority_filter_is_simple_date_effective_active_code_domain",
        "current_plus_deleted_union_is_semantically_equivalent_to_current_snapshot",
        "bounded_zero_overlap_proves_all_old_new_partitions_are_disjoint",
        "mng_no_primary_key_declared",
        "history_is_lossless_event_log",
    ):
        if interpretation.get(key) is not False:
            errors.append(f"authority-partition safety interpretation must keep {key}=false")
    return errors


def validate_authority_domain_reference(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("decision") != "DATE_EFFECTIVE_CURRENT_STATE_AUTHORITY_DOMAINS_APPROVED_PRE_244_POST_244":
        errors.append("authority-domain reference decision changed")
    if review.get("field") != "OPN_ATMY_GRP_CD":
        errors.append("authority-domain reference field changed")

    official = review.get("official_reference", {})
    if official.get("manual_url") != (
        "https://www.localdata.go.kr/images/egovframework/portal/manual_260106.pdf"
    ):
        errors.append("authority-domain official manual URL changed")
    if official.get("manual_reference_filename") != "개방자치단체코드.xlsx":
        errors.append("authority-domain manual reference filename changed")
    if official.get("manual_claim_count") != 245:
        errors.append("authority-domain manual reference count changed")
    if official.get("manual_claim_is_current_enumeration_count") is not False:
        errors.append("manual 245 count must not be promoted to the current enumeration domain")
    if official.get("v1_detail_reference_filename") != "개방자치단체코드_영업상태코드.xlsx":
        errors.append("authority-domain v1 reference filename changed")
    expected_pages = {
        "https://www.data.go.kr/data/15154916/openapi.do",
        "https://www.data.go.kr/data/15154921/openapi.do",
        "https://www.data.go.kr/data/15155252/openapi.do",
    }
    if set(official.get("v1_detail_pages", [])) != expected_pages:
        errors.append("authority-domain v1 detail-page evidence changed")
    expected_official = {
        "notice_url": "https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000004824",
        "notice_date": "2026-07-03",
        "change_effective_date": "2026-07-01",
        "attachment_filename": "개방자치단체코드_영업상태코드_행정체제개편반영_20260702.xlsx",
        "attachment_sha256": "d032ff4bd63148238a8066afb7b62f96770d8a063bd6c632d4f7617e9cc407f8",
        "sheet_name": "1. 개방자치단체코드",
        "active_row_count": 260,
        "active_numeric_code_count": 244,
        "active_aggregate_token_count": 16,
        "deleted_row_count": 34,
        "deleted_numeric_code_count": 32,
        "deleted_aggregate_token_count": 2,
        "new_row_count": 33,
        "new_numeric_code_count": 32,
        "new_aggregate_token_count": 1,
        "current_numeric_authority_list_sha256": "a666c5cb432c439f687064e3046ec2e9a84d2de708dfbe80817330e60b76ddad",
        "new_numeric_authority_list_sha256": "f146a5b199098252a8be05347463f734e948cf69497ce1c78af6f6383be7ae80",
        "manual_count_differs_from_current_numeric_reference": True,
    }
    for key, expected in expected_official.items():
        if official.get(key) != expected:
            errors.append(f"authority-domain official reference {key} changed")

    current_authorities = review.get("official_current_numeric_authorities", [])
    if len(current_authorities) != 244:
        errors.append("authority-domain exact current numeric list must contain 244 rows")
    codes = [str(item.get("code", "")) for item in current_authorities]
    names = [str(item.get("name", "")).strip() for item in current_authorities]
    if len(set(codes)) != 244 or codes != sorted(codes):
        errors.append("authority-domain exact current numeric codes must be unique and sorted")
    if any(len(code) != 7 or not code.isdigit() for code in codes):
        errors.append("authority-domain exact current numeric code format changed")
    if any(not name for name in names):
        errors.append("authority-domain exact current authority names must be nonblank")
    list_payload = "".join(
        f"{item.get('code')}\t{item.get('name')}\n" for item in current_authorities
    ).encode("utf-8")
    if hashlib.sha256(list_payload).hexdigest() != official.get("current_numeric_authority_list_sha256"):
        errors.append("authority-domain exact current numeric list hash changed")

    deleted_authorities = review.get("official_deleted_numeric_authorities", [])
    if len(deleted_authorities) != 32:
        errors.append("authority-domain exact deleted numeric list must contain 32 rows")
    deleted_codes = [str(item.get("code", "")) for item in deleted_authorities]
    deleted_names = [str(item.get("name", "")).strip() for item in deleted_authorities]
    if len(set(deleted_codes)) != 32 or deleted_codes != sorted(deleted_codes):
        errors.append("authority-domain exact deleted numeric codes must be unique and sorted")
    if any(len(code) != 7 or not code.isdigit() for code in deleted_codes):
        errors.append("authority-domain exact deleted numeric code format changed")
    if any(not name for name in deleted_names):
        errors.append("authority-domain exact deleted authority names must be nonblank")
    if set(codes) & set(deleted_codes):
        errors.append("authority-domain current and deleted numeric codes must be disjoint")
    deleted_payload = "".join(
        f"{item.get('code')}\t{item.get('name')}\n" for item in deleted_authorities
    ).encode("utf-8")
    if hashlib.sha256(deleted_payload).hexdigest() != official.get(
        "deleted_numeric_authority_list_sha256"
    ):
        errors.append("authority-domain exact deleted numeric list hash changed")

    new_authorities = review.get("official_new_numeric_authorities", [])
    if len(new_authorities) != 32:
        errors.append("authority-domain exact new numeric list must contain 32 rows")
    new_codes = [str(item.get("code", "")) for item in new_authorities]
    if len(set(new_codes)) != 32 or new_codes != sorted(new_codes):
        errors.append("authority-domain exact new numeric codes must be unique and sorted")
    if not set(new_codes) <= set(codes) or set(new_codes) & set(deleted_codes):
        errors.append("authority-domain new numeric codes must be current-only and disjoint from deleted")
    new_payload = "".join(
        f"{item.get('code')}\t{item.get('name')}\n" for item in new_authorities
    ).encode("utf-8")
    if hashlib.sha256(new_payload).hexdigest() != official.get("new_numeric_authority_list_sha256"):
        errors.append("authority-domain exact new numeric list hash changed")

    pre_authorities = review.get("official_pre_reform_numeric_authorities", [])
    if len(pre_authorities) != 244:
        errors.append("authority-domain exact pre-reform numeric list must contain 244 rows")
    pre_codes = [str(item.get("code", "")) for item in pre_authorities]
    if len(set(pre_codes)) != 244 or pre_codes != sorted(pre_codes):
        errors.append("authority-domain exact pre-reform numeric codes must be unique and sorted")
    if set(pre_codes) != (set(codes) - set(new_codes)) | set(deleted_codes):
        errors.append("authority-domain pre-reform list must equal current minus new plus deleted")
    pre_payload = "".join(
        f"{item.get('code')}\t{item.get('name')}\n" for item in pre_authorities
    ).encode("utf-8")

    history_change = review.get("history_window_change_reference", {})
    expected_history_change = {
        "window_start": "2026-01-01",
        "window_end": "2026-09-06",
        "change_effective_date": "2026-07-01",
        "exact_deleted_numeric_authority_codes_ingested": True,
        "deleted_numeric_authority_count": 32,
        "exact_new_numeric_authority_codes_ingested": True,
        "new_numeric_authority_count": 32,
        "unchanged_numeric_authority_count": 212,
        "pre_reform_numeric_authority_count": 244,
        "pre_reform_numeric_authority_list_sha256": "c4f1810ef53d3633b2422868f4628af024c2e26944d4d79a130c38aaa8246148",
        "pre_reform_current_state_enumeration_policy": "CURRENT_MINUS_NEW_PLUS_DELETED",
        "post_reform_current_state_enumeration_policy": "CURRENT_ONLY_EXCLUDE_DELETED",
        "authority_domain_switch_uses_official_change_effective_date": True,
        "api_queryability_does_not_define_date_effective_membership": True,
        "current_plus_deleted_candidate_union_count": 276,
        "date_effective_history_authority_filter_semantics_verified": False,
        "date_effective_current_state_enumeration_policy_approved": True,
        "deleted_codes_confirmed_queryable_for_prechange_base_dates": True,
        "manual_245_count_reconciled_to_exact_window_domain": False,
    }
    for key, expected in expected_history_change.items():
        if history_change.get(key) != expected:
            errors.append(f"authority-domain history-window change reference {key} changed")
    union_map = {
        **{item.get("code"): item.get("name") for item in deleted_authorities},
        **{item.get("code"): item.get("name") for item in current_authorities},
    }
    union_payload = "".join(
        f"{code}\t{union_map[code]}\n" for code in sorted(union_map)
    ).encode("utf-8")
    if hashlib.sha256(union_payload).hexdigest() != history_change.get(
        "current_plus_deleted_candidate_union_sha256"
    ):
        errors.append("authority-domain history-window candidate union hash changed")
    if hashlib.sha256(pre_payload).hexdigest() != history_change.get(
        "pre_reform_numeric_authority_list_sha256"
    ):
        errors.append("authority-domain pre-reform numeric list hash changed")

    observed = review.get("observed_current_snapshots", {})
    if observed.get("distinct_authority_count") != 230:
        errors.append("authority-domain observed current count changed")
    expected_observed_scalars = {
        "permit_build_id": "permit-v1-9908225df465e2ff",
        "identical_across_three_v1_sources": True,
        "format": "7-digit numeric strings",
        "observed_is_subset_of_current_official_numeric_domain": True,
        "observed_not_in_current_official_numeric_domain_count": 0,
        "current_official_numeric_not_observed_count": 14,
        "observed_new_numeric_code_count": 31,
    }
    for key, expected in expected_observed_scalars.items():
        if observed.get(key) != expected:
            errors.append(f"authority-domain observed current {key} changed")
    missing = observed.get("current_official_numeric_not_observed", [])
    if len(missing) != 14 or len({item.get("code") for item in missing}) != 14:
        errors.append("authority-domain current official unobserved list must contain 14 unique codes")
    current_map = {item.get("code"): item.get("name") for item in current_authorities}
    if any(current_map.get(item.get("code")) != item.get("name") for item in missing):
        errors.append("authority-domain unobserved authorities must be drawn from the official list")

    gate = review.get("ingestion_gate", {})
    for key in (
        "exact_current_official_numeric_code_values_ingested",
        "exact_current_official_numeric_code_list_hash_recorded",
        "exact_current_official_numeric_code_list_validated",
        "current_official_numeric_domain_authoritatively_complete_for_reference_date",
        "current_reference_numeric_enumeration_ready",
        "exact_deleted_numeric_code_values_ingested",
        "exact_new_numeric_code_values_ingested",
        "history_window_date_effective_numeric_enumeration_ready",
        "future_reference_refresh_required",
    ):
        if gate.get(key) is not True:
            errors.append(f"authority-domain ingestion gate must keep {key}=true")
    if gate.get("aggregate_all_tokens_used_for_row_enumeration") is not False:
        errors.append("authority-domain aggregate _ALL tokens must not be used for row enumeration")

    cost = review.get("cost_model_policy", {})
    expected_cost = {
        "observed_nonempty_authority_count": 230,
        "current_official_numeric_authority_count": 244,
        "current_unobserved_official_authority_probe_count_per_source": 14,
        "deleted_numeric_authority_count": 32,
        "new_numeric_authority_count": 32,
        "pre_reform_numeric_authority_count": 244,
        "history_window_candidate_numeric_union_count": 276,
        "current_scale_candidate_union_absent_authority_count_per_source": 46,
        "current_plus_deleted_candidate_union_may_be_used_for_cost_planning": False,
        "candidate_union_is_proven_date_effective_query_domain": False,
        "date_effective_current_state_authority_count_per_date": 244,
        "current_unobserved_authorities_may_be_assumed_historically_empty": False,
        "deleted_authorities_may_be_assumed_unqueryable_for_prechange_dates": False,
        "manual_245_count_may_be_used_as_exact_current_query_domain": False,
    }
    if cost != expected_cost:
        errors.append("authority-domain cost-model policy changed")
    implementation = review.get("implementation", {})
    expected_implementation = {
        "module": "src/korea_business_lifecycle/authority_domain.py",
        "script": "scripts/authority_domain_reference.py",
        "reference_parser_dependency": "openpyxl==3.1.5",
        "current_snapshot_comparison_dependency": "pyarrow==21.0.0",
        "network_required_after_reference_download": False,
        "reference_workbook_git_tracked": False,
        "row_level_business_values_emitted": False,
    }
    if implementation != expected_implementation:
        errors.append("authority-domain implementation contract changed")
    return errors


def validate_history_authority_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("decision") != "DATE_EFFECTIVE_CURRENT_STATE_AUTHORITY_POLICY_APPROVED":
        errors.append("history authority policy decision changed")
    evidence = policy.get("evidence", {})
    expected_evidence = {
        "authority_reference": "provenance/authority_domain_reference.json",
        "deleted_partition_full_probe": "provenance/history_authority_partition_full_probe.json",
        "official_change_effective_date": "2026-07-01",
        "official_reference_attachment_sha256": "d032ff4bd63148238a8066afb7b62f96770d8a063bd6c632d4f7617e9cc407f8",
        "api_deleted_partition_post_reform_count_freeze_pairs": 96,
    }
    if evidence != expected_evidence:
        errors.append("history authority policy evidence changed")
    pre = policy.get("pre_reform", {})
    expected_pre = {
        "date_rule": "BASE_DATE < 2026-07-01",
        "policy": "CURRENT_MINUS_NEW_PLUS_DELETED",
        "numeric_authority_count": 244,
        "numeric_authority_list_sha256": "c4f1810ef53d3633b2422868f4628af024c2e26944d4d79a130c38aaa8246148",
        "new_numeric_codes_excluded": 32,
        "deleted_numeric_codes_included": 32,
    }
    if pre != expected_pre:
        errors.append("history authority pre-reform policy changed")
    post = policy.get("post_reform", {})
    expected_post = {
        "date_rule": "BASE_DATE >= 2026-07-01",
        "policy": "CURRENT_ONLY_EXCLUDE_DELETED",
        "numeric_authority_count": 244,
        "numeric_authority_list_sha256": "a666c5cb432c439f687064e3046ec2e9a84d2de708dfbe80817330e60b76ddad",
        "new_numeric_codes_included": 32,
        "deleted_numeric_codes_excluded": 32,
    }
    if post != expected_post:
        errors.append("history authority post-reform policy changed")
    overlap = policy.get("overlap_semantics", {})
    for key in (
        "same_date_old_new_union_used",
        "same_date_old_new_deduplication_required_by_policy",
        "api_queryability_defines_date_effective_membership",
        "management_number_is_source_primary_key",
    ):
        if overlap.get(key) is not False:
            errors.append(f"history authority overlap policy must keep {key}=false")
    for key in (
        "cross_reform_management_number_may_link_observations",
        "duplicate_management_number_within_one_source_date_fails_closed",
    ):
        if overlap.get(key) is not True:
            errors.append(f"history authority overlap policy must keep {key}=true")
    limits = policy.get("scope_limits", {})
    if limits.get("authority_code_domain_completeness_claimed_from_official_change_reference") is not True:
        errors.append("history authority policy must record official code-domain completeness basis")
    for key in (
        "row_level_api_completeness_guaranteed",
        "history_is_lossless_event_log",
        "aggregate_all_tokens_used_for_row_enumeration",
    ):
        if limits.get(key) is not False:
            errors.append(f"history authority policy scope limit must keep {key}=false")
    implementation = policy.get("implementation", {})
    if implementation != {
        "module": "src/korea_business_lifecycle/history_authority_policy.py",
        "script": "scripts/history_authority_policy.py",
        "network_required": False,
    }:
        errors.append("history authority policy implementation changed")
    return errors


def validate_history_nationwide_acquisition_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("decision") != "MONTHLY_NATIONWIDE_HISTORY_ACQUISITION_APPROVED_NOT_EXECUTED":
        errors.append("nationwide history acquisition plan decision changed")
    scope = plan.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("nationwide history acquisition source scope changed")
    expected_dates = [
        "20260101", "20260201", "20260301", "20260401", "20260501",
        "20260601", "20260701", "20260801", "20260901", "20260906",
    ]
    if scope.get("observation_dates") != expected_dates:
        errors.append("nationwide history acquisition dates changed")
    expected_scope = {
        "window_start": "2026-01-01",
        "window_end": "2026-09-06",
        "observation_date_count": 10,
        "numeric_authority_codes_per_date": 244,
        "planned_snapshot_tasks": 7_320,
        "same_date_old_new_union_used": False,
    }
    for key, expected in expected_scope.items():
        if scope.get(key) != expected:
            errors.append(f"nationwide history acquisition scope {key} changed")
    authority = plan.get("authority_policy", {})
    if authority != {
        "provenance": "provenance/history_authority_policy.json",
        "pre_reform": "CURRENT_MINUS_NEW_PLUS_DELETED",
        "post_reform": "CURRENT_ONLY_EXCLUDE_DELETED",
        "api_queryability_defines_date_effective_membership": False,
    }:
        errors.append("nationwide history acquisition authority policy changed")
    cadence = plan.get("cadence", {})
    expected_cadence = {
        "name": "MONTHLY_ANCHOR_PLUS_END",
        "maximum_gap_days": 31,
        "current_scale_request_lower_bound": 301_258,
        "current_scale_request_upper_bound": 308_380,
        "current_scale_cost_is_not_historical_row_volume_guarantee": True,
    }
    if cadence != expected_cadence:
        errors.append("nationwide history acquisition cadence/cost changed")
    execution = plan.get("execution", {})
    expected_execution = {
        "default_mode": "DRY_RUN",
        "execute_flag": "--execute",
        "execution_performed": False,
        "resumable_complete_snapshots_are_skipped": True,
        "multiple_existing_snapshots_for_one_task_fail_closed": True,
        "hard_network_request_cap_per_run": 400_000,
        "minimum_request_delay_seconds": 0.2,
        "maximum_pages_per_snapshot": 5_000,
        "long_running_action_requires_visible_user_command": True,
        "script": "scripts/acquire_nationwide_history.py",
    }
    if execution != expected_execution:
        errors.append("nationwide history acquisition execution contract changed")
    storage = plan.get("storage", {})
    for key in (
        "history_rows_git_tracked",
        "service_key_written_to_manifest",
        "row_level_values_emitted_by_runner_summary",
    ):
        if storage.get(key) is not False:
            errors.append(f"nationwide history storage safety must keep {key}=false")
    if storage.get("history_rows_under_git_ignored_data_root") is not True:
        errors.append("nationwide history rows must remain under ignored data root")
    semantics = plan.get("semantic_limits", {})
    for key in (
        "history_is_lossless_event_log",
        "monthly_sampling_claims_exact_transition_timestamp",
        "status_code_05_semantics_resolved",
        "reopening_vs_correction_resolved",
        "management_number_source_primary_key_claim",
    ):
        if semantics.get(key) is not False:
            errors.append(f"nationwide history semantic limit must keep {key}=false")
    return errors


def validate_history_episode_materialization_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("decision") != "PRODUCTION_EPISODE_MATERIALIZATION_PREPARED_WAITING_FOR_COMPLETE_HISTORY":
        errors.append("episode materialization plan decision changed")
    scope = plan.get("scope", {})
    expected_scope = {
        "grain": "PERMIT_STATUS_EPISODE",
        "schema": "schemas/permit_status_episode.v1.json",
        "schema_columns": 23,
        "window_start": "2026-01-01",
        "window_end": "2026-09-06",
        "required_history_snapshot_tasks": 7_320,
        "history_acquisition_plan": "provenance/history_nationwide_acquisition_plan.json",
        "authority_policy": "provenance/history_authority_policy.json",
    }
    if scope != expected_scope:
        errors.append("episode materialization plan scope changed")
    implementation = plan.get("implementation", {})
    expected_implementation = {
        "module": "src/korea_business_lifecycle/episode_materialization.py",
        "script": "scripts/materialize_history_episodes.py",
        "verifier_script": "scripts/verify_history_episode_build.py",
        "network_required": False,
        "bucket_count": 256,
        "bucket_hash": "SHA256_FIRST_BYTE_OF_MANAGEMENT_NUMBER_UTF8",
        "pyarrow_version": "21.0.0",
        "compression": "ZSTD",
    }
    if implementation != expected_implementation:
        errors.append("episode materialization plan implementation changed")
    gates = plan.get("gates", {})
    for key in (
        "complete_history_snapshot_tasks_required",
        "raw_history_page_sha256_verified_before_use",
    ):
        if gates.get(key) is not True:
            errors.append(f"episode materialization gate must keep {key}=true")
    for key in (
        "multiple_snapshots_for_one_task_allowed",
        "same_source_management_number_date_duplicate_allowed",
        "management_number_primary_key_claim",
        "history_is_lossless_event_log",
        "public_row_level_release_approved",
    ):
        if gates.get(key) is not False:
            errors.append(f"episode materialization gate must keep {key}=false")
    execution = plan.get("execution", {})
    if execution != {
        "execution_performed": False,
        "long_running_action_requires_visible_user_command": True,
        "preflight_available": True,
    }:
        errors.append("episode materialization execution state changed")
    return errors


def validate_redistribution_clarification_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("decision") != "WRITTEN_SOURCE_SPECIFIC_REDISTRIBUTION_CLARIFICATION_REQUIRED":
        errors.append("redistribution clarification decision changed")
    scope = plan.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("redistribution clarification scope must exactly match v1 sources")
    expected_pages = {
        "https://www.data.go.kr/data/15154916/openapi.do",
        "https://www.data.go.kr/data/15154921/openapi.do",
        "https://www.data.go.kr/data/15155252/openapi.do",
    }
    if set(scope.get("official_detail_pages", [])) != expected_pages:
        errors.append("redistribution clarification source pages changed")
    if scope.get("portal_policy") != "https://www.data.go.kr/ugs/selectPortalPolicyView.do":
        errors.append("redistribution clarification portal policy changed")

    evidence = plan.get("confirmed_evidence", {})
    for key in (
        "all_three_official_pages_show_no_restriction_on_permitted_use",
        "portal_policy_requires_permission_if_third_party_rights_are_included",
    ):
        if evidence.get(key) is not True:
            errors.append(f"redistribution clarification evidence must keep {key}=true")
    if evidence.get("source_use_metadata_gate") != "PASS_METADATA_CONFIRMED":
        errors.append("redistribution clarification source-use gate changed")
    for key in (
        "source_specific_third_party_rights_absence_confirmed",
        "raw_external_mirror_permission_confirmed",
        "privacy_minimized_aggregate_external_redistribution_confirmed",
    ):
        if evidence.get(key) is not False:
            errors.append(f"redistribution clarification evidence must keep {key}=false")

    questions = plan.get("questions_for_written_clarification", [])
    if len(questions) != 4:
        errors.append("redistribution clarification must retain four written questions")
    prepared = plan.get("prepared_inquiry", {})
    if prepared.get("status") != "READY_NOT_SENT" or prepared.get("language") != "ko":
        errors.append("redistribution clarification prepared inquiry state changed")
    if prepared.get("subject_ko") != "행정안전부 지방행정 인허가정보 3종 외부 재배포 가능 여부 서면 확인 요청":
        errors.append("redistribution clarification prepared inquiry subject changed")
    if prepared.get("source_identifiers") != [
        "15154916 일반음식점",
        "15154921 휴게음식점",
        "15155252 제과점영업",
    ]:
        errors.append("redistribution clarification prepared inquiry source identifiers changed")
    inquiry_body = prepared.get("body_ko", "")
    for required in ("15154916", "15154921", "15155252", "Kaggle", "k=10", "제3자 권리"):
        if required not in inquiry_body:
            errors.append(f"redistribution clarification prepared inquiry lost required token {required}")
    if prepared.get("requested_response_form") != "WRITTEN_SOURCE_SPECIFIC":
        errors.append("redistribution clarification requested response form changed")
    if prepared.get("technical_minimization_is_not_claimed_as_legal_privacy_guarantee") is not True:
        errors.append("redistribution clarification must keep k-threshold legal disclaimer")
    execution = plan.get("execution", {})
    for key in (
        "outreach_performed",
        "written_response_received",
        "publication_status_changed",
        "automatic_email_or_message_sending_enabled",
    ):
        if execution.get(key) is not False:
            errors.append(f"redistribution clarification execution must keep {key}=false")
    contacts = plan.get("contact_routes", {})
    expected_contacts = {
        "data_go_kr_inquiry_page": "https://www.data.go.kr/bbs/faq/selectFaqList.do",
        "portal_support_email": "opendata_help@nia.or.kr",
        "portal_support_phone": "1566-0025",
        "provider": "행정안전부",
        "management_department": "지역디지털협력과",
        "note": "The portal support route can direct the question; source-specific written clarification should be archived before any gate changes.",
    }
    if contacts != expected_contacts:
        errors.append("redistribution clarification contact routes changed")
    gates = plan.get("gates", {})
    if gates.get("raw_external_mirror") != "UNRESOLVED_THIRD_PARTY_RIGHTS_CLARIFICATION":
        errors.append("redistribution clarification raw mirror gate changed")
    if gates.get("privacy_minimized_aggregate_redistribution") != "UNRESOLVED":
        errors.append("redistribution clarification aggregate gate changed")
    if gates.get("row_level_public_release") != "BLOCKED" or gates.get("aggregate_publication") != "BLOCKED":
        errors.append("redistribution clarification publication gates must remain blocked")
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
    if next_gate.get("phase") != "Phase 7 Aggregate Publication Release":
        errors.append("next gate must be Phase 7 aggregate publication release")
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
    if next_gate.get("public_permit_aggregate") != "provenance/public_permit_aggregate.json":
        errors.append("public permit aggregate result reference changed")
    if next_gate.get("public_permit_aggregate_status") != "COMPLETED_PASS_VERIFIED_NOT_PUBLICATION_APPROVED":
        errors.append("public permit aggregate status changed")
    if next_gate.get("bounded_episode_reconstruction") != "provenance/bounded_episode_reconstruction.json":
        errors.append("bounded episode reconstruction evidence reference changed")
    if next_gate.get("bounded_episode_reconstruction_status") != (
        "IMPLEMENTED_SYNTHETIC_VALIDATED_PRODUCTION_DISABLED"
    ):
        errors.append("bounded episode reconstruction status changed")
    if next_gate.get("history_observation_strategy") != "provenance/history_observation_strategy.json":
        errors.append("history observation strategy evidence reference changed")
    if next_gate.get("history_observation_strategy_status") != "OPTIONAL_MONTHLY_CADENCE_AVAILABLE":
        errors.append("history observation strategy status changed")
    if next_gate.get("authority_domain_reference") != "provenance/authority_domain_reference.json":
        errors.append("authority-domain reference evidence changed")
    if next_gate.get("authority_domain_reference_status") != (
        "DATE_EFFECTIVE_PRE_244_POST_244_APPROVED"
    ):
        errors.append("authority-domain reference status changed")
    if next_gate.get("history_authority_partition_findings") != (
        "provenance/history_authority_partition_findings.json"
    ):
        errors.append("history authority-partition findings reference changed")
    if next_gate.get("history_authority_partition_findings_status") != "BOUNDED_FREEZE_PATTERN_CONFIRMED":
        errors.append("history authority-partition findings status changed")
    if next_gate.get("history_authority_partition_probe_plan") != (
        "provenance/history_authority_partition_probe_plan.json"
    ):
        errors.append("history authority-partition probe plan reference changed")
    if next_gate.get("history_authority_partition_probe_status") != (
        "FULL_32_COUNT_PROBE_COMPLETED_VERIFIED"
    ):
        errors.append("history authority-partition probe status changed")
    if next_gate.get("history_authority_partition_full_probe") != (
        "provenance/history_authority_partition_full_probe.json"
    ):
        errors.append("history authority-partition full-probe reference changed")
    if next_gate.get("history_authority_partition_full_probe_status") != (
        "POST_REFORM_COUNT_FREEZE_96_OF_96_CONFIRMED"
    ):
        errors.append("history authority-partition full-probe status changed")
    if next_gate.get("history_authority_policy") != "provenance/history_authority_policy.json":
        errors.append("history authority policy reference changed")
    if next_gate.get("history_authority_policy_status") != (
        "DATE_EFFECTIVE_CURRENT_STATE_AUTHORITY_POLICY_APPROVED"
    ):
        errors.append("history authority policy status changed")
    if next_gate.get("history_nationwide_acquisition_plan") != (
        "provenance/history_nationwide_acquisition_plan.json"
    ):
        errors.append("history nationwide acquisition plan reference changed")
    if next_gate.get("history_nationwide_acquisition_status") != "OPTIONAL_NOT_REQUIRED_FOR_V1":
        errors.append("history nationwide acquisition status changed")
    if next_gate.get("history_episode_materialization_plan") != (
        "provenance/history_episode_materialization_plan.json"
    ):
        errors.append("history episode materialization plan reference changed")
    if next_gate.get("history_episode_materialization_status") != "OPTIONAL_REQUIRES_COMPLETE_HISTORY":
        errors.append("history episode materialization status changed")
    if next_gate.get("redistribution_clarification_plan") != "provenance/redistribution_clarification_plan.json":
        errors.append("redistribution clarification plan reference changed")
    if next_gate.get("redistribution_clarification_status") != "OPTIONAL_ADDITIONAL_CONFIRMATION":
        errors.append("redistribution clarification status changed")
    if next_gate.get("v1_release_scope") != "provenance/v1_release_scope.json":
        errors.append("v1 release scope reference changed")
    if next_gate.get("v1_release_scope_status") != "LOCAL_V1_CORE_COMPLETE_AGGREGATE_KAGGLE_APPROVED":
        errors.append("v1 release scope status changed")
    return errors


def validate_bounded_episode_reconstruction(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("decision") != (
        "BOUNDED_EPISODE_RECONSTRUCTOR_IMPLEMENTED_SYNTHETIC_VALIDATED_PRODUCTION_DISABLED"
    ):
        errors.append("bounded episode reconstruction decision changed")
    scope = review.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("bounded episode reconstruction scope must exactly match v1 sources")
    if scope.get("episode_schema") != "schemas/permit_status_episode.v1.json":
        errors.append("bounded episode reconstruction schema reference changed")
    if scope.get("maximum_observations_per_call") != 100_000:
        errors.append("bounded episode reconstruction observation cap changed")
    for key in ("bounded_in_memory_only",):
        if scope.get(key) is not True:
            errors.append(f"bounded episode reconstruction scope must keep {key}=true")
    for key in (
        "history_acquisition_performed",
        "nationwide_production_reconstruction_enabled",
        "public_row_level_release_approved",
    ):
        if scope.get(key) is not False:
            errors.append(f"bounded episode reconstruction scope must keep {key}=false")

    input_contract = review.get("input_contract", {})
    for key in (
        "one_observation_per_permit_date_required",
        "observations_outside_declared_window_fail_closed",
        "duplicate_permit_date_observations_fail_closed",
    ):
        if input_contract.get(key) is not True:
            errors.append(f"bounded episode input contract must keep {key}=true")
    for key in (
        "missing_history_is_interpolated",
        "permit_date_used_as_episode_start",
        "management_number_primary_key_claim",
    ):
        if input_contract.get(key) is not False:
            errors.append(f"bounded episode input contract must keep {key}=false")

    episode = review.get("episode_contract", {})
    expected_state = [
        "source_status_code",
        "source_status_name",
        "source_detail_status_code",
        "source_detail_status_name",
    ]
    if episode.get("state_partition_fields") != expected_state:
        errors.append("bounded episode state partition fields changed")
    if episode.get("first_episode_start_censoring") != "LEFT_CENSORED":
        errors.append("bounded episode first-start censoring changed")
    if episode.get("between_episode_boundary_censoring") != "INTERVAL_CENSORED":
        errors.append("bounded episode transition censoring changed")
    if episode.get("last_episode_end_censoring") != "RIGHT_CENSORED":
        errors.append("bounded episode final-end censoring changed")
    for key in ("closure_date_partitions_episode", "episode_number_persistent_identity", "exact_transition_time_claimed"):
        if episode.get(key) is not False:
            errors.append(f"bounded episode contract must keep {key}=false")

    semantics = review.get("semantic_safety", {})
    for key in (
        "canonical_status_mapping_enabled",
        "status_code_03_irreversible",
        "status_code_05_semantics_resolved",
        "reopening_vs_correction_resolved",
        "closure_date_permanent_terminal_event",
        "terminal_event_claim",
    ):
        if semantics.get(key) is not False:
            errors.append(f"bounded episode semantic safety must keep {key}=false")

    implementation = review.get("implementation", {})
    if implementation.get("module") != "src/korea_business_lifecycle/episode_reconstruction.py":
        errors.append("bounded episode reconstruction module reference changed")
    if implementation.get("function") != "reconstruct_bounded_status_episodes":
        errors.append("bounded episode reconstruction function reference changed")
    if implementation.get("default_max_bounded_observations") != 100_000:
        errors.append("bounded episode reconstruction default cap changed")
    return errors


def validate_history_observation_strategy(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("decision") != "MONTHLY_HISTORY_OBSERVATION_CADENCE_APPROVED_ACQUISITION_NOT_YET_EXECUTED":
        errors.append("history observation strategy decision changed")
    scope = review.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("history observation strategy scope must exactly match v1 sources")
    if scope.get("window_start") != "2026-01-01" or scope.get("window_end") != "2026-09-06":
        errors.append("history observation strategy window changed")
    if scope.get("calendar_days_inclusive") != 249:
        errors.append("history observation strategy calendar length changed")
    for key in ("network_access_performed", "production_episode_reconstruction_enabled"):
        if scope.get(key) is not False:
            errors.append(f"history observation strategy must keep {key}=false")
    if scope.get("production_history_acquisition_approved") is not True:
        errors.append("history observation strategy must approve production history acquisition")

    paging = review.get("paging_basis", {})
    expected_paging = {
        "current_rows_total": 3_010_802,
        "observed_authority_count": 230,
        "manual_reference_authority_count": 245,
        "current_official_numeric_authority_count": 244,
        "current_official_aggregate_token_count": 16,
        "official_deleted_numeric_authority_count": 32,
        "history_window_candidate_numeric_authority_union_count": 276,
        "observed_count_gap_vs_current_official_numeric": 14,
        "observed_count_gap_vs_history_window_candidate_union": 46,
        "observed_authority_domain_authoritatively_complete": False,
        "current_official_numeric_domain_authoritatively_complete_for_reference_date": True,
        "exact_current_official_numeric_authority_codes_ingested": True,
        "exact_deleted_numeric_authority_codes_ingested": True,
        "history_window_date_effective_numeric_enumeration_ready": True,
        "date_effective_history_authority_filter_semantics_verified": False,
        "future_authority_reference_refresh_required": True,
        "page_size": 100,
        "pre_reform_exact_numeric_authority_count": 244,
        "pre_reform_request_lower_bound_per_asof_date": 30_109,
        "pre_reform_request_upper_bound_per_asof_date": 30_838,
        "post_reform_current_domain_probe_requests_per_source_per_asof_date": 14,
        "post_reform_current_domain_probe_requests_total_per_asof_date": 42,
        "post_reform_request_lower_bound_per_asof_date": 30_151,
        "post_reform_request_upper_bound_per_asof_date": 30_838,
        "cost_basis": "CURRENT_ROW_SCALE_DATE_EFFECTIVE_244_CODE_DOMAINS_PRE_REFORM_CURRENT_MINUS_NEW_PLUS_DELETED_POST_REFORM_CURRENT_ONLY_POST_REFORM_230_OBSERVED_PLUS_14_ZERO_PROBES_NOT_HISTORICAL_ROW_COUNT_FORECAST",
    }
    for key, expected in expected_paging.items():
        if paging.get(key) != expected:
            errors.append(f"history observation paging basis {key} changed")
    per_source = paging.get("per_source", [])
    expected_sources = {
        "general_restaurants": (2_295_369, 22_954, 23_183, 244, 22_954, 23_197, 14, 22_968, 23_197),
        "rest_cafes": (645_952, 6_460, 6_689, 244, 6_460, 6_703, 14, 6_474, 6_703),
        "bakeries": (69_481, 695, 924, 244, 695, 938, 14, 709, 938),
    }
    if {item.get("source_key") for item in per_source} != V1_SOURCE_KEYS or len(per_source) != 3:
        errors.append("history observation per-source paging scope changed")
    for item in per_source:
        source_key = item.get("source_key")
        expected = expected_sources.get(source_key)
        observed = (
            item.get("current_rows"),
            item.get("observed_current_nonempty_request_lower_bound_per_asof_date"),
            item.get("observed_current_nonempty_request_upper_bound_per_asof_date"),
            item.get("pre_reform_exact_authority_count"),
            item.get("pre_reform_request_lower_bound_per_asof_date"),
            item.get("pre_reform_request_upper_bound_per_asof_date"),
            item.get("post_reform_current_domain_probe_requests_per_asof_date"),
            item.get("post_reform_request_lower_bound_per_asof_date"),
            item.get("post_reform_request_upper_bound_per_asof_date"),
        )
        if expected is not None and observed != expected:
            errors.append(f"{source_key}: history observation request bounds changed")

    scenarios = {item.get("name"): item for item in review.get("scenarios", [])}
    expected_scenarios = {
        "ENDPOINTS_ONLY": (2, 1, 1, 248, 60_260, 61_676),
        "MONTHLY_ANCHOR_PLUS_END": (10, 6, 4, 31, 301_258, 308_380),
        "WEEKLY_7D_PLUS_END": (37, 26, 11, 7, 1_114_495, 1_141_006),
        "DAILY": (249, 181, 68, 1, 7_499_997, 7_678_662),
    }
    if set(scenarios) != set(expected_scenarios):
        errors.append("history observation scenario set changed")
    for name, expected in expected_scenarios.items():
        item = scenarios.get(name, {})
        observed = (
            item.get("observation_dates"),
            item.get("pre_reform_observation_dates"),
            item.get("post_reform_observation_dates"),
            item.get("maximum_gap_days"),
            item.get("request_lower_bound"),
            item.get("request_upper_bound"),
        )
        if observed != expected:
            errors.append(f"{name}: history observation scenario changed")
        expected_approved = name == "MONTHLY_ANCHOR_PLUS_END"
        if item.get("approved_for_production") is not expected_approved:
            errors.append(f"{name}: history observation scenario approval changed")

    selected = review.get("selected_cadence", {})
    expected_selected = {
        "name": "MONTHLY_ANCHOR_PLUS_END",
        "observation_dates": 10,
        "maximum_gap_days": 31,
        "current_scale_request_lower_bound": 301_258,
        "current_scale_request_upper_bound": 308_380,
        "hard_network_request_cap_per_run": 400_000,
        "request_delay_seconds": 0.2,
        "approved_for_production_history_acquisition": True,
        "approval_does_not_make_history_lossless_event_log": True,
        "current_scale_cost_is_not_historical_row_volume_guarantee": True,
    }
    if selected != expected_selected:
        errors.append("history observation selected cadence changed")

    limits = review.get("semantic_limits", {})
    for key in (
        "as_of_snapshots_are_lossless_event_log",
        "daily_sampling_proves_no_multiple_intraday_transitions",
        "exact_transition_timestamp_claimed",
        "status_code_05_semantics_resolved",
        "reopening_vs_correction_resolved",
    ):
        if limits.get(key) is not False:
            errors.append(f"history observation semantic limit must keep {key}=false")
    partition = review.get("authority_partition_semantics", {})
    expected_partition = {
        "findings": "provenance/history_authority_partition_findings.json",
        "full_deleted_count_probe_plan": "provenance/history_authority_partition_probe_plan.json",
        "full_deleted_count_probe_result": "provenance/history_authority_partition_full_probe.json",
        "date_effective_current_state_policy": "provenance/history_authority_policy.json",
        "authenticated_execution_available": True,
        "bounded_deleted_partition_post_reform_freeze_confirmed": True,
        "bounded_current_partition_post_reform_evolution_confirmed": True,
        "current_plus_deleted_union_semantically_equivalent_to_current_snapshot": False,
        "full_32_deleted_count_probe_executed": True,
        "full_32_deleted_count_probe_request_cap": 384,
        "post_reform_count_frozen_source_authority_pairs": 96,
        "post_reform_current_state_enumeration_policy": "CURRENT_244_ONLY_EXCLUDE_DELETED_32",
        "pre_reform_current_state_enumeration_policy": "CURRENT_MINUS_NEW_PLUS_DELETED",
        "pre_reform_authority_domain_resolved": True,
        "old_new_overlap_requires_same_date_deduplication": False,
        "cross_reform_permit_continuity_still_uses_mng_no_only_as_linkage_candidate": True,
    }
    if partition != expected_partition:
        errors.append("history observation authority-partition semantics changed")
    implementation = review.get("implementation", {})
    if implementation.get("module") != "src/korea_business_lifecycle/history_observation_strategy.py":
        errors.append("history observation strategy module reference changed")
    if implementation.get("script") != "scripts/history_observation_strategy.py":
        errors.append("history observation strategy script reference changed")
    if implementation.get("network_required") is not False:
        errors.append("history observation strategy must remain network-free")
    if review.get("authority_domain_reference") != "provenance/authority_domain_reference.json":
        errors.append("history observation strategy authority-domain reference changed")
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
    if scope.get("execution_status") != "COMPLETED_PASS_VERIFIED":
        errors.append("public permit aggregate plan must record completed verified execution")
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
    if plan.get("result_provenance") != "provenance/public_permit_aggregate.json":
        errors.append("public permit aggregate result provenance reference changed")
    return errors


def validate_public_permit_aggregate(review: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("decision") != "LOCAL_PRIVACY_MINIMIZED_PERMIT_AGGREGATE_MATERIALIZED_AND_VERIFIED":
        errors.append("public permit aggregate result decision changed")

    scope = review.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("public permit aggregate result scope must exactly match v1 sources")
    expected_scalars = {
        "parent_permit_build_id": "permit-v1-9908225df465e2ff",
        "aggregate_build_id": "permit-public-agg-v1-bedd874de6619bee",
        "rows_scanned": 3_010_802,
        "aggregate_cells_total_before_suppression": 297_195,
        "aggregate_cells_released_candidate": 67_267,
        "aggregate_cells_suppressed": 229_928,
        "released_source_rows": 2_383_689,
        "suppressed_source_rows": 627_113,
        "output_bytes": 108_019,
        "minimum_cell_count": 10,
        "redistribution_status": "UNRESOLVED",
    }
    for key, expected in expected_scalars.items():
        if scope.get(key) != expected:
            errors.append(f"public permit aggregate result {key} changed")
    for key in ("row_level_public_projection_approved", "aggregate_publication_approved"):
        if scope.get(key) is not False:
            errors.append(f"public permit aggregate result must keep {key}=false")
    if scope.get("aggregate_cells_released_candidate", 0) + scope.get("aggregate_cells_suppressed", 0) != scope.get(
        "aggregate_cells_total_before_suppression"
    ):
        errors.append("public permit aggregate cell accounting changed")
    if scope.get("released_source_rows", 0) + scope.get("suppressed_source_rows", 0) != scope.get("rows_scanned"):
        errors.append("public permit aggregate source-row accounting changed")

    output = review.get("output", {})
    if output.get("file") != "permit_aggregate.parquet":
        errors.append("public permit aggregate output filename changed")
    if output.get("sha256") != "112fbec3187b2d77df2744edb878fa0f3ecb850cf675496cd4383404092911fb":
        errors.append("public permit aggregate output SHA-256 changed")
    if output.get("parquet_row_groups") != 2:
        errors.append("public permit aggregate row-group count changed")
    if output.get("schema") != "schemas/public_permit_aggregate.v1.json":
        errors.append("public permit aggregate result schema reference changed")
    if output.get("schema_sha256") != "35b3145a3e6aace98881b9d0efb8c6298c740130f71f57b78f45aee74a480a45":
        errors.append("public permit aggregate result schema SHA-256 changed")

    verification = review.get("verification", {})
    if verification.get("status") != "PASS":
        errors.append("public permit aggregate independent verification did not pass")
    for key in (
        "parent_build_verified",
        "manifest_verified",
        "parquet_hash_verified",
        "parquet_schema_verified",
        "zstd_verified",
        "suppression_invariants_verified",
    ):
        if verification.get(key) is not True:
            errors.append(f"public permit aggregate verification must keep {key}=true")
    if verification.get("row_level_values_returned") is not False:
        errors.append("public permit aggregate verification must not return row-level values")

    privacy = review.get("privacy", {})
    for key in (
        "direct_or_linkable_row_fields_emitted",
        "precise_coordinates_emitted",
        "exact_addresses_emitted",
        "business_names_emitted",
        "management_numbers_emitted",
        "minimum_cell_count_is_legal_privacy_guarantee",
        "publication_status_changed",
    ):
        if privacy.get(key) is not False:
            errors.append(f"public permit aggregate privacy evidence must keep {key}=false")
    if privacy.get("technical_minimization_verified") is not True:
        errors.append("public permit aggregate technical minimization must remain verified")
    return errors
