from pathlib import Path

from korea_business_lifecycle.cross_category_audit import (
    audit_cross_category_current_snapshots,
)


HEADER = "개방자치단체코드,관리번호,사업장명,도로명주소,지번주소\n"


def test_cross_category_overlap_is_aggregate_only(tmp_path: Path) -> None:
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    a.write_text(
        HEADER
        + "AUTH,1,합성동일,합성로1,합성지번1\n"
        + "AUTH,2,합성A,합성로2,합성지번2\n",
        encoding="utf-8",
    )
    b.write_text(
        HEADER
        + "AUTH,1,합성동일,합성로1,합성지번1\n"
        + "AUTH,2,합성B,합성로3,합성지번3\n"
        + "OTHER,3,합성C,합성로4,합성지번4\n",
        encoding="utf-8",
    )
    result = audit_cross_category_current_snapshots(
        {"a": a, "b": b},
        sqlite_path=tmp_path / "audit.sqlite",
    )
    assert result["management_number_overlap_across_categories"] == 2
    assert result["authority_plus_management_overlap_across_categories"] == 2
    assert result["overlapping_composite_same_business_name_and_addresses"] == 1
    assert result["overlapping_composite_conflicting_business_name_or_addresses"] == 1
    rendered = str(result)
    assert "합성동일" not in rendered
    assert "합성로1" not in rendered
