from __future__ import annotations

import hashlib
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def current_git_sha(cwd: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def build_artifact_manifest(
    *,
    source_key: str,
    path: Path,
    project_root: Path,
    observed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stat = path.stat()
    return {
        "manifest_version": 1,
        "source_key": source_key,
        "artifact": {
            "filename": path.name,
            "bytes": stat.st_size,
            "sha256": sha256_file(path),
        },
        "observed": observed or {},
        "environment": {
            "profiled_at_utc": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(),
            "project_git_sha": current_git_sha(project_root),
        },
    }
