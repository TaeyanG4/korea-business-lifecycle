from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from .provenance import (
    load_observed_snapshot_summary,
    load_permit_geospatial_materialization,
    load_permit_parent_materialization,
    load_public_permit_aggregate,
    load_v1_release_scope,
)
from .storage import resolve_data_root


AGGREGATE_BUILD_ID = "permit-public-agg-v1-bedd874de6619bee"
AGGREGATE_FILENAME = "permit_aggregate.parquet"
PUBLIC_PARQUET_FILENAME = "korea_food_service_permit_aggregate.parquet"
PUBLIC_CSV_FILENAME = "korea_food_service_permit_aggregate.csv"
SOURCE_SUMMARY_FILENAME = "source_summary.csv"
SCHEMA_FILENAME = "schema.json"
DATA_DICTIONARY_FILENAME = "DATA_DICTIONARY.md"
README_FILENAME = "README.md"
SOURCES_FILENAME = "SOURCES.md"
MANIFEST_FILENAME = "release-manifest.json"
METADATA_FILENAME = "dataset-metadata.json"
PACKAGE_VERSION = 2
EXPECTED_SHA256 = "112fbec3187b2d77df2744edb878fa0f3ecb850cf675496cd4383404092911fb"
EXPECTED_BYTES = 108_019
EXPECTED_ROWS = 67_267
EXPECTED_RELEASED_SOURCE_ROWS = 2_383_689
DATASET_SLUG = "korea-food-service-permit-aggregate"
PUBLIC_COLUMNS = [
    "source_key",
    "authority_code",
    "source_status_code",
    "source_detail_status_code",
    "permit_year",
    "closure_year",
    "cell_count",
]
SOURCE_ORDER = ["general_restaurants", "rest_cafes", "bakeries"]


