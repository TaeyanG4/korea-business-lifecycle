from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from .canonical_permit import (
    PermitTransformError,
    permit_transform_context_from_retrieval_manifest,
    transform_permit_row,
)
from .canonical_schema import FROZEN_V1_SOURCE_COLUMNS, REQUIRED_CANONICAL_COLUMNS
from .profiling import detect_encoding, sniff_dialect
from .provenance import V1_SOURCE_KEYS
from .storage import require_external_artifact, resolve_data_root


DEFAULT_COMPATIBILITY_ROWS = 256
MAX_COMPATIBILITY_ROWS = 10_000
V1_SOURCE_ORDER = ("general_restaurants", "rest_cafes", "bakeries")


class CompatibilityValidationError(RuntimeError):
    """Raised when a bounded real-snapshot compatibility gate cannot be passed safely."""


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompatibilityValidationError("retrieval manifest cannot be read as JSON") from exc
    if not isinstance(value, dict):
        raise CompatibilityValidationError("retrieval manifest must be a JSON object")
    return value


def latest_retrieval_manifest(
    source_key: str,
    *,
    data_root: str | Path | None = None,
) -> Path:
    if source_key not in V1_SOURCE_KEYS:
        raise CompatibilityValidationError(f"unsupported v1 source: {source_key}")
    root = resolve_data_root(data_root)
    source_root = root / "raw" / source_key
    manifests = sorted(source_root.glob("*/retrieval.json"), key=lambda path: path.parent.name)
    if not manifests:
        raise CompatibilityValidationError(f"no current-snapshot retrieval manifest found for {source_key}")
    return require_external_artifact(manifests[-1], root)


def _artifact_from_manifest(
    manifest: Mapping[str, Any],
    *,
    data_root: Path,
) -> tuple[Path, int, str]:
    artifact = manifest.get("artifact")
    if not isinstance(artifact, Mapping):
        raise CompatibilityValidationError("retrieval manifest artifact metadata is missing")
    relative_path = artifact.get("relative_path")
    declared_bytes = artifact.get("bytes")
    declared_sha256 = artifact.get("sha256")
    if not isinstance(relative_path, str) or not relative_path:
        raise CompatibilityValidationError("retrieval manifest artifact path is invalid")
    if not isinstance(declared_bytes, int) or declared_bytes < 1:
        raise CompatibilityValidationError("retrieval manifest artifact byte count is invalid")
    if not isinstance(declared_sha256, str):
        raise CompatibilityValidationError("retrieval manifest artifact SHA-256 is invalid")
    artifact_path = require_external_artifact(data_root / relative_path, data_root)
    if artifact_path.stat().st_size != declared_bytes:
        raise CompatibilityValidationError("current-snapshot artifact byte count does not match retrieval manifest")
    return artifact_path, declared_bytes, declared_sha256


def _sample_text(path: Path, encoding: str, sample_chars: int = 128_000) -> str:
    with path.open("r", encoding=encoding, errors="strict", newline="") as handle:
        return handle.read(sample_chars)


