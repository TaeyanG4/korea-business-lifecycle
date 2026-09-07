from __future__ import annotations

import pytest

from korea_business_lifecycle.history_observation_strategy import (
    HistoryObservationStrategyError,
    history_observation_strategy_plan,
)
from korea_business_lifecycle.provenance import load_history_observation_strategy


def test_current_scale_request_bounds_are_deterministic_without_network() -> None:
    plan = history_observation_strategy_plan()
    assert plan["scope"] == {
        "sources": ["general_restaurants", "rest_cafes", "bakeries"],
        "window_start": "2026-01-01",
        "window_end": "2026-09-06",
        "calendar_days_inclusive": 249,
        "network_access_performed": False,
        "production_episode_reconstruction_enabled": False,
    }
    paging = plan["paging_basis"]
    assert paging["current_rows_total"] == 3_010_802
    assert paging["observed_authority_count"] == 230
    assert paging["manual_reference_authority_count"] == 245
    assert paging["current_official_numeric_authority_count"] == 244
    assert paging["current_official_aggregate_token_count"] == 16
    assert paging["official_deleted_numeric_authority_count"] == 32
    assert paging["history_window_candidate_numeric_authority_union_count"] == 276
    assert paging["observed_count_gap_vs_current_official_numeric"] == 14
    assert paging["observed_count_gap_vs_history_window_candidate_union"] == 46
    assert paging["observed_authority_domain_authoritatively_complete"] is False
    assert paging["current_official_numeric_domain_authoritatively_complete_for_reference_date"] is True
    assert paging["exact_current_official_numeric_authority_codes_ingested"] is True
    assert paging["exact_deleted_numeric_authority_codes_ingested"] is True
    assert paging["date_effective_history_authority_filter_semantics_verified"] is False
    assert paging["history_window_date_effective_numeric_enumeration_ready"] is False
    assert paging["page_size"] == 100
    assert paging["pre_reform_candidate_union_probe_requests_per_source_per_asof_date"] == 46
    assert paging["pre_reform_candidate_union_probe_requests_total_per_asof_date"] == 138
    assert paging["pre_reform_request_lower_bound_per_asof_date"] == 30_247
    assert paging["pre_reform_request_upper_bound_per_asof_date"] == 30_934
    assert paging["post_reform_current_domain_probe_requests_per_source_per_asof_date"] == 14
    assert paging["post_reform_current_domain_probe_requests_total_per_asof_date"] == 42
    assert paging["post_reform_request_lower_bound_per_asof_date"] == 30_151
    assert paging["post_reform_request_upper_bound_per_asof_date"] == 30_838
    assert paging["cost_basis"] == (
        "CURRENT_ROW_SCALE_SPLIT_BY_20260701_POLICY_PRE_REFORM_276_CANDIDATE_UNION_WITH_46_PROBES_PER_SOURCE_POST_REFORM_CURRENT_244_ONLY_WITH_14_PROBES_PER_SOURCE_NOT_HISTORICAL_ROW_COUNT_FORECAST"
    )
    assert [(item["source_key"], item["pre_reform_request_lower_bound_per_asof_date"], item["pre_reform_request_upper_bound_per_asof_date"], item["post_reform_request_lower_bound_per_asof_date"], item["post_reform_request_upper_bound_per_asof_date"]) for item in paging["per_source"]] == [
        ("general_restaurants", 23_000, 23_229, 22_968, 23_197),
        ("rest_cafes", 6_506, 6_735, 6_474, 6_703),
        ("bakeries", 741, 970, 709, 938),
    ]
    assert plan["implementation"]["network_required"] is False


