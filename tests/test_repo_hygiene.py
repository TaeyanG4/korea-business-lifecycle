import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {"AGENTS.md", "SKILL.md", "CLAUDE.md"}


def test_no_local_agent_instruction_files_exist() -> None:
    offenders = [p for p in ROOT.rglob("*") if p.is_file() and p.name in FORBIDDEN_NAMES]
    assert offenders == []


def test_data_work_directories_only_contain_placeholders() -> None:
    for name in ("raw", "staging", "processed", "logs"):
        files = [p.name for p in (ROOT / "data" / name).iterdir() if p.is_file()]
        assert files == [".gitkeep"]


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
        "data/raw/example.csv",
        "data/staging/example.parquet",
        "data/processed/example.parquet",
        "data/logs/build.log",
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


def test_data_gitkeep_is_not_ignored() -> None:
    assert not _is_ignored("data/raw/.gitkeep")
