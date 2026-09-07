from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from korea_business_lifecycle.history_sample_runner import (
    HistorySampleRunnerError,
    build_sample_tasks,
    run_history_sample,
)
from korea_business_lifecycle.provenance import load_history_sample_plan


def test_tracked_sample_expands_to_24_bounded_tasks() -> None:
    tasks = build_sample_tasks(load_history_sample_plan())
    assert len(tasks) == 24
    assert sum(task.expected_pages for task in tasks) == 2192
    assert {task.authority_code for task in tasks} == {
        "4420000",
        "4530000",
        "3830000",
        "3220000",
    }


def test_sample_runner_is_dry_run_by_default(external_tmp_path: Path) -> None:
    root = external_tmp_path / "data"
    root.mkdir()
    result = run_history_sample(data_root=root)
    assert result["mode"] == "DRY_RUN"
    assert result["planned_tasks"] == 24
    assert result["pending_tasks"] == 24
    assert result["planned_requests"] == 2192


def test_sample_runner_refuses_request_cap_below_plan(external_tmp_path: Path) -> None:
    root = external_tmp_path / "data"
    root.mkdir()
    with pytest.raises(HistorySampleRunnerError, match="exceeding cap"):
        run_history_sample(data_root=root, max_requests=2191)


def test_sample_runner_emits_progress_events(external_tmp_path: Path) -> None:
    root = external_tmp_path / "data"
    root.mkdir()
    events: list[dict] = []

    def fake_acquire(source_key: str, **kwargs):
        callback = kwargs["progress_callback"]
        callback(
            {
                "event": "page_complete",
                "source_key": source_key,
                "authority_code": kwargs["authority_code"],
                "base_date": kwargs["base_date"],
                "page_no": 1,
                "total_pages": 1,
                "page_rows": 1,
                "stored_rows": 1,
                "total_count": 1,
            }
        )
        return SimpleNamespace(
            snapshot_dir=root / "synthetic",
            manifest={"observed": {"total_count": 1, "total_pages": 1}},
        )

    result = run_history_sample(
        data_root=root,
        execute=True,
        acquire=fake_acquire,
        progress_callback=events.append,
    )
    assert result["acquired_tasks"] == 24
    assert sum(1 for event in events if event["event"] == "task_start") == 24
    assert sum(1 for event in events if event["event"] == "page_complete") == 24
    assert sum(1 for event in events if event["event"] == "task_complete") == 24