def test_scenarios_quantify_cost_without_approving_a_cadence() -> None:
    plan = history_observation_strategy_plan()
    scenarios = {item["name"]: item for item in plan["scenarios"]}
    assert scenarios["ENDPOINTS_ONLY"] == {
        "name": "ENDPOINTS_ONLY",
        "observation_dates": 2,
        "pre_reform_observation_dates": 1,
        "post_reform_observation_dates": 1,
        "maximum_gap_days": 248,
        "request_lower_bound": 60_398,
        "request_upper_bound": 61_772,
        "approved_for_production": False,
    }
    assert scenarios["MONTHLY_ANCHOR_PLUS_END"]["observation_dates"] == 10
    assert scenarios["MONTHLY_ANCHOR_PLUS_END"]["maximum_gap_days"] == 31
    assert scenarios["MONTHLY_ANCHOR_PLUS_END"]["pre_reform_observation_dates"] == 6
    assert scenarios["MONTHLY_ANCHOR_PLUS_END"]["post_reform_observation_dates"] == 4
    assert scenarios["MONTHLY_ANCHOR_PLUS_END"]["request_lower_bound"] == 302_086
    assert scenarios["MONTHLY_ANCHOR_PLUS_END"]["request_upper_bound"] == 308_956
    assert scenarios["WEEKLY_7D_PLUS_END"]["observation_dates"] == 37
    assert scenarios["WEEKLY_7D_PLUS_END"]["maximum_gap_days"] == 7
    assert scenarios["WEEKLY_7D_PLUS_END"]["pre_reform_observation_dates"] == 26
    assert scenarios["WEEKLY_7D_PLUS_END"]["post_reform_observation_dates"] == 11
    assert scenarios["WEEKLY_7D_PLUS_END"]["request_lower_bound"] == 1_118_083
    assert scenarios["WEEKLY_7D_PLUS_END"]["request_upper_bound"] == 1_143_502
    assert scenarios["DAILY"]["observation_dates"] == 249
    assert scenarios["DAILY"]["maximum_gap_days"] == 1
    assert scenarios["DAILY"]["pre_reform_observation_dates"] == 181
    assert scenarios["DAILY"]["post_reform_observation_dates"] == 68
    assert scenarios["DAILY"]["request_lower_bound"] == 7_524_975
    assert scenarios["DAILY"]["request_upper_bound"] == 7_696_038
    assert all(item["approved_for_production"] is False for item in scenarios.values())


def test_daily_asof_sampling_is_not_promoted_to_lossless_event_history() -> None:
    plan = history_observation_strategy_plan()
    limits = plan["semantic_limits"]
    assert limits["as_of_snapshots_are_lossless_event_log"] is False
    assert limits["daily_sampling_proves_no_multiple_intraday_transitions"] is False
    assert limits["exact_transition_timestamp_claimed"] is False
    assert limits["status_code_05_semantics_resolved"] is False
    assert limits["reopening_vs_correction_resolved"] is False
    partition = plan["authority_partition_semantics"]
    assert partition["authenticated_execution_available"] is True
    assert partition["bounded_deleted_partition_post_reform_freeze_confirmed"] is True
    assert partition["bounded_current_partition_post_reform_evolution_confirmed"] is True
    assert partition["current_plus_deleted_union_semantically_equivalent_to_current_snapshot"] is False
    assert partition["full_32_deleted_count_probe_executed"] is True
    assert partition["full_32_deleted_count_probe_request_cap"] == 384
    assert partition["post_reform_count_frozen_source_authority_pairs"] == 96
    assert partition["post_reform_current_state_enumeration_policy"] == "CURRENT_244_ONLY_EXCLUDE_DELETED_32"
    assert partition["pre_reform_current_plus_deleted_union_policy"] == "UNRESOLVED_DO_NOT_AUTO_UNION"
    assert partition["pre_reform_authority_domain_resolved"] is False
    assert plan["scope"]["production_episode_reconstruction_enabled"] is False
    assert plan["decision"] == (
        "NO_NATIONWIDE_OBSERVATION_CADENCE_APPROVED_PRE_REFORM_AUTHORITY_DOMAIN_AND_COST_REVIEW_REQUIRED"
    )


def test_invalid_window_fails_closed() -> None:
    with pytest.raises(HistoryObservationStrategyError, match="start must be before end"):
        history_observation_strategy_plan(start_date="2026-09-06", end_date="2026-09-06")


def test_default_plan_matches_tracked_provenance() -> None:
    assert history_observation_strategy_plan() == load_history_observation_strategy()
