from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .kaggle_row_release import (
    APPROVED_DATASET_ID,
    DATASET_SLUG,
    EXPECTED_COLUMNS,
    EXPECTED_ROWS,
    _metadata,
)


KAGGLE_ORIGIN = "https://www.kaggle.com"
KAGGLE_OWNER = APPROVED_DATASET_ID.split("/", 1)[0]
KAGGLE_DATASET_NUMERIC_ID = 11_936_072
APPROVED_PUBLIC_VERSION_NUMBER = 2

GET_DATASET_BASICS = "/api/i/datasets.DatasetDetailService/GetDatasetBasics"
GET_DATABUNDLE_EXTERNAL = "/api/i/datasets.databundles.DatabundleService/GetDatabundleExternal"
GET_DATABUNDLE_EXTERNAL_CHILDREN = (
    "/api/i/datasets.databundles.DatabundleService/GetDatabundleExternalChildren"
)
GET_DATABUNDLE_EXTERNAL_COLUMNS = (
    "/api/i/datasets.databundles.DatabundleService/GetDatabundleExternalColumns"
)
GET_DATABUNDLE_EXTERNAL_COLUMNS_BY_PATH = (
    "/api/i/datasets.databundles.DatabundleService/GetDatabundleExternalColumnsByFirestorePath"
)
UPDATE_DATABUNDLE_METADATA_EXTERNAL = (
    "/api/i/datasets.databundles.DatabundleService/UpdateDatabundleMetadataExternal"
)
GET_DATASET_USABILITY = "/api/i/datasets.DatasetDetailService/GetDatasetUsabilityRating"


class KaggleDatasetMaintenanceError(RuntimeError):
    """Raised when live Kaggle metadata cannot be maintained safely."""


class _Response(Protocol):
    status_code: int
    text: str

    def json(self) -> Any: ...

    def raise_for_status(self) -> None: ...


class _Session(Protocol):
    def post(
        self,
        url: str,
        *,
        json: dict[str, Any],
        timeout: float,
    ) -> _Response: ...


@dataclass(frozen=True)
class LiveDatasetContext:
    dataset_id: int
    dataset_version_id: int
    databundle_version_id: int
    version_number: int
    root_firestore_path: str
    file_firestore_paths: dict[str, str]


