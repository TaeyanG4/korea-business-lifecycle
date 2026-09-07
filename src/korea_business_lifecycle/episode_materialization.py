from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter, OrderedDict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from .canonical_schema import (
    load_permit_status_episode_schema,
    validate_permit_status_episode_schema,
)
from .config import project_root
from .episode_reconstruction import EpisodeReconstructionError, reconstruct_bounded_status_episodes
from .history_nationwide import (
    PRODUCTION_WINDOW_END,
    PRODUCTION_WINDOW_START,
    NationwideHistoryTask,
    build_nationwide_history_tasks,
)
from .storage import is_within, resolve_data_root


PYARROW_VERSION = "21.0.0"
BUCKET_COUNT = 256
MAX_OPEN_BUCKET_FILES = 64
PARQUET_VERSION = "2.6"
DATA_PAGE_VERSION = "2.0"
COMPRESSION = "zstd"
COMPRESSION_LEVEL = 9


class EpisodeMaterializationError(RuntimeError):
    """Raised when production lifecycle episode materialization cannot proceed safely."""


def _pyarrow_modules():
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise EpisodeMaterializationError(
            'pyarrow is required for episode materialization; install with python -m pip install -e ".[build]"'
        ) from exc
    if pa.__version__ != PYARROW_VERSION:
        raise EpisodeMaterializationError(
            f"episode materialization requires pyarrow {PYARROW_VERSION}, found {pa.__version__}"
        )
    return pa, pq


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _schema_sha256() -> str:
    return _sha256_file(project_root() / "schemas" / "permit_status_episode.v1.json")


def episode_arrow_schema():
    pa, _ = _pyarrow_modules()
    schema = load_permit_status_episode_schema()
    errors = validate_permit_status_episode_schema(schema)
    if errors:
        raise EpisodeMaterializationError(f"frozen episode schema validation failed: {errors}")
    logical_types = {
        "string": pa.string(),
        "int32": pa.int32(),
        "date32": pa.date32(),
        "bool": pa.bool_(),
    }
    fields = []
    for item in schema["columns"]:
        logical_type = str(item["logical_type"])
        if logical_type not in logical_types:
            raise EpisodeMaterializationError(f"unsupported episode logical type: {logical_type}")
        fields.append(
            pa.field(str(item["name"]), logical_types[logical_type], nullable=bool(item["nullable"]))
        )
    return pa.schema(
        fields,
        metadata={
            b"kbl.schema_name": b"permit_status_episode",
            b"kbl.schema_version": b"1",
            b"kbl.grain": b"PERMIT_STATUS_EPISODE",
            b"kbl.publication_status": b"NOT_APPROVED_FOR_PUBLIC_ROW_LEVEL_BUILD",
        },
    )


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_source_date(value: Any) -> tuple[str | None, str]:
    text = _normalize_text(value)
    if text is None:
        return None, "MISSING"
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat(), "VALID"
        except ValueError:
            pass
    return None, "INVALID"


def _items_from_page(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        items_obj = payload["response"]["body"].get("items")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
        raise EpisodeMaterializationError(f"unexpected history page structure: {path.name}") from exc
    if not items_obj:
        return []
    raw = items_obj.get("item", [])
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return [raw]
    raise EpisodeMaterializationError(f"unexpected history item structure: {path.name}")


def _observation_from_history_row(
    item: Mapping[str, Any],
    *,
    source_key: str,
    base_date: str,
    authority_code: str,
) -> dict[str, Any]:
    management_number = _normalize_text(item.get("MNG_NO"))
    if management_number is None:
        raise EpisodeMaterializationError("history row is missing required MNG_NO")
    row_authority = _normalize_text(item.get("OPN_ATMY_GRP_CD"))
    if row_authority is not None and row_authority != authority_code:
        raise EpisodeMaterializationError("history row authority differs from its query partition")
    closure_date, closure_quality = _parse_source_date(item.get("CLSBIZ_YMD"))
    return {
        "source_key": source_key,
        "management_number": management_number,
        "observed_date": date.fromisoformat(f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:]}").isoformat(),
        "source_status_code": _normalize_text(item.get("SALS_STTS_CD")),
        "source_status_name": _normalize_text(item.get("SALS_STTS_NM")),
        "source_detail_status_code": _normalize_text(item.get("DTL_SALS_STTS_CD")),
        "source_detail_status_name": _normalize_text(item.get("DTL_SALS_STTS_NM")),
        "source_closure_date": closure_date,
        "source_closure_date_quality": closure_quality,
    }


def _bucket_index(management_number: str) -> int:
    return hashlib.sha256(management_number.encode("utf-8")).digest()[0]


