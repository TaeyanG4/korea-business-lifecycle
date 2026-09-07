from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.history_sampling import (
    common_authority_scales,
    count_authorities,
    select_scale_representatives,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Select deterministic authority-code scale representatives from three current snapshots. "
            "Only aggregate counts and authority codes are emitted."
        )
    )
    parser.add_argument("general_restaurants", type=Path)
    parser.add_argument("rest_cafes", type=Path)
    parser.add_argument("bakeries", type=Path)
    parser.add_argument("--exclude", action="append", default=[])
    args = parser.parse_args()

    counts = count_authorities(
        {
            "general_restaurants": args.general_restaurants,
            "rest_cafes": args.rest_cafes,
            "bakeries": args.bakeries,
        }
    )
    scales = common_authority_scales(counts, exclude=args.exclude)
    selected = select_scale_representatives(scales)
    payload = {
        "eligible_authorities": len(scales),
        "selection_method": "combined-current-row-scale nearest-index q10/q50/q90 plus max",
        "excluded": sorted(args.exclude),
        "selected": [
            {
                "label": label,
                "authority_code": item.authority_code,
                "total_rows": item.total_rows,
                "rows_by_source": item.rows_by_source,
            }
            for label, item in selected
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

