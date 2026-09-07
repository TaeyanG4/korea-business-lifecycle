from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from korea_business_lifecycle.config import project_root


@pytest.fixture
def external_tmp_path() -> Path:
    """Temporary test workspace outside the Git repository, cleaned automatically."""
    with tempfile.TemporaryDirectory(prefix=".kbl-test-", dir=project_root().parent) as path:
        yield Path(path)

