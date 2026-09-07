from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

from .canonical_compatibility import V1_SOURCE_ORDER
from .history_acquisition import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_TIMEOUT_SECONDS,
    HistoryAcquisitionError,
    HistorySnapshotResult,
    acquire_history_snapshot,
)
from .history_authority_policy import date_effective_authority_codes
from .provenance import load_history_observation_strategy
from .storage import resolve_data_root


PRODUCTION_WINDOW_START = date(2026, 1, 1)
PRODUCTION_WINDOW_END = date(2026, 9, 6)
PRODUCTION_MAX_PAGES_PER_SNAPSHOT = 5000
PRODUCTION_NETWORK_REQUEST_CAP = 400_000
PRODUCTION_REQUEST_DELAY_SECONDS = 0.2


class HistoryNationwideError(RuntimeError):
    """Raised when approved nationwide history acquisition cannot proceed safely."""


@dataclass(frozen=True)
class NationwideHistoryTask:
    source_key: str
    base_date: str
    authority_code: str


def production_observation_dates() -> tuple[str, ...]:
    values: list[date] = [PRODUCTION_WINDOW_START]
    year, month = PRODUCTION_WINDOW_START.year, PRODUCTION_WINDOW_START.month
    while True:
        month += 1
        if month == 13:
            year += 1
            month = 1
        candidate = date(year, month, 1)
        if candidate >= PRODUCTION_WINDOW_END:
            break
        values.append(candidate)
    if values[-1] != PRODUCTION_WINDOW_END:
        values.append(PRODUCTION_WINDOW_END)
    return tuple(value.strftime("%Y%m%d") for value in values)


def build_nationwide_history_tasks() -> list[NationwideHistoryTask]:
    strategy = load_history_observation_strategy()
    selected = strategy.get("selected_cadence", {})
    if strategy.get("decision") != "MONTHLY_HISTORY_OBSERVATION_CADENCE_APPROVED_ACQUISITION_NOT_YET_EXECUTED":
        raise HistoryNationwideError("tracked history cadence is not approved for acquisition")
    if selected.get("name") != "MONTHLY_ANCHOR_PLUS_END":
        raise HistoryNationwideError("approved production cadence changed")
    if selected.get("approved_for_production_history_acquisition") is not True:
        raise HistoryNationwideError("production history acquisition is not approved")
    if selected.get("hard_network_request_cap_per_run") != PRODUCTION_NETWORK_REQUEST_CAP:
        raise HistoryNationwideError("approved network request cap changed")
    if selected.get("request_delay_seconds") != PRODUCTION_REQUEST_DELAY_SECONDS:
        raise HistoryNationwideError("approved request delay changed")

    dates = production_observation_dates()
    if len(dates) != 10 or selected.get("observation_dates") != len(dates):
        raise HistoryNationwideError("approved monthly observation-date count changed")
    tasks = [
        NationwideHistoryTask(source_key=source_key, base_date=base_date, authority_code=authority_code)
        for base_date in dates
        for source_key in V1_SOURCE_ORDER
        for authority_code in date_effective_authority_codes(base_date)
    ]
    if len(tasks) != 10 * len(V1_SOURCE_ORDER) * 244:
        raise HistoryNationwideError("nationwide monthly task count changed")
    return tasks


