from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping

from .canonical_compatibility import V1_SOURCE_ORDER, latest_retrieval_manifest
from .canonical_permit import (
    PermitTransformError,
    permit_transform_context_from_retrieval_manifest,
    transform_permit_row,
)
from .canonical_schema import FROZEN_V1_SOURCE_COLUMNS, load_permit_parent_schema
from .config import project_root
from .profiling import detect_encoding, sniff_dialect
from .provenance import load_permit_parent_full_dry_run
from .storage import is_within, require_external_artifact, resolve_data_root


PYARROW_VERSION = "21.0.0"
ROWS_PER_BATCH = 50_000
ROWS_PER_ROW_GROUP = 50_000
PARQUET_VERSION = "2.6"
DATA_PAGE_VERSION = "2.0"
COMPRESSION = "zstd"
COMPRESSION_LEVEL = 9
ProgressCallback = Callable[[dict[str, Any]], None]


class PermitMaterializationError(RuntimeError):
    """Raised when local production PERMIT materialization cannot proceed safely."""


def _pyarrow_modules():
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise PermitMaterializationError(
            'pyarrow is required for materialization; install with python -m pip install -e ".[build]"'
        ) from exc
    if pa.__version__ != PYARROW_VERSION:
        raise PermitMaterializationError(
            f"materialization requires pyarrow {PYARROW_VERSION}, found {pa.__version__}"
        )
    return pa, pq


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _schema_sha256() -> str:
    return _sha256_file(project_root() / "schemas" / "permit_parent.v1.json")


def _writer_contract() -> dict[str, Any]:
    return {
        "pyarrow_version": PYARROW_VERSION,
        "format": "PARQUET",
        "parquet_version": PARQUET_VERSION,
        "compression": COMPRESSION.upper(),
        "compression_level": COMPRESSION_LEVEL,
        "data_page_version": DATA_PAGE_VERSION,
        "rows_per_batch": ROWS_PER_BATCH,
        "rows_per_row_group": ROWS_PER_ROW_GROUP,
    }


