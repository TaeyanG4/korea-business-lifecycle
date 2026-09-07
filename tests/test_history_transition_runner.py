from pathlib import Path
from types import SimpleNamespace

import pytest

from korea_business_lifecycle.history_transition_runner import (
    HistoryTransitionRunnerError,
    build_transition_probe_tasks,
    run_transition_probe_batch,
)
from korea_business_lifecycle.provenance import load_reverse_transition_probe_plan


def test_transition_plan_has_six_tasks_and_fixed_request_cap() -> None:
    tasks = build_transition_probe_tasks(load_reverse_transition_probe_plan())
    assert len(tasks) == 6
    assert sum(task.max_pages for task in tasks) == 411
    assert {(task.source_key, task.authority_code) for task in tasks} == {
        ("rest_cafes", "3830000"),
        ("general_restaurants", "4530000"),
    }


def test_transition_runner_is_dry_run_by_default(external_tmp_path: Path) -> None:
    root = external_tmp_path / "data"
    root.mkdir()
    result = run_transition_probe_batch(data_root=root)
    assert result["mode"] == "DRY_RUN"
    assert result["planned_tasks"] == 6
    assert result["pending_tasks"] == 6
    assert result["planned_request_cap"] == 411


def test_transition_runner_refuses_lower_request_cap(external_tmp_path: Path) -> None:
    root = external_tmp_path / "data"
    root.mkdir()
    with pytest.raises(HistoryTransitionRunnerError, match="exceeding cap"):
        run_transition_probe_batch(data_root=root, max_requests=410)


def test_transition_runner_emits_task_and_page_progress(external_tmp_path: Path) -> None:
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

    result = run_transition_probe_batch(
        data_root=root,
        execute=True,
        acquire=fake_acquire,
        progress_callback=events.append,
    )
    assert result["acquired_tasks"] == 6
    assert sum(1 for event in events if event["event"] == "task_start") == 6
    assert sum(1 for event in events if event["event"] == "page_complete") == 6
    assert sum(1 for event in events if event["event"] == "task_complete") == 6
    assert events[-1]["finished_tasks"] == 6
