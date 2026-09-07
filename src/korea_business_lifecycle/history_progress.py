from __future__ import annotations

from typing import Any


def _percent(value: int, total: int) -> str:
    if total <= 0:
        return "100.0%"
    return f"{100.0 * value / total:.1f}%"


def format_history_progress(event: dict[str, Any]) -> str:
    """Format aggregate-only acquisition progress without row values or credentials."""
    kind = str(event.get("event") or "")
    index = int(event.get("task_index", 1))
    total = int(event.get("task_total", 1))
    prefix = f"[{index}/{total}]"
    source = str(event.get("source_key") or "")
    authority = str(event.get("authority_code") or "")
    base_date = str(event.get("base_date") or "")

    if kind == "task_start":
        max_pages = int(event.get("max_pages", 0))
        suffix = f" (max {max_pages} pages)" if max_pages else ""
        return f"{prefix} START {source} {authority} {base_date}{suffix}"

    if kind == "page_complete":
        page_no = int(event.get("page_no", 0))
        total_pages = int(event.get("total_pages", 0))
        stored_rows = int(event.get("stored_rows", 0))
        total_count = int(event.get("total_count", 0))
        return (
            f"{prefix} PAGE {page_no}/{total_pages} ({_percent(page_no, total_pages)}) "
            f"rows {stored_rows:,}/{total_count:,}"
        )

    if kind in {"task_complete", "task_skipped"}:
        finished = int(event.get("finished_tasks", 0))
        verb = "DONE" if kind == "task_complete" else "SKIP"
        detail = ""
        if kind == "task_complete":
            detail = (
                f" pages={int(event.get('observed_pages', 0)):,}"
                f" rows={int(event.get('observed_rows', 0)):,}"
            )
        return (
            f"{prefix} {verb} {source} {authority} {base_date}{detail} | "
            f"overall {finished}/{total} ({_percent(finished, total)})"
        )

    return f"{prefix} {kind or 'PROGRESS'} {source} {authority} {base_date}".strip()
