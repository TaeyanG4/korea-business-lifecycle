from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .history_acquisition import HistorySnapshotResult, acquire_history_snapshot
from .provenance import (
    load_reverse_transition_probe_plan,
    validate_reverse_transition_probe_plan,
)
from .storage import resolve_data_root


class HistoryTransitionRunnerError(RuntimeError):
    """Raised when the bounded reverse-transition follow-up cannot run safely."""


@dataclass(frozen=True)
class TransitionProbeTask:
    source_key: str
    authority_code: str
    base_date: str
    max_pages: int


def build_transition_probe_tasks(plan: dict[str, Any]) -> list[TransitionProbeTask]:
    errors = validate_reverse_transition_probe_plan(plan)
    if errors:
        raise HistoryTransitionRunnerError(
            "invalid reverse-transition probe plan: " + "; ".join(errors)
        )
    tasks: list[TransitionProbeTask] = []
    for case in plan["cases"]:
        for base_date in case["probe_dates"]:
            tasks.append(
                TransitionProbeTask(
                    source_key=str(case["source_key"]),
                    authority_code=str(case["authority_code"]),
                    base_date=str(base_date),
                    max_pages=int(case["max_pages_per_snapshot"]),
                )
            )
    return tasks


def _existing_snapshot_dir(root: Path, task: TransitionProbeTask) -> Path | None:
    parent = root / "history" / task.source_key / task.base_date / task.authority_code
    manifests = sorted(parent.glob("*/manifest.json")) if parent.is_dir() else []
    if len(manifests) > 1:
        raise HistoryTransitionRunnerError(
            f"multiple snapshots exist for {task.source_key}/{task.base_date}/{task.authority_code}"
        )
    return manifests[0].parent if manifests else None


def run_transition_probe_batch(
    *,
    data_root: str | Path | None = None,
    execute: bool = False,
    max_requests: int = 450,
    request_delay_seconds: float = 0.2,
    acquire: Callable[..., HistorySnapshotResult] = acquire_history_snapshot,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Plan or execute only the tracked six-snapshot reverse-transition follow-up."""
    if max_requests < 1:
        raise HistoryTransitionRunnerError("max_requests must be positive")
    if request_delay_seconds < 0 or request_delay_seconds > 5:
        raise HistoryTransitionRunnerError("request_delay_seconds must be between 0 and 5")

    plan = load_reverse_transition_probe_plan()
    tasks = build_transition_probe_tasks(plan)
    planned_request_cap = sum(task.max_pages for task in tasks)
    if planned_request_cap != int(plan["max_network_requests"]):
        raise HistoryTransitionRunnerError(
            "task request cap does not match max_network_requests in the plan"
        )
    if planned_request_cap > max_requests:
        raise HistoryTransitionRunnerError(
            f"planned transition probe permits up to {planned_request_cap} requests, "
            f"exceeding cap {max_requests}"
        )

    root = resolve_data_root(data_root)
    root.mkdir(parents=True, exist_ok=True)
    completed: list[dict[str, Any]] = []
    pending: list[TransitionProbeTask] = []
    existing_by_task: dict[TransitionProbeTask, Path] = {}
    for task in tasks:
        existing = _existing_snapshot_dir(root, task)
        if existing is None:
            pending.append(task)
        else:
            existing_by_task[task] = existing
            completed.append(
                {
                    "source_key": task.source_key,
                    "authority_code": task.authority_code,
                    "base_date": task.base_date,
                    "status": "SKIPPED_EXISTING",
                    "snapshot_dir": str(existing),
                }
            )

    remaining_request_cap = sum(task.max_pages for task in pending)
    if not execute:
        return {
            "mode": "DRY_RUN",
            "planned_tasks": len(tasks),
            "completed_tasks": len(completed),
            "pending_tasks": len(pending),
            "planned_request_cap": planned_request_cap,
            "remaining_request_cap": remaining_request_cap,
            "request_delay_seconds": request_delay_seconds,
        }

    acquired: list[dict[str, Any]] = []
    finished_tasks = 0
    pending_set = set(pending)
    for task_index, task in enumerate(tasks, start=1):
        if task not in pending_set:
            finished_tasks += 1
            if progress_callback is not None:
                progress_callback(
                    {
                        "event": "task_skipped",
                        "task_index": task_index,
                        "task_total": len(tasks),
                        "finished_tasks": finished_tasks,
                        "source_key": task.source_key,
                        "authority_code": task.authority_code,
                        "base_date": task.base_date,
                        "snapshot_dir": str(existing_by_task[task]),
                    }
                )
            continue

        if progress_callback is not None:
            progress_callback(
                {
                    "event": "task_start",
                    "task_index": task_index,
                    "task_total": len(tasks),
                    "finished_tasks": finished_tasks,
                    "source_key": task.source_key,
                    "authority_code": task.authority_code,
                    "base_date": task.base_date,
                    "max_pages": task.max_pages,
                }
            )

        def page_progress(event: dict[str, Any]) -> None:
            if progress_callback is None:
                return
            progress_callback(
                {
                    **event,
                    "task_index": task_index,
                    "task_total": len(tasks),
                    "finished_tasks": finished_tasks,
                }
            )

        result = acquire(
            task.source_key,
            base_date=task.base_date,
            authority_code=task.authority_code,
            data_root=root,
            max_pages=task.max_pages,
            request_delay_seconds=request_delay_seconds,
            progress_callback=page_progress,
        )
        acquired.append(
            {
                "source_key": task.source_key,
                "authority_code": task.authority_code,
                "base_date": task.base_date,
                "status": "ACQUIRED",
                "observed_rows": int(result.manifest["observed"]["total_count"]),
                "observed_pages": int(result.manifest["observed"]["total_pages"]),
                "snapshot_dir": str(result.snapshot_dir),
            }
        )
        finished_tasks += 1
        if progress_callback is not None:
            progress_callback(
                {
                    "event": "task_complete",
                    "task_index": task_index,
                    "task_total": len(tasks),
                    "finished_tasks": finished_tasks,
                    "source_key": task.source_key,
                    "authority_code": task.authority_code,
                    "base_date": task.base_date,
                    "observed_rows": int(result.manifest["observed"]["total_count"]),
                    "observed_pages": int(result.manifest["observed"]["total_pages"]),
                }
            )
    return {
        "mode": "EXECUTED",
        "planned_tasks": len(tasks),
        "previously_completed_tasks": len(completed),
        "acquired_tasks": len(acquired),
        "planned_request_cap": planned_request_cap,
        "remaining_request_cap_before_run": remaining_request_cap,
        "completed": completed,
        "acquired": acquired,
    }
