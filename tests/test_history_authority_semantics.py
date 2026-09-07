from __future__ import annotations

from types import SimpleNamespace

import pytest

from korea_business_lifecycle.history_authority_semantics import (
    EXPECTED_TASK_COUNT,
    HistoryAuthoritySemanticsError,
    PROBE_DATES,
    build_deleted_authority_probe_tasks,
    run_deleted_authority_count_probe,
    summarize_deleted_authority_probe_results,
)


def test_exact_deleted_authority_probe_plan_is_384_single_request_tasks() -> None:
    tasks = build_deleted_authority_probe_tasks()
    assert len(tasks) == EXPECTED_TASK_COUNT == 384
    assert len({task.authority_code for task in tasks}) == 32
    assert len({task.source_key for task in tasks}) == 3
    assert {task.base_date for task in tasks} == set(PROBE_DATES)


def test_deleted_authority_probe_is_dry_run_by_default() -> None:
    result = run_deleted_authority_count_probe()
    assert result["mode"] == "DRY_RUN"
    assert result["planned_requests"] == 384
    assert result["requests_per_task"] == 1
    assert result["num_rows_per_request"] == 1
    assert result["row_level_values_emitted"] is False


def test_deleted_authority_probe_refuses_request_cap_below_plan() -> None:
    with pytest.raises(HistoryAuthoritySemanticsError, match="exceeding cap"):
        run_deleted_authority_count_probe(max_requests=383)


def test_execute_emits_only_aggregate_counts_and_summarizes_freeze_pattern() -> None:
    seen = []

    def fake_probe(source_key: str, *, base_date: str, authority_code: str, num_rows: int):
        assert num_rows == 1
        counts = {
            "20260101": 10,
            "20260630": 12,
            "20260701": 12,
            "20260906": 12,
        }
        return SimpleNamespace(total_count=counts[base_date])

    result = run_deleted_authority_count_probe(
        execute=True,
        probe=fake_probe,
        sleep=lambda _: None,
        request_delay_seconds=0.1,
        progress_callback=seen.append,
    )
    assert result["requests_executed"] == 384
    assert result["row_level_values_emitted"] is False
    assert result["assessment"]["complete_four_date_pairs"] == 96
    assert result["assessment"]["pairs_with_count_growth_20260101_to_20260630"] == 96
    assert result["assessment"]["pairs_with_equal_counts_20260630_20260701_20260906"] == 96
    assert all(set(item) == {"source_key", "authority_code", "base_date", "total_count"} for item in result["results"])
    assert sum(event["event"] == "task_complete" for event in seen) == 384


def test_summary_rejects_duplicate_task_result() -> None:
    item = {
        "source_key": "bakeries",
        "authority_code": "3490000",
        "base_date": "20260101",
        "total_count": 1,
    }
    with pytest.raises(HistoryAuthoritySemanticsError, match="duplicate"):
        summarize_deleted_authority_probe_results([item, dict(item)])