class KaggleReleaseError(RuntimeError):
    """Raised when the aggregate release package cannot be prepared safely."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _file_record(path: Path) -> dict[str, Any]:
    return {
        "name": path.name,
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _validate_owner(owner: str) -> str:
    value = owner.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
        raise KaggleReleaseError("Kaggle owner must be a username/organization slug")
    return value


def _metadata(owner: str) -> dict[str, Any]:
    dataset_id = f"{owner}/{DATASET_SLUG}"
    return {
        "title": "Korea Food-Service Permit Aggregate",
        "subtitle": "Privacy-minimized nationwide local permit snapshot aggregate",
        "description": (
            "A privacy-minimized aggregate derived from the nationwide current snapshot of "
            "three Korean Ministry of the Interior and Safety local-government food-service "
            "permit categories: general restaurants, rest cafes, and bakeries. The verified "
            "parent contains 3,010,802 permit records. This release contains 67,267 aggregate "
            "cells after suppressing cells with fewer than 10 source rows. CSV and Parquet are "
            "two serializations of the same aggregate, not additional row-level records. It "
            "excludes business names, exact addresses, management numbers, phone numbers, precise "
            "coordinates, and other row-level/linkable fields. Permit year is not claimed to be "
            "physical opening year; closure year is not claimed to be an irreversible terminal "
            "event. Status 03 is not treated as irreversible and status 05 remains unresolved. "
            "The official source pages display no restriction on the permitted-use scope. License "
            "metadata is therefore recorded as Other and the official source pages/terms are the "
            "controlling source-use reference; this project does not relicense upstream source records."
        ),
        "id": dataset_id,
        "licenses": [{"name": "other"}],
        "keywords": ["business", "restaurants"],
        "resources": [
            {
                "path": PUBLIC_PARQUET_FILENAME,
                "description": "Typed, compact Parquet serialization of the verified k=10 aggregate.",
            },
            {
                "path": PUBLIC_CSV_FILENAME,
                "description": "UTF-8 CSV serialization of the same 67,267 aggregate cells.",
            },
            {
                "path": SOURCE_SUMMARY_FILENAME,
                "description": "Safe source-level scale summary derived from tracked aggregate provenance.",
            },
        ],
    }


def _write_aggregate_csv(source: Path, destination: Path) -> dict[str, Any]:
    parquet = pq.ParquetFile(source)
    if parquet.schema_arrow.names != PUBLIC_COLUMNS:
        raise KaggleReleaseError("aggregate Parquet column order changed")

    rows = 0
    represented_rows = 0
    cells_by_source = {key: 0 for key in SOURCE_ORDER}
    represented_by_source = {key: 0 for key in SOURCE_ORDER}
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(PUBLIC_COLUMNS)
        for batch in parquet.iter_batches(batch_size=10_000, columns=PUBLIC_COLUMNS):
            for record in batch.to_pylist():
                source_key = record["source_key"]
                if source_key not in cells_by_source:
                    raise KaggleReleaseError(f"unexpected source_key in aggregate: {source_key}")
                cell_count = int(record["cell_count"])
                if cell_count < 10:
                    raise KaggleReleaseError("aggregate contains a cell below k=10")
                writer.writerow(["" if record[name] is None else record[name] for name in PUBLIC_COLUMNS])
                rows += 1
                represented_rows += cell_count
                cells_by_source[source_key] += 1
                represented_by_source[source_key] += cell_count

    if rows != EXPECTED_ROWS:
        raise KaggleReleaseError("CSV row count does not match verified aggregate")
    if represented_rows != EXPECTED_RELEASED_SOURCE_ROWS:
        raise KaggleReleaseError("CSV represented-source-row total does not match verified aggregate")
    return {
        "rows": rows,
        "represented_source_rows": represented_rows,
        "cells_by_source": cells_by_source,
        "represented_by_source": represented_by_source,
    }


def _source_summary_rows(aggregate_stats: dict[str, Any]) -> list[dict[str, Any]]:
    observed = load_observed_snapshot_summary()
    parent = load_permit_parent_materialization()
    geospatial = load_permit_geospatial_materialization()

    observed_by_source = {item["source_key"]: item for item in observed["categories"]}
    parent_by_source = {item["source_key"]: item for item in parent["results"]}
    geo_by_source = {item["source_key"]: item for item in geospatial["results"]}
    if set(observed_by_source) != set(SOURCE_ORDER):
        raise KaggleReleaseError("observed source summary no longer matches v1 sources")
    if set(parent_by_source) != set(SOURCE_ORDER) or set(geo_by_source) != set(SOURCE_ORDER):
        raise KaggleReleaseError("materialization provenance no longer matches v1 sources")

    rows: list[dict[str, Any]] = []
    for source_key in SOURCE_ORDER:
        observed_item = observed_by_source[source_key]
        parent_item = parent_by_source[source_key]
        geo_item = geo_by_source[source_key]
        rows.append(
            {
                "source_key": source_key,
                "source_rows": observed_item["rows"],
                "raw_source_bytes": observed_item["bytes"],
                "canonical_parquet_bytes": parent_item["output_bytes"],
                "coordinate_pairs_present": observed_item["coordinate_pairs_present"],
                "wgs84_sidecar_bytes": geo_item["output_bytes"],
                "published_aggregate_cells": aggregate_stats["cells_by_source"][source_key],
                "published_source_rows": aggregate_stats["represented_by_source"][source_key],
            }
        )
    return rows


def _write_source_summary(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "source_key",
        "source_rows",
        "raw_source_bytes",
        "canonical_parquet_bytes",
        "coordinate_pairs_present",
        "wgs84_sidecar_bytes",
        "published_aggregate_cells",
        "published_source_rows",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _release_schema() -> dict[str, Any]:
    return {
        "schema_name": "public_permit_aggregate_release",
        "schema_version": 1,
        "release_package_version": PACKAGE_VERSION,
        "grain": "PRIVACY_MINIMIZED_PERMIT_AGGREGATE_CELL",
        "artifact_schema_source": {
            "path": "schemas/public_permit_aggregate.v1.json",
            "sha256": "35b3145a3e6aace98881b9d0efb8c6298c740130f71f57b78f45aee74a480a45",
            "note": (
                "The tracked frozen candidate schema preserves historical pre-release gate flags. "
                "This release schema exposes only the published column/semantic contract; final "
                "publication approval is recorded in provenance/v1_release_scope.json."
            ),
        },
        "serializations": {
            "csv": {
                "file": PUBLIC_CSV_FILENAME,
                "encoding": "UTF-8",
                "line_ending": "LF",
                "null_representation": "empty field",
            },
            "parquet": {
                "file": PUBLIC_PARQUET_FILENAME,
                "compression": "ZSTD",
                "compression_level": 9,
                "parquet_version": "2.6",
            },
        },
        "columns": [
            {"name": "source_key", "logical_type": "string", "nullable": False},
            {"name": "authority_code", "logical_type": "string", "nullable": False},
            {"name": "source_status_code", "logical_type": "string", "nullable": True},
            {"name": "source_detail_status_code", "logical_type": "string", "nullable": True},
            {"name": "permit_year", "logical_type": "int32", "nullable": True},
            {"name": "closure_year", "logical_type": "int32", "nullable": True},
            {
                "name": "cell_count",
                "logical_type": "int64",
                "nullable": False,
                "constraints": [">= 10"],
            },
        ],
        "semantic_limits": {
            "permit_year_is_physical_open_year": False,
            "closure_year_is_permanent_terminal_event": False,
            "status_code_03_irreversible": False,
            "status_code_05_semantics_resolved": False,
            "canonical_status_mapping_enabled": False,
        },
        "privacy": {
            "row_level_records_included": False,
            "business_names_included": False,
            "exact_addresses_included": False,
            "management_numbers_included": False,
            "telephone_or_homepage_included": False,
            "precise_coordinates_included": False,
            "minimum_cell_count": 10,
            "minimum_cell_count_is_legal_privacy_guarantee": False,
        },
    }


def _data_dictionary() -> str:
    return """# Data Dictionary

