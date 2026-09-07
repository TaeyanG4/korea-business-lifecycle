from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


class HistoryAuditError(RuntimeError):
    """Raised when two bounded history snapshots cannot be compared safely."""


def _items_from_page(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    try:
        items_obj = payload["response"]["body"].get("items")
    except (KeyError, TypeError, AttributeError) as exc:
        raise HistoryAuditError(f"unexpected history page structure: {path.name}") from exc
    if not items_obj:
        return []
    raw = items_obj.get("item", [])
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return [raw]
    raise HistoryAuditError(f"unexpected item structure: {path.name}")


def _load_snapshot(snapshot_dir: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], int]:
    manifest_path = snapshot_dir / "manifest.json"
    if not manifest_path.is_file():
        raise HistoryAuditError(f"manifest missing: {snapshot_dir}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records: dict[str, dict[str, Any]] = {}
    duplicate_ids = 0
    for page in manifest.get("pages", []):
        for item in _items_from_page(snapshot_dir / page["filename"]):
            mng_no = str(item.get("MNG_NO") or "").strip()
            if not mng_no:
                raise HistoryAuditError("history row missing MNG_NO")
            if mng_no in records:
                duplicate_ids += 1
            else:
                records[mng_no] = item
    return manifest, records, duplicate_ids


def compare_history_snapshots(start_dir: Path, end_dir: Path) -> dict[str, Any]:
    """Return aggregate-only longitudinal evidence; never emit names, addresses or IDs."""
    start_manifest, start, start_duplicate_ids = _load_snapshot(start_dir)
    end_manifest, end, end_duplicate_ids = _load_snapshot(end_dir)
    if start_manifest.get("source_key") != end_manifest.get("source_key"):
        raise HistoryAuditError("snapshot source_key mismatch")
    if start_manifest["query"]["authority_code"] != end_manifest["query"]["authority_code"]:
        raise HistoryAuditError("snapshot authority code mismatch")

    start_ids = set(start)
    end_ids = set(end)
    common = start_ids & end_ids
    transition_counts: Counter[str] = Counter()
    changed: Counter[str] = Counter()
    fields = {
        "status": ("SALS_STTS_CD", "SALS_STTS_NM"),
        "detail_status": ("DTL_SALS_STTS_CD", "DTL_SALS_STTS_NM"),
        "closure_date": ("CLSBIZ_YMD",),
        "permit_date": ("LCPMT_YMD",),
        "business_name": ("BPLC_NM",),
        "address": ("ROAD_NM_ADDR", "LOTNO_ADDR"),
        "coordinates": ("CRD_INFO_X", "CRD_INFO_Y"),
    }

    for mng_no in common:
        before = start[mng_no]
        after = end[mng_no]
        before_status = str(before.get("SALS_STTS_CD") or "")
        after_status = str(after.get("SALS_STTS_CD") or "")
        transition_counts[f"{before_status}->{after_status}"] += 1
        for label, source_fields in fields.items():
            if any(before.get(field) != after.get(field) for field in source_fields):
                changed[label] += 1

    return {
        "source_key": start_manifest["source_key"],
        "authority_code": start_manifest["query"]["authority_code"],
        "start_date": start_manifest["query"]["base_date"],
        "end_date": end_manifest["query"]["base_date"],
        "start_rows": len(start),
        "end_rows": len(end),
        "start_duplicate_mng_no_rows": start_duplicate_ids,
        "end_duplicate_mng_no_rows": end_duplicate_ids,
        "common_mng_no": len(common),
        "added_mng_no": len(end_ids - start_ids),
        "disappeared_mng_no": len(start_ids - end_ids),
        "changed_common_rows": dict(sorted(changed.items())),
        "status_code_transitions": dict(sorted(transition_counts.items())),
        "grain_note": (
            "MNG_NO continuity is empirical for this bounded authority/date pair only; "
            "it is not declared as a source primary key or establishment identity."
        ),
    }

