import hashlib
from pathlib import Path

from korea_business_lifecycle.artifacts import build_artifact_manifest, sha256_file
from korea_business_lifecycle.config import project_root


def test_sha256_file_is_content_addressed(tmp_path: Path) -> None:
    path = tmp_path / "artifact.csv"
    payload = b"a,b\n1,2\n"
    path.write_bytes(payload)
    assert sha256_file(path) == hashlib.sha256(payload).hexdigest()


def test_artifact_manifest_has_no_source_data_values(tmp_path: Path) -> None:
    path = tmp_path / "artifact.csv"
    path.write_text("name\nsynthetic-name\n", encoding="utf-8")
    manifest = build_artifact_manifest(
        source_key="general_restaurants",
        path=path,
        project_root=project_root(),
        observed={"data_row_count": 1},
    )
    assert manifest["artifact"]["bytes"] == path.stat().st_size
    assert len(manifest["artifact"]["sha256"]) == 64
    assert "synthetic-name" not in str(manifest)