class _BucketWriterPool:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._handles: OrderedDict[Path, Any] = OrderedDict()

    def write(self, source_key: str, bucket: int, row: Mapping[str, Any]) -> None:
        path = self.root / source_key / f"bucket-{bucket:03d}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = self._handles.pop(path, None)
        if handle is None:
            if len(self._handles) >= MAX_OPEN_BUCKET_FILES:
                _, oldest = self._handles.popitem(last=False)
                oldest.close()
            handle = path.open("a", encoding="utf-8", newline="\n")
        self._handles[path] = handle
        handle.write(json.dumps(dict(row), ensure_ascii=False, separators=(",", ":")) + "\n")

    def close(self) -> None:
        for handle in self._handles.values():
            handle.close()
        self._handles.clear()


def _snapshot_for_task(root: Path, task: NationwideHistoryTask) -> tuple[Path, dict[str, Any]]:
    parent = root / "history" / task.source_key / task.base_date / task.authority_code
    manifests = sorted(parent.glob("*/manifest.json")) if parent.is_dir() else []
    if len(manifests) != 1:
        raise EpisodeMaterializationError(
            f"expected exactly one complete snapshot for {task.source_key}/{task.base_date}/{task.authority_code}"
        )
    try:
        manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EpisodeMaterializationError("history manifest cannot be read") from exc
    query = manifest.get("query", {})
    observed = manifest.get("observed", {})
    if manifest.get("source_key") != task.source_key:
        raise EpisodeMaterializationError("history manifest source mismatch")
    if query.get("base_date") != task.base_date or query.get("authority_code") != task.authority_code:
        raise EpisodeMaterializationError("history manifest query mismatch")
    if query.get("service_key_redacted") is not True:
        raise EpisodeMaterializationError("history manifest service-key redaction changed")
    if observed.get("stored_rows") != observed.get("total_count"):
        raise EpisodeMaterializationError("history snapshot stored row count is incomplete")
    return manifests[0].parent, manifest


def production_episode_preflight(*, data_root: str | Path | None = None) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    tasks = build_nationwide_history_tasks()
    complete = 0
    rows = 0
    missing = 0
    multiple = 0
    for task in tasks:
        parent = root / "history" / task.source_key / task.base_date / task.authority_code
        manifests = sorted(parent.glob("*/manifest.json")) if parent.is_dir() else []
        if len(manifests) == 1:
            manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
            complete += 1
            rows += int(manifest.get("observed", {}).get("total_count", 0))
        elif len(manifests) == 0:
            missing += 1
        else:
            multiple += 1
    return {
        "planned_snapshots": len(tasks),
        "complete_snapshots": complete,
        "missing_snapshots": missing,
        "multiple_snapshot_tasks": multiple,
        "observed_rows_in_complete_snapshots": rows,
        "ready_for_episode_materialization": complete == len(tasks) and missing == 0 and multiple == 0,
        "row_level_values_emitted": False,
    }


def _writer_contract() -> dict[str, Any]:
    return {
        "pyarrow_version": PYARROW_VERSION,
        "format": "PARQUET",
        "parquet_version": PARQUET_VERSION,
        "compression": COMPRESSION.upper(),
        "compression_level": COMPRESSION_LEVEL,
        "data_page_version": DATA_PAGE_VERSION,
        "bucket_count": BUCKET_COUNT,
        "bucket_hash": "SHA256_FIRST_BYTE_OF_MANAGEMENT_NUMBER_UTF8",
    }


