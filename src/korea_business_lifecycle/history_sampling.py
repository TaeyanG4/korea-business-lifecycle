from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


AUTHORITY_COLUMN = "\uac1c\ubc29\uc790\uce58\ub2e8\uccb4\ucf54\ub4dc"
DEFAULT_QUANTILES = (0.10, 0.50, 0.90)


@dataclass(frozen=True)
class AuthorityScale:
    authority_code: str
    total_rows: int
    rows_by_source: dict[str, int]


def count_authorities(
    source_paths: Mapping[str, Path],
    *,
    encoding: str = "cp949",
) -> dict[str, dict[str, int]]:
    """Count rows by authority without retaining source-row values."""
    counts: dict[str, dict[str, int]] = {source: {} for source in source_paths}
    for source, path in source_paths.items():
        with path.open("r", encoding=encoding, newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or AUTHORITY_COLUMN not in reader.fieldnames:
                raise ValueError(f"required column missing in {source}: {AUTHORITY_COLUMN}")
            for row in reader:
                code = str(row.get(AUTHORITY_COLUMN) or "").strip()
                if not code:
                    raise ValueError(f"blank authority code encountered in {source}")
                counts[source][code] = counts[source].get(code, 0) + 1
    return counts


def common_authority_scales(
    counts_by_source: Mapping[str, Mapping[str, int]],
    *,
    exclude: Iterable[str] = (),
) -> list[AuthorityScale]:
    """Return authorities present in every source, sorted by combined row scale."""
    sources = tuple(sorted(counts_by_source))
    if not sources:
        return []
    common = set(counts_by_source[sources[0]])
    for source in sources[1:]:
        common &= set(counts_by_source[source])
    common -= set(exclude)

    scales: list[AuthorityScale] = []
    for code in common:
        rows_by_source = {source: int(counts_by_source[source][code]) for source in sources}
        scales.append(
            AuthorityScale(
                authority_code=code,
                total_rows=sum(rows_by_source.values()),
                rows_by_source=rows_by_source,
            )
        )
    return sorted(scales, key=lambda item: (item.total_rows, item.authority_code))


def select_scale_representatives(
    scales: list[AuthorityScale],
    *,
    quantiles: tuple[float, ...] = DEFAULT_QUANTILES,
    include_max: bool = True,
) -> list[tuple[str, AuthorityScale]]:
    """Select deterministic nearest-index quantile representatives plus the maximum."""
    if not scales:
        raise ValueError("at least one authority scale is required")
    selected: list[tuple[str, AuthorityScale]] = []
    last_index = len(scales) - 1
    for quantile in quantiles:
        if not 0 <= quantile <= 1:
            raise ValueError("quantiles must be between 0 and 1")
        index = round(last_index * quantile)
        selected.append((f"q{int(round(quantile * 100)):02d}", scales[index]))
    if include_max:
        selected.append(("max", scales[-1]))

    # Deduplicate without changing the deterministic selection order.
    seen: set[str] = set()
    unique: list[tuple[str, AuthorityScale]] = []
    for label, item in selected:
        if item.authority_code in seen:
            continue
        seen.add(item.authority_code)
        unique.append((label, item))
    return unique

