from __future__ import annotations

import math
from calendar import monthrange
from datetime import date, timedelta
from typing import Any

from .provenance import load_history_review, load_observed_snapshot_summary


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
    common = review["common_contract"]
    authority_domain = common["observed_current_authority_code_domain"]
    authority_count = int(authority_domain["distinct_count"])
    page_size = int(common["max_num_of_rows"])
    if authority_count != 230 or page_size != 100:
        raise HistoryObservationStrategyError("tracked history paging assumptions changed")

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
        lower_per_date += lower
        upper_per_date += upper
        per_source.append(
            {
                "source_key": str(item["source_key"]),
                "current_rows": rows,
                "request_lower_bound_per_asof_date": lower,
                "request_upper_bound_per_asof_date": upper,
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
        "window": {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "calendar_days_inclusive": (end - start).days + 1,
        },
        "paging_basis": {
            "sources": [str(item["source_key"]) for item in summary["categories"]],
            "current_rows_total": int(summary["totals"]["rows"]),
            "observed_authority_count": authority_count,
            "authority_domain_authoritatively_complete": bool(
                authority_domain["authoritative_completeness"]
            ),
            "page_size": page_size,
            "request_lower_bound_per_asof_date": lower_per_date,
            "request_upper_bound_per_asof_date": upper_per_date,
            "per_source": per_source,
            "cost_basis": "CURRENT_ROW_SCALE_MATHEMATICAL_PAGE_BOUNDS_NOT_HISTORICAL_ROW_COUNT_FORECAST",
        },
        "scenarios": scenario_rows,
        "semantic_limits": {
            "as_of_snapshots_are_lossless_event_log": False,
            "daily_sampling_proves_no_multiple_intraday_transitions": False,
            "exact_transition_timestamp_claimed": False,
            "status_code_05_semantics_resolved": False,
            "reopening_vs_correction_resolved": False,
        },
        "decision": "NO_NATIONWIDE_OBSERVATION_CADENCE_APPROVED_COST_AND_COMPLETENESS_REVIEW_REQUIRED",
        "network_access_performed": False,
        "production_episode_reconstruction_enabled": False,
    }
