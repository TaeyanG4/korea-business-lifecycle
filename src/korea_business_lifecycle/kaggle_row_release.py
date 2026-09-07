from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.compute as pc
import pyarrow.parquet as pq

from .canonical_compatibility import V1_SOURCE_ORDER
from .canonical_materialization import (
    COMPRESSION,
    COMPRESSION_LEVEL,
    DATA_PAGE_VERSION,
    PARQUET_VERSION,
    ROWS_PER_BATCH,
    ROWS_PER_ROW_GROUP,
    _sha256_file,
    permit_arrow_schema,
)
from .canonical_materialization_verify import expected_permit_build_id, verify_permit_parent_build
from .canonical_schema import load_permit_parent_schema
from .provenance import load_permit_parent_full_dry_run, load_v1_release_scope
from .storage import is_within, resolve_data_root


EXPECTED_ROWS = 3_010_802
EXPECTED_COLUMNS = 26
DATASET_SLUG = "korea-food-service-permits"
PUBLIC_PARQUET_FILENAME = "korea_food_service_permits.parquet"
PUBLIC_CSV_FILENAME = "korea_food_service_permits.csv"
SOURCE_SUMMARY_FILENAME = "source_summary.csv"
SCHEMA_FILENAME = "schema.json"
DATA_DICTIONARY_FILENAME = "DATA_DICTIONARY.md"
README_FILENAME = "README.md"
SOURCES_FILENAME = "SOURCES.md"
MANIFEST_FILENAME = "release-manifest.json"
METADATA_FILENAME = "dataset-metadata.json"
PACKAGE_VERSION = 1
APPROVED_DATASET_ID = "taeyangg4/korea-food-service-permits"


class KaggleRowReleaseError(RuntimeError):
    """Raised when the approved canonical row-level Kaggle package cannot be prepared safely."""


def _validated_owner(owner: str) -> str:
    value = owner.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", value):
        raise KaggleRowReleaseError("Kaggle owner must be a username/organization slug")
    dataset_id = f"{value}/{DATASET_SLUG}"
    if dataset_id != APPROVED_DATASET_ID:
        raise KaggleRowReleaseError(f"row-level publication is approved only for {APPROVED_DATASET_ID}")
    return value


def _sha256(path: Path) -> str:
    return _sha256_file(path)


def _file_record(path: Path) -> dict[str, Any]:
    return {"name": path.name, "bytes": path.stat().st_size, "sha256": _sha256(path)}


def _public_arrow_schema() -> pa.Schema:
    parent = permit_arrow_schema()
    metadata = dict(parent.metadata or {})
    metadata[b"kbl.publication_status"] = b"APPROVED_CANONICAL_ROW_LEVEL_RELEASE"
    metadata[b"kbl.publication_approval_basis"] = b"PROJECT_OWNER_CONFIRMED_PREEXISTING_APPROVAL_2026-09-08"
    metadata[b"kbl.parent_build_id"] = expected_permit_build_id(load_permit_parent_full_dry_run()).encode("ascii")
    return parent.with_metadata(metadata)


def _csv_arrow_schema(public_schema: pa.Schema) -> pa.Schema:
    fields = []
    for field in public_schema:
        if field.name == "source_retrieved_at_utc":
            fields.append(pa.field(field.name, pa.timestamp("us"), nullable=field.nullable))
        else:
            fields.append(field)
    return pa.schema(fields)


def _csv_table(table: pa.Table, csv_schema: pa.Schema) -> pa.Table:
    index = table.schema.get_field_index("source_retrieved_at_utc")
    if index < 0:
        raise KaggleRowReleaseError("source_retrieved_at_utc column is missing")
    utc_naive = pc.cast(table.column(index), pa.timestamp("us"))
    result = table.replace_schema_metadata(None).set_column(index, csv_schema.field(index), utc_naive)
    if not result.schema.equals(csv_schema, check_metadata=True):
        raise KaggleRowReleaseError("CSV serialization schema mismatch")
    return result


