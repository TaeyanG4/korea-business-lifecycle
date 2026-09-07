from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .episode_materialization import (
    COMPRESSION,
    _pyarrow_modules,
    _schema_sha256,
    _sha256_file,
    _writer_contract,
    episode_arrow_schema,
    production_episode_preflight,
)
from .storage import is_within, resolve_data_root


BUILD_ID = re.compile(r"^permit-episode-v1-[0-9a-f]{16}$")


class EpisodeBuildVerificationError(RuntimeError):
    """Raised when a local production episode build fails independent verification."""


def _all_true(value: Any) -> bool:
    import pyarrow.compute as pc

    result = pc.all(value).as_py()
    return result is True


def _verify_row_invariants(table: Any) -> None:
    import pyarrow.compute as pc

    if table.num_rows == 0:
        return
    if not _all_true(pc.greater_equal(table["episode_number"], 1)):
        raise EpisodeBuildVerificationError("episode_number invariant failed")
    if not _all_true(pc.greater_equal(table["observation_count"], 1)):
        raise EpisodeBuildVerificationError("observation_count invariant failed")
    if not _all_true(
        pc.less_equal(table["observation_window_start_date"], table["first_observed_date"])
    ):
        raise EpisodeBuildVerificationError("observation window start invariant failed")
    if not _all_true(pc.less_equal(table["first_observed_date"], table["last_observed_date"])):
        raise EpisodeBuildVerificationError("first/last observation invariant failed")
    if not _all_true(
        pc.less_equal(table["last_observed_date"], table["observation_window_end_date"])
    ):
        raise EpisodeBuildVerificationError("observation window end invariant failed")
    if not _all_true(pc.equal(table["start_boundary_upper_date"], table["first_observed_date"])):
        raise EpisodeBuildVerificationError("episode start upper-bound invariant failed")
    if not _all_true(pc.equal(table["end_boundary_lower_date"], table["last_observed_date"])):
        raise EpisodeBuildVerificationError("episode end lower-bound invariant failed")

    starts = table["start_censoring"]
    left = pc.equal(starts, "LEFT_CENSORED")
    interval_start = pc.equal(starts, "INTERVAL_CENSORED")
    valid_start_labels = pc.or_(left, interval_start)
    if not _all_true(valid_start_labels):
        raise EpisodeBuildVerificationError("episode start censoring value changed")
    lower_is_null = pc.is_null(table["start_boundary_lower_date"])
    left_ok = pc.or_(pc.invert(left), lower_is_null)
    if not _all_true(left_ok):
        raise EpisodeBuildVerificationError("left-censored start lower bound must be null")
    interval_start_order = pc.less(
        table["start_boundary_lower_date"], table["start_boundary_upper_date"]
    )
    interval_start_ok = pc.or_(pc.invert(interval_start), pc.fill_null(interval_start_order, False))
    if not _all_true(interval_start_ok):
        raise EpisodeBuildVerificationError("interval-censored start bound order failed")

    ends = table["end_censoring"]
    right = pc.equal(ends, "RIGHT_CENSORED")
    interval_end = pc.equal(ends, "INTERVAL_CENSORED")
    if not _all_true(pc.or_(right, interval_end)):
        raise EpisodeBuildVerificationError("episode end censoring value changed")
    upper_is_null = pc.is_null(table["end_boundary_upper_date"])
    right_upper_ok = pc.or_(pc.invert(right), upper_is_null)
    right_flag_ok = pc.or_(pc.invert(right), table["right_censored"])
    if not _all_true(right_upper_ok) or not _all_true(right_flag_ok):
        raise EpisodeBuildVerificationError("right-censored end invariant failed")
    interval_end_order = pc.less(table["end_boundary_lower_date"], table["end_boundary_upper_date"])
    interval_end_ok = pc.or_(pc.invert(interval_end), pc.fill_null(interval_end_order, False))
    interval_flag_ok = pc.or_(pc.invert(interval_end), pc.invert(table["right_censored"]))
    if not _all_true(interval_end_ok) or not _all_true(interval_flag_ok):
        raise EpisodeBuildVerificationError("interval-censored end invariant failed")


