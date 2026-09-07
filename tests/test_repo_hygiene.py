import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {"AGENTS.md", "SKILL.md", "CLAUDE.md"}


def test_no_local_agent_instruction_files_exist() -> None:
    offenders = [p for p in ROOT.rglob("*") if p.is_file() and p.name in FORBIDDEN_NAMES]
    assert offenders == []


def _is_ignored(path: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", path],
        cwd=ROOT,
        check=False,
    )
    return result.returncode == 0


def test_sensitive_and_bulk_patterns_are_ignored() -> None:
    for path in (
        ".env",
        "credentials.json",
        "data/local/raw/example.csv",
        "data/local/staging/example.parquet",
        "data/local/processed/example.parquet",
        "data/local/logs/build.log",
        "data/local/history/example.json",
        "private/task.txt",
        "AGENTS.md",
        "nested/SKILL.md",
        "nested/CLAUDE.md",
        ".claude/settings.json",
        ".pytest-kbl/example.tmp",
        ".ruff_cache/cache.db",
        ".mypy_cache/state.json",
        "notebooks/.ipynb_checkpoints/example.ipynb",
        "local-run.log",
    ):
        assert _is_ignored(path), path


def test_data_readme_is_not_ignored() -> None:
    assert not _is_ignored("data/README.md")


def test_runtime_data_root_is_explicitly_ignored() -> None:
    assert _is_ignored("data/local/raw/source.csv")
    assert _is_ignored("data/local/history/page-00001.json")
