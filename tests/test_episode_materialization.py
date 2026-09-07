from __future__ import annotations

import hashlib
import json
from pathlib import Path

from korea_business_lifecycle.episode_materialization import (
    _materialize_history_tasks,
    episode_materialization_plan,
    episode_arrow_schema,
)
from korea_business_lifecycle.episode_materialization_verify import _verify_row_invariants
from korea_business_lifecycle.history_nationwide import NationwideHistoryTask


def _write_snapshot(root: Path, task: NationwideHistoryTask, rows: list[dict]) -> None:
    snapshot = root / "history" / task.source_key / task.base_date / task.authority_code / "synthetic"
    snapshot.mkdir(parents=True)
    payload = {
        "response": {
            "header": {"resultCode": "0", "resultMsg": "OK"},
            "body": {
                "pageNo": 1,
                "numOfRows": 100,
                "totalCount": len(rows),
                "items": {"item": rows},
            },
        }
    }
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    page = snapshot / "page-00001.json"
    page.write_bytes(raw)
    manifest = {
        "source_key": task.source_key,
        "query": {
            "base_date": task.base_date,
            "authority_code": task.authority_code,
            "service_key_redacted": True,
        },
        "observed": {"total_count": len(rows), "stored_rows": len(rows)},
        "pages": [
            {
                "filename": page.name,
                "rows": len(rows),
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        ],
    }
    (snapshot / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def test_episode_arrow_schema_matches_frozen_23_columns() -> None:
    schema = episode_arrow_schema()
    assert len(schema) == 23
    assert schema.metadata[b"kbl.grain"] == b"PERMIT_STATUS_EPISODE"


def test_episode_materialization_plan_waits_for_complete_history() -> None:
    plan = episode_materialization_plan()
    assert plan["decision"] == "PRODUCTION_EPISODE_MATERIALIZATION_PREPARED_WAITING_FOR_COMPLETE_HISTORY"
    assert plan["scope"]["required_history_snapshot_tasks"] == 7_320
    assert plan["implementation"]["bucket_count"] == 256
    assert plan["execution"]["execution_performed"] is False
    assert plan["gates"]["public_row_level_release_approved"] is False


def test_bucketed_materializer_preserves_censoring_and_source_states(external_tmp_path: Path) -> None:
    first = NationwideHistoryTask("bakeries", "20260101", "3000000")
    second = NationwideHistoryTask("bakeries", "20260201", "3000000")
    _write_snapshot(
        external_tmp_path,
        first,
        [
            {
                "MNG_NO": "synthetic-mng",
                "OPN_ATMY_GRP_CD": "3000000",
                "SALS_STTS_CD": "01",
                "SALS_STTS_NM": "active",
                "DTL_SALS_STTS_CD": "01",
                "DTL_SALS_STTS_NM": "active",
                "CLSBIZ_YMD": "",
            }
        ],
    )
    _write_snapshot(
        external_tmp_path,
        second,
        [
            {
                "MNG_NO": "synthetic-mng",
                "OPN_ATMY_GRP_CD": "3000000",
                "SALS_STTS_CD": "03",
                "SALS_STTS_NM": "closed",
                "DTL_SALS_STTS_CD": "02",
                "DTL_SALS_STTS_NM": "closed",
                "CLSBIZ_YMD": "20260115",
            }
        ],
    )
    result = _materialize_history_tasks(
        [first, second],
        data_root=external_tmp_path,
        enforce_production_task_count=False,
    )
    assert result["status"] == "PASS"
    assert result["snapshot_count"] == 2
    assert result["observation_rows"] == 2
    assert result["episode_rows"] == 2
    assert result["row_level_values_emitted"] is False
    import pyarrow.parquet as pq

    parquet_files = list(Path(result["build_directory"]).glob("**/*.parquet"))
    assert len(parquet_files) == 1
    _verify_row_invariants(pq.read_table(parquet_files[0]))