def verify_production_episode_build(
    *,
    data_root: str | Path | None = None,
    build_id: str | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    base = root / "canonical" / "permit_status_episode" / "v1"
    if build_id is None:
        candidates = sorted(path for path in base.glob("permit-episode-v1-*") if path.is_dir())
        if len(candidates) != 1:
            raise EpisodeBuildVerificationError("specify build_id unless exactly one episode build exists")
        build_dir = candidates[0]
        selected_build_id = build_dir.name
    else:
        selected_build_id = str(build_id)
        if BUILD_ID.fullmatch(selected_build_id) is None:
            raise EpisodeBuildVerificationError("episode build_id format is invalid")
        build_dir = base / selected_build_id
    if not is_within(build_dir, root) or not build_dir.is_dir():
        raise EpisodeBuildVerificationError("episode build directory is missing or escaped data root")
    manifest_path = build_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EpisodeBuildVerificationError("episode build manifest cannot be read") from exc

    if manifest.get("build_id") != selected_build_id or manifest.get("manifest_version") != 1:
        raise EpisodeBuildVerificationError("episode build manifest identity changed")
    if manifest.get("grain") != "PERMIT_STATUS_EPISODE":
        raise EpisodeBuildVerificationError("episode build grain changed")
    if manifest.get("schema") != "schemas/permit_status_episode.v1.json":
        raise EpisodeBuildVerificationError("episode schema reference changed")
    if manifest.get("episode_schema_sha256") != _schema_sha256():
        raise EpisodeBuildVerificationError("episode schema SHA-256 mismatch")
    if manifest.get("writer_contract") != _writer_contract():
        raise EpisodeBuildVerificationError("episode writer contract changed")
    if manifest.get("snapshot_count") != 7_320:
        raise EpisodeBuildVerificationError("episode build snapshot count is not 7320")
    if manifest.get("production_materialization_performed") is not True or manifest.get("status") != "PASS":
        raise EpisodeBuildVerificationError("episode build is not recorded as completed PASS")
    for key in (
        "management_number_primary_key_claim",
        "history_is_lossless_event_log",
        "status_code_05_semantics_resolved",
        "reopening_vs_correction_resolved",
        "public_row_level_release_approved",
    ):
        if manifest.get(key) is not False:
            raise EpisodeBuildVerificationError(f"episode semantic/publication invariant {key} changed")
    if manifest.get("same_date_duplicate_linkage_candidates_fail_closed") is not True:
        raise EpisodeBuildVerificationError("same-date duplicate linkage fail-closed policy changed")

    preflight = production_episode_preflight(data_root=root)
    if preflight["ready_for_episode_materialization"] is not True:
        raise EpisodeBuildVerificationError("nationwide source snapshot set is no longer complete and unique")

    _, pq = _pyarrow_modules()
    expected_schema = episode_arrow_schema()
    results = manifest.get("results")
    if not isinstance(results, list) or not results:
        raise EpisodeBuildVerificationError("episode build output inventory is empty")
    seen_files: set[str] = set()
    rows_total = 0
    bytes_total = 0
    verified_files = 0
    for item in results:
        relative = str(item.get("output_file", ""))
        if relative in seen_files:
            raise EpisodeBuildVerificationError("duplicate episode output file in manifest")
        seen_files.add(relative)
        path = build_dir / relative
        if not is_within(path, build_dir) or not path.is_file():
            raise EpisodeBuildVerificationError("episode output file is missing or escaped build directory")
        if path.stat().st_size != item.get("output_bytes"):
            raise EpisodeBuildVerificationError("episode output byte count mismatch")
        if _sha256_file(path) != item.get("output_sha256"):
            raise EpisodeBuildVerificationError("episode output SHA-256 mismatch")
        parquet = pq.ParquetFile(path)
        if parquet.metadata.num_rows != item.get("rows"):
            raise EpisodeBuildVerificationError("episode output row count mismatch")
        if not pq.read_schema(path).equals(expected_schema, check_metadata=True):
            raise EpisodeBuildVerificationError("episode output Arrow schema mismatch")
        for row_group_index in range(parquet.metadata.num_row_groups):
            row_group = parquet.metadata.row_group(row_group_index)
            for column_index in range(row_group.num_columns):
                if row_group.column(column_index).compression != COMPRESSION.upper():
                    raise EpisodeBuildVerificationError("episode output compression changed")
        _verify_row_invariants(pq.read_table(path))
        rows_total += int(item["rows"])
        bytes_total += int(item["output_bytes"])
        verified_files += 1

    if rows_total != manifest.get("episode_rows"):
        raise EpisodeBuildVerificationError("episode manifest total row count mismatch")
    if bytes_total != manifest.get("output_bytes") or verified_files != manifest.get("output_files"):
        raise EpisodeBuildVerificationError("episode manifest output aggregate mismatch")
    return {
        "build_id": selected_build_id,
        "snapshot_count": int(manifest["snapshot_count"]),
        "observation_rows": int(manifest["observation_rows"]),
        "episode_rows": rows_total,
        "output_files": verified_files,
        "output_bytes": bytes_total,
        "manifest_verified": True,
        "output_hashes_verified": True,
        "parquet_schemas_verified": True,
        "row_invariants_verified": True,
        "history_snapshot_set_complete_and_unique": True,
        "row_level_values_returned": False,
        "public_row_level_release_approved": False,
        "status": "PASS",
    }
