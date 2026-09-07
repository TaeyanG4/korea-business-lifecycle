import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_synthetic_fixture_is_small_and_explicitly_synthetic() -> None:
    records = json.loads((ROOT / "tests" / "fixtures" / "synthetic_records.json").read_text(encoding="utf-8"))
    assert 1 <= len(records) <= 10
    assert all(record["synthetic_id"].startswith("fixture-") for record in records)
    assert {record["category"] for record in records} <= {"일반음식점", "휴게음식점", "제과점영업"}
