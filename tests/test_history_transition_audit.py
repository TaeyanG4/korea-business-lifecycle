import json
from pathlib import Path

from korea_business_lifecycle.history_transition_audit import audit_reverse_transition_windows


def _write_snapshot(
    root: Path,
    source: str,
    authority: str,
    date: str,
    rows: list[dict],
) -> None:
    directory = root / "history" / source / date / authority / "synthetic"
    directory.mkdir(parents=True)
    page = {
        "response": {
            "body": {"items": {"item": rows}},
        }
    }
    (directory / "page-00001.json").write_text(json.dumps(page), encoding="utf-8")
    (directory / "manifest.json").write_text(
        json.dumps({"pages": [{"filename": "page-00001.json"}]}), encoding="utf-8"
    )


def test_transition_audit_emits_no_identifier_or_raw_identity_values(
    external_tmp_path: Path, monkeypatch
) -> None:
    root = external_tmp_path / "data"
    root.mkdir()
    plan = {
        "checked_at": "2026-09-07",
        "cases": [
            {
                "source_key": "rest_cafes",
                "authority_code": "3830000",
                "candidate_date_source": "synthetic",
                "candidate_date": "20260901",
                "probe_dates": ["20260831", "20260901", "20260902"],
                "max_pages_per_snapshot": 1,
            }
        ],
        "planned_tasks": 3,
        "max_network_requests": 3,
        "privacy": {
            "management_numbers_committed": False,
            "business_names_committed": False,
            "addresses_committed": False,
            "coordinates_committed": False,
        },
        "hard_limit": "synthetic",
    }
    monkeypatch.setattr(
        "korea_business_lifecycle.history_transition_audit.load_reverse_transition_probe_plan",
        lambda: plan,
    )
    monkeypatch.setattr(
        "korea_business_lifecycle.history_transition_audit.validate_reverse_transition_probe_plan",
        lambda _plan: [],
    )
    start = {
        "MNG_NO": "secret-id",
        "SALS_STTS_CD": "03",
        "CLSBIZ_YMD": "20200101",
        "LCPMT_YMD": "20190101",
        "BPLC_NM": "Private Name",
        "ROAD_NM_ADDR": "Private Address",
        "CRD_INFO_X": "1",
        "CRD_INFO_Y": "2",
    }
    end = dict(start, SALS_STTS_CD="01", CLSBIZ_YMD="")
    _write_snapshot(root, "rest_cafes", "3830000", "20260101", [start])
    _write_snapshot(root, "rest_cafes", "3830000", "20260906", [end])
    _write_snapshot(root, "rest_cafes", "3830000", "20260831", [start])
    _write_snapshot(root, "rest_cafes", "3830000", "20260901", [end])
    _write_snapshot(root, "rest_cafes", "3830000", "20260902", [end])
    result = audit_reverse_transition_windows(data_root=root)
    assert result["results"][0]["assessment"] == "REVERSAL_OBSERVED_IN_THREE_DATE_WINDOW"
    rendered = json.dumps(result)
    assert "secret-id" not in rendered
    assert "Private Name" not in rendered
    assert "Private Address" not in rendered

