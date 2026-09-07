from __future__ import annotations

import csv
import hashlib
import json
import math
import sqlite3
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from .profiling import DATE_FORMATS, ProfileError, detect_encoding


REQUIRED_AUDIT_COLUMNS = {
    "개방자치단체코드",
    "관리번호",
    "인허가일자",
    "영업상태명",
    "폐업일자",
    "사업장명",
    "상세영업상태명",
    "상세영업상태코드",
    "영업상태코드",
    "전화번호",
    "좌표정보(X)",
    "좌표정보(Y)",
    "도로명주소",
    "지번주소",
}


class SnapshotAuditError(RuntimeError):
    """Raised when an empirical current-snapshot audit cannot be completed safely."""


def _parse_date(value: str) -> date | None:
    stripped = value.strip()
    if not stripped:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(stripped, fmt).date()
        except ValueError:
            continue
    return None


def _parsed_row_hash(row: Iterable[str]) -> bytes:
    digest = hashlib.sha256()
    for value in row:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.digest()


def _finite_float(value: str) -> float | None:
    stripped = value.strip()
    if not stripped:
        return None
    try:
        parsed = float(stripped)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def _sqlite_duplicate_summary(connection: sqlite3.Connection, column: str) -> dict[str, int]:
    allowed = {"management_no", "composite_key", "row_hash"}
    if column not in allowed:
        raise SnapshotAuditError(f"unsupported duplicate column: {column}")
    where = f"{column} IS NOT NULL"
    distinct = connection.execute(
        f"SELECT COUNT(DISTINCT {column}) FROM audit_keys WHERE {where}"
    ).fetchone()[0]
    populated = connection.execute(
        f"SELECT COUNT(*) FROM audit_keys WHERE {where}"
    ).fetchone()[0]
    duplicate_values = connection.execute(
        f"SELECT COUNT(*) FROM ("
        f"SELECT {column} FROM audit_keys WHERE {where} GROUP BY {column} HAVING COUNT(*) > 1"
        f")"
    ).fetchone()[0]
    max_multiplicity = connection.execute(
        f"SELECT COALESCE(MAX(n), 0) FROM ("
        f"SELECT COUNT(*) AS n FROM audit_keys WHERE {where} GROUP BY {column}"
        f")"
    ).fetchone()[0]
    return {
        "populated_rows": int(populated),
        "distinct_values": int(distinct),
        "duplicate_values": int(duplicate_values),
        "duplicate_rows_beyond_first": int(populated - distinct),
        "max_multiplicity": int(max_multiplicity),
    }