def _column_metadata() -> list[dict[str, str]]:
    descriptions = {
        "source_key": "Dataset category key: general_restaurants, rest_cafes, or bakeries.",
        "source_row_number": (
            "1-based row number within the retrieved source CSV. Lineage aid only; not a stable business identifier."
        ),
        "source_artifact_sha256": "SHA-256 of the exact retrieved source artifact used to create this record.",
        "source_retrieved_at_utc": "UTC timestamp when the source artifact was retrieved for this snapshot.",
        "authority_code": (
            "Local-government authority code from the source field 개방자치단체코드. Stored as text to preserve leading zeroes."
        ),
        "management_number": (
            "Source management number (관리번호). Useful as a bounded continuity candidate, but not asserted as an official primary key."
        ),
        "permit_date": (
            "Source permit date (인허가일자). This is an administrative permit date, not necessarily the physical opening date."
        ),
        "permit_date_quality": "Parse-quality flag for permit_date: VALID, MISSING, or INVALID.",
        "source_status_code": (
            "Raw business-status code (영업상태코드) from the source. No project-level active/closed mapping is imposed."
        ),
        "source_status_name": "Raw business-status name (영업상태명) from the source.",
        "source_detail_status_code": "Raw detailed business-status code (상세영업상태코드) from the source.",
        "source_detail_status_name": "Raw detailed business-status name (상세영업상태명) from the source.",
        "closure_date": (
            "Source closure date (폐업일자), when present. It is not treated as proof of an irreversible terminal event."
        ),
        "closure_date_quality": "Parse-quality flag for closure_date: VALID, MISSING, or INVALID.",
        "business_name": "Business or establishment name (사업장명) reported in the current source snapshot.",
        "business_type_name": "Business-type label (업태구분명) reported by the source.",
        "hygiene_business_type_name": "Hygiene business-type label (위생업태명) reported by the source.",
        "lot_postal_code": "Postal code associated with the lot-address field (소재지우편번호), stored as text.",
        "road_postal_code": "Postal code associated with the road-name address (도로명우편번호), stored as text.",
        "lot_address": "Lot-based address (지번주소) reported in the source snapshot.",
        "road_address": "Road-name address (도로명주소) reported in the source snapshot.",
        "source_coordinate_x": (
            "Source X coordinate (좌표정보(X)) in EPSG:5174; interpreted as easting for this verified snapshot."
        ),
        "source_coordinate_y": (
            "Source Y coordinate (좌표정보(Y)) in EPSG:5174; interpreted as northing for this verified snapshot."
        ),
        "source_data_update_type": "Raw source data-update classification (데이터갱신구분).",
        "source_data_updated_at_raw": (
            "Raw source data-update timestamp text (데이터갱신시점). Kept as source text because timezone semantics are not normalized."
        ),
        "source_last_modified_at_raw": (
            "Raw source last-modified timestamp text (최종수정시점). Kept as source text because timezone semantics are not normalized."
        ),
    }
    kaggle_types = {
        "source_row_number": "integer",
        "source_retrieved_at_utc": "datetime",
        "permit_date": "datetime",
        "closure_date": "datetime",
        "source_coordinate_x": "numeric",
        "source_coordinate_y": "numeric",
    }
    schema = load_permit_parent_schema()
    return [
        {
            "name": item["name"],
            "description": descriptions[item["name"]],
            "type": kaggle_types.get(item["name"], "string"),
        }
        for item in schema["columns"]
    ]


def _source_summary_fields() -> list[dict[str, str]]:
    return [
        {"name": "source_key", "description": "Dataset category key.", "type": "string"},
        {
            "name": "rows",
            "description": "Number of canonical records contributed by this source category.",
            "type": "integer",
        },
        {
            "name": "parent_parquet_bytes",
            "description": "Byte size of the verified per-source canonical parent Parquet artifact.",
            "type": "integer",
        },
        {
            "name": "parent_parquet_sha256",
            "description": "SHA-256 of the verified per-source canonical parent Parquet artifact.",
            "type": "string",
        },
    ]


