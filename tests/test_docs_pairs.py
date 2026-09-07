from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_korean_english_public_docs_are_paired() -> None:
    ko = {p.name for p in (ROOT / "docs" / "ko").glob("*.md")}
    en = {p.name for p in (ROOT / "docs" / "en").glob("*.md")}
    assert ko
    assert ko == en