def _validated_full_dry_run(evidence: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    if evidence.get("decision") != "FULL_CURRENT_SNAPSHOT_DRY_RUN_PASSED":
        raise PermitMaterializationError("full-snapshot dry-run evidence is not in PASSED state")
    scope = evidence.get("scope")
    if not isinstance(scope, Mapping):
        raise PermitMaterializationError("full-snapshot dry-run evidence scope is invalid")
    if scope.get("production_materialization_performed") is not False:
        raise PermitMaterializationError("full-snapshot dry-run evidence unexpectedly claims materialization")
    results = evidence.get("results")
    if not isinstance(results, list) or len(results) != 3:
        raise PermitMaterializationError("full-snapshot dry-run evidence must contain three source results")
    by_source = {
        str(item.get("source_key")): dict(item)
        for item in results
        if isinstance(item, Mapping) and item.get("source_key") in V1_SOURCE_ORDER
    }
    if set(by_source) != set(V1_SOURCE_ORDER):
        raise PermitMaterializationError("full-snapshot dry-run evidence source scope changed")
    expected_total = sum(int(item.get("expected_rows", -1)) for item in by_source.values())
    if expected_total < 1 or scope.get("rows_examined_total") != expected_total:
        raise PermitMaterializationError("full-snapshot dry-run evidence row total is invalid")
    for source_key, item in by_source.items():
        if item.get("status") != "PASS":
            raise PermitMaterializationError(f"{source_key}: full dry-run did not pass")
        if item.get("duplicate_linkage_candidates") != 0:
            raise PermitMaterializationError(f"{source_key}: full dry-run uniqueness proof failed")
        if item.get("temporary_uniqueness_index_removed") is not True:
            raise PermitMaterializationError(f"{source_key}: full dry-run temporary uniqueness state was not removed")
        if item.get("rows_examined") != item.get("expected_rows"):
            raise PermitMaterializationError(f"{source_key}: full dry-run row count is incomplete")
    return by_source


def _build_id(evidence: Mapping[str, Any]) -> str:
    by_source = _validated_full_dry_run(evidence)
    payload = {
        "materializer_version": 1,
        "permit_schema_sha256": _schema_sha256(),
        "writer_contract": _writer_contract(),
        "sources": [
            {
                "source_key": source_key,
                "artifact_sha256": by_source[source_key]["artifact_sha256"],
                "rows": by_source[source_key]["expected_rows"],
            }
            for source_key in V1_SOURCE_ORDER
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"permit-v1-{hashlib.sha256(encoded).hexdigest()[:16]}"


def permit_arrow_schema():
    pa, _ = _pyarrow_modules()
    logical_types = {
        "string": pa.string(),
        "int64": pa.int64(),
        "date32": pa.date32(),
        "timestamp[us,UTC]": pa.timestamp("us", tz="UTC"),
        "float64": pa.float64(),
    }
    schema = load_permit_parent_schema()
    fields = []
    for item in schema["columns"]:
        logical_type = str(item["logical_type"])
        if logical_type not in logical_types:
            raise PermitMaterializationError(f"unsupported PERMIT logical type: {logical_type}")
        fields.append(
            pa.field(
                str(item["name"]),
                logical_types[logical_type],
                nullable=bool(item["nullable"]),
            )
        )
    metadata = {
        b"kbl.schema_name": b"permit_parent",
        b"kbl.schema_version": b"1",
        b"kbl.grain": b"PERMIT",
        b"kbl.publication_status": b"NOT_APPROVED_FOR_PUBLIC_ROW_LEVEL_BUILD",
    }
    return pa.schema(fields, metadata=metadata)


def materialization_plan(
    *,
    data_root: str | Path | None = None,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    selected_evidence = evidence or load_permit_parent_full_dry_run()
    by_source = _validated_full_dry_run(selected_evidence)
    build_id = _build_id(selected_evidence)
    final_dir = root / "canonical" / "permit" / "v1" / build_id
    return {
        "build_id": build_id,
        "scope": list(V1_SOURCE_ORDER),
        "expected_rows_total": sum(int(by_source[key]["expected_rows"]) for key in V1_SOURCE_ORDER),
        "input_bytes_total": sum(int(by_source[key]["artifact_bytes"]) for key in V1_SOURCE_ORDER),
        "input_evidence": "provenance/permit_parent_full_dry_run.json",
        "permit_schema_sha256": _schema_sha256(),
        "writer_contract": _writer_contract(),
        "output_directory": str(final_dir),
        "output_directory_exists": final_dir.exists(),
        "production_materialization_performed": False,
        "public_row_level_release_approved": False,
        "network_access_required": False,
        "status": "READY_FOR_USER_EXECUTION" if not final_dir.exists() else "OUTPUT_ALREADY_EXISTS",
    }


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PermitMaterializationError("retrieval manifest cannot be read as JSON") from exc
    if not isinstance(value, dict):
        raise PermitMaterializationError("retrieval manifest must be a JSON object")
    return value


def _sample_text(path: Path, encoding: str, sample_chars: int = 128_000) -> str:
    with path.open("r", encoding=encoding, errors="strict", newline="") as handle:
        return handle.read(sample_chars)


def _source_artifact(
    source_key: str,
    *,
    root: Path,
    expected: Mapping[str, Any],
) -> tuple[Path, dict[str, Any]]:
    manifest_path = latest_retrieval_manifest(source_key, data_root=root)
    manifest = _load_manifest(manifest_path)
    context = permit_transform_context_from_retrieval_manifest(manifest)
    if context.source_key != source_key:
        raise PermitMaterializationError(f"{source_key}: retrieval manifest source key mismatch")
    artifact = manifest.get("artifact")
    if not isinstance(artifact, Mapping):
        raise PermitMaterializationError(f"{source_key}: retrieval artifact metadata missing")
    relative_path = artifact.get("relative_path")
    if not isinstance(relative_path, str):
        raise PermitMaterializationError(f"{source_key}: retrieval artifact path invalid")
    artifact_path = require_external_artifact(root / relative_path, root)
    if artifact_path.stat().st_size != expected.get("artifact_bytes"):
        raise PermitMaterializationError(f"{source_key}: artifact byte count differs from full dry-run evidence")
    if artifact.get("sha256") != expected.get("artifact_sha256"):
        raise PermitMaterializationError(f"{source_key}: manifest SHA-256 differs from full dry-run evidence")
    if manifest.get("retrieval_id") != expected.get("retrieval_id"):
        raise PermitMaterializationError(f"{source_key}: retrieval id differs from full dry-run evidence")
    return artifact_path, manifest


def _percent(value: int, total: int) -> str:
    if total <= 0:
        return "100.0%"
    return f"{100.0 * value / total:.1f}%"


def format_materialization_progress(event: Mapping[str, Any]) -> str:
    """Format aggregate-only production-build progress without row-level values."""
    kind = str(event.get("event") or "")
    index = int(event.get("task_index", 1))
    task_total = int(event.get("task_total", 1))
    source_key = str(event.get("source_key") or "")
    prefix = f"[{index}/{task_total}]"
    expected_rows = int(event.get("expected_rows", 0))
    rows_written = int(event.get("rows_written", 0))
    overall_rows = int(event.get("overall_rows_written", 0))
    overall_expected = int(event.get("overall_expected_rows", 0))
    if kind == "hash_start":
        return f"{prefix} HASH {source_key} START"
    if kind == "hash_complete":
        return f"{prefix} HASH {source_key} OK"
    if kind == "task_start":
        return f"{prefix} START {source_key} materialization rows={expected_rows:,}"
    if kind == "row_progress":
        return (
            f"{prefix} WRITE {source_key} {rows_written:,}/{expected_rows:,} "
            f"({_percent(rows_written, expected_rows)}) | overall "
            f"{overall_rows:,}/{overall_expected:,} ({_percent(overall_rows, overall_expected)})"
        )
    if kind == "task_complete":
        return (
            f"{prefix} DONE {source_key} rows={rows_written:,} | overall "
            f"{overall_rows:,}/{overall_expected:,} ({_percent(overall_rows, overall_expected)})"
        )
    return f"{prefix} {kind or 'PROGRESS'} {source_key}".strip()


def _write_source_parquet(
    source_key: str,
    *,
    root: Path,
    staging_dir: Path,
    expected: Mapping[str, Any],
    arrow_schema: Any,
    progress: ProgressCallback | None,
    task_index: int,
    task_total: int,
    overall_rows_before: int,
    overall_expected_rows: int,
) -> dict[str, Any]:
    pa, pq = _pyarrow_modules()
    artifact_path, manifest = _source_artifact(source_key, root=root, expected=expected)
    if progress is not None:
        progress({"event": "hash_start", "task_index": task_index, "task_total": task_total, "source_key": source_key})
    actual_sha256 = _sha256_file(artifact_path)
    if actual_sha256 != expected["artifact_sha256"]:
        raise PermitMaterializationError(f"{source_key}: artifact bytes do not match approved SHA-256")
    if progress is not None:
        progress({"event": "hash_complete", "task_index": task_index, "task_total": task_total, "source_key": source_key})

    context = permit_transform_context_from_retrieval_manifest(manifest)
    encoding = str(detect_encoding(artifact_path)["selected"])
    dialect = sniff_dialect(_sample_text(artifact_path, encoding))
    expected_rows = int(expected["expected_rows"])
    output_path = staging_dir / f"{source_key}.parquet"
    permit_quality: Counter[str] = Counter()
    closure_quality: Counter[str] = Counter()
    null_x = 0
    null_y = 0
    rows_written = 0
    batch: list[dict[str, Any]] = []

    if progress is not None:
        progress(
            {
                "event": "task_start",
                "task_index": task_index,
                "task_total": task_total,
                "source_key": source_key,
                "expected_rows": expected_rows,
                "overall_rows_written": overall_rows_before,
                "overall_expected_rows": overall_expected_rows,
            }
        )

    writer = pq.ParquetWriter(
        output_path,
        arrow_schema,
        version=PARQUET_VERSION,
        compression=COMPRESSION,
        compression_level=COMPRESSION_LEVEL,
        use_dictionary=True,
        write_statistics=True,
        data_page_version=DATA_PAGE_VERSION,
    )
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
                raise PermitMaterializationError(f"{source_key}: current-snapshot CSV is empty") from exc
            if len(header) != len(set(header)):
                raise PermitMaterializationError(f"{source_key}: duplicate source header names")
            if len(header) != 39 or set(header) != FROZEN_V1_SOURCE_COLUMNS:
                raise PermitMaterializationError(f"{source_key}: source header differs from frozen inventory")

            for source_row_number, values in enumerate(reader, start=1):
                if len(values) != len(header):
                    raise PermitMaterializationError(
                        f"{source_key}: source row width differs at row {source_row_number}"
                    )
                try:
                    canonical = transform_permit_row(
                        dict(zip(header, values)),
                        context=context,
                        source_row_number=source_row_number,
                    )
                except PermitTransformError as exc:
                    raise PermitMaterializationError(
                        f"{source_key}: PERMIT transform failed at source row {source_row_number}: {exc}"
                    ) from exc
                batch.append(canonical)
                permit_quality[str(canonical["permit_date_quality"])] += 1
                closure_quality[str(canonical["closure_date_quality"])] += 1
                null_x += int(canonical["source_coordinate_x"] is None)
                null_y += int(canonical["source_coordinate_y"] is None)
                rows_written += 1
                if rows_written > expected_rows:
                    raise PermitMaterializationError(f"{source_key}: source exceeded approved row count")

                if len(batch) >= ROWS_PER_BATCH:
                    writer.write_table(pa.Table.from_pylist(batch, schema=arrow_schema), row_group_size=ROWS_PER_ROW_GROUP)
                    batch.clear()
                    if progress is not None:
                        progress(
                            {
                                "event": "row_progress",
                                "task_index": task_index,
                                "task_total": task_total,
                                "source_key": source_key,
                                "expected_rows": expected_rows,
                                "rows_written": rows_written,
                                "overall_rows_written": overall_rows_before + rows_written,
                                "overall_expected_rows": overall_expected_rows,
                            }
                        )
        if batch:
            writer.write_table(pa.Table.from_pylist(batch, schema=arrow_schema), row_group_size=ROWS_PER_ROW_GROUP)
            batch.clear()
        if rows_written != expected_rows:
            raise PermitMaterializationError(f"{source_key}: source row count differs from approved full dry-run")
    except (csv.Error, UnicodeDecodeError) as exc:
        raise PermitMaterializationError(f"{source_key}: CSV parse/decode failed") from exc
    finally:
        writer.close()

    parquet_file = pq.ParquetFile(output_path)
    if parquet_file.metadata.num_rows != expected_rows:
        raise PermitMaterializationError(f"{source_key}: Parquet metadata row count mismatch")
    output_schema = pq.read_schema(output_path)
    if not output_schema.equals(arrow_schema, check_metadata=True):
        raise PermitMaterializationError(f"{source_key}: Parquet Arrow schema mismatch")
    output_sha256 = _sha256_file(output_path)
    output_bytes = output_path.stat().st_size

    if progress is not None:
        progress(
            {
                "event": "task_complete",
                "task_index": task_index,
                "task_total": task_total,
                "source_key": source_key,
                "expected_rows": expected_rows,
                "rows_written": rows_written,
                "overall_rows_written": overall_rows_before + rows_written,
                "overall_expected_rows": overall_expected_rows,
            }
        )

    return {
        "source_key": source_key,
        "input_retrieval_id": expected["retrieval_id"],
        "input_artifact_sha256": expected["artifact_sha256"],
        "input_artifact_bytes": expected["artifact_bytes"],
        "rows": rows_written,
        "permit_date_quality": dict(sorted(permit_quality.items())),
        "closure_date_quality": dict(sorted(closure_quality.items())),
        "null_source_coordinate_x": null_x,
        "null_source_coordinate_y": null_y,
        "uniqueness_validation": "REUSED_EXACT_FULL_DRY_RUN_FOR_IDENTICAL_SHA256",
        "output_file": output_path.name,
        "output_bytes": output_bytes,
        "output_sha256": output_sha256,
        "parquet_row_groups": parquet_file.metadata.num_row_groups,
        "status": "PASS",
    }


def materialize_permit_parent(
    *,
    data_root: str | Path | None = None,
    evidence: Mapping[str, Any] | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    selected_evidence = evidence or load_permit_parent_full_dry_run()
    by_source = _validated_full_dry_run(selected_evidence)
    build_id = _build_id(selected_evidence)
    final_dir = root / "canonical" / "permit" / "v1" / build_id
    if final_dir.exists():
        raise PermitMaterializationError("final build directory already exists; immutable builds are never overwritten")
    staging_dir = root / ".tmp" / "permit-materialization" / f"{build_id}-{os.getpid()}"
    if staging_dir.exists():
        raise PermitMaterializationError("unique staging directory unexpectedly already exists")
    staging_dir.mkdir(parents=True)
    if not is_within(staging_dir, root):
        raise PermitMaterializationError("staging directory escaped KBL_DATA_ROOT")

    arrow_schema = permit_arrow_schema()
    expected_total = sum(int(by_source[key]["expected_rows"]) for key in V1_SOURCE_ORDER)
    results: list[dict[str, Any]] = []
    overall_before = 0
    try:
        for index, source_key in enumerate(V1_SOURCE_ORDER, start=1):
            result = _write_source_parquet(
                source_key,
                root=root,
                staging_dir=staging_dir,
                expected=by_source[source_key],
                arrow_schema=arrow_schema,
                progress=progress,
                task_index=index,
                task_total=len(V1_SOURCE_ORDER),
                overall_rows_before=overall_before,
                overall_expected_rows=expected_total,
            )
            results.append(result)
            overall_before += int(result["rows"])

        manifest = {
            "manifest_version": 1,
            "build_id": build_id,
            "grain": "PERMIT",
            "schema": "schemas/permit_parent.v1.json",
            "permit_schema_sha256": _schema_sha256(),
            "full_dry_run_evidence": "provenance/permit_parent_full_dry_run.json",
            "writer_contract": _writer_contract(),
            "rows_total": sum(int(item["rows"]) for item in results),
            "source_count": len(results),
            "results": results,
            "production_materialization_performed": True,
            "public_row_level_release_approved": False,
            "wgs84_generated": False,
            "episode_reconstruction_performed": False,
            "status": "PASS",
        }
        if manifest["rows_total"] != expected_total:
            raise PermitMaterializationError("materialized row total differs from approved full dry-run")
        (staging_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        final_dir.parent.mkdir(parents=True, exist_ok=True)
        staging_dir.rename(final_dir)
        manifest["output_directory"] = str(final_dir)
        return manifest
    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise
