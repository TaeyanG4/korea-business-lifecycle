from pathlib import Path

import pytest

from korea_business_lifecycle.config import project_root
from korea_business_lifecycle.storage import (
    DataRootError,
    default_data_root,
    require_external_artifact,
    resolve_data_root,
)


def test_repository_local_data_root_must_be_under_data_local() -> None:
    with pytest.raises(DataRootError, match="data/local"):
        resolve_data_root(project_root() / "tmp-data")


def test_default_data_root_is_project_local_ignored_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("KBL_DATA_ROOT", raising=False)
    resolved = resolve_data_root()
    assert resolved == default_data_root().resolve()
    assert resolved == (project_root() / "data" / "local").resolve()


def test_external_artifact_must_be_under_data_root(external_tmp_path: Path) -> None:
    root = external_tmp_path / "root"
    root.mkdir()
    outside = external_tmp_path / "outside.csv"
    outside.write_text("a\n1\n", encoding="utf-8")
    with pytest.raises(DataRootError, match="under KBL_DATA_ROOT"):
        require_external_artifact(outside, root)


def test_external_artifact_accepts_file_under_root(external_tmp_path: Path) -> None:
    root = external_tmp_path / "root"
    artifact = root / "raw" / "source.csv"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("a\n1\n", encoding="utf-8")
    assert require_external_artifact(artifact, root) == artifact.resolve()


def test_repository_local_artifact_accepts_file_under_default_root() -> None:
    root = default_data_root()
    artifact = root / "test-storage" / "synthetic.csv"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("a\n1\n", encoding="utf-8")
    try:
        assert require_external_artifact(artifact, root) == artifact.resolve()
    finally:
        artifact.unlink(missing_ok=True)
        artifact.parent.rmdir()