def _metadata(owner: str) -> dict[str, Any]:
    main_fields = _column_metadata()
    return {
        "title": "South Korea Food-Service Permits - Snapshot",
        "subtitle": "3,010,802 restaurant, cafe and bakery permit records nationwide",
        "description": (
            "## What this dataset is\n\n"
            "A nationwide **current snapshot** of South Korean local-government food-service permits from Ministry of "
            "the Interior and Safety / LOCALDATA sources. It contains **3,010,802 records x 26 columns** across three "
            "categories: general restaurants, rest cafes, and bakeries. **This is not a historical time series or a "
            "lossless lifecycle event log.**\n\n"
            "## Coverage\n\n"
            "- General restaurants: **2,295,369** records\n"
            "- Rest cafes: **645,952** records\n"
            "- Bakeries: **69,481** records\n"
            "- Nationwide current snapshot: **3,010,802** records\n\n"
            "## Main files\n\n"
            "- `korea_food_service_permits.csv` - 1.40 GB UTF-8 CSV for broad compatibility\n"
            "- `korea_food_service_permits.parquet` - 165 MB typed ZSTD Parquet for fast analytics\n"
            "- Both files contain the **same 3,010,802 rows and the same 26 columns**\n"
            "- `DATA_DICTIONARY.md`, `schema.json`, `SOURCES.md`, and `release-manifest.json` document every field and "
            "the release lineage\n\n"
            "## Good starting points\n\n"
            "Regional restaurant-market mapping, permit-status analysis, business-type profiling, address/geospatial "
            "preprocessing, public-sector data engineering, and data-quality research.\n\n"
            "Public Quickstart / EDA notebook: "
            "https://www.kaggle.com/code/taeyangg4/korea-food-service-permits-3m-row-quickstart\n\n"
            "## Important interpretation limits\n\n"
            "- `management_number` is a bounded continuity candidate, **not an asserted official primary key**.\n"
            "- `permit_date` is an administrative permit date, **not necessarily the physical opening date**.\n"
            "- `closure_date` is contextual and **not treated as an irreversible terminal event**.\n"
            "- Source status `03` is reversible in observed evidence; status `05` remains unresolved.\n"
            "- `source_coordinate_x` / `source_coordinate_y` use **EPSG:5174** for this verified snapshot.\n"
            "- The separately derived WGS84 sidecar and partial history are not included.\n\n"
            "## Provenance\n\n"
            "Official source identifiers and links are listed in `SOURCES.md`. The project repository is "
            "https://github.com/TaeyanG4/korea-business-lifecycle.\n\n"
            "## License / reuse\n\n"
            "Kaggle license metadata is set to `Other` so this project does not claim to relicense upstream public "
            "records. The three official Public Data Portal source pages currently display `이용허락범위 제한 없음` "
            "(no restriction on the permitted-use scope). Attribution and source links are preserved in `SOURCES.md`."
        ),
        "id": f"{owner}/{DATASET_SLUG}",
        "licenses": [{"name": "other"}],
        "keywords": ["business", "restaurants", "food", "government", "geospatial analysis"],
        "expectedUpdateFrequency": "monthly",
        "userSpecifiedSources": (
            "Ministry of the Interior and Safety (MOIS), Republic of Korea, via Public Data Portal / LOCALDATA: "
            "[15154916 general restaurants](https://www.data.go.kr/data/15154916/openapi.do), "
            "[15154921 rest cafes](https://www.data.go.kr/data/15154921/openapi.do), and "
            "[15155252 bakeries](https://www.data.go.kr/data/15155252/openapi.do). "
            "The official source pages report 이용허락범위 제한 없음. See `SOURCES.md` for attribution details."
        ),
        "resources": [
            {
                "path": PUBLIC_CSV_FILENAME,
                "description": (
                    "Primary compatibility file: UTF-8 CSV containing all 3,010,802 current-snapshot permit rows "
                    "and all 26 canonical columns."
                ),
                "schema": {"fields": main_fields},
            },
            {
                "path": PUBLIC_PARQUET_FILENAME,
                "description": (
                    "Primary analytics file: typed ZSTD Parquet containing the same 3,010,802 rows and 26 columns "
                    "as the CSV, at much smaller size."
                ),
                "schema": {"fields": main_fields},
            },
            {
                "path": SOURCE_SUMMARY_FILENAME,
                "description": (
                    "Three-row source inventory with per-category record counts and verified parent-artifact sizes/hashes."
                ),
                "schema": {"fields": _source_summary_fields()},
            },
            {
                "path": DATA_DICTIONARY_FILENAME,
                "description": "Human-readable 26-column data dictionary and interpretation caveats.",
            },
            {
                "path": README_FILENAME,
                "description": "Quick overview of dataset shape, files, scope, and semantic limitations.",
            },
            {
                "path": SOURCES_FILENAME,
                "description": "Official MOIS/Public Data Portal source identifiers, links, attribution, and source-use notes.",
            },
            {
                "path": SCHEMA_FILENAME,
                "description": "Machine-readable release schema, row grain, geospatial metadata, and semantic limits.",
            },
            {
                "path": MANIFEST_FILENAME,
                "description": "Release manifest with row counts, serialization guarantees, file hashes, sizes, and build lineage.",
            },
        ],
    }


