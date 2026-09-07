from __future__ import annotations

import json
from pathlib import Path

from korea_business_lifecycle.history_audit import compare_history_snapshots


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
