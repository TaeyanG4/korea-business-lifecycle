from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from functools import lru_cache
from typing import Any, Iterable, Mapping

from .canonical_schema import (
    FROZEN_V1_SOURCE_COLUMNS,
    FORBIDDEN_CANONICAL_COLUMNS,
    REQUIRED_CANONICAL_COLUMNS,
    load_permit_parent_schema,
    validate_permit_parent_schema,
)
from .profiling import DATE_FORMATS
from .provenance import V1_SOURCE_KEYS


SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class PermitTransformError(ValueError):
    """Raised when a source row cannot satisfy the frozen PERMIT contract safely."""


@dataclass(frozen=True)
class PermitTransformContext:
    source_key: str
    source_artifact_sha256: str
    source_retrieved_at_utc: datetime


def _parse_utc_timestamp(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise PermitTransformError("source retrieval timestamp is not valid ISO-8601") from exc
    else:
        raise PermitTransformError("source retrieval timestamp must be an ISO-8601 string or datetime")

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PermitTransformError("source retrieval timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def build_permit_transform_context(
    *,
    source_key: str,
    source_artifact_sha256: str,
    source_retrieved_at_utc: str | datetime,
) -> PermitTransformContext:
    if source_key not in V1_SOURCE_KEYS:
        raise PermitTransformError(f"unsupported v1 source: {source_key}")
    if not SHA256_PATTERN.fullmatch(source_artifact_sha256):
        raise PermitTransformError("source artifact SHA-256 must be 64 lowercase hexadecimal characters")
    return PermitTransformContext(
        source_key=source_key,
        source_artifact_sha256=source_artifact_sha256,
        source_retrieved_at_utc=_parse_utc_timestamp(source_retrieved_at_utc),
    )


def permit_transform_context_from_retrieval_manifest(
    manifest: Mapping[str, Any],
) -> PermitTransformContext:
    if manifest.get("manifest_version") != 1:
        raise PermitTransformError("unsupported current-snapshot retrieval manifest version")
    artifact = manifest.get("artifact")
    request = manifest.get("request")
    if not isinstance(artifact, Mapping) or not isinstance(request, Mapping):
        raise PermitTransformError("retrieval manifest is missing artifact/request metadata")
    completed = request.get("completed")
    if not isinstance(completed, Mapping):
        raise PermitTransformError("retrieval manifest is missing request.completed metadata")
    source_key = manifest.get("source_key")
    sha256 = artifact.get("sha256")
    retrieved_at_utc = completed.get("utc")
    if not isinstance(source_key, str) or not isinstance(sha256, str):
        raise PermitTransformError("retrieval manifest source lineage metadata is invalid")
    if not isinstance(retrieved_at_utc, (str, datetime)):
        raise PermitTransformError("retrieval manifest UTC completion timestamp is invalid")
    return build_permit_transform_context(
        source_key=source_key,
        source_artifact_sha256=sha256,
        source_retrieved_at_utc=retrieved_at_utc,
    )


def _normalize_string(raw: Any, *, field: str) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise PermitTransformError(f"{field} must arrive as decoded source text")
    normalized = raw.strip()
    return normalized or None


def _required_string(raw: Any, *, field: str) -> str:
    value = _normalize_string(raw, field=field)
    if value is None:
        raise PermitTransformError(f"required source identifier {field} is blank")
    return value


def _parse_source_date(raw: Any, *, field: str) -> tuple[date | None, str]:
    value = _normalize_string(raw, field=field)
    if value is None:
        return None, "MISSING"
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date(), "VALID"
        except ValueError:
            continue
    return None, "INVALID"


def _parse_coordinate(raw: Any, *, field: str) -> float | None:
    value = _normalize_string(raw, field=field)
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise PermitTransformError(f"nonblank {field} cannot be parsed as float64") from exc
    if not math.isfinite(parsed):
        raise PermitTransformError(f"nonblank {field} must be finite float64")
    return parsed


@lru_cache(maxsize=1)
def _canonical_column_order() -> tuple[str, ...]:
    schema = load_permit_parent_schema()
    errors = validate_permit_parent_schema(schema)
    if errors:
        raise PermitTransformError(f"frozen PERMIT schema validation failed: {errors}")
    return tuple(str(item["name"]) for item in schema["columns"])


def _validate_source_shape(row: Mapping[str, Any]) -> None:
    columns = set(row)
    if columns != FROZEN_V1_SOURCE_COLUMNS or len(row) != len(FROZEN_V1_SOURCE_COLUMNS):
        missing = sorted(FROZEN_V1_SOURCE_COLUMNS - columns)
        extra = sorted(columns - FROZEN_V1_SOURCE_COLUMNS)
        raise PermitTransformError(
            f"source row must exactly match frozen 39-column inventory; missing={missing}, extra={extra}"
        )


def transform_permit_row(
    row: Mapping[str, Any],
    *,
    context: PermitTransformContext,
    source_row_number: int,
) -> dict[str, Any]:
    """Transform one already-decoded current-snapshot row into the frozen PERMIT shape."""
    if source_row_number < 1:
        raise PermitTransformError("source_row_number must be 1-based and positive")
    _validate_source_shape(row)

    permit_date, permit_date_quality = _parse_source_date(row["인허가일자"], field="인허가일자")
    closure_date, closure_date_quality = _parse_source_date(row["폐업일자"], field="폐업일자")

    values: dict[str, Any] = {
        "source_key": context.source_key,
        "source_row_number": source_row_number,
        "source_artifact_sha256": context.source_artifact_sha256,
        "source_retrieved_at_utc": context.source_retrieved_at_utc,
        "authority_code": _required_string(row["개방자치단체코드"], field="개방자치단체코드"),
        "management_number": _required_string(row["관리번호"], field="관리번호"),
        "permit_date": permit_date,
        "permit_date_quality": permit_date_quality,
        "source_status_code": _normalize_string(row["영업상태코드"], field="영업상태코드"),
        "source_status_name": _normalize_string(row["영업상태명"], field="영업상태명"),
        "source_detail_status_code": _normalize_string(
            row["상세영업상태코드"], field="상세영업상태코드"
        ),
        "source_detail_status_name": _normalize_string(
            row["상세영업상태명"], field="상세영업상태명"
        ),
        "closure_date": closure_date,
        "closure_date_quality": closure_date_quality,
        "business_name": _normalize_string(row["사업장명"], field="사업장명"),
        "business_type_name": _normalize_string(row["업태구분명"], field="업태구분명"),
        "hygiene_business_type_name": _normalize_string(row["위생업태명"], field="위생업태명"),
        "lot_postal_code": _normalize_string(row["소재지우편번호"], field="소재지우편번호"),
        "road_postal_code": _normalize_string(row["도로명우편번호"], field="도로명우편번호"),
        "lot_address": _normalize_string(row["지번주소"], field="지번주소"),
        "road_address": _normalize_string(row["도로명주소"], field="도로명주소"),
        "source_coordinate_x": _parse_coordinate(row["좌표정보(X)"], field="좌표정보(X)"),
        "source_coordinate_y": _parse_coordinate(row["좌표정보(Y)"], field="좌표정보(Y)"),
        "source_data_update_type": _normalize_string(
            row["데이터갱신구분"], field="데이터갱신구분"
        ),
        "source_data_updated_at_raw": _normalize_string(
            row["데이터갱신시점"], field="데이터갱신시점"
        ),
        "source_last_modified_at_raw": _normalize_string(
            row["최종수정시점"], field="최종수정시점"
        ),
    }

    if set(values) != REQUIRED_CANONICAL_COLUMNS:
        raise PermitTransformError("PERMIT transformer output no longer matches frozen canonical columns")
    if set(values) & FORBIDDEN_CANONICAL_COLUMNS:
        raise PermitTransformError("PERMIT transformer emitted a forbidden inferred semantic field")
    return {name: values[name] for name in _canonical_column_order()}


def transform_current_snapshot_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    context: PermitTransformContext,
) -> list[dict[str, Any]]:
    """Synthetic/bounded in-memory transformer; fail closed on duplicate linkage candidates."""
    transformed: list[dict[str, Any]] = []
    seen_linkage: set[tuple[str, str]] = set()
    for source_row_number, row in enumerate(rows, start=1):
        canonical = transform_permit_row(
            row,
            context=context,
            source_row_number=source_row_number,
        )
        linkage = (canonical["source_key"], canonical["management_number"])
        if linkage in seen_linkage:
            raise PermitTransformError(
                f"duplicate expected uniqueness candidate encountered at source row {source_row_number}"
            )
        seen_linkage.add(linkage)
        transformed.append(canonical)
    return transformed
