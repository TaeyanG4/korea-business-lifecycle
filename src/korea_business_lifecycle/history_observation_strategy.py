from __future__ import annotations

import math
from calendar import monthrange
from datetime import date, timedelta
from typing import Any

from .provenance import (
    load_authority_domain_reference,
    load_history_authority_partition_findings,
    load_history_authority_partition_probe_plan,
    load_history_review,
    load_observed_snapshot_summary,
)


class HistoryObservationStrategyError(RuntimeError):
    """Raised when a nationwide history cost scenario cannot be bounded safely."""


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HistoryObservationStrategyError(f"invalid strategy date: {value}") from exc


def _monthly_dates(start: date, end: date) -> list[date]:
    values = [start]
    year, month = start.year, start.month
    while True:
        month += 1
        if month == 13:
            year += 1
            month = 1
        day = min(start.day, monthrange(year, month)[1])
        candidate = date(year, month, day)
        if candidate >= end:
            break
        values.append(candidate)
    if values[-1] != end:
        values.append(end)
    return values


def _fixed_step_dates(start: date, end: date, *, days: int) -> list[date]:
    if days < 1:
        raise HistoryObservationStrategyError("step days must be positive")
    values = [start]
    cursor = start
    while cursor + timedelta(days=days) < end:
        cursor += timedelta(days=days)
        values.append(cursor)
    if values[-1] != end:
        values.append(end)
    return values


def _max_gap_days(values: list[date]) -> int:
    if len(values) < 2:
        return 0
    return max((right - left).days for left, right in zip(values, values[1:]))


def _page_bounds(rows: int, *, authority_count: int, page_size: int) -> tuple[int, int]:
    if rows < authority_count:
        raise HistoryObservationStrategyError(
            "current rows cannot support the observed non-empty authority count"
        )
    lower = max(authority_count, math.ceil(rows / page_size))
    upper = lower + authority_count - 1
    return lower, upper


