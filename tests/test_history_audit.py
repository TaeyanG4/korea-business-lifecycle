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
    rendered = json.dumps(result)
    assert "secret-A" not in rendered
    assert "Private Name" not in rendered

