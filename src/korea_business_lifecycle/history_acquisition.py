from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlencode, urlsplit

from .artifacts import current_git_sha
from .config import project_root
from .history_probe import (
    HISTORY_HOST,
    HistoryProbeError,
    _read_bounded,
    history_endpoint,
    parse_base_date,
    require_service_key,
    validate_authority_code,
)
from .storage import resolve_data_root


PAGE_SIZE = 100
DEFAULT_MAX_PAGES = 500
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30
KST = timezone(timedelta(hours=9), name="Asia/Seoul")


class HistoryAcquisitionError(RuntimeError):
    """Raised when a bounded history snapshot cannot be acquired safely."""


@dataclass(frozen=True)
class HistorySnapshotResult:
    snapshot_dir: Path
    manifest_path: Path
    manifest: dict[str, Any]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamps(moment: datetime) -> dict[str, str]:
    return {
        "utc": moment.astimezone(timezone.utc).isoformat(),
        "asia_seoul": moment.astimezone(KST).isoformat(),
    }


def _open_url(request: urllib.request.Request, timeout: int) -> Any:
    return urllib.request.urlopen(request, timeout=timeout)


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="json-", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _parse_payload(raw: bytes) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        payload = json.loads(raw.decode("utf-8"))
        response_obj = payload["response"]
        header = response_obj["header"]
        body = response_obj["body"]
        result_code = str(header.get("resultCode", ""))
        result_message = str(header.get("resultMsg", ""))
        total_count = int(body["totalCount"])
        page_no = int(body["pageNo"])
        num_rows = int(body["numOfRows"])
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise HistoryAcquisitionError("unexpected history JSON structure") from exc
    if result_code not in {"0", "00"}:
        raise HistoryAcquisitionError(
            f"history API returned resultCode={result_code!r}: {result_message}"
        )
    if num_rows > PAGE_SIZE:
        raise HistoryAcquisitionError(f"history API returned invalid numOfRows={num_rows}")
    items_obj = body.get("items")
    if not items_obj:
        items: list[dict[str, Any]] = []
    elif isinstance(items_obj, dict):
        raw_item = items_obj.get("item", [])
        if raw_item is None:
            items = []
        elif isinstance(raw_item, list):
            items = raw_item
        elif isinstance(raw_item, dict):
            items = [raw_item]
        else:
            raise HistoryAcquisitionError("unexpected history item structure")
    else:
        raise HistoryAcquisitionError("unexpected history items structure")
    return {
        "result_code": result_code,
        "result_message": result_message,
        "total_count": total_count,
        "page_no": page_no,
        "num_rows": num_rows,
    }, items


