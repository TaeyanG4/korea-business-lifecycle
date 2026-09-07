from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

from .canonical_materialization_verify import expected_permit_build_id
from .provenance import load_permit_parent_full_dry_run, load_v1_release_scope
from .kaggle_row_release import (
    APPROVED_DATASET_ID,
    DATA_DICTIONARY_FILENAME,
    EXPECTED_COLUMNS,
    EXPECTED_ROWS,
    MANIFEST_FILENAME,
    METADATA_FILENAME,
    PACKAGE_VERSION,
    PUBLIC_CSV_FILENAME,
    PUBLIC_PARQUET_FILENAME,
    README_FILENAME,
    SCHEMA_FILENAME,
    SOURCES_FILENAME,
    SOURCE_SUMMARY_FILENAME,
    _public_arrow_schema,
    _sha256,
)
from .storage import is_within, resolve_data_root


class KaggleRowReleaseVerificationError(RuntimeError):
    """Raised when the prepared canonical row-level Kaggle package fails independent verification."""


def verify_prepared_kaggle_row_release(*, data_root: str | Path | None = None) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    parent_build_id = expected_permit_build_id(load_permit_parent_full_dry_run())
    package = root / "kaggle_release" / "row-level-v1" / parent_build_id / f"package-v{PACKAGE_VERSION}"
    if not package.is_dir() or not is_within(package, root) or package.is_symlink():
        raise KaggleRowReleaseVerificationError("prepared row-level package directory is missing or unsafe")

    expected_files = {
        PUBLIC_CSV_FILENAME,
        PUBLIC_PARQUET_FILENAME,
        SOURCE_SUMMARY_FILENAME,
        SCHEMA_FILENAME,
        DATA_DICTIONARY_FILENAME,
        README_FILENAME,
        SOURCES_FILENAME,
        MANIFEST_FILENAME,
        METADATA_FILENAME,
    }
    actual_files = {path.name for path in package.iterdir() if path.is_file() and not path.is_symlink()}
    if actual_files != expected_files:
        raise KaggleRowReleaseVerificationError("prepared row-level package file allowlist mismatch")

    manifest = json.loads((package / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    if manifest.get("decision") != "CANONICAL_ROW_LEVEL_KAGGLE_PACKAGE_PREPARED":
        raise KaggleRowReleaseVerificationError("row-level package decision changed")
    if manifest.get("dataset_id") != APPROVED_DATASET_ID:
        raise KaggleRowReleaseVerificationError("row-level package dataset id changed")
    if manifest.get("parent_permit_build_id") != parent_build_id:
        raise KaggleRowReleaseVerificationError("row-level parent build id changed")
    if manifest.get("rows") != EXPECTED_ROWS or manifest.get("columns") != EXPECTED_COLUMNS:
        raise KaggleRowReleaseVerificationError("row-level package shape changed")
    if manifest.get("serializations") != ["CSV", "PARQUET"]:
        raise KaggleRowReleaseVerificationError("row-level serialization contract changed")
    scope = load_v1_release_scope()["public_release"]
    if manifest.get("publication_approval_basis") != scope.get("row_level_publication_approval_basis"):
        raise KaggleRowReleaseVerificationError("row-level publication approval basis mismatch")

    listed = {item["name"]: item for item in manifest.get("files", [])}
    expected_payload = expected_files - {MANIFEST_FILENAME, METADATA_FILENAME}
    if set(listed) != expected_payload:
        raise KaggleRowReleaseVerificationError("row-level manifest payload inventory changed")
    for name, item in listed.items():
        path = package / name
        if path.stat().st_size != item.get("bytes") or _sha256(path) != item.get("sha256"):
            raise KaggleRowReleaseVerificationError(f"row-level payload hash/size mismatch: {name}")

    parquet_path = package / PUBLIC_PARQUET_FILENAME
    parquet_file = pq.ParquetFile(parquet_path)
    try:
        parquet_rows = parquet_file.metadata.num_rows
        parquet_columns = parquet_file.schema_arrow.names
    finally:
        close = getattr(parquet_file, "close", None)
        if callable(close):
            close()
    if parquet_rows != EXPECTED_ROWS or len(parquet_columns) != EXPECTED_COLUMNS:
        raise KaggleRowReleaseVerificationError("row-level Parquet shape mismatch")
    if not pq.read_schema(parquet_path).equals(_public_arrow_schema(), check_metadata=True):
        raise KaggleRowReleaseVerificationError("row-level Parquet schema mismatch")

    csv_path = package / PUBLIC_CSV_FILENAME
    csv_reader = pacsv.open_csv(
        csv_path,
        read_options=pacsv.ReadOptions(block_size=16 * 1024 * 1024),
        convert_options=pacsv.ConvertOptions(column_types={name: pa.string() for name in parquet_columns}),
    )
    csv_columns = csv_reader.schema.names
    csv_rows = sum(batch.num_rows for batch in csv_reader)
    if csv_rows != EXPECTED_ROWS or csv_columns != parquet_columns:
        raise KaggleRowReleaseVerificationError("row-level CSV and Parquet shape/column contract differ")

    return {
        "status": "PASS",
        "dataset_id": APPROVED_DATASET_ID,
        "parent_permit_build_id": parent_build_id,
        "rows": EXPECTED_ROWS,
        "columns": EXPECTED_COLUMNS,
        "csv_rows_verified": csv_rows,
        "parquet_rows_verified": parquet_rows,
        "column_order_verified": True,
        "payload_hashes_verified": True,
        "csv": {"bytes": csv_path.stat().st_size, "sha256": _sha256(csv_path)},
        "parquet": {"bytes": parquet_path.stat().st_size, "sha256": _sha256(parquet_path)},
    }
