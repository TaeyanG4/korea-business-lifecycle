from __future__ import annotations

import io
import json
import urllib.error
from datetime import date
from email.message import Message
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request

import pytest

from korea_business_lifecycle.history_probe import (
    HistoryProbeError,
    SERVICE_KEY_ENV,
    parse_base_date,
    probe_history,
    require_service_key,
    validate_authority_code,
)


class FakeResponse:
    def __init__(self, payload: dict, *, url: str) -> None:
        self._stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        self._url = url
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = "application/json"

    def read(self, size: int = -1) -> bytes:
        return self._stream.read(size)

    def getcode(self) -> int:
        return self.status

    def geturl(self) -> str:
        return self._url

    def close(self) -> None:
        self._stream.close()


def success_payload(total_count: int = 12) -> dict:
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE"},
            "body": {
                "dataType": "JSON",
                "numOfRows": 1,
                "pageNo": 1,
                "totalCount": total_count,
                "items": {"item": [{"MNG_NO": "synthetic-never-emitted"}]},
            },
        }
    }


def test_service_key_is_required_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(SERVICE_KEY_ENV, raising=False)
    with pytest.raises(HistoryProbeError, match=SERVICE_KEY_ENV):
        require_service_key()


def test_history_date_bounds_are_explicit() -> None:
    today = date(2026, 9, 7)
    assert parse_base_date("20260101", today_kst=today) == date(2026, 1, 1)
    assert parse_base_date("20260906", today_kst=today) == date(2026, 9, 6)
    with pytest.raises(HistoryProbeError, match="earlier"):
        parse_base_date("20251231", today_kst=today)
    with pytest.raises(HistoryProbeError, match="later"):
        parse_base_date("20260907", today_kst=today)


def test_authority_code_matches_observed_current_format() -> None:
    assert validate_authority_code("3000000") == "3000000"
    with pytest.raises(HistoryProbeError, match="7 digits"):
        validate_authority_code("300000")


def test_probe_is_single_page_bounded_and_does_not_emit_key() -> None:
    secret = "very-secret-decoding-key"
    seen_urls: list[str] = []

    def opener(request: Request, _timeout: int) -> FakeResponse:
        seen_urls.append(request.full_url)
        parts = urlsplit(request.full_url)
        query = parse_qs(parts.query)
        assert query["serviceKey"] == [secret]
        assert query["pageNo"] == ["1"]
        assert query["numOfRows"] == ["1"]
        assert query["cond[BASE_DATE::EQ]"] == ["20260101"]
        assert query["cond[OPN_ATMY_GRP_CD::EQ]"] == ["3000000"]
        return FakeResponse(success_payload(), url=request.full_url)

    result = probe_history(
        "bakeries",
        base_date="20260101",
        authority_code="3000000",
        service_key=secret,
        today_kst=date(2026, 9, 7),
        opener=opener,
    )
    rendered = json.dumps(result.as_dict())
    assert result.total_count == 12
    assert result.returned_rows == 1
    assert result.service_key_redacted is True
    assert secret not in rendered
    assert len(seen_urls) == 1


def test_probe_reports_authentication_failure_without_key_leak() -> None:
    secret = "secret"

    def opener(request: Request, _timeout: int):
        raise urllib.error.HTTPError(request.full_url, 401, "Unauthorized", {}, None)

    with pytest.raises(HistoryProbeError, match="authentication failed") as error:
        probe_history(
            "rest_cafes",
            base_date="20260101",
            authority_code="3000000",
            service_key=secret,
            today_kst=date(2026, 9, 7),
            opener=opener,
        )
    assert secret not in str(error.value)


def test_probe_rejects_more_than_official_max_rows() -> None:
    with pytest.raises(HistoryProbeError, match="between 1 and 100"):
        probe_history(
            "general_restaurants",
            base_date="20260101",
            authority_code="3000000",
            num_rows=101,
            service_key="synthetic",
            today_kst=date(2026, 9, 7),
        )
