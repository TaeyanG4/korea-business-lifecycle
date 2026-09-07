from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import Message
from pathlib import Path
from typing import Any, BinaryIO, Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .artifacts import current_git_sha
from .config import project_root
from .provenance import V1_SOURCE_KEYS, load_source_registry
from .storage import resolve_data_root


DEFAULT_MIN_FREE_BYTES = 5 * 1024**3
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_MAX_DOWNLOAD_BYTES = 10 * 1024**3
DOWNLOAD_CHUNK_BYTES = 1024 * 1024
ALLOWED_BULK_HOSTS = {"file.localdata.go.kr"}
KST = timezone(timedelta(hours=9), name="Asia/Seoul")
SENSITIVE_QUERY_KEYS = {
    "apikey",
    "api_key",
    "key",
    "servicekey",
    "service_key",
    "token",
    "access_token",
}


class AcquisitionError(RuntimeError):
    """Raised when a bounded source acquisition cannot be completed safely."""


@dataclass(frozen=True)
class AcquisitionResult:
    artifact_path: Path
    manifest_path: Path
    manifest: dict[str, Any]


def sanitize_url(url: str) -> str:
    """Redact secret-like query values before writing provenance."""
    parts = urlsplit(url)
    if parts.username or parts.password:
        raise AcquisitionError("URLs containing embedded credentials are prohibited")
    sanitized = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        sanitized.append((key, "REDACTED" if key.casefold() in SENSITIVE_QUERY_KEYS else value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(sanitized), parts.fragment))


def validate_bulk_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise AcquisitionError("bulk acquisition requires HTTPS")
    if (parts.hostname or "").casefold() not in ALLOWED_BULK_HOSTS:
        raise AcquisitionError(f"bulk host is not allowlisted: {parts.hostname}")
    sanitize_url(url)


def validate_final_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise AcquisitionError("final download URL must use HTTPS")
    if (parts.hostname or "").casefold() not in ALLOWED_BULK_HOSTS:
        raise AcquisitionError(f"final download host is not allowlisted: {parts.hostname}")
    if parts.path.casefold().endswith("/error.html") or "/error/" in parts.path.casefold():
        raise AcquisitionError(f"official bulk endpoint redirected to an error page: {parts.path}")
    sanitize_url(url)


def source_entry(source_key: str) -> dict[str, Any]:
    if source_key not in V1_SOURCE_KEYS:
        raise AcquisitionError(f"unsupported v1 source: {source_key}")
    registry = load_source_registry()
    for item in registry["categories"]:
        if item["source_key"] == source_key:
            return item
    raise AcquisitionError(f"source missing from registry: {source_key}")


def _free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def ensure_disk_capacity(
    data_root: Path,
    *,
    content_length: int | None = None,
    min_free_bytes: int = DEFAULT_MIN_FREE_BYTES,
) -> None:
    free = _free_bytes(data_root)
    required = min_free_bytes
    if content_length is not None:
        if content_length < 0:
            raise AcquisitionError("negative Content-Length is invalid")
        required = max(required, content_length + min_free_bytes)
    if free < required:
        raise AcquisitionError(
            f"insufficient free space: {free} bytes available, {required} required"
        )


def _header_int(headers: Message | Any, name: str) -> int | None:
    value = headers.get(name)
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise AcquisitionError(f"invalid {name}: {value!r}") from exc
    if parsed < 0:
        raise AcquisitionError(f"invalid {name}: {value!r}")
    return parsed


def _safe_headers(headers: Message | Any) -> dict[str, str | None]:
    return {
        "content_type": headers.get("Content-Type"),
        "content_length": headers.get("Content-Length"),
        "etag": headers.get("ETag"),
        "last_modified": headers.get("Last-Modified"),
        "content_disposition": headers.get("Content-Disposition"),
    }


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamps(moment: datetime) -> dict[str, str]:
    return {
        "utc": moment.astimezone(timezone.utc).isoformat(),
        "asia_seoul": moment.astimezone(KST).isoformat(),
    }


def _open_url(request: urllib.request.Request, timeout: int) -> Any:
    return urllib.request.urlopen(request, timeout=timeout)


def _write_stream(
    response: BinaryIO,
    destination: Path,
    *,
    expected_bytes: int | None,
    max_bytes: int,
) -> tuple[int, str]:
    digest = hashlib.sha256()
    total = 0
    with destination.open("wb") as handle:
        while True:
            chunk = response.read(DOWNLOAD_CHUNK_BYTES)
            if not chunk:
                break
            handle.write(chunk)
            digest.update(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise AcquisitionError(
                    f"download exceeded configured byte cap: {total} > {max_bytes}"
                )
        handle.flush()
        os.fsync(handle.fileno())
    if expected_bytes is not None and total != expected_bytes:
        raise AcquisitionError(
            f"downloaded byte count mismatch: expected {expected_bytes}, observed {total}"
        )
    if total == 0:
        raise AcquisitionError("downloaded artifact is empty")
    return total, digest.hexdigest()


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="manifest-", suffix=".tmp", dir=path.parent)
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