def history_observation_strategy_plan(
    *,
    start_date: str = "2026-01-01",
    end_date: str = "2026-09-06",
) -> dict[str, Any]:
    """Compare non-approved nationwide as-of observation cost scenarios without network I/O."""

    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start >= end:
        raise HistoryObservationStrategyError("strategy start must be before end")

    summary = load_observed_snapshot_summary()
    review = load_history_review()
    authority_reference = load_authority_domain_reference()
    authority_partition_findings = load_history_authority_partition_findings()
    authority_partition_probe_plan = load_history_authority_partition_probe_plan()
    common = review["common_contract"]
    authority_domain = common["observed_current_authority_code_domain"]
    authority_count = int(authority_domain["distinct_count"])
    official = authority_reference["official_reference"]
    gate = authority_reference["ingestion_gate"]
    cost_policy = authority_reference["cost_model_policy"]
    manual_reference_count = int(official["manual_claim_count"])
    official_authority_count = int(official["active_numeric_code_count"])
    deleted_authority_count = int(
        authority_reference["history_window_change_reference"][
            "deleted_numeric_authority_count"
        ]
    )
    candidate_union_count = int(
        authority_reference["history_window_change_reference"][
            "current_plus_deleted_candidate_union_count"
        ]
    )
    current_absent_candidate_count = int(
        cost_policy["current_scale_candidate_union_absent_authority_count_per_source"]
    )
    page_size = int(common["max_num_of_rows"])
    if (
        authority_count != 230
        or manual_reference_count != 245
        or official_authority_count != 244
        or deleted_authority_count != 32
        or candidate_union_count != 276
        or current_absent_candidate_count != 46
        or page_size != 100
    ):
        raise HistoryObservationStrategyError("tracked history paging assumptions changed")
    if gate["exact_current_official_numeric_code_values_ingested"] is not True:
        raise HistoryObservationStrategyError("exact current official authority domain is not ingested")
    if gate["exact_deleted_numeric_code_values_ingested"] is not True:
        raise HistoryObservationStrategyError("deleted authority-code change reference is not ingested")
    if gate["history_window_date_effective_numeric_enumeration_ready"] is not False:
        raise HistoryObservationStrategyError("history-window enumeration must remain unapproved")
    if cost_policy["current_unobserved_authorities_may_be_assumed_historically_empty"] is not False:
        raise HistoryObservationStrategyError("historical-empty authority assumption must remain disabled")
    if authority_partition_findings["interpretation"][
        "deleted_partition_frozen_after_reform_in_bounded_full_row_sample"
    ] is not True:
        raise HistoryObservationStrategyError("bounded deleted-authority freeze evidence changed")
    if authority_partition_findings["interpretation"][
        "current_plus_deleted_union_is_semantically_equivalent_to_current_snapshot"
    ] is not False:
        raise HistoryObservationStrategyError("candidate authority union must not be promoted to current-state semantics")
    if authority_partition_probe_plan["execution"]["execution_performed"] is not False:
        raise HistoryObservationStrategyError("full deleted-authority count probe execution state changed")

    per_source: list[dict[str, Any]] = []
    lower_per_date = 0
    upper_per_date = 0
    for item in summary["categories"]:
        rows = int(item["rows"])
        lower, upper = _page_bounds(
            rows,
            authority_count=authority_count,
            page_size=page_size,
        )
        candidate_lower = lower + current_absent_candidate_count
        candidate_upper = upper + current_absent_candidate_count
        lower_per_date += candidate_lower
        upper_per_date += candidate_upper
        per_source.append(
            {
                "source_key": str(item["source_key"]),
                "current_rows": rows,
                "observed_nonempty_request_lower_bound_per_asof_date": lower,
                "observed_nonempty_request_upper_bound_per_asof_date": upper,
                "current_scale_candidate_union_probe_requests_per_asof_date": current_absent_candidate_count,
                "request_lower_bound_per_asof_date": candidate_lower,
                "request_upper_bound_per_asof_date": candidate_upper,
            }
        )

    scenarios = {
        "ENDPOINTS_ONLY": [start, end],
        "MONTHLY_ANCHOR_PLUS_END": _monthly_dates(start, end),
        "WEEKLY_7D_PLUS_END": _fixed_step_dates(start, end, days=7),
        "DAILY": _fixed_step_dates(start, end, days=1),
    }
    scenario_rows = []
    for name, dates in scenarios.items():
        scenario_rows.append(
            {
                "name": name,
                "observation_dates": len(dates),
                "maximum_gap_days": _max_gap_days(dates),
                "request_lower_bound": lower_per_date * len(dates),
                "request_upper_bound": upper_per_date * len(dates),
                "approved_for_production": False,
            }
        )

    return {
        "checked_at": "2026-09-07",
        "scope": {
            "sources": [str(item["source_key"]) for item in summary["categories"]],
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "calendar_days_inclusive": (end - start).days + 1,
            "network_access_performed": False,
            "production_episode_reconstruction_enabled": False,
        },
        "paging_basis": {
            "current_rows_total": int(summary["totals"]["rows"]),
            "observed_authority_count": authority_count,
            "manual_reference_authority_count": manual_reference_count,
            "current_official_numeric_authority_count": official_authority_count,
            "current_official_aggregate_token_count": int(official["active_aggregate_token_count"]),
            "official_deleted_numeric_authority_count": deleted_authority_count,
            "history_window_candidate_numeric_authority_union_count": candidate_union_count,
            "observed_count_gap_vs_current_official_numeric": official_authority_count - authority_count,
            "observed_count_gap_vs_history_window_candidate_union": current_absent_candidate_count,
            "observed_authority_domain_authoritatively_complete": bool(
                authority_domain["authoritative_completeness"]
            ),
            "current_official_numeric_domain_authoritatively_complete_for_reference_date": bool(
                gate["current_official_numeric_domain_authoritatively_complete_for_reference_date"]
            ),
            "exact_current_official_numeric_authority_codes_ingested": bool(
                gate["exact_current_official_numeric_code_values_ingested"]
            ),
            "exact_deleted_numeric_authority_codes_ingested": bool(
                gate["exact_deleted_numeric_code_values_ingested"]
            ),
            "history_window_date_effective_numeric_enumeration_ready": bool(
                gate["history_window_date_effective_numeric_enumeration_ready"]
            ),
            "date_effective_history_authority_filter_semantics_verified": bool(
                authority_reference["history_window_change_reference"][
                    "date_effective_history_authority_filter_semantics_verified"
                ]
            ),
            "future_authority_reference_refresh_required": bool(
                gate["future_reference_refresh_required"]
            ),
            "page_size": page_size,
            "current_scale_candidate_union_probe_requests_per_source_per_asof_date": current_absent_candidate_count,
            "current_scale_candidate_union_probe_requests_total_per_asof_date": (
                current_absent_candidate_count * len(summary["categories"])
            ),
            "request_lower_bound_per_asof_date": lower_per_date,
            "request_upper_bound_per_asof_date": upper_per_date,
            "per_source": per_source,
            "cost_basis": "CURRENT_ROW_SCALE_WITH_276_CURRENT_PLUS_DELETED_NUMERIC_CANDIDATE_UNION_230_CURRENTLY_NONEMPTY_PLUS_46_ONE_REQUEST_PROBES_PER_SOURCE_DATE_EFFECTIVE_HISTORY_SEMANTICS_UNVERIFIED_NOT_HISTORICAL_ROW_COUNT_FORECAST",
        },
        "scenarios": scenario_rows,
        "semantic_limits": {
            "as_of_snapshots_are_lossless_event_log": False,
            "daily_sampling_proves_no_multiple_intraday_transitions": False,
            "exact_transition_timestamp_claimed": False,
            "status_code_05_semantics_resolved": False,
            "reopening_vs_correction_resolved": False,
        },
        "authority_partition_semantics": {
            "findings": "provenance/history_authority_partition_findings.json",
            "full_deleted_count_probe_plan": "provenance/history_authority_partition_probe_plan.json",
            "authenticated_execution_available": True,
            "bounded_deleted_partition_post_reform_freeze_confirmed": True,
            "bounded_current_partition_post_reform_evolution_confirmed": True,
            "current_plus_deleted_union_semantically_equivalent_to_current_snapshot": False,
            "full_32_deleted_count_probe_executed": False,
            "full_32_deleted_count_probe_request_cap": 384,
        },
        "implementation": {
            "module": "src/korea_business_lifecycle/history_observation_strategy.py",
            "script": "scripts/history_observation_strategy.py",
            "test_module": "tests/test_history_observation_strategy.py",
            "network_required": False,
        },
        "authority_domain_reference": "provenance/authority_domain_reference.json",
        "decision": "NO_NATIONWIDE_OBSERVATION_CADENCE_APPROVED_LEGACY_AUTHORITY_PARTITION_POLICY_AND_COST_REVIEW_REQUIRED",
        "next_gate": (
            "execute the prepared 384-request count-only probe across all 32 deleted authority codes, "
            "define an explicit frozen-legacy-partition inclusion policy, then make a cadence/request-budget "
            "decision before any nationwide acquisition or production episode reconstruction"
        ),
    }
