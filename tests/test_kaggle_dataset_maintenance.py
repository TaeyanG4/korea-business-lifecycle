from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from korea_business_lifecycle.kaggle_dataset_maintenance import (
    GET_DATABUNDLE_EXTERNAL,
    GET_DATABUNDLE_EXTERNAL_COLUMNS,
    GET_DATABUNDLE_EXTERNAL_COLUMNS_BY_PATH,
    GET_DATASET_BASICS,
    GET_DATASET_USABILITY,
    KAGGLE_ORIGIN,
    UPDATE_DATABUNDLE_METADATA_EXTERNAL,
    KaggleDatasetMaintenanceError,
    apply_metadata_update_plan,
    build_metadata_update_plan,
    get_usability_rating,
    load_live_context,
    summarize_plan,
)
from korea_business_lifecycle.kaggle_row_release import _metadata


ROOT_PATH = "bundle/versions/current"


@dataclass
class FakeResponse:
    payload: dict[str, Any]
    status_code: int = 200
    text: str = ""

    def json(self) -> dict[str, Any]:
        return self.payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, *, wrong_rows: bool = False) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.wrong_rows = wrong_rows
        resources = _metadata("taeyangg4")["resources"]
        self.resources = {resource["path"]: resource for resource in resources}

    def post(self, url: str, *, json: dict[str, Any], timeout: float) -> FakeResponse:
        del timeout
        self.calls.append((url, json))
        endpoint = url.removeprefix(KAGGLE_ORIGIN)
        if endpoint == GET_DATASET_BASICS:
            return FakeResponse(
                {
                    "datasetId": 11936072,
                    "datasetVersionId": 19491720,
                    "datasetVersionNumber": 2,
                    "slug": "korea-food-service-permits",
                    "data": {"versionId": 20603554},
                }
            )
        if endpoint == GET_DATABUNDLE_EXTERNAL:
            files = []
            for name, resource in self.resources.items():
                item: dict[str, Any] = {
                    "name": name,
                    "path": f"{ROOT_PATH}/files/{name}",
                }
                fields = resource.get("schema", {}).get("fields", [])
                if fields:
                    rows = 3 if name == "source_summary.csv" else 3_010_802
                    if self.wrong_rows and name == "korea_food_service_permits.csv":
                        rows -= 1
                    item["tableInfo"] = {
                        "totalRows": rows,
                        "tableColumns": {"totalChildren": len(fields)},
                    }
                files.append(item)
            return FakeResponse(
                {
                    "dataSource": {
                        "sourceId": 11936072,
                        "slug": "korea-food-service-permits",
                        "versionNumber": 2,
                        "path": ROOT_PATH,
                        "databundleVersion": {
                            "legacyEntityId": 20603554,
                            "datasetVersionInfo": {"datasetVersionId": 19491720},
                            "filesetInfo": {"files": {"children": files}},
                        },
                    }
                }
            )
        if endpoint == GET_DATABUNDLE_EXTERNAL_COLUMNS:
            file_name = json["firestorePath"].rsplit("/", 1)[-1]
            fields = self.resources[file_name]["schema"]["fields"]
            return FakeResponse(
                {
                    "columns": [
                        {
                            "name": field["name"],
                            "firestorePath": f"{json['firestorePath']}/columns/{index}",
                            "order": index,
                        }
                        for index, field in enumerate(fields)
                    ]
                }
            )
        if endpoint == GET_DATABUNDLE_EXTERNAL_COLUMNS_BY_PATH:
            return FakeResponse(
                {
                    "columns": [
                        {
                            "path": path,
                            "tableColumnInfo": (
                                {"type": "NUMERIC"} if path.endswith("/1") else {}
                            ),
                        }
                        for path in json["firestorePaths"]
                    ]
                }
            )
        if endpoint == GET_DATASET_USABILITY:
            return FakeResponse(
                {"rating": {"score": 0.8235294, "columnDescriptionScore": 0}}
            )
        if endpoint == UPDATE_DATABUNDLE_METADATA_EXTERNAL:
            return FakeResponse({"usabilityRating": {"score": 1.0}})
        raise AssertionError(endpoint)


def test_build_plan_targets_all_files_and_all_live_columns() -> None:
    session = FakeSession()
    context, updates = build_metadata_update_plan(session)
    summary = summarize_plan(context, updates)
    assert summary["dataset_id"] == "taeyangg4/korea-food-service-permits"
    assert summary["version_number"] == 2
    assert summary["files"] == 8
    assert summary["columns"] == 56
    assert set(summary["file_names"]) == set(session.resources)
    csv_update = next(
        update
        for update in updates
        if update["firestorePath"].endswith("korea_food_service_permits.csv")
    )
    assert len(csv_update["columns"]) == 26
    assert all(column["description"] for column in csv_update["columns"])
    assert all(column["type"] in {"STRING", "NUMERIC"} for column in csv_update["columns"])
    assert all(
        column["extendedType"] == "EXTENDED_DATA_TYPE_UNSPECIFIED"
        for column in csv_update["columns"]
    )
    basics_calls = [
        payload
        for url, payload in session.calls
        if url == f"{KAGGLE_ORIGIN}{GET_DATASET_BASICS}"
    ]
    assert basics_calls[0]["datasetVersionNumber"] == 2


def test_build_plan_fails_closed_if_live_main_shape_changes() -> None:
    with pytest.raises(KaggleDatasetMaintenanceError, match="live table shape changed"):
        build_metadata_update_plan(FakeSession(wrong_rows=True))


def test_explicit_version_is_sent_to_dataset_basics() -> None:
    session = FakeSession()
    context = load_live_context(session, dataset_version_number=2)
    assert context.version_number == 2
    basics_calls = [
        payload
        for url, payload in session.calls
        if url == f"{KAGGLE_ORIGIN}{GET_DATASET_BASICS}"
    ]
    assert basics_calls == [
        {
            "ownerSlug": "taeyangg4",
            "datasetSlug": "korea-food-service-permits",
            "datasetVersionNumber": 2,
        }
    ]


def test_apply_and_usability_use_expected_internal_endpoints() -> None:
    session = FakeSession()
    _, updates = build_metadata_update_plan(session)
    results = apply_metadata_update_plan(session, updates)
    rating = get_usability_rating(session)
    assert len(results) == 8
    assert rating["score"] == pytest.approx(0.8235294)
    update_calls = [
        payload
        for url, payload in session.calls
        if url == f"{KAGGLE_ORIGIN}{UPDATE_DATABUNDLE_METADATA_EXTERNAL}"
    ]
    assert len(update_calls) == 8
    assert all(
        call["verificationInfo"]
        == {"databundleVersionId": 20603554, "datasetId": 11936072}
        for call in update_calls
    )
