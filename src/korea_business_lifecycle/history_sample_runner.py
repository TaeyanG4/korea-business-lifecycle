from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .history_acquisition import HistorySnapshotResult, acquire_history_snapshot
from .provenance import V1_SOURCE_KEYS, load_history_sample_plan, validate_history_sample_plan
from .storage import resolve_data_root


class HistorySampleRunnerError(RuntimeError):
    """Raised when a bounded history sample batch cannot be run safely."""


@dataclass(frozen=True)
class HistorySampleTask:
    authority_code: str
    source_key: str
    base_date: str
    expected_rows: int
    expected_pages: int


def build_sample_tasks(plan: dict[str, Any]) -> list[HistorySampleTask]:
    errors = validate_history_sample_plan(plan)
    if errors:
        raise HistorySampleRunnerError("invalid history sample plan: " + "; ".join(errors))

    dates = list(plan["history_dates"])
    probe_results = plan["probe_results"]
    tasks: list[HistorySampleTask] = []
    for representative in plan["selection"]["representatives"]:
        authority = str(representative["authority_code"])
        for source in sorted(V1_SOURCE_KEYS):
            for base_date in dates:
                try:
                    expected_rows = int(probe_results[authority][source][base_date])
                except (KeyError, TypeError, ValueError) as exc:
                    raise HistorySampleRunnerError(
                        f"missing probe result for {authority}/{source}/{base_date}"
                    ) from exc
                if expected_rows < 0:
                    raise HistorySampleRunnerError("probe row counts must be non-negative")
                tasks.append(
                    HistorySampleTask(
                        authority_code=authority,
                        source_key=source,
                        base_date=base_date,
                        expected_rows=expected_rows,
                        expected_pages=math.ceil(expected_rows / 100) if expected_rows else 0,
                    )
                )

    expected_requests = sum(task.expected_pages for task in tasks)
    if expected_requests != int(plan["additional_history_requests"]):
        raise HistorySampleRunnerError(
            "task page total does not match additional_history_requests in the plan"
        )
    return tasks


def _existing_snapshot_dir(root: Path, task: HistorySampleTask) -> Path | None:
    parent = root / "history" / task.source_key / task.base_date / task.authority_code
    manifests = sorted(parent.glob("*/manifest.json")) if parent.is_dir() else []
    if len(manifests) > 1:
        raise HistorySampleRunnerError(
            f"multiple snapshots exist for {task.source_key}/{task.base_date}/{task.authority_code}"
        )
    return manifests[0].parent if manifests else None


def run_history_sample(
    *,
    data_root: str | Path | None = None,
    execute: bool = False,
    max_requests: int = 2500,
    request_delay_seconds: float = 0.2,
    acquire: Callable[..., HistorySnapshotResult] = acquire_history_snapshot,
) -> dict[str, Any]:
    """Plan or execute the deterministic four-authority expansion sample.

    Existing complete snapshots are skipped so the command can be resumed safely.
    The function never broadens the authority/date/source scope beyond the tracked plan.
    """
    if max_requests < 1:
        raise HistorySampleRunnerError("max_requests must be positive")
    if request_delay_seconds < 0 or request_delay_seconds > 5:
        raise HistorySampleRunnerError("request_delay_seconds must be between 0 and 5")

    plan = load_history_sample_plan()
    tasks = build_sample_tasks(plan)
    planned_requests = sum(task.expected_pages for task in tasks)
    if planned_requests > max_requests:
        raise HistorySampleRunnerError(
            f"planned sample requires {planned_requests} requests, exceeding cap {max_requests}"
        )

    root = resolve_data_root(data_root)
    root.mkdir(parents=True, exist_ok=True)

    completed: list[dict[str, Any]] = []
    pending: list[HistorySampleTask] = []
    for task in tasks:
        existing = _existing_snapshot_dir(root, task)
        if existing is not None:
            completed.append(
                {
                    "authority_code": task.authority_code,
                    "source_key": task.source_key,
                    "base_date": task.base_date,
                    "status": "SKIPPED_EXISTING",
                    "snapshot_dir": str(existing),
                }
            )
        else:
            pending.append(task)

    remaining_expected_requests = sum(task.expected_pages for task in pending)
    if not execute:
        return {
            "mode": "DRY_RUN",
            "planned_tasks": len(tasks),
            "completed_tasks": len(completed),
            "pending_tasks": len(pending),
            "planned_requests": planned_requests,
            "remaining_expected_requests": remaining_expected_requests,
            "request_delay_seconds": request_delay_seconds,
            "authorities": [
                item["authority_code"] for item in plan["selection"]["representatives"]
            ],
        }

    acquired: list[dict[str, Any]] = []
    for task in pending:
        # Two pages of headroom allow small upstream corrections while keeping each
        # explicitly selected snapshot tightly bounded.
        max_pages = max(1, task.expected_pages + 2)
        result = acquire(
            task.source_key,
            base_date=task.base_date,
            authority_code=task.authority_code,
            data_root=root,
            max_pages=max_pages,
            request_delay_seconds=request_delay_seconds,
        )
        observed_rows = int(result.manifest["observed"]["total_count"])
        observed_pages = int(result.manifest["observed"]["total_pages"])
        acquired.append(
            {
                "authority_code": task.authority_code,
                "source_key": task.source_key,
                "base_date": task.base_date,
                "status": "ACQUIRED",
                "expected_rows": task.expected_rows,
                "observed_rows": observed_rows,
                "observed_pages": observed_pages,
                "probe_count_changed": observed_rows != task.expected_rows,
                "snapshot_dir": str(result.snapshot_dir),
            }
        )

    return {
        "mode": "EXECUTED",
        "planned_tasks": len(tasks),
        "previously_completed_tasks": len(completed),
        "acquired_tasks": len(acquired),
        "planned_requests": planned_requests,
        "remaining_expected_requests_before_run": remaining_expected_requests,
        "request_delay_seconds": request_delay_seconds,
        "probe_count_changes": sum(1 for item in acquired if item["probe_count_changed"]),
        "completed": completed,
        "acquired": acquired,
    }
