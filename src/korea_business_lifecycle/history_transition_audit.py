from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .provenance import (
    load_reverse_transition_probe_plan,
    validate_reverse_transition_probe_plan,
)
from .storage import resolve_data_root


class HistoryTransitionAuditError(RuntimeError):
    """Raised when a tracked reverse transition cannot be audited safely."""


def _single_snapshot_dir(root: Path, source: str, date: str, authority: str) -> Path:
    parent = root / "history" / source / date / authority
    manifests = sorted(parent.glob("*/manifest.json")) if parent.is_dir() else []
    if len(manifests) != 1:
        raise HistoryTransitionAuditError(
            f"expected exactly one snapshot for {source}/{date}/{authority}; found {len(manifests)}"
        )
    return manifests[0].parent


def _load_records(snapshot_dir: Path) -> dict[str, dict[str, Any]]:
    manifest = json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))
    records: dict[str, dict[str, Any]] = {}
    for page in manifest.get("pages", []):
        payload = json.loads((snapshot_dir / page["filename"]).read_text(encoding="utf-8"))
        items_obj = payload["response"]["body"].get("items") or {}
        raw = items_obj.get("item", []) if isinstance(items_obj, dict) else []
        if isinstance(raw, dict):
            rows = [raw]
        elif isinstance(raw, list):
            rows = raw
        else:
            raise HistoryTransitionAuditError("unexpected history item structure")
        for row in rows:
            mng_no = str(row.get("MNG_NO") or "").strip()
            if not mng_no:
                raise HistoryTransitionAuditError("history row missing MNG_NO")
            if mng_no in records:
                raise HistoryTransitionAuditError("duplicate MNG_NO in transition snapshot")
            records[mng_no] = row
    return records


def _find_unique_reverse_id(
    start: dict[str, dict[str, Any]], end: dict[str, dict[str, Any]]
) -> str:
    matches = [
        mng_no
        for mng_no in start.keys() & end.keys()
        if str(start[mng_no].get("SALS_STTS_CD") or "") == "03"
        and str(end[mng_no].get("SALS_STTS_CD") or "") == "01"
    ]
    if len(matches) != 1:
        raise HistoryTransitionAuditError(
            f"expected exactly one 03->01 candidate in tracked source/authority; found {len(matches)}"
        )
    return matches[0]


def _same(row: dict[str, Any], reference: dict[str, Any], fields: tuple[str, ...]) -> bool:
    return all(row.get(field) == reference.get(field) for field in fields)


def audit_reverse_transition_windows(
    *, data_root: str | Path | None = None
) -> dict[str, Any]:
    """Audit tracked transition windows without emitting MNG_NO or source row values."""
    plan = load_reverse_transition_probe_plan()
    errors = validate_reverse_transition_probe_plan(plan)
    if errors:
        raise HistoryTransitionAuditError("invalid transition probe plan: " + "; ".join(errors))
    root = resolve_data_root(data_root)
    results: list[dict[str, Any]] = []
    for case in plan["cases"]:
        source = str(case["source_key"])
        authority = str(case["authority_code"])
        start = _load_records(_single_snapshot_dir(root, source, "20260101", authority))
        end = _load_records(_single_snapshot_dir(root, source, "20260906", authority))
        candidate_id = _find_unique_reverse_id(start, end)
        reference = start[candidate_id]
        sequence: list[dict[str, Any]] = []
        for date in case["probe_dates"]:
            records = _load_records(_single_snapshot_dir(root, source, str(date), authority))
            row = records.get(candidate_id)
            if row is None:
                sequence.append({"date": str(date), "present": False})
                continue
            sequence.append(
                {
                    "date": str(date),
                    "present": True,
                    "status_code": str(row.get("SALS_STTS_CD") or ""),
                    "closure_present": bool(str(row.get("CLSBIZ_YMD") or "").strip()),
                    "permit_date_same_as_start": _same(row, reference, ("LCPMT_YMD",)),
                    "business_name_same_as_start": _same(row, reference, ("BPLC_NM",)),
                    "address_same_as_start": _same(row, reference, ("ROAD_NM_ADDR", "LOTNO_ADDR")),
                    "coordinates_same_as_start": _same(row, reference, ("CRD_INFO_X", "CRD_INFO_Y")),
                }
            )

        observed_statuses = [item.get("status_code") for item in sequence if item.get("present")]
        reversal_observed = any(
            left == "03" and right == "01"
            for left, right in zip(observed_statuses, observed_statuses[1:])
        )
        if not all(item.get("present") for item in sequence):
            assessment = "CANDIDATE_MISSING_IN_PROBE_WINDOW"
        elif reversal_observed:
            assessment = "REVERSAL_OBSERVED_IN_THREE_DATE_WINDOW"
        else:
            assessment = "REVERSAL_NOT_LOCALIZED_IN_THREE_DATE_WINDOW"
        results.append(
            {
                "source_key": source,
                "authority_code": authority,
                "candidate_date": str(case["candidate_date"]),
                "sequence": sequence,
                "assessment": assessment,
                "sensitive_values_emitted": False,
            }
        )
    return {
        "case_count": len(results),
        "results": results,
        "scope_note": (
            "MNG_NO is used only in local memory to follow the two previously observed reverse cases. "
            "No identifier, business name, address, coordinate value, or closure-date value is emitted."
        ),
    }