def acquire_current_snapshot(
    source_key: str,
    *,
    data_root: str | os.PathLike[str] | None = None,
    min_free_bytes: int = DEFAULT_MIN_FREE_BYTES,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_download_bytes: int = DEFAULT_MAX_DOWNLOAD_BYTES,
    opener: Callable[[urllib.request.Request, int], Any] = _open_url,
    sleep: Callable[[float], None] = time.sleep,
) -> AcquisitionResult:
    """Download one current bulk snapshot with bounded retries and immutable provenance."""
    if max_attempts < 1 or max_attempts > 5:
        raise AcquisitionError("max_attempts must be between 1 and 5")
    if timeout_seconds < 1:
        raise AcquisitionError("timeout_seconds must be positive")
    if max_download_bytes < 1:
        raise AcquisitionError("max_download_bytes must be positive")

    root = resolve_data_root(data_root)
    root.mkdir(parents=True, exist_ok=True)
    ensure_disk_capacity(root, min_free_bytes=min_free_bytes)

    source = source_entry(source_key)
    url = source["bulk_url"]
    validate_bulk_url(url)
    safe_request_url = sanitize_url(url)

    temp_root = root / ".tmp" / "downloads"
    temp_root.mkdir(parents=True, exist_ok=True)
    raw_root = root / "raw" / source_key
    raw_root.mkdir(parents=True, exist_ok=True)

    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        started = _utc_now()
        temp_path = temp_root / f"{source_key}-{os.getpid()}-{attempt}.part"
        if temp_path.exists():
            temp_path.unlink()
        request = urllib.request.Request(
            url,
            method="GET",
            headers={
                "User-Agent": "korea-business-lifecycle/0.0.0 (+https://github.com/TaeyanG4/korea-business-lifecycle)",
                "Accept": "text/csv,application/octet-stream,*/*;q=0.1",
            },
        )
        try:
            response = opener(request, timeout_seconds)
            try:
                status = getattr(response, "status", None) or response.getcode()
                if status != 200:
                    raise AcquisitionError(f"unexpected HTTP status: {status}")
                headers = response.headers
                content_length = _header_int(headers, "Content-Length")
                if content_length is not None and content_length > max_download_bytes:
                    raise AcquisitionError(
                        f"Content-Length exceeds configured byte cap: "
                        f"{content_length} > {max_download_bytes}"
                    )
                content_type = (headers.get("Content-Type") or "").casefold()
                if "text/html" in content_type:
                    raise AcquisitionError(
                        f"bulk endpoint returned HTML instead of source data: {content_type}"
                    )
                final_url = sanitize_url(response.geturl())
                validate_final_url(final_url)
                ensure_disk_capacity(
                    root,
                    content_length=content_length,
                    min_free_bytes=min_free_bytes,
                )
                bytes_written, sha256 = _write_stream(
                    response,
                    temp_path,
                    expected_bytes=content_length,
                    max_bytes=max_download_bytes,
                )
            finally:
                response.close()

            completed = _utc_now()
            retrieval_id = f"{started.strftime('%Y%m%dT%H%M%SZ')}-{sha256[:12]}"
            final_dir = raw_root / retrieval_id
            if final_dir.exists():
                raise AcquisitionError(f"retrieval directory already exists: {final_dir}")
            final_dir.mkdir(parents=True, exist_ok=False)
            artifact_path = final_dir / "source.csv"
            os.replace(temp_path, artifact_path)

            manifest = {
                "manifest_version": 1,
                "retrieval_id": retrieval_id,
                "source_key": source_key,
                "source": {
                    "api_dataset_id": source.get("api_dataset_id"),
                    "file_dataset_id": source.get("file_dataset_id"),
                    "standard_dataset_id": source.get("standard_dataset_id"),
                    "request_url": safe_request_url,
                    "final_url": final_url,
                },
                "request": {
                    "method": "GET",
                    "attempt": attempt,
                    "max_attempts": max_attempts,
                    "timeout_seconds": timeout_seconds,
                    "started": _timestamps(started),
                    "completed": _timestamps(completed),
                },
                "response": {
                    "status": status,
                    **_safe_headers(headers),
                },
                "artifact": {
                    "relative_path": artifact_path.relative_to(root).as_posix(),
                    "bytes": bytes_written,
                    "sha256": sha256,
                },
                "software": {
                    "project_git_sha": current_git_sha(project_root()),
                },
            }
            manifest_path = final_dir / "retrieval.json"
            _write_json_atomic(manifest_path, manifest)
            return AcquisitionResult(
                artifact_path=artifact_path,
                manifest_path=manifest_path,
                manifest=manifest,
            )
        except (AcquisitionError, OSError, urllib.error.URLError) as exc:
            last_error = exc
            if temp_path.exists():
                temp_path.unlink()
            if attempt >= max_attempts:
                break
            sleep(min(2 ** (attempt - 1), 4))

    raise AcquisitionError(
        f"failed to acquire {source_key} after {max_attempts} attempts: {last_error}"
    )