def nationwide_history_acquisition_plan() -> dict[str, Any]:
    strategy = load_history_observation_strategy()
    tasks = build_nationwide_history_tasks()
    selected = strategy["selected_cadence"]
    return {
        "checked_at": "2026-09-07",
        "decision": "MONTHLY_NATIONWIDE_HISTORY_ACQUISITION_APPROVED_NOT_EXECUTED",
        "scope": {
            "sources": list(V1_SOURCE_ORDER),
            "window_start": PRODUCTION_WINDOW_START.isoformat(),
            "window_end": PRODUCTION_WINDOW_END.isoformat(),
            "observation_dates": list(production_observation_dates()),
            "observation_date_count": 10,
            "numeric_authority_codes_per_date": 244,
            "planned_snapshot_tasks": len(tasks),
            "same_date_old_new_union_used": False,
        },
        "authority_policy": {
            "provenance": "provenance/history_authority_policy.json",
            "pre_reform": "CURRENT_MINUS_NEW_PLUS_DELETED",
            "post_reform": "CURRENT_ONLY_EXCLUDE_DELETED",
            "api_queryability_defines_date_effective_membership": False,
        },
        "cadence": {
            "name": selected["name"],
            "maximum_gap_days": selected["maximum_gap_days"],
            "current_scale_request_lower_bound": selected["current_scale_request_lower_bound"],
            "current_scale_request_upper_bound": selected["current_scale_request_upper_bound"],
            "current_scale_cost_is_not_historical_row_volume_guarantee": True,
        },
        "execution": {
            "default_mode": "DRY_RUN",
            "execute_flag": "--execute",
            "execution_performed": False,
            "resumable_complete_snapshots_are_skipped": True,
            "multiple_existing_snapshots_for_one_task_fail_closed": True,
            "hard_network_request_cap_per_run": PRODUCTION_NETWORK_REQUEST_CAP,
            "minimum_request_delay_seconds": PRODUCTION_REQUEST_DELAY_SECONDS,
            "maximum_pages_per_snapshot": PRODUCTION_MAX_PAGES_PER_SNAPSHOT,
            "long_running_action_requires_visible_user_command": True,
            "script": "scripts/acquire_nationwide_history.py",
        },
        "storage": {
            "history_rows_git_tracked": False,
            "history_rows_under_git_ignored_data_root": True,
            "service_key_written_to_manifest": False,
            "row_level_values_emitted_by_runner_summary": False,
        },
        "semantic_limits": {
            "history_is_lossless_event_log": False,
            "monthly_sampling_claims_exact_transition_timestamp": False,
            "status_code_05_semantics_resolved": False,
            "reopening_vs_correction_resolved": False,
            "management_number_source_primary_key_claim": False,
        },
        "next_gate": (
            "execute the resumable nationwide monthly acquisition, require all 7320 snapshot tasks complete "
            "with no multiple-snapshot task, then materialize and independently verify lifecycle episodes"
        ),
    }


def _read_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoryNationwideError(f"history manifest cannot be read: {path}") from exc
    if not isinstance(value, dict):
        raise HistoryNationwideError("history manifest must be a JSON object")
    return value


def _existing_snapshot(root: Path, task: NationwideHistoryTask) -> tuple[Path, dict[str, Any]] | None:
    parent = root / "history" / task.source_key / task.base_date / task.authority_code
    manifests = sorted(parent.glob("*/manifest.json")) if parent.is_dir() else []
    if len(manifests) > 1:
        raise HistoryNationwideError(
            f"multiple snapshots exist for {task.source_key}/{task.base_date}/{task.authority_code}"
        )
    if not manifests:
        return None
    manifest = _read_manifest(manifests[0])
    query = manifest.get("query", {})
    observed = manifest.get("observed", {})
    if manifest.get("source_key") != task.source_key:
        raise HistoryNationwideError("existing history manifest source mismatch")
    if query.get("base_date") != task.base_date or query.get("authority_code") != task.authority_code:
        raise HistoryNationwideError("existing history manifest query mismatch")
    if query.get("service_key_redacted") is not True:
        raise HistoryNationwideError("existing history manifest does not redact the service key")
    if observed.get("stored_rows") != observed.get("total_count"):
        raise HistoryNationwideError("existing history manifest row count is incomplete")
    if not isinstance(manifest.get("pages"), list) or not manifest["pages"]:
        raise HistoryNationwideError("existing history manifest has no stored page records")
    return manifests[0].parent, manifest


