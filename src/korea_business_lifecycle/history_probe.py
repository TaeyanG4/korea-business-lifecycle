from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import urlencode, urlsplit

from .config import project_root
from .provenance import V1_SOURCE_KEYS, load_history_review


SERVICE_KEY_ENV = "KBL_DATA_GO_KR_SERVICE_KEY"
HISTORY_HOST = "apis.data.go.kr"
MIN_BASE_DATE = date(2026, 1, 1)
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
KST = timezone(timedelta(hours=9), name="Asia/Seoul")
AUTHORITY_CODE_RE = re.compile(r"^[0-9]{7}$")


class HistoryProbeError(RuntimeError):
    """Raised when the bounded authenticated history probe cannot safely complete."""


@dataclass(frozen=True)
class HistoryProbeResult:
    source_key: str
    base_date: str
    authority_code: str
    endpoint: str
    result_code: str
    result_message: str
    page_no: int
    requested_rows: int
    returned_rows: int
    total_count: int
    service_key_redacted: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_key": self.source_key,
            "base_date": self.base_date,
            "authority_code": self.authority_code,
            "endpoint": self.endpoint,
            "result_code": self.result_code,
            "result_message": self.result_message,
            "page_no": self.page_no,
            "requested_rows": self.requested_rows,
            "returned_rows": self.returned_rows,
            "total_count": self.total_count,
            "service_key_redacted": self.service_key_redacted,
        }


def _current_kst_date() -> date:
    return datetime.now(timezone.utc).astimezone(KST).date()


def parse_base_date(value: str, *, today_kst: date | None = None) -> date:
    try:
        parsed = datetime.strptime(value, "%Y%m%d").date()
    except ValueError as exc:
        raise HistoryProbeError("BASE_DATE must be YYYYMMDD") from exc
    upper = (today_kst or _current_kst_date()) - timedelta(days=1)
    if parsed < MIN_BASE_DATE:
        raise HistoryProbeError("BASE_DATE cannot be earlier than 20260101")
    if parsed > upper:
        raise HistoryProbeError(
            f"BASE_DATE cannot be later than the day before query date ({upper:%Y%m%d})"
        )
    return parsed


def validate_authority_code(value: str) -> str:
    if not AUTHORITY_CODE_RE.fullmatch(value):
        raise HistoryProbeError(
            "authority code must be exactly 7 digits; this matches the observed v1 current snapshots"
        )
    return value


def history_endpoint(source_key: str) -> str:
    if source_key not in V1_SOURCE_KEYS:
        raise HistoryProbeError(f"unsupported v1 source: {source_key}")
    review = load_history_review()
    for item in review["categories"]:
        if item["source_key"] == source_key:
            endpoint = item["history_url"]
            parts = urlsplit(endpoint)
            if parts.scheme != "https" or (parts.hostname or "").casefold() != HISTORY_HOST:
                raise HistoryProbeError("history endpoint is not the approved HTTPS data.go.kr host")
            return endpoint
    raise HistoryProbeError(f"history endpoint missing from review: {source_key}")


def require_service_key(value: str | None = None) -> str:
    key = value if value is not None else os.environ.get(SERVICE_KEY_ENV)
    if not key:
        dotenv_path = project_root() / ".env"
        if dotenv_path.is_file():
            try:
                lines = dotenv_path.read_text(encoding="utf-8-sig").splitlines()
            except UnicodeDecodeError as exc:
                raise HistoryProbeError("local .env must be UTF-8 text") from exc
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                name, raw_value = stripped.split("=", 1)
                if name.strip() != SERVICE_KEY_ENV:
                    continue
                candidate = raw_value.strip()
                if len(candidate) >= 2 and candidate[0] == candidate[-1] and candidate[0] in {"'", '"'}:
                    candidate = candidate[1:-1]
                key = candidate
                break
    if not key:
        raise HistoryProbeError(
            f"{SERVICE_KEY_ENV} is required in the environment or local .env; "
            "use the data.go.kr Decoding service key and keep it out of Git/logs"
        )
    if any(char.isspace() for char in key):
        raise HistoryProbeError("service key must not contain whitespace")
    return key


def _open_url(request: urllib.request.Request, timeout: int) -> Any:
    return urllib.request.urlopen(request, timeout=timeout)


