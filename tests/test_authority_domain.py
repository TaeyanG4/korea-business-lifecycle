from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from openpyxl import Workbook

from korea_business_lifecycle.authority_domain import (
    AuthorityDomainError,
    observed_authority_sets_from_permit_build,
    parse_authority_reference_workbook,
)


def _write_reference(path: Path, *, second_number: int = 2) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "1. 개방자치단체코드"
    sheet.append(["번호", "자치단체명", "자치단체 코드", "변경여부", "변경일", "변경사유"])
    sheet.append([1, "서울특별시 전체", "6110000_ALL", None, None, None])
    sheet.append([second_number, "서울특별시", 6110000, None, None, None])
    sheet.append([3, "신규자치단체", 6130000, "신규", 20260701, "synthetic change"])
    sheet.append([None, "삭제자치단체", 6290000, "삭제", 20260701, "synthetic change"])
    workbook.save(path)


def test_reference_parser_separates_numeric_codes_from_aggregate_tokens(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(path)
    parsed = parse_authority_reference_workbook(path)
    assert parsed["active_row_count"] == 3
    assert parsed["active_numeric_code_count"] == 2
    assert parsed["active_aggregate_token_count"] == 1
    assert parsed["new_numeric_code_count"] == 1
    assert parsed["new_aggregate_token_count"] == 0
    assert parsed["deleted_numeric_code_count"] == 1
    assert parsed["deleted_numeric_authorities"] == [
        {"code": "6290000", "name": "삭제자치단체"},
    ]
    assert parsed["active_numeric_authorities"] == [
        {"code": "6110000", "name": "서울특별시"},
        {"code": "6130000", "name": "신규자치단체"},
    ]
    assert len(parsed["active_numeric_authority_list_sha256"]) == 64
    assert len(parsed["deleted_numeric_authority_list_sha256"]) == 64


def test_reference_parser_rejects_noncontiguous_active_numbers(tmp_path: Path) -> None:
    path = tmp_path / "reference.xlsx"
    _write_reference(path, second_number=4)
    with pytest.raises(AuthorityDomainError, match="not contiguous"):
        parse_authority_reference_workbook(path)


def test_observed_authority_scan_reads_only_v1_parquet_domain(tmp_path: Path) -> None:
    for source_key in ("general_restaurants", "rest_cafes", "bakeries"):
        table = pa.table({"authority_code": ["3000000", "3010000", "3000000"]})
        pq.write_table(table, tmp_path / f"{source_key}.parquet")
    observed = observed_authority_sets_from_permit_build(tmp_path)
    assert set(observed) == {"general_restaurants", "rest_cafes", "bakeries"}
    assert all(values == {"3000000", "3010000"} for values in observed.values())