def _write_docs(output: Path, parent_build_id: str, rows_by_source: dict[str, int]) -> list[Path]:
    schema = load_permit_parent_schema()
    release_schema = {
        "schema_name": "public_canonical_permit_release",
        "schema_version": 1,
        "package_version": PACKAGE_VERSION,
        "grain": "PERMIT",
        "parent_build_id": parent_build_id,
        "rows": EXPECTED_ROWS,
        "columns": schema["columns"],
        "semantic_limits": {
            "management_number_is_official_primary_key": False,
            "permit_date_is_physical_open_date": False,
            "closure_date_is_irreversible_terminal_event": False,
            "status_code_03_irreversible": False,
            "status_code_05_semantics_resolved": False,
            "canonical_status_mapping_enabled": False,
        },
        "geospatial": {
            "source_coordinate_crs": "EPSG:5174",
            "wgs84_coordinates_included": False,
        },
    }
    schema_path = output / SCHEMA_FILENAME
    schema_path.write_text(json.dumps(release_schema, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    dictionary_lines = [
        "# Data Dictionary",
        "",
        "This release contains the 26-column canonical PERMIT schema. One row is one source permit record in the selected current snapshot.",
        "",
        "| Column | Type | Nullable | Description |",
        "| --- | --- | --- | --- |",
    ]
    descriptions = {item["name"]: item["description"] for item in _column_metadata()}
    for item in schema["columns"]:
        dictionary_lines.append(
            f"| `{item['name']}` | `{item['logical_type']}` | {'yes' if item['nullable'] else 'no'} | {descriptions[item['name']]} |"
        )
    dictionary_lines.extend(
        [
            "",
            "Interpretation limits: management_number is not claimed as an official primary key; permit_date is not physical opening date; closure_date is not necessarily a permanent terminal event; status 03 is not irreversible; status 05 remains unresolved.",
            "",
            "Coordinates source_coordinate_x/source_coordinate_y use the source CRS EPSG:5174. WGS84 coordinates are not included in this release.",
            "",
        ]
    )
    dictionary_path = output / DATA_DICTIONARY_FILENAME
    dictionary_path.write_text("\n".join(dictionary_lines), encoding="utf-8", newline="\n")

    readme = f"""# South Korea Food-Service Permits - Snapshot

This is the row-level nationwide current-snapshot release for three Korean food-service permit categories.

## Shape

- Rows: {EXPECTED_ROWS:,}
- Columns: {EXPECTED_COLUMNS}
- General restaurants: {rows_by_source['general_restaurants']:,}
- Rest cafes: {rows_by_source['rest_cafes']:,}
- Bakeries: {rows_by_source['bakeries']:,}

## Main files

- `{PUBLIC_CSV_FILENAME}`: UTF-8 CSV for direct use in common tools.
- `{PUBLIC_PARQUET_FILENAME}`: typed ZSTD-compressed Parquet for analytical engines.
- `{SOURCE_SUMMARY_FILENAME}`: source-level row counts and verified parent hashes.
- `{SCHEMA_FILENAME}` and `{DATA_DICTIONARY_FILENAME}`: exact 26-column contract.
- `{MANIFEST_FILENAME}`: package hashes, sizes, row counts, and lineage.

CSV and Parquet contain the same {EXPECTED_ROWS:,} records and the same 26 columns.

## Scope and interpretation

The source is a current snapshot, not a lossless lifecycle event log. `management_number` is retained but is only a bounded continuity candidate, not an asserted official primary key. `permit_date` is not claimed to be physical opening date. `closure_date` is contextual and is not claimed to be permanent terminal closure. Status code 03 is not irreversible and status code 05 remains unresolved.

The canonical source coordinates are retained in EPSG:5174. The separately derived WGS84 sidecar is not included here.

Repository: https://github.com/TaeyanG4/korea-business-lifecycle
"""
    readme_path = output / README_FILENAME
    readme_path.write_text(readme, encoding="utf-8", newline="\n")

    sources = """# Official sources and terms

Provider: Ministry of the Interior and Safety (MOIS), Republic of Korea.

- General restaurants - data.go.kr ID 15154916: https://www.data.go.kr/data/15154916/openapi.do
- Rest cafes - data.go.kr ID 15154921: https://www.data.go.kr/data/15154921/openapi.do
- Bakeries - data.go.kr ID 15155252: https://www.data.go.kr/data/15155252/openapi.do
- Public Data Portal policy: https://www.data.go.kr/ugs/selectPortalPolicyView.do

Kaggle license metadata uses `other`; official source pages and portal terms remain the controlling source-use references. This project does not claim to relicense upstream government records.
"""
    sources_path = output / SOURCES_FILENAME
    sources_path.write_text(sources, encoding="utf-8", newline="\n")
    return [schema_path, dictionary_path, readme_path, sources_path]


def prepare_kaggle_row_release(*, owner: str, data_root: str | Path | None = None) -> dict[str, Any]:
    owner = _validated_owner(owner)
    root = resolve_data_root(data_root)
    release_scope = load_v1_release_scope()
    public = release_scope["public_release"]
    if public.get("row_level_permit_publication_approved") is not True:
        raise KaggleRowReleaseError("current release scope does not approve canonical row-level publication")
    if public.get("row_level_rows") != EXPECTED_ROWS or public.get("row_level_columns") != EXPECTED_COLUMNS:
        raise KaggleRowReleaseError("approved row-level release shape changed")
    if public.get("row_level_kaggle_dataset_id") != APPROVED_DATASET_ID:
        raise KaggleRowReleaseError("approved row-level Kaggle dataset id changed")
    if public.get("canonical_source_epsg5174_coordinates_publication_approved") is not True:
        raise KaggleRowReleaseError("canonical EPSG:5174 source coordinates are not approved for this release")

    evidence = load_permit_parent_full_dry_run()
    parent_build_id = expected_permit_build_id(evidence)
    verified = verify_permit_parent_build(data_root=root, evidence=evidence)
    if verified.get("status") != "PASS" or verified.get("rows_verified_total") != EXPECTED_ROWS:
        raise KaggleRowReleaseError("verified canonical parent is not in the expected PASS state")
    rows_by_source = {item["source_key"]: int(item["rows"]) for item in verified["results"]}
    if sum(rows_by_source.values()) != EXPECTED_ROWS:
        raise KaggleRowReleaseError("source row totals do not reconcile")

    output = root / "kaggle_release" / "row-level-v1" / parent_build_id / f"package-v{PACKAGE_VERSION}"
    if not is_within(output, root) or output.is_symlink():
        raise KaggleRowReleaseError("row-level Kaggle staging escaped KBL_DATA_ROOT or is a symlink")
    if output.exists():
        allowed = {
            PUBLIC_PARQUET_FILENAME, PUBLIC_CSV_FILENAME, SOURCE_SUMMARY_FILENAME, SCHEMA_FILENAME,
            DATA_DICTIONARY_FILENAME, README_FILENAME, SOURCES_FILENAME, MANIFEST_FILENAME, METADATA_FILENAME,
        }
        unknown = [p.name for p in output.iterdir() if p.name not in allowed]
        if unknown:
            raise KaggleRowReleaseError("unexpected files already exist in row-level staging: " + ", ".join(sorted(unknown)))
        for path in output.iterdir():
            if not path.is_file() or path.is_symlink():
                raise KaggleRowReleaseError(f"managed row-level staging path is not a regular file: {path.name}")
            path.unlink()
    else:
        output.mkdir(parents=True)

    parquet_path = output / PUBLIC_PARQUET_FILENAME
    csv_path = output / PUBLIC_CSV_FILENAME
    public_schema = _public_arrow_schema()
    csv_schema = _csv_arrow_schema(public_schema)
    parquet_writer = pq.ParquetWriter(
        parquet_path,
        public_schema,
        version=PARQUET_VERSION,
        compression=COMPRESSION,
        compression_level=COMPRESSION_LEVEL,
        use_dictionary=True,
        write_statistics=True,
        data_page_version=DATA_PAGE_VERSION,
    )
    csv_writer = pacsv.CSVWriter(
        csv_path,
        csv_schema,
        write_options=pacsv.WriteOptions(include_header=True, quoting_style="needed"),
    )
    rows_written = 0
    try:
        for source_key in V1_SOURCE_ORDER:
            parent_path = root / "canonical" / "permit" / "v1" / parent_build_id / f"{source_key}.parquet"
            parent_file = pq.ParquetFile(parent_path)
            source_rows = 0
            try:
                for batch in parent_file.iter_batches(batch_size=ROWS_PER_BATCH):
                    table = pa.Table.from_batches([batch]).replace_schema_metadata(public_schema.metadata)
                    if table.schema.names != public_schema.names:
                        raise KaggleRowReleaseError(f"{source_key}: canonical column order changed")
                    parquet_writer.write_table(table, row_group_size=ROWS_PER_ROW_GROUP)
                    csv_writer.write_table(_csv_table(table, csv_schema))
                    rows_written += table.num_rows
                    source_rows += table.num_rows
            finally:
                close = getattr(parent_file, "close", None)
                if callable(close):
                    close()
            if source_rows != rows_by_source[source_key]:
                raise KaggleRowReleaseError(f"{source_key}: emitted row count changed")
    finally:
        parquet_writer.close()
        csv_writer.close()

    if rows_written != EXPECTED_ROWS:
        raise KaggleRowReleaseError("combined CSV/Parquet row count did not preserve all canonical rows")
    parquet_file = pq.ParquetFile(parquet_path)
    try:
        if parquet_file.metadata.num_rows != EXPECTED_ROWS:
            raise KaggleRowReleaseError("combined Parquet row count mismatch")
        parquet_row_groups = parquet_file.metadata.num_row_groups
    finally:
        close = getattr(parquet_file, "close", None)
        if callable(close):
            close()
    if not pq.read_schema(parquet_path).equals(public_schema, check_metadata=True):
        raise KaggleRowReleaseError("combined Parquet schema mismatch")

    source_summary = output / SOURCE_SUMMARY_FILENAME
    source_summary.write_text(
        "source_key,rows,parent_parquet_bytes,parent_parquet_sha256\n" +
        "\n".join(
            f"{item['source_key']},{int(item['rows'])},{int(item['output_bytes'])},{item['output_sha256']}"
            for item in verified["results"]
        ) + "\n",
        encoding="ascii",
        newline="\n",
    )
    docs = _write_docs(output, parent_build_id, rows_by_source)
    metadata_path = output / METADATA_FILENAME
    metadata_path.write_text(json.dumps(_metadata(owner), ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    payload_paths = [parquet_path, csv_path, source_summary, *docs]
    records = [_file_record(path) for path in payload_paths]
    manifest = {
        "decision": "CANONICAL_ROW_LEVEL_KAGGLE_PACKAGE_PREPARED",
        "package_version": PACKAGE_VERSION,
        "dataset_id": f"{owner}/{DATASET_SLUG}",
        "parent_permit_build_id": parent_build_id,
        "rows": EXPECTED_ROWS,
        "columns": EXPECTED_COLUMNS,
        "rows_by_source": rows_by_source,
        "serializations": ["CSV", "PARQUET"],
        "csv_and_parquet_same_rows_and_columns": True,
        "csv_source_retrieved_at_utc_serialization": "UTC timestamp rendered without timezone suffix; values remain UTC",
        "wgs84_coordinates_included": False,
        "history_included": False,
        "publication_approval_basis": public["row_level_publication_approval_basis"],
        "parquet_row_groups": parquet_row_groups,
        "files": records,
        "manifest_self_hash_included": False,
        "metadata_control_file_in_payload_inventory": False,
    }
    manifest_path = output / MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    actual = {p.name for p in output.iterdir() if p.is_file()}
    expected = {PUBLIC_PARQUET_FILENAME, PUBLIC_CSV_FILENAME, SOURCE_SUMMARY_FILENAME, SCHEMA_FILENAME,
                DATA_DICTIONARY_FILENAME, README_FILENAME, SOURCES_FILENAME, MANIFEST_FILENAME, METADATA_FILENAME}
    if actual != expected:
        raise KaggleRowReleaseError(f"row-level Kaggle package file allowlist mismatch: {sorted(actual)}")
    return {
        "status": "PASS",
        "output_dir": str(output),
        "dataset_id": f"{owner}/{DATASET_SLUG}",
        "rows": EXPECTED_ROWS,
        "columns": EXPECTED_COLUMNS,
        "csv": _file_record(csv_path),
        "parquet": _file_record(parquet_path),
        "manifest": _file_record(manifest_path),
    }
