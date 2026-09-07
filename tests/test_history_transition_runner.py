from pathlib import Path

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

