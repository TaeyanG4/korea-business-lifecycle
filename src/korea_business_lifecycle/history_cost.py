from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any


AUTHORITY_COLUMN = "\uac1c\ubc29\uc790\uce58\ub2e8\uccb4\ucf54\ub4dc"


def estimate_pages_for_current_csv(
    path: Path,
    *,
    encoding: str = "cp949",
    page_size: int = 100,
) -> dict[str, Any]:
    if page_size < 1:
        raise ValueError("page_size must be positive")
    counts: dict[str, int] = {}
    rows = 0
    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or AUTHORITY_COLUMN not in reader.fieldnames:
            raise ValueError(f"required column missing: {AUTHORITY_COLUMN}")
        for row in reader:
            code = str(row.get(AUTHORITY_COLUMN) or "").strip()
            if not code:
                raise ValueError("blank authority code encountered")
            counts[code] = counts.get(code, 0) + 1
            rows += 1
    pages = sum(math.ceil(count / page_size) for count in counts.values())
    return {
        "rows": rows,
        "authority_count": len(counts),
        "page_size": page_size,
        "estimated_pages_per_asof_date": pages,
    }
