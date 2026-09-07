from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .history_probe import HistoryProbeResult, probe_history
from .provenance import V1_SOURCE_KEYS, load_authority_domain_reference


PROBE_DATES = ("20260101", "20260630", "20260701", "20260906")
EXPECTED_DELETED_AUTHORITY_COUNT = 32
EXPECTED_TASK_COUNT = EXPECTED_DELETED_AUTHORITY_COUNT * len(V1_SOURCE_KEYS) * len(PROBE_DATES)


class HistoryAuthoritySemanticsError(RuntimeError):
    """Raised when the bounded deleted-authority semantics probe cannot run safely."""


@dataclass(frozen=True)
class DeletedAuthorityProbeTask:
    source_key: str
    authority_code: str
    base_date: str


def build_deleted_authority_probe_tasks(
    authority_reference: Mapping[str, Any] | None = None,
) -> list[DeletedAuthorityProbeTask]:
    reference = authority_reference or load_authority_domain_reference()
    if reference.get("field") != "OPN_ATMY_GRP_CD":
        raise HistoryAuthoritySemanticsError("authority reference field changed")
    deleted = reference.get("official_deleted_numeric_authorities")
    if not isinstance(deleted, list) or len(deleted) != EXPECTED_DELETED_AUTHORITY_COUNT:
        raise HistoryAuthoritySemanticsError("exact deleted authority list must contain 32 entries")
    codes = [str(item.get("code", "")) for item in deleted if isinstance(item, Mapping)]
    if len(codes) != EXPECTED_DELETED_AUTHORITY_COUNT or len(set(codes)) != EXPECTED_DELETED_AUTHORITY_COUNT:
        raise HistoryAuthoritySemanticsError("deleted authority codes must be 32 unique values")
    if any(len(code) != 7 or not code.isdigit() for code in codes):
        raise HistoryAuthoritySemanticsError("deleted authority codes must be seven-digit numeric strings")

    tasks = [
        DeletedAuthorityProbeTask(
            source_key=source_key,
            authority_code=authority_code,
            base_date=base_date,
        )
        for authority_code in sorted(codes)
        for source_key in sorted(V1_SOURCE_KEYS)
        for base_date in PROBE_DATES
    ]
    if len(tasks) != EXPECTED_TASK_COUNT:
        raise HistoryAuthoritySemanticsError("deleted-authority probe task count changed")
    return tasks


def summarize_deleted_authority_probe_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        raise HistoryAuthoritySemanticsError("at least one deleted-authority probe result is required")
    by_pair: dict[tuple[str, str], dict[str, int]] = {}
    seen_tasks: set[tuple[str, str, str]] = set()
    for item in results:
        source_key = str(item.get("source_key", ""))
        authority_code = str(item.get("authority_code", ""))
        base_date = str(item.get("base_date", ""))
        task = (source_key, authority_code, base_date)
        if task in seen_tasks:
            raise HistoryAuthoritySemanticsError("duplicate deleted-authority probe result")
        seen_tasks.add(task)
        if source_key not in V1_SOURCE_KEYS or base_date not in PROBE_DATES:
            raise HistoryAuthoritySemanticsError("deleted-authority probe result scope changed")
        if len(authority_code) != 7 or not authority_code.isdigit():
            raise HistoryAuthoritySemanticsError("invalid authority code in probe result")
        try:
            total_count = int(item["total_count"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HistoryAuthoritySemanticsError("probe result total_count must be an integer") from exc
        if total_count < 0:
            raise HistoryAuthoritySemanticsError("probe result total_count must be non-negative")
        by_pair.setdefault((source_key, authority_code), {})[base_date] = total_count

    complete_pairs = 0
    prechange_growth_pairs = 0
    postchange_frozen_count_pairs = 0
    positive_prechange_pairs = 0
    for dates in by_pair.values():
        if set(dates) != set(PROBE_DATES):
            continue
        complete_pairs += 1
        if dates["20260630"] > dates["20260101"]:
            prechange_growth_pairs += 1
        if dates["20260630"] > 0:
            positive_prechange_pairs += 1
        if dates["20260630"] == dates["20260701"] == dates["20260906"]:
            postchange_frozen_count_pairs += 1

    return {
        "result_rows": len(results),
        "source_authority_pairs": len(by_pair),
        "complete_four_date_pairs": complete_pairs,
        "pairs_with_positive_20260630_count": positive_prechange_pairs,
        "pairs_with_count_growth_20260101_to_20260630": prechange_growth_pairs,
        "pairs_with_equal_counts_20260630_20260701_20260906": postchange_frozen_count_pairs,
        "row_level_values_emitted": False,
    }


def run_deleted_authority_count_probe(
    *,
    execute: bool = False,
    max_requests: int = EXPECTED_TASK_COUNT,
    request_delay_seconds: float = 0.2,
    probe: Callable[..., HistoryProbeResult] = probe_history,
    sleep: Callable[[float], None] = time.sleep,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Plan or run one page-1 count probe for every deleted-code/source/date task.

    The probe intentionally returns only aggregate totalCount values. It never emits
    source rows or identifiers and it never broadens beyond the tracked 32-code domain.
    """
    if max_requests < 1:
        raise HistoryAuthoritySemanticsError("max_requests must be positive")
    if request_delay_seconds < 0 or request_delay_seconds > 5:
        raise HistoryAuthoritySemanticsError("request_delay_seconds must be between 0 and 5")
    tasks = build_deleted_authority_probe_tasks()
    if len(tasks) > max_requests:
        raise HistoryAuthoritySemanticsError(
            f"planned deleted-authority probe requires {len(tasks)} requests, exceeding cap {max_requests}"
        )
    if not execute:
        return {
            "mode": "DRY_RUN",
            "deleted_authorities": EXPECTED_DELETED_AUTHORITY_COUNT,
            "sources": len(V1_SOURCE_KEYS),
            "dates": list(PROBE_DATES),
            "planned_tasks": len(tasks),
            "planned_requests": len(tasks),
            "requests_per_task": 1,
            "num_rows_per_request": 1,
            "request_delay_seconds": request_delay_seconds,
            "row_level_values_emitted": False,
        }

    results: list[dict[str, Any]] = []
    for index, task in enumerate(tasks, start=1):
        if progress_callback is not None:
            progress_callback(
                {
                    "event": "task_start",
                    "task_index": index,
                    "task_total": len(tasks),
                    "source_key": task.source_key,
                    "authority_code": task.authority_code,
                    "base_date": task.base_date,
                }
            )
        observed = probe(
            task.source_key,
            base_date=task.base_date,
            authority_code=task.authority_code,
            num_rows=1,
        )
        results.append(
            {
                "source_key": task.source_key,
                "authority_code": task.authority_code,
                "base_date": task.base_date,
                "total_count": int(observed.total_count),
            }
        )
        if progress_callback is not None:
            progress_callback(
                {
                    "event": "task_complete",
                    "task_index": index,
                    "task_total": len(tasks),
                    "source_key": task.source_key,
                    "authority_code": task.authority_code,
                    "base_date": task.base_date,
                    "total_count": int(observed.total_count),
                }
            )
        if request_delay_seconds and index < len(tasks):
            sleep(request_delay_seconds)

    return {
        "mode": "EXECUTED",
        "planned_tasks": len(tasks),
        "requests_executed": len(results),
        "requests_per_task": 1,
        "num_rows_per_request": 1,
        "request_delay_seconds": request_delay_seconds,
        "row_level_values_emitted": False,
        "results": results,
        "assessment": summarize_deleted_authority_probe_results(results),
    }