This file describes the seven columns shared by the CSV and Parquet aggregate files.

| Column | Type | Nullable | Meaning |
| --- | --- | --- | --- |
| `source_key` | string | no | One of `general_restaurants`, `rest_cafes`, or `bakeries`. |
| `authority_code` | string | no | Local-government authority grouping code. It is a grouping geography/code, not a business identifier. |
| `source_status_code` | string | yes | Raw source status code. No invented canonical status label is applied. |
| `source_detail_status_code` | string | yes | Raw source detail-status code. No invented canonical status label is applied. |
| `permit_year` | int32 | yes | Calendar year derived from the source permit date. It is not claimed to be the physical opening year. |
| `closure_year` | int32 | yes | Calendar year derived from the source closure-date field when present. It is contextual and is not claimed to be a permanent terminal event. |
| `cell_count` | int64 | no | Number of source rows represented by the aggregate cell. Every released cell is at least 10. |

## Status and lifecycle limits

- Status `03` is not irreversible: two source-level `03->01` reversals were observed during project validation.
- Status `05` remains unresolved/unmapped.
- `permit_year` must not be converted into a claim about physical opening date.
- `closure_year` must not be converted into a claim about permanent closure.
- The current snapshot does not establish reopening events or full lifecycle histories.

## Privacy boundary

No business name, exact address, management number, phone/homepage, exact date, source row number, or precise source/WGS84 coordinate is included. The k=10 threshold is a technical minimization rule, not a legal privacy guarantee.
"""


def _sources_text() -> str:
    return """# Official sources and terms

Provider: Ministry of the Interior and Safety (MOIS), Republic of Korea.

- General restaurants - data.go.kr ID 15154916: https://www.data.go.kr/data/15154916/openapi.do
- Rest cafes - data.go.kr ID 15154921: https://www.data.go.kr/data/15154921/openapi.do
- Bakeries - data.go.kr ID 15155252: https://www.data.go.kr/data/15155252/openapi.do
- Public Data Portal policy: https://www.data.go.kr/ugs/selectPortalPolicyView.do

The three official API detail pages were rechecked on 2026-09-08 and displayed no restriction on the permitted-use scope. Kaggle metadata uses the `other` license category so this project does not invent or impose a different license on upstream government records. This public package contains only the independently verified privacy-minimized aggregate; row-level records and precise coordinates are not included.
"""


def _readme_text(*, csv_bytes: int, source_summary_rows: list[dict[str, Any]]) -> str:
    source_summary_cells = sum(int(item["published_aggregate_cells"]) for item in source_summary_rows)
    source_summary_represented = sum(int(item["published_source_rows"]) for item in source_summary_rows)
    if source_summary_cells != EXPECTED_ROWS or source_summary_represented != EXPECTED_RELEASED_SOURCE_ROWS:
        raise KaggleReleaseError("source summary does not reconcile to verified aggregate totals")
    return f"""# Korea Food-Service Permit Aggregate

