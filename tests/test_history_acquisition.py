from __future__ import annotations

import io
import json
from email.message import Message
from pathlib import Path
from urllib.request import Request

import pytest

from korea_business_lifecycle.history_acquisition import (
    HistoryAcquisitionError,
    acquire_history_snapshot,
)


class FakeResponse:
    def __init__(self, payload: dict, url: str) -> None:
        self._body = io.BytesIO(json.dumps(payload).encode("utf-8"))
        self._url = url
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = "application/json"

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)

    def getcode(self) -> int:
        return 200

    def geturl(self) -> str:
        return self._url

    def close(self) -> None:
        self._body.close()


def payload(page_no: int, total_count: int, ids: list[str]) -> dict:
    return {
        "response": {
            "header": {"resultCode": "0", "resultMsg": "OK"},
            "body": {
                "pageNo": page_no,
                "numOfRows": 100,
                "totalCount": total_count,
                "items": {"item": [{"MNG_NO": value} for value in ids]},
            },
        }
    }


def test_bounded_history_snapshot_writes_pages_without_key(
    external_tmp_path: Path,
) -> None:
    root = external_tmp_path / "data"
    root.mkdir()
    seen: list[str] = []

    def opener(request: Request, _timeout: int) -> FakeResponse:
        seen.append(request.full_url)
        page_no = 1 if "pageNo=1" in request.full_url else 2
        body = payload(page_no, 101, ["A"] * 100 if page_no == 1 else ["B"])
        return FakeResponse(body, request.full_url)

    result = acquire_history_snapshot(
        "bakeries",
        base_date="20260101",
        authority_code="3000000",
        data_root=root,
        max_pages=2,
        max_attempts=1,
        service_key="synthetic-secret",
        opener=opener,
    )
    assert result.manifest["observed"]["total_count"] == 101
    assert result.manifest["observed"]["total_pages"] == 2
    assert len(result.manifest["pages"]) == 2
    rendered = json.dumps(result.manifest)
    assert "synthetic-secret" not in rendered
    assert result.manifest["query"]["service_key_redacted"] is True
    assert all("synthetic-secret" in url for url in seen)


def test_history_snapshot_refuses_page_count_above_cap(external_tmp_path: Path) -> None:
    root = external_tmp_path / "data"
    root.mkdir()

    def opener(request: Request, _timeout: int) -> FakeResponse:
        return FakeResponse(payload(1, 201, ["A"] * 100), request.full_url)

    with pytest.raises(HistoryAcquisitionError, match="exceeding max_pages"):
        acquire_history_snapshot(
            "general_restaurants",
            base_date="20260101",
            authority_code="3000000",
            data_root=root,
            max_pages=2,
            max_attempts=1,
            service_key="synthetic",
            opener=opener,
        )

