from __future__ import annotations

import csv
import hashlib
import sqlite3
from pathlib import Path
from typing import Any, Mapping

from .profiling import detect_encoding


REQUIRED_COLUMNS = {
    "개방자치단체코드",
    "관리번호",
    "사업장명",
    "도로명주소",
    "지번주소",
}


class CrossCategoryAuditError(RuntimeError):
    """Raised when a cross-category current-snapshot audit cannot complete."""


def _identity_context_hash(name: str, road: str, lot: str) -> bytes:
    digest = hashlib.sha256()
    for value in (name.strip(), road.strip(), lot.strip()):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.digest()


def _overlap_count(connection: sqlite3.Connection, column: str) -> int:
    if column not in {"management_no", "composite_key"}:
        raise CrossCategoryAuditError(f"unsupported overlap column: {column}")
    return int(
        connection.execute(
            f"SELECT COUNT(*) FROM ("
            f"SELECT {column} FROM records WHERE {column} IS NOT NULL "
            f"GROUP BY {column} HAVING COUNT(DISTINCT source_key) > 1"
            f")"
        ).fetchone()[0]
    )


def audit_cross_category_current_snapshots(
    sources: Mapping[str, Path],
    *,
    sqlite_path: Path,
    batch_size: int = 5_000,
) -> dict[str, Any]:
    if len(sources) < 2:
        raise CrossCategoryAuditError("at least two sources are required")
    if sqlite_path.exists():
        sqlite_path.unlink()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(sqlite_path)
    connection.execute("PRAGMA journal_mode=OFF")
    connection.execute("PRAGMA synchronous=OFF")
    connection.execute("PRAGMA temp_store=MEMORY")
    connection.execute(
        "CREATE TABLE records ("
        "source_key TEXT NOT NULL, management_no TEXT, composite_key TEXT, context_hash BLOB)"
    )
    counts: dict[str, int] = {}

    try:
        for source_key, path in sorted(sources.items()):
            encoding = detect_encoding(path)["selected"]
            pending: list[tuple[str, str | None, str | None, bytes]] = []
            rows = 0
            with path.open("r", encoding=encoding, errors="strict", newline="") as handle:
                reader = csv.reader(
                    handle,
                    delimiter=",",
                    quotechar='"',
                    doublequote=True,
                    strict=True,
                )
                headers = next(reader)
                missing = sorted(REQUIRED_COLUMNS - set(headers))
                if missing:
                    raise CrossCategoryAuditError(
                        f"{source_key}: required columns missing: {missing}"
                    )
                index = {name: headers.index(name) for name in REQUIRED_COLUMNS}
                for row in reader:
                    rows += 1
                    if len(row) != len(headers):
                        raise CrossCategoryAuditError(
                            f"{source_key}: row {rows + 1} has {len(row)} fields; expected {len(headers)}"
                        )
                    management = row[index["관리번호"]].strip()
                    authority = row[index["개방자치단체코드"]].strip()
                    composite = (
                        f"{authority}\x1f{management}" if authority and management else None
                    )
                    context = _identity_context_hash(
                        row[index["사업장명"]],
                        row[index["도로명주소"]],
                        row[index["지번주소"]],
                    )
                    pending.append((source_key, management or None, composite, context))
                    if len(pending) >= batch_size:
                        connection.executemany(
                            "INSERT INTO records VALUES(?,?,?,?)", pending
                        )
                        pending.clear()
                if pending:
                    connection.executemany("INSERT INTO records VALUES(?,?,?,?)", pending)
            counts[source_key] = rows
        connection.commit()

        management_overlap = _overlap_count(connection, "management_no")
        composite_overlap = _overlap_count(connection, "composite_key")
        composite_same_context = int(
            connection.execute(
                "SELECT COUNT(*) FROM ("
                "SELECT composite_key FROM records WHERE composite_key IS NOT NULL "
                "GROUP BY composite_key "
                "HAVING COUNT(DISTINCT source_key) > 1 AND COUNT(DISTINCT context_hash) = 1"
                ")"
            ).fetchone()[0]
        )
        composite_conflicting_context = int(
            connection.execute(
                "SELECT COUNT(*) FROM ("
                "SELECT composite_key FROM records WHERE composite_key IS NOT NULL "
                "GROUP BY composite_key "
                "HAVING COUNT(DISTINCT source_key) > 1 AND COUNT(DISTINCT context_hash) > 1"
                ")"
            ).fetchone()[0]
        )
    except (csv.Error, UnicodeDecodeError, sqlite3.Error) as exc:
        raise CrossCategoryAuditError(str(exc)) from exc
    finally:
        connection.close()

    return {
        "audit_version": 1,
        "scope": "CURRENT_SNAPSHOTS_ONLY",
        "rows_by_source": counts,
        "management_number_overlap_across_categories": management_overlap,
        "authority_plus_management_overlap_across_categories": composite_overlap,
        "overlapping_composite_same_business_name_and_addresses": composite_same_context,
        "overlapping_composite_conflicting_business_name_or_addresses": composite_conflicting_context,
        "interpretation": (
            "Cross-category overlap is evidence about simultaneous current records only. "
            "It does not prove category transition, relocation, or establishment continuity."
        ),
        "privacy": (
            "Business names and addresses are hashed only inside the temporary audit database; "
            "no source values or hashes are emitted."
        ),
    }