This Kaggle dataset is the public, privacy-minimized release of a much larger nationwide current-snapshot pipeline covering general restaurants, rest cafes, and bakeries in Korea.

## Why the public data is much smaller than the collected source

The project retrieved and validated **3,010,802 source rows / 926,587,446 bytes (~926.6 MB)** of current CSV data. It then materialized a private canonical `PERMIT` build of **165,176,236 bytes (~165.2 MB)** and a private WGS84 sidecar of **50,805,782 bytes (~50.8 MB)**.

The public release is intentionally smaller because it:

1. aggregates 3,010,802 row-level permits into 67,267 released cells;
2. suppresses 229,928 cells with fewer than 10 source rows;
3. removes high-cardinality/linkable fields such as business names, exact addresses, management numbers, phone numbers, and coordinates; and
4. stores low-cardinality aggregate data efficiently in ZSTD-compressed Parquet.

The **108,019-byte Parquet file does not mean only 108 KB was collected**. It is the compact public representation after aggregation and minimization. The CSV serialization is **{csv_bytes:,} bytes** and contains the same 67,267 cells in a more broadly accessible format. Rows are never duplicated merely to inflate dataset size.

## Package files

- `{PUBLIC_CSV_FILENAME}` - UTF-8 CSV for preview, spreadsheets, and broad tooling.
- `{PUBLIC_PARQUET_FILENAME}` - typed/compact Parquet for analytical engines.
- `{SOURCE_SUMMARY_FILENAME}` - one safe scale-summary row per source category.
- `{SCHEMA_FILENAME}` - release-oriented column/type/semantic schema.
- `{DATA_DICTIONARY_FILENAME}` - column definitions and interpretation limits.
- `{SOURCES_FILENAME}` - official source pages and source-use notes.
- `{MANIFEST_FILENAME}` - package version, build lineage, byte sizes, and SHA-256 hashes.

## Coverage and suppression

- Verified parent snapshot rows: 3,010,802
- Aggregate cells before suppression: 297,195
- Released aggregate cells: 67,267
- Suppressed aggregate cells: 229,928
- Source rows represented by released cells: 2,383,689
- Source rows represented by suppressed cells: 627,113
- Minimum released cell count: 10

The seven public columns are `source_key`, `authority_code`, `source_status_code`, `source_detail_status_code`, `permit_year`, `closure_year`, and `cell_count`.

## Important interpretation limits

- `permit_year` is not claimed to be a physical opening year.
- `closure_year` is not claimed to be a permanent terminal event.
- Status `03` is not treated as irreversible; two source-level `03->01` reversals were observed during project validation.
- Status `05` remains unresolved.
- `authority_code` is a grouping code, not a business identifier.
- `k=10` is a technical minimization threshold, not a legal privacy guarantee.

## Public/private boundary

This Kaggle package does **not** contain row-level `PERMIT`, business names, exact addresses, management numbers, phone/homepage fields, precise EPSG:5174 coordinates, WGS84 coordinates, or partial history snapshots. The canonical row-level Parquet and WGS84 sidecar remain private runtime artifacts.

CSV and Parquet are two serializations of the same privacy-minimized aggregate. They do not broaden the public record scope.

