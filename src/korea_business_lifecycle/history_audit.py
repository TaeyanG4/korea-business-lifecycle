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
    start_status_counts = Counter(str(row.get("SALS_STTS_CD") or "") for row in start.values())
    end_status_counts = Counter(str(row.get("SALS_STTS_CD") or "") for row in end.values())
    transition_counts: Counter[str] = Counter()
    changed: Counter[str] = Counter()
    status_closure_alignment: Counter[str] = Counter()
    simultaneous_identity_changes = 0
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
        changed_flags: dict[str, bool] = {}
        for label, source_fields in fields.items():
            did_change = any(before.get(field) != after.get(field) for field in source_fields)
            changed_flags[label] = did_change
            if did_change:
                changed[label] += 1

        if changed_flags["status"] and changed_flags["closure_date"]:
            status_closure_alignment["status_and_closure_changed"] += 1
        elif changed_flags["status"]:
            status_closure_alignment["status_changed_without_closure_change"] += 1
        elif changed_flags["closure_date"]:
            status_closure_alignment["closure_changed_without_status_change"] += 1

        if (
            changed_flags["business_name"]
            and changed_flags["address"]
            and changed_flags["coordinates"]
        ):
            simultaneous_identity_changes += 1

    change_counts = {label: changed.get(label, 0) for label in fields}
    continuity = "STRONG"
    continuity_reasons: list[str] = []
    if start_duplicate_ids or end_duplicate_ids:
        continuity = "WEAK"
        continuity_reasons.append("duplicate MNG_NO values exist within a bounded snapshot")
    elif len(start_ids - end_ids) or change_counts["permit_date"]:
        continuity = "MIXED"
        if len(start_ids - end_ids):
            continuity_reasons.append("one or more starting MNG_NO values disappeared")
        if change_counts["permit_date"]:
            continuity_reasons.append("permit date changed for one or more common MNG_NO values")
    else:
        continuity_reasons.append(
            "no duplicate MNG_NO, no starting IDs disappeared, and no common permit dates changed"
        )

    status_changed = change_counts["status"]
    status_without_closure = status_closure_alignment.get(
        "status_changed_without_closure_change", 0
    )
    closure_without_status = status_closure_alignment.get(
        "closure_changed_without_status_change", 0
    )
    reverse_transition_count = sum(
        count
        for transition, count in transition_counts.items()
        if transition == "03->01"
    )
    if (
        status_changed > 0
        and status_without_closure == 0
        and closure_without_status == 0
        and reverse_transition_count == 0
    ):
        lifecycle_signal = "USABLE_FOR_FURTHER_AUDIT"
        lifecycle_reason = (
            "all observed status changes are row-aligned with closure-date changes, "
            "with no closure-only changes or 03->01 reverse transitions in this bounded pair"
        )
    else:
        lifecycle_signal = "AMBIGUOUS"
        lifecycle_reason = (
            "bounded pair contains absent or contradictory status/closure transition evidence"
        )

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
        "changed_common_rows": change_counts,
        "status_closure_alignment": {
            "status_and_closure_changed": status_closure_alignment.get(
                "status_and_closure_changed", 0
            ),
            "status_changed_without_closure_change": status_without_closure,
            "closure_changed_without_status_change": closure_without_status,
        },
        "simultaneous_name_address_coordinate_changes": simultaneous_identity_changes,
        "status_code_transitions": dict(sorted(transition_counts.items())),
        "status_code_counts_start": dict(sorted(start_status_counts.items())),
        "status_code_counts_end": dict(sorted(end_status_counts.items())),
        "status_codes_added": sorted(set(end_status_counts) - set(start_status_counts)),
        "status_codes_removed": sorted(set(start_status_counts) - set(end_status_counts)),
        "assessment": {
            "mng_no_continuity": continuity,
            "mng_no_continuity_reasons": continuity_reasons,
            "lifecycle_signal": lifecycle_signal,
            "lifecycle_signal_reason": lifecycle_reason,
            "reopening_like_03_to_01": reverse_transition_count,
            "status_vocabulary_changed": set(start_status_counts) != set(end_status_counts),
        },
        "grain_note": (
            "MNG_NO continuity is empirical for this bounded authority/date pair only; "
            "it is not declared as a source primary key or establishment identity."
        ),
    }
