from __future__ import annotations

from pathlib import Path

from korea_business_lifecycle.history_cost import estimate_pages_for_current_csv


def test_history_cost_counts_partitioned_pages(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    header = "\uac1c\ubc29\uc790\uce58\ub2e8\uccb4\ucf54\ub4dc,value\n"
    rows = ["3000000,x\n"] * 101 + ["4000000,y\n"] * 100
    path.write_text(header + "".join(rows), encoding="utf-8")
    result = estimate_pages_for_current_csv(path, encoding="utf-8")
    assert result == {
        "rows": 201,
        "authority_count": 2,
        "page_size": 100,
        "estimated_pages_per_asof_date": 3,
    }
