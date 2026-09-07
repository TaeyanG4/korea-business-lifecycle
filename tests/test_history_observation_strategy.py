from __future__ import annotations

import pytest

from korea_business_lifecycle.history_observation_strategy import (
    HistoryObservationStrategyError,
    history_observation_strategy_plan,
)


def test_current_scale_request_bounds_are_deterministic_without_network() -> None:
    plan = history_observation_strategy_plan()
    assert plan["window"] == {
        "start_date": "2026-01-01",
        "end_date": "2026-09-06",
        "calendar_days_inclusive": 249,
    }
    paging = plan["paging_basis"]
    assert paging["current_rows_total"] == 3_010_802
    assert paging["observed_authority_count"] == 230
    assert paging["authority_domain_authoritatively_complete"] is False
    assert paging["page_size"] == 100
    assert paging["request_lower_bound_per_asof_date"] == 30_109
    assert paging["request_upper_bound_per_asof_date"] == 30_796
    assert [(item["source_key"], item["request_lower_bound_per_asof_date"], item["request_upper_bound_per_asof_date"]) for item in paging["per_source"]] == [
        ("general_restaurants", 22_954, 23_183),
        ("rest_cafes", 6_460, 6_689),
        ("bakeries", 695, 924),
    ]
    assert plan["network_access_performed"] is False


def test_scenarios_quantify_cost_without_approving_a_cadence() -> None:
    plan = history_observation_strategy_plan()
    scenarios = {item["name"]: item for item in plan["scenarios"]}
    assert scenarios["ENDPOINTS_ONLY"] == {
        "name": "ENDPOINTS_ONLY",
        "observation_dates": 2,
        "maximum_gap_days": 248,
        "request_lower_bound": 60_218,
        "request_upper_bound": 61_592,
        "approved_for_production": False,
    }
    assert scenarios["MONTHLY_ANCHOR_PLUS_END"]["observation_dates"] == 10
    assert scenarios["MONTHLY_ANCHOR_PLUS_END"]["maximum_gap_days"] == 31
    assert scenarios["MONTHLY_ANCHOR_PLUS_END"]["request_lower_bound"] == 301_090
    assert scenarios["MONTHLY_ANCHOR_PLUS_END"]["request_upper_bound"] == 307_960
    assert scenarios["WEEKLY_7D_PLUS_END"]["observation_dates"] == 37
    assert scenarios["WEEKLY_7D_PLUS_END"]["maximum_gap_days"] == 7
    assert scenarios["WEEKLY_7D_PLUS_END"]["request_lower_bound"] == 1_114_033
    assert scenarios["WEEKLY_7D_PLUS_END"]["request_upper_bound"] == 1_139_452
    assert scenarios["DAILY"]["observation_dates"] == 249
    assert scenarios["DAILY"]["maximum_gap_days"] == 1
    assert scenarios["DAILY"]["request_lower_bound"] == 7_497_141
    assert scenarios["DAILY"]["request_upper_bound"] == 7_668_204
    assert all(item["approved_for_production"] is False for item in scenarios.values())


def test_daily_asof_sampling_is_not_promoted_to_lossless_event_history() -> None:
    plan = history_observation_strategy_plan()
    limits = plan["semantic_limits"]
    assert limits["as_of_snapshots_are_lossless_event_log"] is False
    assert limits["daily_sampling_proves_no_multiple_intraday_transitions"] is False
    assert limits["exact_transition_timestamp_claimed"] is False
    assert limits["status_code_05_semantics_resolved"] is False
    assert limits["reopening_vs_correction_resolved"] is False
    assert plan["production_episode_reconstruction_enabled"] is False
    assert plan["decision"] == (
        "NO_NATIONWIDE_OBSERVATION_CADENCE_APPROVED_COST_AND_COMPLETENESS_REVIEW_REQUIRED"
    )


def test_invalid_window_fails_closed() -> None:
    with pytest.raises(HistoryObservationStrategyError, match="start must be before end"):
        history_observation_strategy_plan(start_date="2026-09-06", end_date="2026-09-06")
