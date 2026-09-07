from pathlib import Path

import pytest

from korea_business_lifecycle.config import project_root
from korea_business_lifecycle.storage import DataRootError, require_external_artifact, resolve_data_root


def test_data_root_must_be_outside_repository() -> None:
    with pytest.raises(DataRootError, match="outside"):
        resolve_data_root(project_root() / "data")


def test_external_artifact_must_be_under_data_root(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text("a\n1\n", encoding="utf-8")
    with pytest.raises(DataRootError, match="under KBL_DATA_ROOT"):
        require_external_artifact(outside, root)


def test_external_artifact_accepts_file_under_root(tmp_path: Path) -> None:
    root = tmp_path / "root"
    artifact = root / "raw" / "source.csv"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("a\n1\n", encoding="utf-8")
    assert require_external_artifact(artifact, root) == artifact.resolve()
