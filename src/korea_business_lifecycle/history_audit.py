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
    transition_closure_patterns: Counter[str] = Counter()
    changed: Counter[str] = Counter()
    status_closure_alignment: Counter[str] = Counter()
    reverse_transition_evidence: Counter[str] = Counter()
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

        before_closure = str(before.get("CLSBIZ_YMD") or "").strip()
        after_closure = str(after.get("CLSBIZ_YMD") or "").strip()
        if not before_closure and after_closure:
            closure_direction = "blank->value"
        elif before_closure and not after_closure:
            closure_direction = "value->blank"
        elif before_closure != after_closure:
            closure_direction = "value->different_value"
        else:
            closure_direction = "unchanged"

        if changed_flags["status"]:
            transition_closure_patterns[
                f"{before_status}->{after_status}|{closure_direction}"
            ] += 1

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

        if before_status == "03" and after_status == "01":
            reverse_transition_evidence["total"] += 1
            reverse_transition_evidence[f"closure_{closure_direction}"] += 1
            for label in ("permit_date", "business_name", "address", "coordinates"):
                if changed_flags[label]:
                    reverse_transition_evidence[f"{label}_changed"] += 1
            if (
                changed_flags["business_name"]
                and changed_flags["address"]
                and changed_flags["coordinates"]
            ):
                reverse_transition_evidence["name_address_coordinates_all_changed"] += 1

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
    if status_changed == 0:
        lifecycle_signal = "INSUFFICIENT_EVENT_EVIDENCE"
        lifecycle_reason = "no status change occurred in this bounded pair, so event semantics were not exercised"
    elif status_without_closure or closure_without_status:
        lifecycle_signal = "AMBIGUOUS"
        lifecycle_reason = "status and closure-date changes are not row-aligned in this bounded pair"
    elif reverse_transition_count:
        lifecycle_signal = "REVERSIBLE_OR_CORRECTION_SIGNAL"
        lifecycle_reason = (
            "status and closure-date changes are row-aligned, but one or more 03->01 reverse transitions "
            "require reopening-versus-correction review"
        )
    else:
        lifecycle_signal = "USABLE_FOR_FURTHER_AUDIT"
        lifecycle_reason = (
            "all observed status changes are row-aligned with closure-date changes, "
            "with no closure-only changes or 03->01 reverse transitions in this bounded pair"
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
        "status_transition_closure_patterns": dict(sorted(transition_closure_patterns.items())),
        "reverse_03_to_01_evidence": {
            key: reverse_transition_evidence.get(key, 0)
            for key in (
                "total",
                "closure_value->blank",
                "closure_blank->value",
                "closure_value->different_value",
                "closure_unchanged",
                "permit_date_changed",
                "business_name_changed",
                "address_changed",
                "coordinates_changed",
                "name_address_coordinates_all_changed",
            )
        },
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


def summarize_history_audits(audits: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine aggregate-only pair audits without introducing new semantic assumptions."""
    if not audits:
        raise HistoryAuditError("at least one history audit is required")

    pair_keys: set[tuple[str, str]] = set()
    totals: Counter[str] = Counter()
    changed: Counter[str] = Counter()
    alignment: Counter[str] = Counter()
    transitions: Counter[str] = Counter()
    transition_closure_patterns: Counter[str] = Counter()
    reverse_evidence: Counter[str] = Counter()
    continuity: Counter[str] = Counter()
    lifecycle: Counter[str] = Counter()
    status_vocab_changes: list[dict[str, Any]] = []
    flags: Counter[str] = Counter()

    for audit in audits:
        source = str(audit["source_key"])
        authority = str(audit["authority_code"])
        pair_key = (source, authority)
        if pair_key in pair_keys:
            raise HistoryAuditError(f"duplicate source/authority audit: {source}/{authority}")
        pair_keys.add(pair_key)

        for key in (
            "start_rows",
            "end_rows",
            "start_duplicate_mng_no_rows",
            "end_duplicate_mng_no_rows",
            "common_mng_no",
            "added_mng_no",
            "disappeared_mng_no",
            "simultaneous_name_address_coordinate_changes",
        ):
            totals[key] += int(audit.get(key, 0))

        changed.update({key: int(value) for key, value in audit.get("changed_common_rows", {}).items()})
        alignment.update(
            {key: int(value) for key, value in audit.get("status_closure_alignment", {}).items()}
        )
        transitions.update(
            {key: int(value) for key, value in audit.get("status_code_transitions", {}).items()}
        )
        transition_closure_patterns.update(
            {
                key: int(value)
                for key, value in audit.get("status_transition_closure_patterns", {}).items()
            }
        )
        reverse_evidence.update(
            {key: int(value) for key, value in audit.get("reverse_03_to_01_evidence", {}).items()}
        )

        assessment = audit.get("assessment", {})
        continuity[str(assessment.get("mng_no_continuity", "UNKNOWN"))] += 1
        lifecycle[str(assessment.get("lifecycle_signal", "UNKNOWN"))] += 1

        if int(audit.get("start_duplicate_mng_no_rows", 0)) or int(
            audit.get("end_duplicate_mng_no_rows", 0)
        ):
            flags["pairs_with_duplicate_mng_no"] += 1
        if int(audit.get("disappeared_mng_no", 0)):
            flags["pairs_with_disappeared_mng_no"] += 1
        if int(audit.get("changed_common_rows", {}).get("permit_date", 0)):
            flags["pairs_with_permit_date_changes"] += 1
        if int(assessment.get("reopening_like_03_to_01", 0)):
            flags["pairs_with_03_to_01"] += 1
        if int(audit.get("status_closure_alignment", {}).get("status_changed_without_closure_change", 0)) or int(
            audit.get("status_closure_alignment", {}).get("closure_changed_without_status_change", 0)
        ):
            flags["pairs_with_status_closure_mismatch"] += 1
        if int(audit.get("simultaneous_name_address_coordinate_changes", 0)):
            flags["pairs_with_simultaneous_name_address_coordinate_changes"] += 1
        if assessment.get("status_vocabulary_changed"):
            flags["pairs_with_status_vocabulary_change"] += 1
            status_vocab_changes.append(
                {
                    "source_key": source,
                    "authority_code": authority,
                    "status_codes_added": list(audit.get("status_codes_added", [])),
                    "status_codes_removed": list(audit.get("status_codes_removed", [])),
                }
            )

    pair_count = len(audits)
    all_strong = continuity.get("STRONG", 0) == pair_count
    ambiguous_pairs = lifecycle.get("AMBIGUOUS", 0)
    reversible_pairs = lifecycle.get("REVERSIBLE_OR_CORRECTION_SIGNAL", 0)
    event_pairs = lifecycle.get("USABLE_FOR_FURTHER_AUDIT", 0)
    no_event_pairs = lifecycle.get("INSUFFICIENT_EVENT_EVIDENCE", 0)
    if ambiguous_pairs:
        sample_lifecycle = "MIXED_SAMPLE"
    elif reversible_pairs:
        sample_lifecycle = "REVERSIBLE_OR_CORRECTION_SIGNAL_PRESENT"
    elif event_pairs:
        sample_lifecycle = "CONSISTENT_EVENT_SIGNAL"
    elif no_event_pairs == pair_count:
        sample_lifecycle = "INSUFFICIENT_EVENT_EVIDENCE"
    else:
        sample_lifecycle = "MIXED_SAMPLE"
    return {
        "pair_count": pair_count,
        "authorities": sorted({authority for _, authority in pair_keys}),
        "sources": sorted({source for source, _ in pair_keys}),
        "totals": dict(sorted(totals.items())),
        "changed_common_rows": dict(sorted(changed.items())),
        "status_closure_alignment": dict(sorted(alignment.items())),
        "status_code_transitions": dict(sorted(transitions.items())),
        "status_transition_closure_patterns": dict(sorted(transition_closure_patterns.items())),
        "reverse_03_to_01_evidence": dict(sorted(reverse_evidence.items())),
        "assessment_counts": {
            "mng_no_continuity": dict(sorted(continuity.items())),
            "lifecycle_signal": dict(sorted(lifecycle.items())),
        },
        "flags": dict(sorted(flags.items())),
        "status_vocabulary_changes": sorted(
            status_vocab_changes,
            key=lambda item: (item["source_key"], item["authority_code"]),
        ),
        "sample_assessment": {
            "mng_no_continuity": "CONSISTENT_ACROSS_SAMPLE" if all_strong else "MIXED_SAMPLE",
            "lifecycle_signal": sample_lifecycle,
            "scope_note": (
                "This conclusion applies only to the bounded authority/date sample. It does not declare "
                "MNG_NO as a source primary key or prove establishment identity nationwide."
            ),
        },
    }
