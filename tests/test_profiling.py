from pathlib import Path

import pytest

from korea_business_lifecycle.profiling import ProfileError, compare_column_sets, profile_csv


def test_profile_csv_reports_structure_dates_status_and_numeric_range(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    path.write_text(
        "관리번호,인허가일자,영업상태,소재지주소,좌표정보(X),좌표정보(Y)\n"
        "A1,20200102,영업,서울 합성로 1,200000,450000\n"
        "A2,2020-03-04,폐업,,200100,450100\n"
        "A3,,영업,   ,,\n",
        encoding="utf-8",
    )
    profile = profile_csv(path)
    assert profile["encoding"]["selected"] == "utf-8"
    assert profile["rows"]["parsed_data_rows"] == 3
    assert profile["header"]["column_count"] == 6
    by_name = {column["name"]: column for column in profile["columns"]}
    assert by_name["인허가일자"]["date_parse_count"] == 2
    assert by_name["인허가일자"]["date_min"] == "2020-01-02"
    assert by_name["인허가일자"]["date_max"] == "2020-03-04"
    assert "date_like_name" in by_name["인허가일자"]["name_hints"]
    assert "status_like_name" in by_name["영업상태"]["name_hints"]
    assert {item["value"] for item in by_name["영업상태"]["top_values"]} == {"영업", "폐업"}
    assert by_name["소재지주소"]["top_values"] == []
    assert by_name["좌표정보(X)"]["numeric_min"] == 200000.0
    assert by_name["소재지주소"]["blank_count"] == 1
    assert by_name["소재지주소"]["whitespace_only_count"] == 1


def test_profile_csv_detects_cp949_without_replacement(tmp_path: Path) -> None:
    path = tmp_path / "cp949.csv"
    path.write_bytes("영업상태,사업장명\n영업,합성업소\n".encode("cp949"))
    profile = profile_csv(path)
    assert profile["encoding"]["selected"] == "cp949"
    assert profile["encoding"]["confidence"] == "ambiguous_legacy"
    assert profile["rows"]["parsed_data_rows"] == 1


def test_profile_csv_caps_high_cardinality(tmp_path: Path) -> None:
    path = tmp_path / "values.csv"
    path.write_text("id\na\nb\nc\n", encoding="utf-8")
    profile = profile_csv(path, distinct_cap=2)
    column = profile["columns"][0]
    assert column["distinct_count"] is None
    assert column["distinct_count_lower_bound"] == 2
    assert column["distinct_count_exact"] is False


def test_profile_csv_rejects_variable_field_count(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("a,b\n1,2\n3\n", encoding="utf-8")
    with pytest.raises(ProfileError, match="expected 2"):
        profile_csv(path)


def test_profile_csv_uses_deterministic_standard_csv_quote_rules(tmp_path: Path) -> None:
    path = tmp_path / "quoted.csv"
    path.write_text(
        '관리번호,사업장명\nA1,"합성 ""카페"""\nA2,일반명\n',
        encoding="utf-8",
    )
    profile = profile_csv(path)
    assert profile["rows"]["parsed_data_rows"] == 2
    assert profile["header"]["column_count"] == 2
    assert profile["dialect"]["doublequote"] is True


def test_type_parsing_is_bounded_for_non_semantic_columns(tmp_path: Path) -> None:
    path = tmp_path / "bounded.csv"
    path.write_text("value\n1\n2\n3\n4\n", encoding="utf-8")
    profile = profile_csv(path, type_probe_cap=2)
    column = profile["columns"][0]
    assert column["numeric_parse_examined_count"] == 2
    assert column["numeric_parse_exact"] is False
    assert column["date_parse_examined_count"] == 2
    assert column["date_parse_exact"] is False


def test_compare_column_sets_does_not_claim_semantic_equivalence(tmp_path: Path) -> None:
    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"
    first.write_text("common,only_a\n1,2\n", encoding="utf-8")
    second.write_text("common,only_b\n1,3\n", encoding="utf-8")
    result = compare_column_sets(
        [("a", profile_csv(first)), ("b", profile_csv(second))]
    )
    assert result["exact_intersection"] == ["common"]
    assert result["category_specific"] == {"a": ["only_a"], "b": ["only_b"]}
    assert result["semantic_equivalence"] == "NOT_ASSESSED_BY_NAME_ONLY"