def _post_json(
    session: _Session,
    endpoint: str,
    payload: dict[str, Any],
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    response = session.post(
        f"{KAGGLE_ORIGIN}{endpoint}",
        json=payload,
        timeout=timeout,
    )
    try:
        response.raise_for_status()
    except Exception as exc:
        body = getattr(response, "text", "") or ""
        compact = " ".join(body.split())[:500]
        detail = f": {compact}" if compact else ""
        raise KaggleDatasetMaintenanceError(
            f"Kaggle request failed for {endpoint} (HTTP {getattr(response, 'status_code', '?')}){detail}"
        ) from exc
    try:
        value = response.json()
    except Exception as exc:
        raise KaggleDatasetMaintenanceError(
            f"Kaggle returned a non-JSON response for {endpoint}"
        ) from exc
    if not isinstance(value, dict):
        raise KaggleDatasetMaintenanceError(
            f"Kaggle returned an unexpected response for {endpoint}"
        )
    if int(value.get("code", 0) or 0) >= 400:
        raise KaggleDatasetMaintenanceError(
            f"Kaggle rejected {endpoint}: {value.get('message', 'unknown error')}"
        )
    return value


def _verification_info(context: LiveDatasetContext) -> dict[str, int]:
    return {
        "databundleVersionId": context.databundle_version_id,
        "datasetId": context.dataset_id,
    }


def load_live_context(
    session: _Session,
    *,
    dataset_version_number: int | None = None,
) -> LiveDatasetContext:
    request: dict[str, Any] = {
        "ownerSlug": KAGGLE_OWNER,
        "datasetSlug": DATASET_SLUG,
    }
    if dataset_version_number is not None:
        if dataset_version_number <= 0:
            raise KaggleDatasetMaintenanceError("dataset version number must be positive")
        request["datasetVersionNumber"] = dataset_version_number
    basics = _post_json(
        session,
        GET_DATASET_BASICS,
        request,
    )
    if int(basics.get("datasetId", 0) or 0) != KAGGLE_DATASET_NUMERIC_ID:
        raise KaggleDatasetMaintenanceError("Kaggle dataset numeric id changed")
    if basics.get("slug") not in {None, "", DATASET_SLUG}:
        raise KaggleDatasetMaintenanceError("Kaggle dataset slug changed")

    data = basics.get("data")
    if not isinstance(data, dict):
        raise KaggleDatasetMaintenanceError("Kaggle dataset has no current databundle")
    databundle_version_id = int(data.get("versionId", 0) or 0)
    dataset_version_id = int(basics.get("datasetVersionId", 0) or 0)
    version_number = int(basics.get("datasetVersionNumber", 0) or 0)
    if databundle_version_id <= 0 or dataset_version_id <= 0 or version_number <= 0:
        raise KaggleDatasetMaintenanceError("Kaggle current version identifiers are incomplete")
    if dataset_version_number is not None and version_number != dataset_version_number:
        raise KaggleDatasetMaintenanceError(
            f"Kaggle returned version {version_number} while version {dataset_version_number} was requested"
        )

    provisional = LiveDatasetContext(
        dataset_id=KAGGLE_DATASET_NUMERIC_ID,
        dataset_version_id=dataset_version_id,
        databundle_version_id=databundle_version_id,
        version_number=version_number,
        root_firestore_path="",
        file_firestore_paths={},
    )
    external = _post_json(
        session,
        GET_DATABUNDLE_EXTERNAL,
        {"verificationInfo": _verification_info(provisional)},
    )
    data_source = external.get("dataSource")
    if not isinstance(data_source, dict):
        raise KaggleDatasetMaintenanceError("Kaggle Data Explorer returned no data source")
    if int(data_source.get("sourceId", 0) or 0) != KAGGLE_DATASET_NUMERIC_ID:
        raise KaggleDatasetMaintenanceError("Data Explorer dataset id changed")
    if data_source.get("slug") not in {None, "", DATASET_SLUG}:
        raise KaggleDatasetMaintenanceError("Data Explorer dataset slug changed")
    if int(data_source.get("versionNumber", 0) or 0) != version_number:
        raise KaggleDatasetMaintenanceError("Data Explorer version number disagrees with dataset basics")

    root_path = str(data_source.get("path") or "")
    version = data_source.get("databundleVersion")
    if not root_path or not isinstance(version, dict):
        raise KaggleDatasetMaintenanceError("Data Explorer current version tree is incomplete")
    if int(version.get("legacyEntityId", 0) or 0) != databundle_version_id:
        raise KaggleDatasetMaintenanceError("Data Explorer databundle version id changed")
    version_info = version.get("datasetVersionInfo")
    if not isinstance(version_info, dict) or int(version_info.get("datasetVersionId", 0) or 0) != dataset_version_id:
        raise KaggleDatasetMaintenanceError("Data Explorer dataset version id changed")

    fileset_info = version.get("filesetInfo")
    files_container = fileset_info.get("files") if isinstance(fileset_info, dict) else None
    files = files_container.get("children") if isinstance(files_container, dict) else None
    if not isinstance(files, list):
        raise KaggleDatasetMaintenanceError("Data Explorer file listing is unavailable")
    file_paths: dict[str, str] = {}
    table_shapes: dict[str, tuple[int, int]] = {}
    for item in files:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        firestore_path = str(item.get("path") or "")
        if not name or not firestore_path:
            raise KaggleDatasetMaintenanceError("Data Explorer returned a file without name/path")
        file_paths[name] = firestore_path
        table_info = item.get("tableInfo")
        if isinstance(table_info, dict):
            table_columns = table_info.get("tableColumns")
            total_columns = int(table_info.get("totalColumns", 0) or 0)
            if total_columns == 0 and isinstance(table_columns, dict):
                total_columns = int(table_columns.get("totalChildren", 0) or 0)
            table_shapes[name] = (
                int(table_info.get("totalRows", 0) or 0),
                total_columns,
            )

    resources = _metadata(KAGGLE_OWNER)["resources"]
    expected_files = {str(resource["path"]) for resource in resources}
    if set(file_paths) != expected_files:
        raise KaggleDatasetMaintenanceError(
            "live Kaggle file set changed: "
            f"expected {sorted(expected_files)}, got {sorted(file_paths)}"
        )
    for main_name in (
        "korea_food_service_permits.csv",
        "korea_food_service_permits.parquet",
    ):
        shape = table_shapes.get(main_name)
        if shape is None or shape[0] != EXPECTED_ROWS or shape[1] not in {0, EXPECTED_COLUMNS}:
            raise KaggleDatasetMaintenanceError(
                f"{main_name}: live table shape changed from {EXPECTED_ROWS} x {EXPECTED_COLUMNS}; "
                f"got {shape!r}"
            )
    source_summary_shape = table_shapes.get("source_summary.csv")
    if (
        source_summary_shape is None
        or source_summary_shape[0] != 3
        or source_summary_shape[1] not in {0, 4}
    ):
        raise KaggleDatasetMaintenanceError(
            f"source_summary.csv live table shape changed from 3 x 4; got {source_summary_shape!r}"
        )

    return LiveDatasetContext(
        dataset_id=KAGGLE_DATASET_NUMERIC_ID,
        dataset_version_id=dataset_version_id,
        databundle_version_id=databundle_version_id,
        version_number=version_number,
        root_firestore_path=root_path,
        file_firestore_paths=file_paths,
    )


def _column_updates(
    session: _Session,
    context: LiveDatasetContext,
    *,
    file_path: str,
    expected_fields: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    verification = _verification_info(context)
    base = _post_json(
        session,
        GET_DATABUNDLE_EXTERNAL_COLUMNS,
        {"verificationInfo": verification, "firestorePath": file_path},
    )
    columns = base.get("columns")
    if not isinstance(columns, list):
        raise KaggleDatasetMaintenanceError("Kaggle column listing is unavailable")
    ordered = sorted(
        (item for item in columns if isinstance(item, dict)),
        key=lambda item: int(item.get("order", 0) or 0),
    )
    live_names = [str(item.get("name") or "") for item in ordered]
    expected_names = [str(item["name"]) for item in expected_fields]
    if live_names != expected_names:
        raise KaggleDatasetMaintenanceError(
            f"column order changed for {file_path}: expected {expected_names}, got {live_names}"
        )
    paths = [str(item.get("firestorePath") or "") for item in ordered]
    if any(not path for path in paths) or len(set(paths)) != len(paths):
        raise KaggleDatasetMaintenanceError(f"invalid column Firestore paths for {file_path}")

    hydrated = _post_json(
        session,
        GET_DATABUNDLE_EXTERNAL_COLUMNS_BY_PATH,
        {"verificationInfo": verification, "firestorePaths": paths},
    )
    full_columns = hydrated.get("columns")
    if not isinstance(full_columns, list):
        raise KaggleDatasetMaintenanceError("Kaggle hydrated column metadata is unavailable")
    by_path = {
        str(item.get("path") or item.get("firestorePath") or ""): item
        for item in full_columns
        if isinstance(item, dict)
    }
    if set(by_path) != set(paths):
        raise KaggleDatasetMaintenanceError(f"hydrated column paths changed for {file_path}")

    description_by_name = {
        str(field["name"]): str(field["description"]) for field in expected_fields
    }
    result: list[dict[str, Any]] = []
    for item, path in zip(ordered, paths, strict=True):
        name = str(item["name"])
        full = by_path[path]
        info = full.get("tableColumnInfo")
        if not isinstance(info, dict):
            raise KaggleDatasetMaintenanceError(f"{name}: tableColumnInfo is missing")
        # Proto3 JSON omits zero-valued enums. Kaggle's generated UI client
        # restores those omitted defaults as STRING / UNSPECIFIED before it
        # submits UpdateDatabundleMetadataExternal, so mirror that behavior.
        harmonized_type = info.get("type", "STRING")
        extended_type = info.get("extendedType", "EXTENDED_DATA_TYPE_UNSPECIFIED")
        if not isinstance(harmonized_type, str) or not harmonized_type:
            raise KaggleDatasetMaintenanceError(f"{name}: harmonized type is invalid")
        if not isinstance(extended_type, str) or not extended_type:
            raise KaggleDatasetMaintenanceError(f"{name}: extended type is invalid")
        result.append(
            {
                "firestorePath": path,
                "description": description_by_name[name],
                "type": harmonized_type,
                "extendedType": extended_type,
            }
        )
    return result


def build_metadata_update_plan(
    session: _Session,
    context: LiveDatasetContext | None = None,
) -> tuple[LiveDatasetContext, list[dict[str, Any]]]:
    # Never rely on Kaggle's implicit "current version" selection here. During
    # the v2 maintenance investigation that route returned v1 even though v2
    # was the published version. Pin the repository-approved version unless an
    # already-validated context is supplied by the caller.
    context = context or load_live_context(
        session,
        dataset_version_number=APPROVED_PUBLIC_VERSION_NUMBER,
    )
    resources = _metadata(KAGGLE_OWNER)["resources"]
    updates: list[dict[str, Any]] = []
    verification = _verification_info(context)
    for resource in resources:
        name = str(resource["path"])
        file_path = context.file_firestore_paths[name]
        fields = resource.get("schema", {}).get("fields", [])
        columns = (
            _column_updates(
                session,
                context,
                file_path=file_path,
                expected_fields=fields,
            )
            if fields
            else []
        )
        updates.append(
            {
                "verificationInfo": verification,
                "firestorePath": file_path,
                "description": str(resource["description"]),
                "columns": columns,
            }
        )
    return context, updates


def get_live_metadata_coverage(
    session: _Session,
    context: LiveDatasetContext,
) -> dict[str, Any]:
    """Compare explicit-version Data Explorer descriptions with the approved metadata.

    The nested file tree returned by GetDatabundleExternal can omit file
    descriptions even when they are persisted. GetDatabundleExternalChildren
    at the version root returns the authoritative file-description view used
    here. Column descriptions are hydrated by their exact Firestore paths.
    """

    resources = {
        str(resource["path"]): resource
        for resource in _metadata(KAGGLE_OWNER)["resources"]
    }
    verification = _verification_info(context)
    root_children = _post_json(
        session,
        GET_DATABUNDLE_EXTERNAL_CHILDREN,
        {
            "verificationInfo": verification,
            "firestorePath": context.root_firestore_path,
            "offset": 0,
            "count": max(100, len(resources)),
            "depth": 1,
        },
    )
    live_files = root_children.get("files")
    if not isinstance(live_files, list):
        raise KaggleDatasetMaintenanceError("Kaggle root file metadata is unavailable")
    descriptions_by_file = {
        str(item.get("name") or ""): str(item.get("description") or "")
        for item in live_files
        if isinstance(item, dict) and item.get("name")
    }
    if set(descriptions_by_file) != set(resources):
        raise KaggleDatasetMaintenanceError(
            "Kaggle root file metadata set changed: "
            f"expected {sorted(resources)}, got {sorted(descriptions_by_file)}"
        )

    exact_files = sum(
        descriptions_by_file[name] == str(resource["description"])
        for name, resource in resources.items()
    )
    target_columns = 0
    exact_columns = 0
    per_table: dict[str, dict[str, int]] = {}
    for name, resource in resources.items():
        fields = resource.get("schema", {}).get("fields", [])
        if not fields:
            continue
        target_columns += len(fields)
        file_path = context.file_firestore_paths[name]
        base = _post_json(
            session,
            GET_DATABUNDLE_EXTERNAL_COLUMNS,
            {"verificationInfo": verification, "firestorePath": file_path},
        )
        columns = base.get("columns")
        if not isinstance(columns, list):
            raise KaggleDatasetMaintenanceError(f"{name}: Kaggle column listing is unavailable")
        ordered = sorted(
            (item for item in columns if isinstance(item, dict)),
            key=lambda item: int(item.get("order", 0) or 0),
        )
        live_names = [str(item.get("name") or "") for item in ordered]
        expected_names = [str(field["name"]) for field in fields]
        if live_names != expected_names:
            raise KaggleDatasetMaintenanceError(
                f"{name}: live column order changed: expected {expected_names}, got {live_names}"
            )
        paths = [str(item.get("firestorePath") or "") for item in ordered]
        if any(not path for path in paths) or len(set(paths)) != len(paths):
            raise KaggleDatasetMaintenanceError(f"{name}: invalid column Firestore paths")
        hydrated = _post_json(
            session,
            GET_DATABUNDLE_EXTERNAL_COLUMNS_BY_PATH,
            {"verificationInfo": verification, "firestorePaths": paths},
        )
        full_columns = hydrated.get("columns")
        if not isinstance(full_columns, list):
            raise KaggleDatasetMaintenanceError(f"{name}: hydrated column metadata is unavailable")
        by_path = {
            str(item.get("path") or item.get("firestorePath") or ""): item
            for item in full_columns
            if isinstance(item, dict)
        }
        if set(by_path) != set(paths):
            raise KaggleDatasetMaintenanceError(f"{name}: hydrated column paths changed")

        exact_for_table = 0
        for item, field, path in zip(ordered, fields, paths, strict=True):
            if str(item.get("name") or "") != str(field["name"]):
                raise KaggleDatasetMaintenanceError(f"{name}: column name/order mismatch")
            full = by_path[path]
            info = full.get("tableColumnInfo")
            nested_description = info.get("description") if isinstance(info, dict) else None
            live_description = str(full.get("description") or nested_description or "")
            if live_description == str(field["description"]):
                exact_for_table += 1
        exact_columns += exact_for_table
        per_table[name] = {
            "exact_column_descriptions": exact_for_table,
            "target_column_descriptions": len(fields),
        }

    return {
        "target_file_descriptions": len(resources),
        "exact_file_descriptions": exact_files,
        "target_column_descriptions": target_columns,
        "exact_column_descriptions": exact_columns,
        "all_file_descriptions_exact": exact_files == len(resources),
        "all_column_descriptions_exact": exact_columns == target_columns,
        "metadata_complete": exact_files == len(resources) and exact_columns == target_columns,
        "per_table": per_table,
    }


def get_usability_rating(session: _Session) -> dict[str, Any]:
    response = _post_json(
        session,
        GET_DATASET_USABILITY,
        {"datasetId": KAGGLE_DATASET_NUMERIC_ID},
    )
    rating = response.get("rating")
    if not isinstance(rating, dict):
        raise KaggleDatasetMaintenanceError("Kaggle usability rating is unavailable")
    return rating


def apply_metadata_update_plan(
    session: _Session,
    updates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _post_json(session, UPDATE_DATABUNDLE_METADATA_EXTERNAL, update)
        for update in updates
    ]


def summarize_plan(
    context: LiveDatasetContext,
    updates: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "dataset_id": APPROVED_DATASET_ID,
        "dataset_numeric_id": context.dataset_id,
        "dataset_version_id": context.dataset_version_id,
        "databundle_version_id": context.databundle_version_id,
        "version_number": context.version_number,
        "files": len(updates),
        "columns": sum(len(update["columns"]) for update in updates),
        "file_names": [
            update["firestorePath"].rsplit("/", 1)[-1] for update in updates
        ],
    }