def _request_page(
    source_key: str,
    *,
    base_date: str,
    authority_code: str,
    page_no: int,
    service_key: str,
    timeout_seconds: int,
    opener: Callable[[urllib.request.Request, int], Any],
) -> tuple[bytes, dict[str, Any], list[dict[str, Any]]]:
    endpoint = history_endpoint(source_key)
    query = urlencode(
        {
            "serviceKey": service_key,
            "pageNo": str(page_no),
            "numOfRows": str(PAGE_SIZE),
            "returnType": "json",
            "cond[BASE_DATE::EQ]": base_date,
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
            raise HistoryAcquisitionError(
                "history authentication failed; verify service-key activation and API authorization"
            ) from exc
        raise HistoryAcquisitionError(f"history HTTP error: {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise HistoryAcquisitionError(f"history network error: {exc.reason}") from exc
    try:
        status = getattr(response, "status", None) or response.getcode()
        if status != 200:
            raise HistoryAcquisitionError(f"unexpected history HTTP status: {status}")
        final = urlsplit(response.geturl())
        if final.scheme != "https" or (final.hostname or "").casefold() != HISTORY_HOST:
            raise HistoryAcquisitionError("history request redirected outside approved host")
        raw = _read_bounded(response)
    except HistoryProbeError as exc:
        raise HistoryAcquisitionError(str(exc)) from exc
    finally:
        response.close()
    meta, items = _parse_payload(raw)
    if meta["page_no"] != page_no:
        raise HistoryAcquisitionError(
            f"history API returned pageNo={meta['page_no']} for requested page {page_no}"
        )
    return raw, meta, items


def acquire_history_snapshot(
    source_key: str,
    *,
    base_date: str,
    authority_code: str,
    data_root: str | os.PathLike[str] | None = None,
    max_pages: int = DEFAULT_MAX_PAGES,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    request_delay_seconds: float = 0.0,
    service_key: str | None = None,
    opener: Callable[[urllib.request.Request, int], Any] = _open_url,
    sleep: Callable[[float], None] = time.sleep,
) -> HistorySnapshotResult:
    """Acquire one explicitly bounded `(source, date, authority)` history snapshot."""
    parsed_date = parse_base_date(base_date).strftime("%Y%m%d")
    authority_code = validate_authority_code(authority_code)
    if max_pages < 1 or max_pages > 5000:
        raise HistoryAcquisitionError("max_pages must be between 1 and 5000")
    if max_attempts < 1 or max_attempts > 5:
        raise HistoryAcquisitionError("max_attempts must be between 1 and 5")
    if timeout_seconds < 1 or timeout_seconds > 120:
        raise HistoryAcquisitionError("timeout_seconds must be between 1 and 120")
    if request_delay_seconds < 0 or request_delay_seconds > 5:
        raise HistoryAcquisitionError("request_delay_seconds must be between 0 and 5")
    key = unquote(require_service_key(service_key))
    root = resolve_data_root(data_root)
    root.mkdir(parents=True, exist_ok=True)

    started = _utc_now()
    temp_parent = root / ".tmp" / "history"
    temp_parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix=f"{source_key}-{parsed_date}-{authority_code}-", dir=temp_parent))
    page_records: list[dict[str, Any]] = []
    total_count: int | None = None
    total_pages: int | None = None
    try:
        for page_no in range(1, max_pages + 1):
            for attempt in range(1, max_attempts + 1):
                try:
                    raw, meta, items = _request_page(
                        source_key,
                        base_date=parsed_date,
                        authority_code=authority_code,
                        page_no=page_no,
                        service_key=key,
                        timeout_seconds=timeout_seconds,
                        opener=opener,
                    )
                    break
                except (HistoryAcquisitionError, OSError) as exc:
                    if attempt >= max_attempts:
                        raise HistoryAcquisitionError(
                            f"history page {page_no} failed after {max_attempts} attempts: {exc}"
                        ) from exc
                    sleep(float(attempt))

            if total_count is None:
                total_count = int(meta["total_count"])
                total_pages = math.ceil(total_count / PAGE_SIZE) if total_count else 0
                if total_pages > max_pages:
                    raise HistoryAcquisitionError(
                        f"history snapshot requires {total_pages} pages, exceeding max_pages={max_pages}"
                    )
            elif int(meta["total_count"]) != total_count:
                raise HistoryAcquisitionError(
                    "history totalCount changed during paginated acquisition; snapshot is unstable"
                )

            page_path = temp_dir / f"page-{page_no:05d}.json"
            page_path.write_bytes(raw)
            page_records.append(
                {
                    "page_no": page_no,
                    "rows": len(items),
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "filename": page_path.name,
                }
            )
            if total_pages == 0 or page_no >= total_pages:
                break
            if request_delay_seconds:
                sleep(request_delay_seconds)
        else:
            raise HistoryAcquisitionError("history acquisition reached page cap without completion")

        observed_rows = sum(item["rows"] for item in page_records)
        if total_count is None or total_pages is None:
            raise HistoryAcquisitionError("history acquisition produced no page metadata")
        if observed_rows != total_count:
            raise HistoryAcquisitionError(
                f"history row count mismatch: expected {total_count}, observed {observed_rows}"
            )

        completed = _utc_now()
        retrieval_id = started.strftime("%Y%m%dT%H%M%SZ")
        final_dir = root / "history" / source_key / parsed_date / authority_code / retrieval_id
        if final_dir.exists():
            raise HistoryAcquisitionError(f"history retrieval directory already exists: {final_dir}")
        final_dir.parent.mkdir(parents=True, exist_ok=True)
        os.replace(temp_dir, final_dir)
        manifest = {
            "manifest_version": 1,
            "retrieval_id": retrieval_id,
            "source_key": source_key,
            "query": {
                "endpoint": history_endpoint(source_key),
                "base_date": parsed_date,
                "authority_code": authority_code,
                "page_size": PAGE_SIZE,
                "service_key_redacted": True,
            },
            "bounds": {
                "max_pages": max_pages,
                "max_attempts": max_attempts,
                "timeout_seconds": timeout_seconds,
                "request_delay_seconds": request_delay_seconds,
            },
            "observed": {
                "total_count": total_count,
                "total_pages": total_pages,
                "stored_pages": len(page_records),
                "stored_rows": observed_rows,
            },
            "pages": page_records,
            "timestamps": {
                "started": _timestamps(started),
                "completed": _timestamps(completed),
            },
            "environment": {"project_git_sha": current_git_sha(project_root())},
        }
        manifest_path = final_dir / "manifest.json"
        _atomic_json(manifest_path, manifest)
        return HistorySnapshotResult(final_dir, manifest_path, manifest)
    finally:
        if temp_dir.exists():
            for child in temp_dir.iterdir():
                if child.is_file():
                    child.unlink()
            temp_dir.rmdir()
