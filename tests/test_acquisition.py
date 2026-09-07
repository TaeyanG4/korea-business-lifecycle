from __future__ import annotations

import io
from email.message import Message
from pathlib import Path
from urllib.request import Request

import pytest

from korea_business_lifecycle.acquisition import (
    AcquisitionError,
    acquire_current_snapshot,
    sanitize_url,
    validate_bulk_url,
    validate_final_url,
)


class FakeResponse:
    def __init__(
        self,
        body: bytes,
        *,
        url: str = "https://file.localdata.go.kr/file/download/general_restaurants/info",
        status: int = 200,
        content_length: int | None = None,
    ) -> None:
        self._stream = io.BytesIO(body)
        self._url = url
        self.status = status
        headers = Message()
        headers["Content-Type"] = "text/csv"
        if content_length is not None:
            headers["Content-Length"] = str(content_length)
        headers["ETag"] = '"synthetic-etag"'
        self.headers = headers

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def getcode(self) -> int:
        return self.status

    def geturl(self) -> str:
        return self._url

    def close(self) -> None:
        self._stream.close()


def test_sanitize_url_redacts_secret_like_query_values() -> None:
    result = sanitize_url("https://example.test/data?serviceKey=secret&page=1")
    assert "secret" not in result
    assert "REDACTED" in result
    assert "page=1" in result


def test_validate_bulk_url_rejects_non_official_hosts() -> None:
    with pytest.raises(AcquisitionError, match="not allowlisted"):
        validate_bulk_url("https://example.test/file.csv")


def test_validate_final_url_rejects_official_error_page() -> None:
    with pytest.raises(AcquisitionError, match="error page"):
        validate_final_url("https://file.localdata.go.kr/error.html")


def test_acquisition_writes_immutable_artifact_and_manifest(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "external-data"
    data_root.mkdir()
    body = "관리번호,인허가일자\nA1,20200102\n".encode("utf-8")
    calls: list[tuple[str, int]] = []

    def opener(request: Request, timeout: int) -> FakeResponse:
        calls.append((request.full_url, timeout))
        return FakeResponse(body, content_length=len(body))

    result = acquire_current_snapshot(
        "general_restaurants",
        data_root=data_root,
        min_free_bytes=0,
        max_attempts=1,
        timeout_seconds=7,
        opener=opener,
    )

    assert result.artifact_path.read_bytes() == body
    assert result.manifest_path.is_file()
    assert result.manifest["artifact"]["bytes"] == len(body)
    assert len(result.manifest["artifact"]["sha256"]) == 64
    assert result.manifest["response"]["etag"] == '"synthetic-etag"'
    assert result.manifest["request"]["attempt"] == 1
    assert calls == [("https://file.localdata.go.kr/file/download/general_restaurants/info", 7)]


def test_acquisition_retries_are_bounded(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "external-data"
    data_root.mkdir()
    calls = 0
    sleeps: list[float] = []

    def opener(_request: Request, _timeout: int) -> FakeResponse:
        nonlocal calls
        calls += 1
        raise OSError("synthetic network failure")

    with pytest.raises(AcquisitionError, match="after 3 attempts"):
        acquire_current_snapshot(
            "rest_cafes",
            data_root=data_root,
            min_free_bytes=0,
            max_attempts=3,
            opener=opener,
            sleep=sleeps.append,
        )
    assert calls == 3
    assert sleeps == [1, 2]


def test_acquisition_rejects_truncated_response(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "external-data"
    data_root.mkdir()
    body = b"short"

    def opener(_request: Request, _timeout: int) -> FakeResponse:
        return FakeResponse(body, content_length=len(body) + 1)

    with pytest.raises(AcquisitionError, match="byte count mismatch"):
        acquire_current_snapshot(
            "bakeries",
            data_root=data_root,
            min_free_bytes=0,
            max_attempts=1,
            opener=opener,
        )


def test_acquisition_rejects_html_error_response(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "external-data"
    data_root.mkdir()

    def opener(_request: Request, _timeout: int) -> FakeResponse:
        response = FakeResponse(
            b"<html>error</html>",
            url="https://file.localdata.go.kr/error.html",
        )
        response.headers.replace_header("Content-Type", "text/html; charset=utf-8")
        return response

    with pytest.raises(AcquisitionError, match="HTML"):
        acquire_current_snapshot(
            "general_restaurants",
            data_root=data_root,
            min_free_bytes=0,
            max_attempts=1,
            opener=opener,
        )


def test_acquisition_enforces_independent_byte_cap(external_tmp_path: Path) -> None:
    data_root = external_tmp_path / "external-data"
    data_root.mkdir()

    def opener(_request: Request, _timeout: int) -> FakeResponse:
        return FakeResponse(b"123456", content_length=None)

    with pytest.raises(AcquisitionError, match="byte cap"):
        acquire_current_snapshot(
            "bakeries",
            data_root=data_root,
            min_free_bytes=0,
            max_attempts=1,
            max_download_bytes=5,
            opener=opener,
        )


def test_acquisition_rejects_embedded_credentials() -> None:
    with pytest.raises(AcquisitionError, match="embedded credentials"):
        sanitize_url("https://user:password@file.localdata.go.kr/file/test/info")