def _read_bounded(response: Any, max_bytes: int = MAX_RESPONSE_BYTES) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(min(64 * 1024, max_bytes + 1 - total))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise HistoryProbeError(f"history response exceeded {max_bytes} bytes")
    return b"".join(chunks)


def _extract_items(body: dict[str, Any]) -> list[Any]:
    items = body.get("items")
    if not items:
        return []
    if isinstance(items, dict):
        item = items.get("item", [])
        if item is None:
            return []
        if isinstance(item, list):
            return item
        return [item]
    raise HistoryProbeError("unexpected history items structure")


def probe_history(
    source_key: str,
    *,
    base_date: str,
    authority_code: str,
    num_rows: int = 1,
    service_key: str | None = None,
    timeout_seconds: int = 30,
    today_kst: date | None = None,
    opener: Callable[[urllib.request.Request, int], Any] = _open_url,
) -> HistoryProbeResult:
    """Perform exactly one authenticated, bounded page-1 history query."""
    parsed_base_date = parse_base_date(base_date, today_kst=today_kst)
    authority_code = validate_authority_code(authority_code)
    if num_rows < 1 or num_rows > 100:
        raise HistoryProbeError("num_rows must be between 1 and 100")
    if timeout_seconds < 1 or timeout_seconds > 120:
        raise HistoryProbeError("timeout_seconds must be between 1 and 120")
    key = require_service_key(service_key)
    endpoint = history_endpoint(source_key)

    query = urlencode(
        {
            "serviceKey": key,
            "pageNo": "1",
            "numOfRows": str(num_rows),
            "returnType": "json",
            "cond[BASE_DATE::EQ]": parsed_base_date.strftime("%Y%m%d"),
            "cond[OPN_ATMY_GRP_CD::EQ]": authority_code,
        }
    )
    request = urllib.request.Request(
        f"{endpoint}?{query}",
        method="GET",
        headers={
            "User-Agent": "korea-business-lifecycle/0.0.0 (+https://github.com/TaeyanG4/korea-business-lifecycle)",
            "Accept": "application/json",
        },
    )

    try:
        response = opener(request, timeout_seconds)
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            raise HistoryProbeError(
                "history authentication failed; verify the data.go.kr service key and API authorization"
            ) from exc
        raise HistoryProbeError(f"history HTTP error: {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise HistoryProbeError(f"history network error: {exc.reason}") from exc

    try:
        status = getattr(response, "status", None) or response.getcode()
        if status != 200:
            raise HistoryProbeError(f"unexpected history HTTP status: {status}")
        final = urlsplit(response.geturl())
        if final.scheme != "https" or (final.hostname or "").casefold() != HISTORY_HOST:
            raise HistoryProbeError("history request redirected outside approved HTTPS data.go.kr host")
        raw = _read_bounded(response)
    finally:
        response.close()

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HistoryProbeError("history endpoint did not return valid UTF-8 JSON") from exc
    try:
        response_obj = payload["response"]
        header = response_obj["header"]
        body = response_obj["body"]
        result_code = str(header.get("resultCode", ""))
        result_message = str(header.get("resultMsg", ""))
        total_count = int(body["totalCount"])
        page_no = int(body["pageNo"])
        response_num_rows = int(body["numOfRows"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HistoryProbeError("unexpected history JSON response structure") from exc

    if result_code not in {"00", "0"}:
        raise HistoryProbeError(
            f"history API returned resultCode={result_code!r}: {result_message}"
        )
    if page_no != 1:
        raise HistoryProbeError(f"history API returned unexpected pageNo={page_no}")
    if response_num_rows > 100:
        raise HistoryProbeError(f"history API returned invalid numOfRows={response_num_rows}")

    items = _extract_items(body)
    if len(items) > num_rows:
        raise HistoryProbeError(
            f"history API returned {len(items)} items for requested num_rows={num_rows}"
        )
    if total_count < len(items):
        raise HistoryProbeError("history totalCount is smaller than returned item count")

    return HistoryProbeResult(
        source_key=source_key,
        base_date=parsed_base_date.strftime("%Y%m%d"),
        authority_code=authority_code,
        endpoint=endpoint,
        result_code=result_code,
        result_message=result_message,
        page_no=page_no,
        requested_rows=num_rows,
        returned_rows=len(items),
        total_count=total_count,
    )
