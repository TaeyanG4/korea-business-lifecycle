from __future__ import annotations

import csv
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from korea_business_lifecycle.canonical_full_dry_run import (
    FullSnapshotDryRunError,
    dry_run_full_snapshot,
    dry_run_latest_full_snapshots,
    format_full_dry_run_progress,
    full_dry_run_plan,
)


ROOT = Path(__file__).resolve().parents[1]


def _rows() -> list[dict[str, str]]:
    value = json.loads(
        (ROOT / "tests" / "fixtures" / "synthetic_permit_rows.json").read_text(encoding="utf-8")
    )
    assert isinstance(value, list)
    return value


def _write_snapshot(
    data_root: Path,
    source_key: str,
    retrieval_id: str,
    rows: list[dict[str, str]],
) -> tuple[Path, dict[str, object]]:
    destination = data_root / "raw" / source_key / retrieval_id
    destination.mkdir(parents=True)
    artifact_path = destination / "source.csv"
    with artifact_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    payload = artifact_path.read_bytes()
    sha256 = hashlib.sha256(payload).hexdigest()
    manifest = {
        "manifest_version": 1,
        "retrieval_id": retrieval_id,
        "source_key": source_key,
        "request": {"completed": {"utc": "2026-09-07T00:00:00+00:00"}},
        "artifact": {
            "relative_path": artifact_path.relative_to(data_root).as_posix(),
            "bytes": len(payload),
            "sha256": sha256,
        },
    }
    manifest_path = destination / "retrieval.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    expected = {
        "source_key": source_key,
        "artifact_sha256": sha256,
        "bytes": len(payload),
        "rows": len(rows),
    }
    return manifest_path, expected


def _summary(categories: list[dict[str, object]]) -> dict[str, object]:
    return {
        "categories": categories,
        "totals": {"rows": sum(int(item["rows"]) for item in categories)},
    }


def test_full_dry_run_streams_every_row_and_cleans_ephemeral_index(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    rows = _rows()
    manifest, expected = _write_snapshot(
        data_root,
        "general_restaurants",
        "20260907T000000Z-a",
        rows,
    )
    events: list[dict[str, object]] = []
    result = dry_run_full_snapshot(
        manifest,
        expected=expected,
        data_root=data_root,
        progress_every_rows=1,
        sqlite_batch_rows=2,
        progress=events.append,
    )

    assert result["rows_examined"] == len(rows)
    assert result["rows_transformed"] == len(rows)
    assert result["duplicate_linkage_candidates"] == 0
    assert result["temporary_uniqueness_index_removed"] is True
    assert result["production_materialization_performed"] is False
    assert result["row_level_values_returned"] is False
    assert [event["event"] for event in events] == [
        "task_start",
        "row_progress",
        "row_progress",
        "row_progress",
        "task_complete",
    ]
    temp_dir = data_root / ".tmp" / "canonical-full-dry-run"
    assert list(temp_dir.glob("*.sqlite3")) == []


def test_full_dry_run_fails_closed_on_duplicate_without_exposing_management_number(
    external_tmp_path: Path,
) -> None:
    data_root = external_tmp_path / "data"
    rows = deepcopy(_rows())
    rows[1]["관리번호"] = rows[0]["관리번호"]
    manifest, expected = _write_snapshot(
        data_root,
        "general_restaurants",
        "20260907T000000Z-a",
        rows,
    )
    with pytest.raises(FullSnapshotDryRunError, match="duplicate expected uniqueness candidate") as exc:
        dry_run_full_snapshot(
            manifest,
            expected=expected,
            data_root=data_root,
            sqlite_batch_rows=2,
        )
    assert rows[0]["관리번호"] not in str(exc.value)
    assert list((data_root / ".tmp" / "canonical-full-dry-run").glob("*.sqlite3")) == []


def test_full_dry_run_requires_exact_expected_artifact_and_row_count(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    manifest, expected = _write_snapshot(
        data_root,
        "bakeries",
        "20260907T000000Z-a",
        _rows(),
    )
    wrong_hash = dict(expected)
    wrong_hash["artifact_sha256"] = "0" * 64
    with pytest.raises(FullSnapshotDryRunError, match="SHA-256 differs"):
        dry_run_full_snapshot(manifest, expected=wrong_hash, data_root=data_root)

    wrong_rows = dict(expected)
    wrong_rows["rows"] = int(expected["rows"]) + 1
    with pytest.raises(FullSnapshotDryRunError, match="row count differs"):
        dry_run_full_snapshot(manifest, expected=wrong_rows, data_root=data_root)


def test_full_dry_run_summary_and_plan_are_aggregate_only(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "data"
    categories = []
    for source_key in ("general_restaurants", "rest_cafes", "bakeries"):
        _manifest, expected = _write_snapshot(
            data_root,
            source_key,
            "20260907T000000Z-a",
            _rows()[:1],
        )
        categories.append(expected)
    observed_summary = _summary(categories)

    plan = full_dry_run_plan(observed_summary=observed_summary)
    assert plan["expected_rows_total"] == 3
    assert plan["production_materialization_performed"] is False
    assert plan["row_level_values_returned"] is False
    assert "management_number" not in str(plan)

    result = dry_run_latest_full_snapshots(
        data_root=data_root,
        progress_every_rows=1,
        sqlite_batch_rows=1,
        observed_summary=observed_summary,
    )
    assert result["rows_examined_total"] == 3
    assert result["rows_transformed_total"] == 3
    assert result["duplicate_linkage_candidates"] == 0
    assert result["production_materialization_performed"] is False
    assert result["row_level_values_returned"] is False


def test_progress_formatter_shows_source_and_overall_percentages() -> None:
    rendered = format_full_dry_run_progress(
        {
            "event": "row_progress",
            "task_index": 1,
            "task_total": 3,
            "source_key": "general_restaurants",
            "rows_processed": 100_000,
            "expected_rows": 2_000_000,
            "overall_rows_processed": 100_000,
            "overall_expected_rows": 3_000_000,
        }
    )
    assert rendered == (
        "[1/3] ROWS general_restaurants 100,000/2,000,000 (5.0%) | "
        "overall 100,000/3,000,000 (3.3%)"
    )
