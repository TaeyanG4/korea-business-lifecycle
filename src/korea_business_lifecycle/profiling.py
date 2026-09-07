from __future__ import annotations

import csv
import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


DATE_FORMATS = ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d")
DEFAULT_DISTINCT_CAP = 10_000
DEFAULT_TOP_N = 20
DEFAULT_TYPE_PROBE_CAP = 10_000


class ProfileError(ValueError):
    """Raised when a source artifact cannot be profiled deterministically."""


@dataclass
class ColumnAccumulator:
    name: str
    distinct_cap: int
    top_n: int
    type_probe_cap: int
    row_count: int = 0
    null_count: int = 0
    blank_count: int = 0
    whitespace_only_count: int = 0
    non_null_count: int = 0
    min_length: int | None = None
    max_length: int | None = None
    numeric_parse_count: int = 0
    numeric_parse_examined_count: int = 0
    numeric_min: float | None = None
    numeric_max: float | None = None
    date_parse_count: int = 0
    date_parse_examined_count: int = 0
    date_formats: Counter[str] = field(default_factory=Counter)
    date_min: str | None = None
    date_max: str | None = None
    distinct_values: set[str] = field(default_factory=set)
    distinct_truncated: bool = False
    value_counts: Counter[str] = field(default_factory=Counter)
    _hints: list[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._hints = column_name_hints(self.name)

    def add(self, raw: str | None) -> None:
        self.row_count += 1
        if raw is None:
            self.null_count += 1
            return
        if raw == "":
            self.blank_count += 1
            return
        stripped = raw.strip()
        if stripped == "":
            self.whitespace_only_count += 1
            return

        self.non_null_count += 1
        length = len(raw)
        self.min_length = length if self.min_length is None else min(self.min_length, length)
        self.max_length = length if self.max_length is None else max(self.max_length, length)

        if raw in self.distinct_values:
            self.value_counts[raw] += 1
        elif len(self.distinct_values) < self.distinct_cap:
            self.distinct_values.add(raw)
            self.value_counts[raw] = 1
        else:
            self.distinct_truncated = True

        numeric_full_scan = "coordinate_like_name" in self._hints
        if numeric_full_scan or self.numeric_parse_examined_count < self.type_probe_cap:
            self.numeric_parse_examined_count += 1
            try:
                number = float(stripped)
            except ValueError:
                pass
            else:
                if math.isfinite(number):
                    self.numeric_parse_count += 1
                    self.numeric_min = (
                        number if self.numeric_min is None else min(self.numeric_min, number)
                    )
                    self.numeric_max = (
                        number if self.numeric_max is None else max(self.numeric_max, number)
                    )

        date_full_scan = "date_like_name" in self._hints
        if date_full_scan or self.date_parse_examined_count < self.type_probe_cap:
            self.date_parse_examined_count += 1
            for fmt in DATE_FORMATS:
                try:
                    parsed_date = datetime.strptime(stripped, fmt).date()
                except ValueError:
                    continue
                self.date_parse_count += 1
                self.date_formats[fmt] += 1
                iso_date = parsed_date.isoformat()
                self.date_min = iso_date if self.date_min is None else min(self.date_min, iso_date)
                self.date_max = iso_date if self.date_max is None else max(self.date_max, iso_date)
                break

    def finish(self) -> dict[str, Any]:
        tracked_distinct = len(self.distinct_values)
        hints = self._hints
        expose_top_values = "status_like_name" in hints
        return {
            "name": self.name,
            "row_count": self.row_count,
            "null_count": self.null_count,
            "blank_count": self.blank_count,
            "whitespace_only_count": self.whitespace_only_count,
            "non_null_count": self.non_null_count,
            "null_or_blank_pct": _pct(
                self.null_count + self.blank_count + self.whitespace_only_count,
                self.row_count,
            ),
            "distinct_count": None if self.distinct_truncated else tracked_distinct,
            "distinct_count_lower_bound": tracked_distinct,
            "distinct_count_exact": not self.distinct_truncated,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "numeric_parse_count": self.numeric_parse_count,
            "numeric_parse_examined_count": self.numeric_parse_examined_count,
            "numeric_parse_exact": self.numeric_parse_examined_count == self.non_null_count,
            "numeric_parse_pct": _pct(
                self.numeric_parse_count, self.numeric_parse_examined_count
            ),
            "numeric_min": self.numeric_min,
            "numeric_max": self.numeric_max,
            "date_parse_count": self.date_parse_count,
            "date_parse_examined_count": self.date_parse_examined_count,
            "date_parse_exact": self.date_parse_examined_count == self.non_null_count,
            "date_parse_pct": _pct(self.date_parse_count, self.date_parse_examined_count),
            "observed_date_formats": dict(sorted(self.date_formats.items())),
            "date_min": self.date_min,
            "date_max": self.date_max,
            "top_values": [
                {"value": value, "count": count}
                for value, count in self.value_counts.most_common(self.top_n)
            ] if expose_top_values else [],
            "top_values_policy": "raw_values_only_for_status_like_columns",
            "name_hints": hints,
        }


def _pct(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(100.0 * numerator / denominator, 6)


def column_name_hints(name: str) -> list[str]:
    lowered = name.casefold()
    hints: list[str] = []
    if any(token in lowered for token in ("일자", "날짜", "date")):
        hints.append("date_like_name")
    if any(token in lowered for token in ("상태", "status")):
        hints.append("status_like_name")
    if any(token in lowered for token in ("주소", "address")):
        hints.append("address_like_name")
    if any(token in lowered for token in ("번호", "코드", "관리번호", " id", "_id")):
        hints.append("identifier_like_name")
    if lowered.strip() in {"x", "y", "좌표정보(x)", "좌표정보(y)"} or "좌표" in lowered:
        hints.append("coordinate_like_name")
    return hints


def detect_encoding(path: Path, sample_bytes: int = 1024 * 1024) -> dict[str, Any]:
    with path.open("rb") as handle:
        sample = handle.read(sample_bytes)
    if sample.startswith(b"\xef\xbb\xbf"):
        return {"selected": "utf-8-sig", "confidence": "bom", "candidates": ["utf-8-sig"]}

    candidates: list[str] = []
    for encoding in ("utf-8", "cp949", "euc-kr"):
        try:
            sample.decode(encoding, errors="strict")
        except UnicodeDecodeError:
            continue
        candidates.append(encoding)

    if not candidates:
        raise ProfileError("sample cannot be decoded as UTF-8, CP949, or EUC-KR")
    if candidates[0] == "utf-8":
        return {"selected": "utf-8", "confidence": "high", "candidates": candidates}
    return {"selected": "cp949", "confidence": "ambiguous_legacy", "candidates": candidates}


def sniff_dialect(sample_text: str) -> dict[str, Any]:
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=",\t|;")
    except csv.Error:
        first_line = sample_text.splitlines()[0] if sample_text.splitlines() else ""
        counts = {delimiter: first_line.count(delimiter) for delimiter in (",", "\t", "|", ";")}
        delimiter, count = max(counts.items(), key=lambda item: item[1])
        if count == 0:
            # The upstream contract is CSV. A one-column CSV contains no visible
            # delimiter, so comma is the deterministic neutral default.
            delimiter = ","
        return {
            "delimiter": delimiter,
            "quotechar": '"',
            "doublequote": True,
            "escapechar": None,
            "detection": "header_fallback",
        }
    # Source files are published as CSV. Python's Sniffer can incorrectly infer
    # doublequote=False from an early sample and then split valid later rows.
    # Detect only the delimiter; keep conventional CSV quoting deterministic.
    return {
        "delimiter": dialect.delimiter,
        "quotechar": '"',
        "doublequote": True,
        "escapechar": None,
        "detection": "sniffer_delimiter_rfc4180_quotes",
    }


def _sample_text(path: Path, encoding: str, sample_chars: int = 128_000) -> str:
    with path.open("r", encoding=encoding, errors="strict", newline="") as handle:
        return handle.read(sample_chars)


def profile_csv(
    path: Path,
    *,
    distinct_cap: int = DEFAULT_DISTINCT_CAP,
    top_n: int = DEFAULT_TOP_N,
    type_probe_cap: int = DEFAULT_TYPE_PROBE_CAP,
) -> dict[str, Any]:
    if distinct_cap < 1:
        raise ProfileError("distinct_cap must be positive")
    if type_probe_cap < 1:
        raise ProfileError("type_probe_cap must be positive")
    encoding_info = detect_encoding(path)
    encoding = encoding_info["selected"]
    sample = _sample_text(path, encoding)
    dialect_info = sniff_dialect(sample)

    accumulators: list[ColumnAccumulator] = []
    parsed_rows = 0
    malformed_rows = 0
    duplicate_headers: list[str] = []

    with path.open("r", encoding=encoding, errors="strict", newline="") as handle:
        reader = csv.reader(
            handle,
            delimiter=dialect_info["delimiter"],
            quotechar=dialect_info["quotechar"],
            doublequote=dialect_info["doublequote"],
            escapechar=dialect_info["escapechar"],
            strict=True,
        )
        try:
            headers = next(reader)
        except StopIteration as exc:
            raise ProfileError("CSV file is empty") from exc
        if not headers:
            raise ProfileError("CSV header is empty")
        seen: set[str] = set()
        for header in headers:
            if header in seen:
                duplicate_headers.append(header)
            seen.add(header)
        accumulators = [
            ColumnAccumulator(
                h,
                distinct_cap=distinct_cap,
                top_n=top_n,
                type_probe_cap=type_probe_cap,
            )
            for h in headers
        ]

        try:
            for row in reader:
                parsed_rows += 1
                if len(row) != len(headers):
                    malformed_rows += 1
                    raise ProfileError(
                        f"row {parsed_rows + 1} has {len(row)} fields; expected {len(headers)}"
                    )
                for accumulator, raw in zip(accumulators, row):
                    accumulator.add(raw)
        except csv.Error as exc:
            raise ProfileError(f"CSV parse error near physical line {reader.line_num}: {exc}") from exc
        except UnicodeDecodeError as exc:
            raise ProfileError(f"full-file strict decode failed for {encoding}: {exc}") from exc

    columns = [acc.finish() for acc in accumulators]
    return {
        "profile_version": 1,
        "format": "CSV",
        "encoding": encoding_info,
        "dialect": dialect_info,
        "header": {
            "column_count": len(accumulators),
            "columns": [acc.name for acc in accumulators],
            "duplicate_headers": sorted(set(duplicate_headers)),
        },
        "rows": {
            "parsed_data_rows": parsed_rows,
            "malformed_rows": malformed_rows,
        },
        "limits": {
            "distinct_cap_per_column": distinct_cap,
            "top_values_per_column": top_n,
            "type_probe_cap_per_non_date_non_coordinate_column": type_probe_cap,
        },
        "columns": columns,
    }


def compare_column_sets(profiles: Iterable[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    entries = list(profiles)
    if not entries:
        raise ProfileError("at least one profile is required")
    by_source = {
        source_key: set(profile["header"]["columns"])
        for source_key, profile in entries
    }
    intersection = set.intersection(*by_source.values())
    union = set.union(*by_source.values())
    return {
        "sources": sorted(by_source),
        "exact_intersection": sorted(intersection),
        "exact_union": sorted(union),
        "category_specific": {
            source_key: sorted(columns - intersection)
            for source_key, columns in sorted(by_source.items())
        },
        "semantic_equivalence": "NOT_ASSESSED_BY_NAME_ONLY",
    }
