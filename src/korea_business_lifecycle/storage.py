from __future__ import annotations

import os
from pathlib import Path

from .config import project_root


class DataRootError(ValueError):
    """Raised when a real-data path violates the external-storage policy."""


def is_within(path: Path, parent: Path) -> bool:
    path = path.resolve()
    parent = parent.resolve()
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def default_data_root() -> Path:
    """Return the project-scoped sibling directory used for real data by default."""
    return project_root().parent / "korea-business-lifecycle-data"


def resolve_data_root(value: str | os.PathLike[str] | None = None) -> Path:
    raw = str(value) if value is not None else os.environ.get("KBL_DATA_ROOT")
    if not raw:
        raw = str(default_data_root())
    root = Path(raw).expanduser().resolve()
    if is_within(root, project_root()) or root == project_root().resolve():
        raise DataRootError("KBL_DATA_ROOT must resolve outside the Git repository")
    return root


def require_external_artifact(path: str | os.PathLike[str], data_root: Path) -> Path:
    artifact = Path(path).expanduser().resolve()
    if not artifact.is_file():
        raise DataRootError(f"artifact does not exist: {artifact}")
    if not is_within(artifact, data_root):
        raise DataRootError("artifact must be stored under KBL_DATA_ROOT")
    if is_within(artifact, project_root()):
        raise DataRootError("real artifacts must not be stored inside the Git repository")
    return artifact
