from __future__ import annotations

import json
from pathlib import Path

from korea_business_lifecycle.history_audit import (
    HistoryAuditError,
    compare_history_snapshots,
    summarize_history_audits,
)


def _write_snapshot(root: Path, date: str, rows: list[dict]) -> Path:
    directory = root / date
    directory.mkdir(parents=True)
    page = {
        "response": {
            "header": {"resultCode": "0", "resultMsg": "OK"},
            "body": {"items": {"item": rows}},
        }
    }
    (directory / "page-00001.json").write_text(json.dumps(page), encoding="utf-8")
    manifest = {
        "source_key": "bakeries",
        "query": {"authority_code": "3000000", "base_date": date},
        "pages": [{"filename": "page-00001.json"}],
    }
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return directory


def test_compare_history_snapshots_is_aggregate_only(tmp_path: Path) -> None:
    start = _write_snapshot(
        tmp_path,
        "20260101",
        [
            {"MNG_NO": "secret-A", "SALS_STTS_CD": "1", "BPLC_NM": "Private Name"},
            {"MNG_NO": "secret-B", "SALS_STTS_CD": "1"},
        ],
    )
    end = _write_snapshot(
        tmp_path,
        "20260906",
        [
            {"MNG_NO": "secret-A", "SALS_STTS_CD": "3", "BPLC_NM": "Changed Name"},
            {"MNG_NO": "secret-C", "SALS_STTS_CD": "1"},
        ],
    )
    result = compare_history_snapshots(start, end)
    assert result["common_mng_no"] == 1
    assert result["added_mng_no"] == 1
    assert result["disappeared_mng_no"] == 1
    assert result["changed_common_rows"]["status"] == 1
    assert result["changed_common_rows"]["business_name"] == 1
    assert result["changed_common_rows"]["permit_date"] == 0
    assert result["status_closure_alignment"]["status_changed_without_closure_change"] == 1
    assert result["assessment"]["mng_no_continuity"] == "MIXED"
    assert result["assessment"]["lifecycle_signal"] == "AMBIGUOUS"
    assert result["status_code_counts_start"] == {"1": 2}
    assert result["status_code_counts_end"] == {"1": 1, "3": 1}
    assert result["status_codes_added"] == ["3"]
    rendered = json.dumps(result)
    assert "secret-A" not in rendered
    assert "Private Name" not in rendered


def test_summarize_history_audits_keeps_scope_and_flags_explicit() -> None:
    audit = {
        "source_key": "bakeries",
        "authority_code": "3000000",
        "start_rows": 10,
        "end_rows": 12,
        "start_duplicate_mng_no_rows": 0,
        "end_duplicate_mng_no_rows": 0,
        "common_mng_no": 10,
        "added_mng_no": 2,
        "disappeared_mng_no": 0,
        "changed_common_rows": {"permit_date": 0, "status": 1},
        "status_closure_alignment": {
            "status_and_closure_changed": 1,
            "status_changed_without_closure_change": 0,
            "closure_changed_without_status_change": 0,
        },
        "simultaneous_name_address_coordinate_changes": 1,
        "status_code_transitions": {"01->03": 1, "03->03": 9},
        "status_transition_closure_patterns": {"01->03|blank->value": 1},
        "reverse_03_to_01_evidence": {"total": 0},
        "status_codes_added": ["05"],
        "status_codes_removed": [],
        "assessment": {
            "mng_no_continuity": "STRONG",
            "lifecycle_signal": "USABLE_FOR_FURTHER_AUDIT",
            "reopening_like_03_to_01": 0,
            "status_vocabulary_changed": True,
        },
    }
    result = summarize_history_audits([audit])
    assert result["sample_assessment"]["mng_no_continuity"] == "CONSISTENT_ACROSS_SAMPLE"
    assert result["sample_assessment"]["lifecycle_signal"] == "CONSISTENT_EVENT_SIGNAL"
    assert result["flags"]["pairs_with_status_vocabulary_change"] == 1
    assert result["flags"]["pairs_with_simultaneous_name_address_coordinate_changes"] == 1
    assert result["totals"]["disappeared_mng_no"] == 0


def test_summarize_history_audits_rejects_duplicate_pairs() -> None:
    audit = {
        "source_key": "bakeries",
        "authority_code": "3000000",
        "assessment": {},
    }
    try:
        summarize_history_audits([audit, dict(audit)])
    except HistoryAuditError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate pair must fail")


def test_reverse_transition_is_separated_from_contradictory_alignment(tmp_path: Path) -> None:
    start = _write_snapshot(
        tmp_path,
        "20260101",
        [
            {
                "MNG_NO": "secret-A",
                "SALS_STTS_CD": "03",
                "CLSBIZ_YMD": "20250101",
                "LCPMT_YMD": "20200101",
                "BPLC_NM": "Same Name",
                "ROAD_NM_ADDR": "Same Address",
                "CRD_INFO_X": "1",
                "CRD_INFO_Y": "2",
            }
        ],
    )
    end = _write_snapshot(
        tmp_path,
        "20260906",
        [
            {
                "MNG_NO": "secret-A",
                "SALS_STTS_CD": "01",
                "CLSBIZ_YMD": "",
                "LCPMT_YMD": "20200101",
                "BPLC_NM": "Same Name",
                "ROAD_NM_ADDR": "Same Address",
                "CRD_INFO_X": "1",
                "CRD_INFO_Y": "2",
            }
        ],
    )
    result = compare_history_snapshots(start, end)
    assert result["assessment"]["lifecycle_signal"] == "REVERSIBLE_OR_CORRECTION_SIGNAL"
    assert result["reverse_03_to_01_evidence"]["closure_value->blank"] == 1
    assert result["reverse_03_to_01_evidence"]["permit_date_changed"] == 0
    assert result["status_transition_closure_patterns"]["03->01|value->blank"] == 1


def test_no_status_change_is_insufficient_event_evidence(tmp_path: Path) -> None:
    start = _write_snapshot(tmp_path, "20260101", [{"MNG_NO": "A", "SALS_STTS_CD": "01"}])
    end = _write_snapshot(tmp_path, "20260906", [{"MNG_NO": "A", "SALS_STTS_CD": "01"}])
    result = compare_history_snapshots(start, end)
    assert result["assessment"]["lifecycle_signal"] == "INSUFFICIENT_EVENT_EVIDENCE"


def test_compare_history_snapshots_can_mark_strong_bounded_continuity(tmp_path: Path) -> None:
    start = _write_snapshot(
        tmp_path,
        "20260101",
        [
            {
                "MNG_NO": "secret-A",
                "SALS_STTS_CD": "01",
                "SALS_STTS_NM": "active",
                "CLSBIZ_YMD": "",
                "LCPMT_YMD": "20200101",
            }
        ],
    )
    end = _write_snapshot(
        tmp_path,
        "20260906",
        [
            {
                "MNG_NO": "secret-A",
                "SALS_STTS_CD": "03",
                "SALS_STTS_NM": "closed",
                "CLSBIZ_YMD": "20260401",
                "LCPMT_YMD": "20200101",
            },
            {"MNG_NO": "secret-B", "SALS_STTS_CD": "01", "LCPMT_YMD": "20260801"},
        ],
    )
    result = compare_history_snapshots(start, end)
    assert result["assessment"]["mng_no_continuity"] == "STRONG"
    assert result["assessment"]["lifecycle_signal"] == "USABLE_FOR_FURTHER_AUDIT"
    assert result["status_closure_alignment"]["status_and_closure_changed"] == 1
    assert result["assessment"]["reopening_like_03_to_01"] == 0
    assert result["assessment"]["status_vocabulary_changed"] is True
