from __future__ import annotations

from pathlib import Path

from korea_business_lifecycle.history_nationwide import (
    PRODUCTION_NETWORK_REQUEST_CAP,
    RateLimitedRequestBudget,
    build_nationwide_history_tasks,
    nationwide_history_acquisition_plan,
    production_observation_dates,
    run_nationwide_history_acquisition,
)


def test_monthly_production_dates_and_exact_task_count() -> None:
    dates = production_observation_dates()
    assert dates == (
        "20260101",
        "20260201",
        "20260301",
        "20260401",
        "20260501",
        "20260601",
        "20260701",
        "20260801",
        "20260901",
        "20260906",
    )
    tasks = build_nationwide_history_tasks()
    assert len(tasks) == 7_320
    assert len({(task.source_key, task.base_date, task.authority_code) for task in tasks}) == 7_320


def test_nationwide_plan_is_approved_but_not_executed() -> None:
    plan = nationwide_history_acquisition_plan()
    assert plan["decision"] == "MONTHLY_NATIONWIDE_HISTORY_ACQUISITION_APPROVED_NOT_EXECUTED"
    assert plan["scope"]["planned_snapshot_tasks"] == 7_320
    assert plan["cadence"]["name"] == "MONTHLY_ANCHOR_PLUS_END"
    assert plan["execution"]["execution_performed"] is False
    assert plan["execution"]["hard_network_request_cap_per_run"] == 400_000
    assert plan["execution"]["resumable_complete_snapshots_are_skipped"] is True
    assert plan["storage"]["row_level_values_emitted_by_runner_summary"] is False


def test_dry_run_is_network_free_and_reports_approved_budget(external_tmp_path: Path) -> None:
    result = run_nationwide_history_acquisition(data_root=external_tmp_path)
    assert result["mode"] == "DRY_RUN"
    assert result["planned_tasks"] == 7_320
    assert result["completed_tasks"] == 0
    assert result["pending_tasks"] == 7_320
    assert result["minimum_remaining_network_requests"] == 7_320
    assert result["max_network_requests_this_run"] == PRODUCTION_NETWORK_REQUEST_CAP
    assert result["row_level_values_emitted"] is False


def test_global_request_budget_paces_every_request() -> None:
    moments = iter([0.0, 0.0, 0.05, 0.2, 0.21, 0.4])
    sleeps: list[float] = []
    opened: list[str] = []

    class Response:
        pass

    def opener(request, timeout):
        opened.append(request.full_url)
        return Response()

    limiter = RateLimitedRequestBudget(
        max_requests=3,
        delay_seconds=0.2,
        opener=opener,
        sleep=sleeps.append,
        monotonic=lambda: next(moments),
    )
    import urllib.request

    request = urllib.request.Request("https://example.invalid")
    limiter.open(request, 1)
    limiter.open(request, 1)
    limiter.open(request, 1)
    assert limiter.requests_used == 3
    assert len(opened) == 3
    assert all(value >= 0 for value in sleeps)