Repository and full reproducibility/provenance: https://github.com/TaeyanG4/korea-business-lifecycle
"""


def _assert_ascii_stage(paths: list[Path]) -> None:
    for path in paths:
        data = path.read_bytes()
        if any(byte > 0x7F for byte in data):
            raise KaggleReleaseError(
                f"Kaggle staging text must remain ASCII-only for the verified Windows CLI path: {path.name}"
            )


def prepare_kaggle_release(
    *,
    owner: str | None = None,
    data_root: str | Path | None = None,
) -> dict[str, Any]:
    root = resolve_data_root(data_root)
    source = (
        root
        / "public_candidate"
        / "permit_aggregate"
        / "v1"
        / AGGREGATE_BUILD_ID
        / AGGREGATE_FILENAME
    )
    if not source.is_file():
        raise KaggleReleaseError(f"verified aggregate artifact not found: {source}")
    if source.stat().st_size != EXPECTED_BYTES:
        raise KaggleReleaseError("aggregate byte size does not match verified provenance")
    actual_sha = _sha256(source)
    if actual_sha != EXPECTED_SHA256:
        raise KaggleReleaseError("aggregate SHA-256 does not match verified provenance")

    release_scope = load_v1_release_scope()
    public = release_scope["public_release"]
    if public.get("aggregate_publication_approved") is not True:
        raise KaggleReleaseError("final v1 release scope does not approve aggregate publication")
    if public.get("row_level_permit_publication_approved") is not False:
        raise KaggleReleaseError("row-level publication invariant changed")
    if public.get("precise_wgs84_publication_approved") is not False:
        raise KaggleReleaseError("precise-coordinate publication invariant changed")
    if public.get("aggregate_sha256") != actual_sha:
        raise KaggleReleaseError("release-scope aggregate hash mismatch")

    aggregate_provenance = load_public_permit_aggregate()
    if aggregate_provenance["scope"]["aggregate_cells_released_candidate"] != EXPECTED_ROWS:
        raise KaggleReleaseError("aggregate provenance row count changed")
    if aggregate_provenance["scope"]["released_source_rows"] != EXPECTED_RELEASED_SOURCE_ROWS:
        raise KaggleReleaseError("aggregate provenance represented-row count changed")

    managed_names = {
        PUBLIC_PARQUET_FILENAME,
        PUBLIC_CSV_FILENAME,
        SOURCE_SUMMARY_FILENAME,
        SCHEMA_FILENAME,
        DATA_DICTIONARY_FILENAME,
        README_FILENAME,
        SOURCES_FILENAME,
        MANIFEST_FILENAME,
        METADATA_FILENAME,
    }
    output = root / "kaggle_release" / "v1" / AGGREGATE_BUILD_ID / f"package-v{PACKAGE_VERSION}"
    output.mkdir(parents=True, exist_ok=True)
    existing = list(output.iterdir())
    unknown = sorted(path.name for path in existing if path.name not in managed_names)
    if unknown:
        raise KaggleReleaseError(
            "Kaggle staging directory contains unexpected files; refusing to risk unintended upload: "
            + ", ".join(unknown)
        )
    for name in managed_names:
        path = output / name
        if path.exists() and not path.is_file():
            raise KaggleReleaseError(f"managed Kaggle staging path is not a regular file: {path.name}")
        if path.is_file():
            path.unlink()

    parquet_destination = output / PUBLIC_PARQUET_FILENAME
    shutil.copyfile(source, parquet_destination)
    if _sha256(parquet_destination) != actual_sha:
        raise KaggleReleaseError("copied Kaggle Parquet hash mismatch")

    csv_destination = output / PUBLIC_CSV_FILENAME
    aggregate_stats = _write_aggregate_csv(parquet_destination, csv_destination)
    source_summary_rows = _source_summary_rows(aggregate_stats)
    source_summary_path = output / SOURCE_SUMMARY_FILENAME
    _write_source_summary(source_summary_path, source_summary_rows)

    schema_path = output / SCHEMA_FILENAME
    schema_path.write_text(
        json.dumps(_release_schema(), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    dictionary_path = output / DATA_DICTIONARY_FILENAME
    dictionary_path.write_text(_data_dictionary(), encoding="utf-8", newline="\n")
    sources_path = output / SOURCES_FILENAME
    sources_path.write_text(_sources_text(), encoding="utf-8", newline="\n")
    readme_path = output / README_FILENAME
    readme_path.write_text(
        _readme_text(csv_bytes=csv_destination.stat().st_size, source_summary_rows=source_summary_rows),
        encoding="utf-8",
        newline="\n",
    )

    payload_paths = [
        readme_path,
        sources_path,
        dictionary_path,
        schema_path,
        source_summary_path,
        csv_destination,
        parquet_destination,
    ]
    _assert_ascii_stage([path for path in payload_paths if path.suffix != ".parquet"])
    file_records = [_file_record(path) for path in payload_paths]

    observed = load_observed_snapshot_summary()
    parent = load_permit_parent_materialization()
    geospatial = load_permit_geospatial_materialization()
    manifest = {
        "decision": "KAGGLE_AGGREGATE_RELEASE_PACKAGE_PREPARED",
        "package_version": PACKAGE_VERSION,
        "aggregate_build_id": AGGREGATE_BUILD_ID,
        "parent_permit_build_id": parent["scope"]["build_id"],
        "source_parquet_sha256": actual_sha,
        "aggregate_cells": public["aggregate_rows"],
        "minimum_cell_count": public["minimum_cell_count"],
        "source_rows_scanned": aggregate_provenance["scope"]["rows_scanned"],
        "source_rows_represented_by_release": aggregate_provenance["scope"]["released_source_rows"],
        "source_rows_suppressed": aggregate_provenance["scope"]["suppressed_source_rows"],
        "source_scale": {
            "raw_current_csv_bytes": observed["totals"]["bytes"],
            "canonical_permit_parquet_bytes": parent["scope"]["output_bytes_total"],
            "wgs84_sidecar_parquet_bytes": geospatial["scope"]["output_bytes_total"],
        },
        "serializations": ["CSV", "PARQUET"],
        "row_level_values_included": False,
        "precise_coordinates_included": False,
        "kaggle_license_metadata": public["kaggle_license_metadata"],
        "owner_configured": owner is not None,
        "dataset_slug": DATASET_SLUG,
        "release_scope_provenance": "provenance/v1_release_scope.json",
        "aggregate_provenance": "provenance/public_permit_aggregate.json",
        "files": file_records,
        "manifest_self_hash_included": False,
        "dataset_metadata_control_file": METADATA_FILENAME if owner is not None else None,
        "dataset_metadata_control_file_in_payload_inventory": False,
        "deterministic_csv_contract": {
            "source": PUBLIC_PARQUET_FILENAME,
            "encoding": "UTF-8",
            "line_ending": "LF",
            "row_order": "preserve verified Parquet row order",
            "column_order": PUBLIC_COLUMNS,
            "null_representation": "empty field",
        },
    }
    if owner is not None:
        normalized_owner = _validate_owner(owner)
        metadata = _metadata(normalized_owner)
        (output / METADATA_FILENAME).write_text(
            json.dumps(metadata, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        manifest["dataset_id"] = metadata["id"]

    manifest_path = output / MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    ascii_paths = [readme_path, sources_path, dictionary_path, schema_path, source_summary_path, csv_destination, manifest_path]
    if owner is not None:
        ascii_paths.append(output / METADATA_FILENAME)
    _assert_ascii_stage(ascii_paths)

    expected_names = {
        PUBLIC_PARQUET_FILENAME,
        PUBLIC_CSV_FILENAME,
        SOURCE_SUMMARY_FILENAME,
        SCHEMA_FILENAME,
        DATA_DICTIONARY_FILENAME,
        README_FILENAME,
        SOURCES_FILENAME,
        MANIFEST_FILENAME,
    }
    if owner is not None:
        expected_names.add(METADATA_FILENAME)
    actual_names = {path.name for path in output.iterdir()}
    if actual_names != expected_names:
        raise KaggleReleaseError(
            f"Kaggle staging allowlist mismatch: expected={sorted(expected_names)} actual={sorted(actual_names)}"
        )

    return {
        "status": "PASS",
        "package_version": PACKAGE_VERSION,
        "output_dir": str(output),
        "parquet": _file_record(parquet_destination),
        "csv": _file_record(csv_destination),
        "source_summary": _file_record(source_summary_path),
        "aggregate_rows": aggregate_stats["rows"],
        "represented_source_rows": aggregate_stats["represented_source_rows"],
        "owner_configured": owner is not None,
        "dataset_id": manifest.get("dataset_id"),
        "row_level_values_emitted": False,
        "precise_coordinates_emitted": False,
    }