def audit_snapshot(
    path: Path,
    *,
    retrieval_date: date,
    sqlite_path: Path,
    batch_size: int = 5_000,
) -> dict[str, Any]:
    """Audit one current snapshot without assigning canonical lifecycle semantics."""
    if batch_size < 1:
        raise SnapshotAuditError("batch_size must be positive")
    encoding = detect_encoding(path)["selected"]
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()

    connection = sqlite3.connect(sqlite_path)
    connection.execute("PRAGMA journal_mode=OFF")
    connection.execute("PRAGMA synchronous=OFF")
    connection.execute("PRAGMA temp_store=MEMORY")
    connection.execute(
        "CREATE TABLE audit_keys (management_no TEXT, composite_key TEXT, row_hash BLOB)"
    )

    row_count = 0
    management_null = 0
    org_null = 0
    permit_blank = 0
    permit_unparseable = 0
    permit_after_retrieval = 0
    closure_blank = 0
    closure_unparseable = 0
    closure_before_permit = 0
    closure_after_retrieval = 0
    closed_label_count = 0
    closed_label_without_closure = 0
    non_closed_label_with_closure = 0
    business_name_present = 0
    phone_present = 0
    road_address_present = 0
    lot_address_present = 0
    coordinates_both_present = 0
    coordinates_both_missing = 0
    coordinates_one_missing = 0
    coordinate_parse_failure = 0
    coordinate_zero_pairs = 0
    coordinate_negative_any = 0
    status_mapping_counts: Counter[tuple[str, str, str, str]] = Counter()
    pending: list[tuple[str | None, str | None, bytes]] = []

    try:
        with path.open("r", encoding=encoding, errors="strict", newline="") as handle:
            reader = csv.reader(handle, delimiter=",", quotechar='"', doublequote=True, strict=True)
            try:
                headers = next(reader)
            except StopIteration as exc:
                raise SnapshotAuditError("snapshot CSV is empty") from exc
            missing = sorted(REQUIRED_AUDIT_COLUMNS - set(headers))
            if missing:
                raise SnapshotAuditError(f"required audit columns missing: {missing}")
            index = {name: headers.index(name) for name in REQUIRED_AUDIT_COLUMNS}

            for row in reader:
                row_count += 1
                if len(row) != len(headers):
                    raise SnapshotAuditError(
                        f"row {row_count + 1} has {len(row)} fields; expected {len(headers)}"
                    )

                org = row[index["개방자치단체코드"]].strip()
                management = row[index["관리번호"]].strip()
                if not org:
                    org_null += 1
                if not management:
                    management_null += 1
                composite = f"{org}\x1f{management}" if org and management else None
                pending.append((management or None, composite, _parsed_row_hash(row)))
                if len(pending) >= batch_size:
                    connection.executemany(
                        "INSERT INTO audit_keys(management_no, composite_key, row_hash) VALUES(?,?,?)",
                        pending,
                    )
                    pending.clear()

                permit_raw = row[index["인허가일자"]]
                permit_date = _parse_date(permit_raw)
                if not permit_raw.strip():
                    permit_blank += 1
                elif permit_date is None:
                    permit_unparseable += 1
                elif permit_date > retrieval_date:
                    permit_after_retrieval += 1

                closure_raw = row[index["폐업일자"]]
                closure_date = _parse_date(closure_raw)
                if not closure_raw.strip():
                    closure_blank += 1
                elif closure_date is None:
                    closure_unparseable += 1
                else:
                    if permit_date is not None and closure_date < permit_date:
                        closure_before_permit += 1
                    if closure_date > retrieval_date:
                        closure_after_retrieval += 1

                status_name = row[index["영업상태명"]].strip()
                detail_name = row[index["상세영업상태명"]].strip()
                status_code = row[index["영업상태코드"]].strip()
                detail_code = row[index["상세영업상태코드"]].strip()
                status_mapping_counts[(status_code, status_name, detail_code, detail_name)] += 1
                has_closure = bool(closure_raw.strip())
                if status_name == "폐업":
                    closed_label_count += 1
                    if not has_closure:
                        closed_label_without_closure += 1
                elif has_closure:
                    non_closed_label_with_closure += 1

                if row[index["사업장명"]].strip():
                    business_name_present += 1
                if row[index["전화번호"]].strip():
                    phone_present += 1
                if row[index["도로명주소"]].strip():
                    road_address_present += 1
                if row[index["지번주소"]].strip():
                    lot_address_present += 1

                x_raw = row[index["좌표정보(X)"]].strip()
                y_raw = row[index["좌표정보(Y)"]].strip()
                if x_raw and y_raw:
                    coordinates_both_present += 1
                    x = _finite_float(x_raw)
                    y = _finite_float(y_raw)
                    if x is None or y is None:
                        coordinate_parse_failure += 1
                    else:
                        if x == 0 and y == 0:
                            coordinate_zero_pairs += 1
                        if x < 0 or y < 0:
                            coordinate_negative_any += 1
                elif not x_raw and not y_raw:
                    coordinates_both_missing += 1
                else:
                    coordinates_one_missing += 1

        if pending:
            connection.executemany(
                "INSERT INTO audit_keys(management_no, composite_key, row_hash) VALUES(?,?,?)",
                pending,
            )
        connection.commit()

        management_summary = _sqlite_duplicate_summary(connection, "management_no")
        composite_summary = _sqlite_duplicate_summary(connection, "composite_key")
        row_hash_summary = _sqlite_duplicate_summary(connection, "row_hash")
    except (csv.Error, UnicodeDecodeError, sqlite3.Error, ProfileError) as exc:
        raise SnapshotAuditError(str(exc)) from exc
    finally:
        connection.close()

    return {
        "audit_version": 1,
        "grain_claim": "UNRESOLVED_EMPIRICAL_CURRENT_SNAPSHOT_ONLY",
        "retrieval_date": retrieval_date.isoformat(),
        "encoding": encoding,
        "rows": row_count,
        "candidate_identity": {
            "management_number": {
                "source_field": "관리번호",
                "null_rows": management_null,
                **management_summary,
                "interpretation": "EMPIRICAL_ONLY_NOT_A_DECLARED_PRIMARY_KEY",
            },
            "authority_plus_management": {
                "source_fields": ["개방자치단체코드", "관리번호"],
                "authority_null_rows": org_null,
                **composite_summary,
                "interpretation": "EMPIRICAL_ONLY_NOT_A_DECLARED_PRIMARY_KEY",
            },
        },
        "parsed_row_duplicates": {
            **row_hash_summary,
            "definition": "SHA-256 of length-prefixed parsed field values; not raw-byte identity",
        },
        "dates": {
            "permit_blank": permit_blank,
            "permit_unparseable_nonblank": permit_unparseable,
            "permit_after_retrieval_date": permit_after_retrieval,
            "closure_blank": closure_blank,
            "closure_unparseable_nonblank": closure_unparseable,
            "closure_before_permit": closure_before_permit,
            "closure_after_retrieval_date": closure_after_retrieval,
        },
        "source_status_vs_closure_field": {
            "closed_label": "폐업",
            "closed_label_count": closed_label_count,
            "closed_label_without_closure_field": closed_label_without_closure,
            "non_closed_label_with_closure_field": non_closed_label_with_closure,
            "closure_date_alone_sufficient": False
            if closed_label_without_closure or non_closed_label_with_closure
            else "NOT_FALSIFIED_IN_THIS_SNAPSHOT",
            "warning": "This compares source labels/fields only and does not define canonical lifecycle semantics.",
        },
        "status_mapping_counts": [
            {
                "status_code": key[0],
                "status_name": key[1],
                "detail_status_code": key[2],
                "detail_status_name": key[3],
                "count": count,
            }
            for key, count in sorted(status_mapping_counts.items())
        ],
        "privacy_presence": {
            "business_name_nonblank": business_name_present,
            "phone_nonblank": phone_present,
            "road_address_nonblank": road_address_present,
            "lot_address_nonblank": lot_address_present,
            "public_allowlist_decision": "REVIEW_REQUIRED",
        },
        "coordinates": {
            "both_present": coordinates_both_present,
            "both_missing": coordinates_both_missing,
            "one_missing": coordinates_one_missing,
            "parse_failure_when_both_present": coordinate_parse_failure,
            "zero_pairs": coordinate_zero_pairs,
            "negative_any": coordinate_negative_any,
            "crs_transform_performed": False,
            "warning": "Source CRS is documented separately; X/Y field semantics still require explicit verification before transformation.",
        },
        "not_testable_from_current_snapshot": [
            "longitudinal identifier stability",
            "relocations",
            "category changes",
            "reopenings",
            "history ordering and update semantics",
        ],
    }


def retrieval_date_from_manifest(manifest_path: Path) -> date:
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    try:
        stamp = value["request"]["completed"]["asia_seoul"]
    except (KeyError, TypeError) as exc:
        raise SnapshotAuditError("retrieval manifest lacks Asia/Seoul completion timestamp") from exc
    try:
        return datetime.fromisoformat(stamp).date()
    except ValueError as exc:
        raise SnapshotAuditError(f"invalid retrieval timestamp: {stamp!r}") from exc