def _build_id(input_content_sha256: str) -> str:
    payload = {
        "materializer_version": 1,
        "episode_schema_sha256": _schema_sha256(),
        "writer_contract": _writer_contract(),
        "window_start": PRODUCTION_WINDOW_START.isoformat(),
        "window_end": PRODUCTION_WINDOW_END.isoformat(),
        "input_content_sha256": input_content_sha256,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"permit-episode-v1-{hashlib.sha256(encoded).hexdigest()[:16]}"


def _write_episode_parquet(path: Path, rows: list[dict[str, Any]], arrow_schema: Any) -> dict[str, Any]:
    pa, pq = _pyarrow_modules()
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows, schema=arrow_schema)
    pq.write_table(
        table,
        path,
        version=PARQUET_VERSION,
        compression=COMPRESSION,
        compression_level=COMPRESSION_LEVEL,
        use_dictionary=True,
        write_statistics=True,
        data_page_version=DATA_PAGE_VERSION,
    )
    return {
        "rows": table.num_rows,
        "bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _materialize_history_tasks(
    tasks: Iterable[NationwideHistoryTask],
    *,
    data_root: str | Path,
    enforce_production_task_count: bool,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    task_list = list(tasks)
    if enforce_production_task_count and len(task_list) != 7_320:
        raise EpisodeMaterializationError("production episode input task count changed")
    if not task_list:
        raise EpisodeMaterializationError("episode materialization requires at least one history task")
    temp_parent = root / ".tmp"
    temp_parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="episode-materialization-", dir=temp_parent))
    bucket_root = temp_dir / "buckets"
    pool = _BucketWriterPool(bucket_root)
    digest = hashlib.sha256()
    snapshot_count = 0
    page_count = 0
    observation_count = 0
    observations_by_source: Counter[str] = Counter()
    try:
        for task_index, task in enumerate(task_list, start=1):
            if progress_callback is not None:
                progress_callback(
                    {
                        "event": "snapshot_start",
                        "task_index": task_index,
                        "task_total": len(task_list),
                        "source_key": task.source_key,
                        "base_date": task.base_date,
                        "authority_code": task.authority_code,
                        "observation_rows": observation_count,
                    }
                )
            snapshot_dir, manifest = _snapshot_for_task(root, task)
            snapshot_count += 1
            pages = manifest.get("pages", [])
            if not isinstance(pages, list) or not pages:
                raise EpisodeMaterializationError("history manifest page inventory is empty")
            task_rows = 0
            for page in pages:
                filename = str(page.get("filename", ""))
                page_path = snapshot_dir / filename
                if not page_path.is_file() or not is_within(page_path, snapshot_dir):
                    raise EpisodeMaterializationError("history page is missing or escaped its snapshot directory")
                actual_sha = _sha256_file(page_path)
                if actual_sha != page.get("sha256"):
                    raise EpisodeMaterializationError("history page SHA-256 differs from its manifest")
                digest.update(
                    f"{task.source_key}\t{task.base_date}\t{task.authority_code}\t{filename}\t{actual_sha}\n".encode(
                        "utf-8"
                    )
                )
                rows = _items_from_page(page_path)
                if len(rows) != int(page.get("rows", -1)):
                    raise EpisodeMaterializationError("history page row count differs from its manifest")
                page_count += 1
                for item in rows:
                    observation = _observation_from_history_row(
                        item,
                        source_key=task.source_key,
                        base_date=task.base_date,
                        authority_code=task.authority_code,
                    )
                    pool.write(
                        task.source_key,
                        _bucket_index(str(observation["management_number"])),
                        observation,
                    )
                    task_rows += 1
                    observation_count += 1
                    observations_by_source[task.source_key] += 1
            if task_rows != int(manifest["observed"]["total_count"]):
                raise EpisodeMaterializationError("history snapshot row count differs after page verification")
            if progress_callback is not None:
                progress_callback(
                    {
                        "event": "snapshot_complete",
                        "task_index": task_index,
                        "task_total": len(task_list),
                        "source_key": task.source_key,
                        "base_date": task.base_date,
                        "authority_code": task.authority_code,
                        "observation_rows": observation_count,
                    }
                )
        pool.close()

        input_content_sha256 = digest.hexdigest()
        build_id = _build_id(input_content_sha256)
        final_dir = root / "canonical" / "permit_status_episode" / "v1" / build_id
        if final_dir.exists():
            raise EpisodeMaterializationError(f"immutable episode build already exists: {build_id}")
        output_staging = temp_dir / "output"
        output_staging.mkdir(parents=True, exist_ok=True)
        arrow_schema = episode_arrow_schema()
        output_results: list[dict[str, Any]] = []
        total_episode_rows = 0
        total_output_bytes = 0
        for source_key in sorted(observations_by_source):
            source_episode_rows = 0
            source_output_bytes = 0
            source_files = 0
            for bucket in range(BUCKET_COUNT):
                bucket_path = bucket_root / source_key / f"bucket-{bucket:03d}.jsonl"
                if not bucket_path.is_file():
                    continue
                observations: list[dict[str, Any]] = []
                with bucket_path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        observations.append(json.loads(line))
                try:
                    episodes = reconstruct_bounded_status_episodes(
                        observations,
                        observation_window_start_date=PRODUCTION_WINDOW_START,
                        observation_window_end_date=PRODUCTION_WINDOW_END,
                        max_observations=max(1, len(observations)),
                    )
                except EpisodeReconstructionError as exc:
                    raise EpisodeMaterializationError(
                        "episode reconstruction failed; duplicate source/date linkage candidates or invalid history semantics detected"
                    ) from exc
                if not episodes:
                    continue
                output_path = output_staging / source_key / f"part-{bucket:03d}.parquet"
                written = _write_episode_parquet(output_path, episodes, arrow_schema)
                output_results.append(
                    {
                        "source_key": source_key,
                        "bucket": bucket,
                        "output_file": f"{source_key}/{output_path.name}",
                        "rows": written["rows"],
                        "output_bytes": written["bytes"],
                        "output_sha256": written["sha256"],
                    }
                )
                source_episode_rows += int(written["rows"])
                source_output_bytes += int(written["bytes"])
                source_files += 1
                if progress_callback is not None:
                    progress_callback(
                        {
                            "event": "bucket_complete",
                            "source_key": source_key,
                            "bucket": bucket,
                            "bucket_total": BUCKET_COUNT,
                            "episode_rows": total_episode_rows + source_episode_rows,
                            "observation_rows": observation_count,
                        }
                    )
            total_episode_rows += source_episode_rows
            total_output_bytes += source_output_bytes

        manifest = {
            "manifest_version": 1,
            "build_id": build_id,
            "grain": "PERMIT_STATUS_EPISODE",
            "schema": "schemas/permit_status_episode.v1.json",
            "episode_schema_sha256": _schema_sha256(),
            "authority_policy": "provenance/history_authority_policy.json",
            "observation_strategy": "provenance/history_observation_strategy.json",
            "observation_window_start_date": PRODUCTION_WINDOW_START.isoformat(),
            "observation_window_end_date": PRODUCTION_WINDOW_END.isoformat(),
            "snapshot_count": snapshot_count,
            "history_page_count": page_count,
            "observation_rows": observation_count,
            "episode_rows": total_episode_rows,
            "input_content_sha256": input_content_sha256,
            "writer_contract": _writer_contract(),
            "output_bytes": total_output_bytes,
            "output_files": len(output_results),
            "results": output_results,
            "production_materialization_performed": True,
            "same_date_duplicate_linkage_candidates_fail_closed": True,
            "management_number_primary_key_claim": False,
            "history_is_lossless_event_log": False,
            "status_code_05_semantics_resolved": False,
            "reopening_vs_correction_resolved": False,
            "public_row_level_release_approved": False,
            "status": "PASS",
        }
        (output_staging / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        final_dir.parent.mkdir(parents=True, exist_ok=True)
        os.replace(output_staging, final_dir)
        return {
            "build_id": build_id,
            "build_directory": str(final_dir),
            "snapshot_count": snapshot_count,
            "history_page_count": page_count,
            "observation_rows": observation_count,
            "episode_rows": total_episode_rows,
            "output_files": len(output_results),
            "output_bytes": total_output_bytes,
            "input_content_sha256": input_content_sha256,
            "row_level_values_emitted": False,
            "public_row_level_release_approved": False,
            "status": "PASS",
        }
    finally:
        pool.close()
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def materialize_production_history_episodes(
    *,
    data_root: str | Path | None = None,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    preflight = production_episode_preflight(data_root=root)
    if preflight["ready_for_episode_materialization"] is not True:
        raise EpisodeMaterializationError(
            f"nationwide history snapshot set is incomplete: complete={preflight['complete_snapshots']} "
            f"missing={preflight['missing_snapshots']} multiple={preflight['multiple_snapshot_tasks']}"
        )
    return _materialize_history_tasks(
        build_nationwide_history_tasks(),
        data_root=root,
        enforce_production_task_count=True,
        progress_callback=progress_callback,
    )


def episode_materialization_plan() -> dict[str, Any]:
    return {
        "checked_at": "2026-09-07",
        "decision": "PRODUCTION_EPISODE_MATERIALIZATION_PREPARED_WAITING_FOR_COMPLETE_HISTORY",
        "scope": {
            "grain": "PERMIT_STATUS_EPISODE",
            "schema": "schemas/permit_status_episode.v1.json",
            "schema_columns": 23,
            "window_start": PRODUCTION_WINDOW_START.isoformat(),
            "window_end": PRODUCTION_WINDOW_END.isoformat(),
            "required_history_snapshot_tasks": 7_320,
            "history_acquisition_plan": "provenance/history_nationwide_acquisition_plan.json",
            "authority_policy": "provenance/history_authority_policy.json",
        },
        "implementation": {
            "module": "src/korea_business_lifecycle/episode_materialization.py",
            "script": "scripts/materialize_history_episodes.py",
            "verifier_script": "scripts/verify_history_episode_build.py",
            "network_required": False,
            "bucket_count": BUCKET_COUNT,
            "bucket_hash": "SHA256_FIRST_BYTE_OF_MANAGEMENT_NUMBER_UTF8",
            "pyarrow_version": PYARROW_VERSION,
            "compression": COMPRESSION.upper(),
        },
        "gates": {
            "complete_history_snapshot_tasks_required": True,
            "multiple_snapshots_for_one_task_allowed": False,
            "raw_history_page_sha256_verified_before_use": True,
            "same_source_management_number_date_duplicate_allowed": False,
            "management_number_primary_key_claim": False,
            "history_is_lossless_event_log": False,
            "public_row_level_release_approved": False,
        },
        "execution": {
            "execution_performed": False,
            "long_running_action_requires_visible_user_command": True,
            "preflight_available": True,
        },
        "next_gate": "complete and verify all nationwide monthly history snapshots before episode materialization",
    }
