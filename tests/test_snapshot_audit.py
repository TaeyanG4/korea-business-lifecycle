from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from korea_business_lifecycle.snapshot_audit import audit_snapshot, retrieval_date_from_manifest


HEADER = (
    "개방자치단체코드,관리번호,인허가일자,영업상태명,폐업일자,사업장명,"
    "상세영업상태명,상세영업상태코드,영업상태코드,전화번호,좌표정보(X),좌표정보(Y),"
    "도로명주소,지번주소\n"
)


def test_snapshot_audit_falsifies_closure_date_only_rule(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    source.write_text(
        HEADER
        + "A,1,20200101,폐업,,합성A,폐업,02,03,02-000-0000,200000,450000,합성로1,합성동1\n"
        + "A,2,20200102,영업/정상,20200103,합성B,영업,01,01,,200100,450100,합성로2,합성동2\n"
        + "A,2,20200102,영업/정상,20200103,합성B,영업,01,01,,200100,450100,합성로2,합성동2\n",
        encoding="utf-8",
    )
    audit = audit_snapshot(
        source,
        retrieval_date=date(2026, 9, 7),
        sqlite_path=tmp_path / "audit.sqlite",
        batch_size=2,
    )
    assert audit["rows"] == 3
    assert audit["candidate_identity"]["management_number"]["duplicate_rows_beyond_first"] == 1
    assert audit["parsed_row_duplicates"]["duplicate_rows_beyond_first"] == 1
    state = audit["source_status_vs_closure_field"]
    assert state["closed_label_without_closure_field"] == 1
    assert state["non_closed_label_with_closure_field"] == 2
    assert state["closure_date_alone_sufficient"] is False


def test_snapshot_audit_counts_date_and_coordinate_contradictions(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    source.write_text(
        HEADER
        + "A,1,20260102,폐업,20250101,합성A,폐업,02,03,,,-1,합성로1,합성동1\n"
        + "B,2,20270101,폐업,20270102,합성B,폐업,02,03,,0,0,,합성동2\n",
        encoding="utf-8",
    )
    audit = audit_snapshot(
        source,
        retrieval_date=date(2026, 9, 7),
        sqlite_path=tmp_path / "audit.sqlite",
    )
    assert audit["dates"]["closure_before_permit"] == 1
    assert audit["dates"]["permit_after_retrieval_date"] == 1
    assert audit["dates"]["closure_after_retrieval_date"] == 1
    assert audit["coordinates"]["one_missing"] == 1
    assert audit["coordinates"]["zero_pairs"] == 1


def test_snapshot_audit_output_does_not_emit_sensitive_values(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    secret_name = "민감합성이름"
    secret_phone = "010-1234-5678"
    secret_address = "합성민감주소 99"
    source.write_text(
        HEADER
        + f"A,1,20200101,영업/정상,,{secret_name},영업,01,01,{secret_phone},200000,450000,{secret_address},합성동\n",
        encoding="utf-8",
    )
    audit = audit_snapshot(
        source,
        retrieval_date=date(2026, 9, 7),
        sqlite_path=tmp_path / "audit.sqlite",
    )
    rendered = json.dumps(audit, ensure_ascii=False)
    assert secret_name not in rendered
    assert secret_phone not in rendered
    assert secret_address not in rendered


def test_retrieval_date_from_manifest_uses_korean_local_date(tmp_path: Path) -> None:
    manifest = tmp_path / "retrieval.json"
    manifest.write_text(
        json.dumps(
            {"request": {"completed": {"asia_seoul": "2026-09-07T11:30:00+09:00"}}}
        ),
        encoding="utf-8",
    )
    assert retrieval_date_from_manifest(manifest) == date(2026, 9, 7)
