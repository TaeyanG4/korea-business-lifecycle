from __future__ import annotations

from pathlib import Path

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