class RateLimitedRequestBudget:
    def __init__(
        self,
        *,
        max_requests: int,
        delay_seconds: float,
        opener: Callable[[urllib.request.Request, int], Any] | None = None,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_requests < 1 or max_requests > PRODUCTION_NETWORK_REQUEST_CAP:
            raise HistoryNationwideError(
                f"max_requests must be between 1 and {PRODUCTION_NETWORK_REQUEST_CAP}"
            )
        if delay_seconds < PRODUCTION_REQUEST_DELAY_SECONDS or delay_seconds > 5:
            raise HistoryNationwideError(
                f"delay_seconds must be between {PRODUCTION_REQUEST_DELAY_SECONDS} and 5"
            )
        self.max_requests = max_requests
        self.delay_seconds = delay_seconds
        self.requests_used = 0
        self._opener = opener or self._default_open
        self._sleep = sleep
        self._monotonic = monotonic
        self._last_started: float | None = None

    @staticmethod
    def _default_open(request: urllib.request.Request, timeout: int) -> Any:
        return urllib.request.urlopen(request, timeout=timeout)

    def open(self, request: urllib.request.Request, timeout: int) -> Any:
        if self.requests_used >= self.max_requests:
            raise OSError("approved nationwide history network request cap reached")
        now = self._monotonic()
        if self._last_started is not None:
            remaining = self.delay_seconds - (now - self._last_started)
            if remaining > 0:
                self._sleep(remaining)
        self.requests_used += 1
        self._last_started = self._monotonic()
        return self._opener(request, timeout)


def run_nationwide_history_acquisition(
    *,
    data_root: str | Path | None = None,
    execute: bool = False,
    max_network_requests: int = PRODUCTION_NETWORK_REQUEST_CAP,
    request_delay_seconds: float = PRODUCTION_REQUEST_DELAY_SECONDS,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    acquire: Callable[..., HistorySnapshotResult] = acquire_history_snapshot,
    opener: Callable[[urllib.request.Request, int], Any] | None = None,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    tasks = build_nationwide_history_tasks()
    root = resolve_data_root(data_root)
    root.mkdir(parents=True, exist_ok=True)
    if max_attempts < 1 or max_attempts > 5:
        raise HistoryNationwideError("max_attempts must be between 1 and 5")
    if timeout_seconds < 1 or timeout_seconds > 120:
        raise HistoryNationwideError("timeout_seconds must be between 1 and 120")

    completed: dict[NationwideHistoryTask, tuple[Path, dict[str, Any]]] = {}
    pending: list[NationwideHistoryTask] = []
    existing_rows = 0
    for task in tasks:
        existing = _existing_snapshot(root, task)
        if existing is None:
            pending.append(task)
        else:
            completed[task] = existing
            existing_rows += int(existing[1]["observed"]["total_count"])

    strategy = load_history_observation_strategy()
    selected = strategy["selected_cadence"]
    dry_run = {
        "mode": "DRY_RUN",
        "cadence": selected["name"],
        "observation_dates": list(production_observation_dates()),
        "authority_codes_per_date": 244,
        "planned_tasks": len(tasks),
        "completed_tasks": len(completed),
        "pending_tasks": len(pending),
        "minimum_remaining_network_requests": len(pending),
        "current_scale_request_lower_bound_full_run": selected["current_scale_request_lower_bound"],
        "current_scale_request_upper_bound_full_run": selected["current_scale_request_upper_bound"],
        "max_network_requests_this_run": max_network_requests,
        "request_delay_seconds": request_delay_seconds,
        "existing_rows": existing_rows,
        "row_level_values_emitted": False,
    }
    if not execute:
        return dry_run
    if len(pending) > max_network_requests:
        raise HistoryNationwideError(
            "pending snapshot count alone exceeds the requested network request cap"
        )

    budget = RateLimitedRequestBudget(
        max_requests=max_network_requests,
        delay_seconds=request_delay_seconds,
        opener=opener,
    )
    acquired_tasks = 0
    acquired_rows = 0
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
                        "base_date": task.base_date,
                        "authority_code": task.authority_code,
                        "network_requests_used": budget.requests_used,
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
                    "base_date": task.base_date,
                    "authority_code": task.authority_code,
                    "network_requests_used": budget.requests_used,
                }
            )

        def page_progress(event: dict[str, Any]) -> None:
            if progress_callback is not None:
                progress_callback(
                    {
                        **event,
                        "task_index": task_index,
                        "task_total": len(tasks),
                        "finished_tasks": finished_tasks,
                        "network_requests_used": budget.requests_used,
                    }
                )

        try:
            result = acquire(
                task.source_key,
                base_date=task.base_date,
                authority_code=task.authority_code,
                data_root=root,
                max_pages=PRODUCTION_MAX_PAGES_PER_SNAPSHOT,
                max_attempts=max_attempts,
                timeout_seconds=timeout_seconds,
                request_delay_seconds=0.0,
                opener=budget.open,
                progress_callback=page_progress,
            )
        except (HistoryAcquisitionError, OSError) as exc:
            raise HistoryNationwideError(
                f"nationwide acquisition stopped at task {task_index}/{len(tasks)}; completed snapshots are resumable: {exc}"
            ) from exc
        acquired_tasks += 1
        acquired_rows += int(result.manifest["observed"]["total_count"])
        finished_tasks += 1
        if progress_callback is not None:
            progress_callback(
                {
                    "event": "task_complete",
                    "task_index": task_index,
                    "task_total": len(tasks),
                    "finished_tasks": finished_tasks,
                    "source_key": task.source_key,
                    "base_date": task.base_date,
                    "authority_code": task.authority_code,
                    "observed_rows": int(result.manifest["observed"]["total_count"]),
                    "network_requests_used": budget.requests_used,
                }
            )

    return {
        "mode": "EXECUTED",
        "cadence": selected["name"],
        "planned_tasks": len(tasks),
        "previously_completed_tasks": len(completed),
        "acquired_tasks": acquired_tasks,
        "completed_tasks_after_run": len(completed) + acquired_tasks,
        "network_requests_used": budget.requests_used,
        "max_network_requests_this_run": max_network_requests,
        "request_delay_seconds": request_delay_seconds,
        "existing_rows": existing_rows,
        "acquired_rows": acquired_rows,
        "all_tasks_complete": len(completed) + acquired_tasks == len(tasks),
        "row_level_values_emitted": False,
    }
