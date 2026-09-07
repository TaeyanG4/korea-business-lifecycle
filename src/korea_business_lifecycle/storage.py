from __future__ import annotations

import os
from pathlib import Path

from .config import project_root


class DataRootError(ValueError):
    """Raised when a real-data path violates the local-storage policy."""


def is_within(path: Path, parent: Path) -> bool:
    path = path.resolve()
    parent = parent.resolve()
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def default_data_root() -> Path:
    """Return the ignored project-local directory used for real data by default."""
    return project_root() / "data" / "local"


def resolve_data_root(value: str | os.PathLike[str] | None = None) -> Path:
    raw = str(value) if value is not None else os.environ.get("KBL_DATA_ROOT")
    if not raw:
        raw = str(default_data_root())
    root = Path(raw).expanduser().resolve()
    repo = project_root().resolve()
    allowed_local = default_data_root().resolve()
    if is_within(root, repo) and not is_within(root, allowed_local):
        raise DataRootError(
            "repository-local KBL_DATA_ROOT must resolve under data/local, which is Git-ignored"
        )
    return root


def require_external_artifact(path: str | os.PathLike[str], data_root: Path) -> Path:
    artifact = Path(path).expanduser().resolve()
    if not artifact.is_file():
        raise DataRootError(f"artifact does not exist: {artifact}")
    if not is_within(artifact, data_root):
        raise DataRootError("artifact must be stored under KBL_DATA_ROOT")
    if is_within(artifact, project_root()) and not is_within(
        artifact, default_data_root()
    ):
        raise DataRootError("repository-local artifacts must stay under ignored data/local")
    return artifact