def validate_snapshot_compatibility(
    manifest_path: str | Path,
    *,
    data_root: str | Path | None = None,
    max_rows: int = DEFAULT_COMPATIBILITY_ROWS,
) -> dict[str, Any]:
    """Validate a bounded head sample without returning or persisting row-level values."""
    if max_rows < 1 or max_rows > MAX_COMPATIBILITY_ROWS:
        raise CompatibilityValidationError(
            f"max_rows must be between 1 and {MAX_COMPATIBILITY_ROWS}"
        )

    root = resolve_data_root(data_root)
    manifest_file = require_external_artifact(manifest_path, root)
    manifest = _load_manifest(manifest_file)
    context = permit_transform_context_from_retrieval_manifest(manifest)
    artifact_path, artifact_bytes, artifact_sha256 = _artifact_from_manifest(
        manifest,
        data_root=root,
    )

    encoding_info = detect_encoding(artifact_path)
    encoding = str(encoding_info["selected"])
    dialect = sniff_dialect(_sample_text(artifact_path, encoding))

    permit_quality: Counter[str] = Counter()
    closure_quality: Counter[str] = Counter()
    null_x = 0
    null_y = 0
    rows_examined = 0
    seen_linkage: set[tuple[str, str]] = set()

    try:
        with artifact_path.open("r", encoding=encoding, errors="strict", newline="") as handle:
            reader = csv.reader(
                handle,
                delimiter=str(dialect["delimiter"]),
                quotechar=str(dialect["quotechar"]),
                doublequote=bool(dialect["doublequote"]),
                escapechar=dialect["escapechar"],
                strict=True,
            )
            try:
                header = next(reader)
            except StopIteration as exc:
                raise CompatibilityValidationError("current-snapshot CSV is empty") from exc

            if len(header) != len(set(header)):
                raise CompatibilityValidationError("current-snapshot CSV contains duplicate header names")
            if len(header) != 39 or set(header) != FROZEN_V1_SOURCE_COLUMNS:
                raise CompatibilityValidationError(
                    "current-snapshot CSV header does not match the frozen 39-column inventory"
                )

            for source_row_number, values in enumerate(reader, start=1):
                if rows_examined >= max_rows:
                    break
                if len(values) != len(header):
                    raise CompatibilityValidationError(
                        "current-snapshot CSV row width differs from the frozen 39-column inventory"
                    )
                raw_row = dict(zip(header, values))
                canonical = transform_permit_row(
                    raw_row,
                    context=context,
                    source_row_number=source_row_number,
                )
                linkage = (canonical["source_key"], canonical["management_number"])
                if linkage in seen_linkage:
                    raise CompatibilityValidationError(
                        "duplicate expected uniqueness candidate encountered within bounded sample"
                    )
                seen_linkage.add(linkage)
                permit_quality[str(canonical["permit_date_quality"])] += 1
                closure_quality[str(canonical["closure_date_quality"])] += 1
                null_x += int(canonical["source_coordinate_x"] is None)
                null_y += int(canonical["source_coordinate_y"] is None)
                rows_examined += 1
    except PermitTransformError as exc:
        raise CompatibilityValidationError(
            f"bounded sample cannot satisfy frozen PERMIT transform contract: {exc}"
        ) from exc
    except (csv.Error, UnicodeDecodeError) as exc:
        raise CompatibilityValidationError("bounded current-snapshot CSV parse/decode failed") from exc

    if rows_examined == 0:
        raise CompatibilityValidationError("current-snapshot CSV contains no data rows")

    return {
        "source_key": context.source_key,
        "retrieval_id": manifest.get("retrieval_id"),
        "artifact_sha256": artifact_sha256,
        "artifact_bytes": artifact_bytes,
        "sample_policy": "HEAD_ROWS_AFTER_HEADER",
        "max_rows": max_rows,
        "rows_examined": rows_examined,
        "rows_transformed": rows_examined,
        "encoding": encoding,
        "source_column_count": len(header),
        "output_column_count": len(REQUIRED_CANONICAL_COLUMNS),
        "permit_date_quality": dict(sorted(permit_quality.items())),
        "closure_date_quality": dict(sorted(closure_quality.items())),
        "null_source_coordinate_x": null_x,
        "null_source_coordinate_y": null_y,
        "duplicate_linkage_candidates": 0,
        "row_level_values_returned": False,
        "production_materialization_performed": False,
        "status": "PASS",
    }


def validate_latest_current_snapshots(
    *,
    data_root: str | Path | None = None,
    max_rows: int = DEFAULT_COMPATIBILITY_ROWS,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    results = [
        validate_snapshot_compatibility(
            latest_retrieval_manifest(source_key, data_root=root),
            data_root=root,
            max_rows=max_rows,
        )
        for source_key in V1_SOURCE_ORDER
    ]
    return {
        "scope": list(V1_SOURCE_ORDER),
        "sample_policy": "HEAD_ROWS_AFTER_HEADER",
        "max_rows_per_source": max_rows,
        "rows_examined_total": sum(int(item["rows_examined"]) for item in results),
        "production_materialization_performed": False,
        "row_level_values_returned": False,
        "results": results,
        "status": "PASS",
    }
